# SAFFRON simulation code with NO Markov lag

import numpy as np
import math


class SAFFRON_async_proc_batch:
    def __init__(self, alpha0, numhyp, lbd, gamma_vec_exponent, markov_lag, async_param):
        self.alpha0 = alpha0 # FDR level
        self.lbd = lbd # candidate threshold lambda

        # Compute the discount gamma sequence and make it sum to 1
        tmp = range(1, 10000)
        self.gamma_vec = np.true_divide(np.ones(len(tmp)),
                np.power(tmp, gamma_vec_exponent))
        self.gamma_vec = self.gamma_vec / np.float(sum(self.gamma_vec))

        self.w0 = (1 - lbd) * self.alpha0/2 # initial wealth, has to satisfy w0 < (1 - lbd)*alpha0
        self.wealth_vec = np.zeros(numhyp + 1) # vector of wealth at every step
        self.wealth_vec[0] = self.w0
        self.alpha = np.zeros(numhyp + 1) # vector of test levels alpha_t at every step
        self.alpha[0:2] = [0, self.gamma_vec[0] * self.w0]
        self.markov_lag = 0
        self.async_param = async_param



    # Computing the number of candidates after each rejection
    def count_candidates(self, last_rej, candidates, timestep):
        ret_val = [];
        for j in range(1,len(last_rej)):
            ret_val = np.append(ret_val, sum(candidates[last_rej[j]+1:timestep - self.markov_lag]))
        return ret_val.astype(int)

    # Running SAFFRON on pvec
    def run_fdr(self, pvec):
        numhyp = len(pvec)
        last_rej = []
        first = 0
        flag = 0
        rej = np.zeros(numhyp + 1)
        candidates = np.zeros(numhyp + 1)
        finish_times = np.zeros(numhyp + 1)
        report = np.zeros(numhyp)

        for k in range(0, numhyp):

            if self.wealth_vec[k] > 0:
                finish_times[k+1] = min(numhyp-1,math.ceil(k + 1 + np.random.exponential(self.async_param)))
                # Get candidate and rejection indicators
                this_alpha = self.alpha[k + 1]
                candidates[(int)(finish_times[k+1])] = candidates[(int)(finish_times[k+1])] + (int)(pvec[k] < self.lbd)
                rej[(int)(finish_times[k+1])] = rej[(int)(finish_times[k+1])] + (int)(pvec[k] < this_alpha)
                report[k] = pvec[k]<this_alpha

                # Check first rejection
                if (rej[k + 1] >= 1):
                    if (first == 0):
                        first = 1
                        flag = 1
                    for t in range((int)(rej[k+1])):
                        last_rej = np.append(last_rej, finish_times[k+1]).astype(int)

                # Update wealth
                # wealth = self.wealth_vec[k] - (1-candidates[k+1])*this_alpha + rej[k + 1] * (1-self.lbd)*(self.alpha0) - rej[k + 1] * flag * self.w0
                # self.wealth_vec[k + 1] = wealth
                self.wealth_vec[k + 1] = 1

                candidates_total = sum(candidates[0:k+2-self.markov_lag])
                zero_gam = self.gamma_vec[k + 1 - (int)(candidates_total)]
                # Update alpha_t
                last_rej_sorted = sorted(last_rej)
                if len(last_rej) > 0:
                    if last_rej_sorted[0]<= (k+1 - self.markov_lag):
                        candidates_after_first = sum(candidates[last_rej_sorted[0]+1:k+1-self.markov_lag])
                        first_gam = self.gamma_vec[k + 1 - last_rej_sorted[0] - (int)(candidates_after_first)]
                    else:
                        first_gam = 0
                    if len(last_rej) >= 2:
                        sum_gam = self.gamma_vec[(k + 1) * np.ones(len(last_rej_sorted)-1, dtype=int) - last_rej_sorted[1:] - self.count_candidates(last_rej_sorted, candidates, k+1)]
                        indic = np.asarray(last_rej_sorted)<=(k+1-self.markov_lag)
                        sum_gam = sum(np.multiply(sum_gam, indic[1:]))
                    else:
                        sum_gam = 0
                    next_alpha = min(self.lbd, zero_gam * self.w0 + ((1-self.lbd)*self.alpha0 - self.w0) * first_gam + (1-self.lbd)*self.alpha0 * sum_gam)
                else:
                    next_alpha = min(self.lbd, zero_gam * self.w0)
                if k < numhyp - 1:
                    self.alpha[k + 2] = next_alpha

                flag = 0

            else:
                break

        self.alpha = self.alpha[1:]
        return report

