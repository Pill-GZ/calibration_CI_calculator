from collections.abc import Iterable

import numpy as np
import pandas as pd
from scipy.stats import beta
from scipy.optimize import fmin

from constants import _P_VAL_COL, _MULT_ADJ_P_VAL_COL

# from numpy import random
# from matplotlib import pyplot as plt


def ci_ote(n, o, e, cl=0.95):
    """
    Calculates the "confidence interval" for OTE

    Parameters
    ----------
    n : int
        number of observations
    o : float, non-negative
        number of observed defaults
    e : float, positive
        number of expected defaults
    cl : float, optional
        the confidence level, by default 0.95

    Returns
    -------
    numpy.array
        the left and right end points of the "CI for OTE"
    """
    # CI for "true default probability"
    dist = beta(a=(1 / 2 + o), b=(1 / 2 + n - o))
    ci_default_prob = np.array([dist.ppf((1 - cl) / 2), dist.ppf((1 + cl) / 2)])
    # correction at edges
    # ... which statsmodels.stats.proportion.proportion_confint does not do
    if o == 0:
        ci_default_prob[0] = 0
    if n == o:
        ci_default_prob[1] = 1
    # CI for "OTE"
    ci = ci_default_prob * n / e
    return tuple(ci)


def ci_ote_hdi(n, o, e, cl=0.95):
    beta_hdi = calculate_beta_hdi(a=(1 / 2 + o), b=(1 / 2 + (n - o)), p=cl)
    ci = beta_hdi * n / e
    return ci


def calculate_beta_hdi(a, b, p=0.95):
    """
    Find the highest-density interval of a beta distribution.

    Parameters:
    ----------
    a: first parameter of beta distribution, aka \alpha
    b: second parameter of beta distribution, aka \beta
    p: desired probability mass
    """
    # freeze distribution with given arguments
    dist = beta(a=a, b=b)
    # initial guess for HDIlowTailPr
    q = 1.0 - p

    def interval_width(lower_tail_prob):
        return dist.ppf(p + lower_tail_prob) - dist.ppf(lower_tail_prob)

    # find lower_tail_prob that minimizes interval_width
    HDI_CI_left = fmin(interval_width, q, ftol=1e-4, disp=False)[0]
    # return interval as array([low, high])
    return dist.ppf([HDI_CI_left, p + HDI_CI_left])


def calculate_p_value(n, o, e):
    conf_levels = (
        list(np.arange(0.01, 0.99, 0.01))
        + list(np.arange(0.99, 0.999, 0.001))
        + list(np.arange(0.999, 1, 0.0001))
    )
    for cl in conf_levels:
        ci = ci_ote(n, o, e, cl=cl)
        if (ci[0] < 1) and (1 < ci[1]):
            break
    return 1 - cl


def p_val_to_str(p_val):
    """
    Turn a p-value into a string with indicators of statistical significance.
    - Values between 0.05 and 0.01 will be assigned (*)
    - Values between 0.01 and 0.001 will be assigned (**)
    - Values less than 0.001 will be assigned (***)

    Parameters
    ----------
    p_val : float

    Returns
    -------
    str
    """
    sig_level = ""
    if p_val < 0.001:
        p_val_str = "0.001 (<) ***"
    else:
        if p_val < 0.01:
            sig_level = " **"
        elif p_val < 0.05:
            sig_level = " *"
        p_val_str = str(np.round(p_val, 3)) + sig_level
    return p_val_str


def BH_adjusted_pval(p_vals):
    """
    Given an iterable of p-values, calculate the multiple-testing-adjusted p-values.
    We use the standard Benjamini-Hochberg adjustments for FDR control.

    Returns a Pandas series of G-H adjusted p-values.
    """
    if isinstance(p_vals, Iterable):
        p_val_series = pd.Series(p_vals, name=_P_VAL_COL)
    else:
        raise ValueError(
            f"BH adjustment only takes an iterable of p-vals; received {p_vals=}"
        )

    p_val_df = p_val_series.astype(float).to_frame()
    p_val_df["rank"] = p_val_df[_P_VAL_COL].astype(float).rank()
    p_val_df.sort_values(by="rank", ascending=False, inplace=True)
    p_val_df[_MULT_ADJ_P_VAL_COL] = (
        p_val_df[_P_VAL_COL] * len(p_val_df) / p_val_df["rank"]
    ).cummin()
    p_val_df[_MULT_ADJ_P_VAL_COL] = np.minimum(p_val_df[_MULT_ADJ_P_VAL_COL], 1)
    p_val_df.sort_index(inplace=True)
    return p_val_df[_MULT_ADJ_P_VAL_COL]
