# -*- coding: utf-8 -*-

#Math imports
import numpy as np
from scipy import fft
from scipy.stats import entropy
from scipy.signal import filtfilt
from scipy.signal.filter_design import cheby1
from scipy.signal.fir_filter_design import firwin

from pyunicorn.timeseries import RecurrencePlot

"""
Tools to calculate the features
Code from Jonas Abernot
"""

########################################### FFt features
##code from features_function/fft_features.py
def _get_spectrum(signal):
    return (np.array(np.abs(fft(signal)[1:len(signal)/2]))**2)

def _clip_mean(array, min_i, max_i):
    return  np.mean(array[min_i:max_i])


def power_in_band(signal, sampling_rate, band):
    """
        Compute average power of the signal in the given frequency band, average being done on the integer frequencies.
        :type sampling_rate: frequency , in Hz
        :type band: tuple of frequencies, in Hz
    """
    signal_duration = len(signal) / sampling_rate
    band_int = int(band[0] * signal_duration), int(band[1] * signal_duration)

    spectrum = _get_spectrum(signal)
    return _clip_mean(spectrum, band_int[0], band_int[1])

def power_in_bands(signal, sampling_rate, bands):
    """
        Compute average power of the signal in the given frequency bands, average being done on the integer frequencies.
        :type sampling_rate: frequency , in Hz
        :type bands: list of tuples of frequencies, in Hz
    """
    try: 
        signal_duration = len(signal) / sampling_rate
        bands_int = [ (int(min_band * signal_duration),int(max_band * signal_duration)) for (min_band,max_band) in bands ]

        spectrum = _get_spectrum(signal)

        ret = [ _clip_mean(spectrum, min_band, max_band) for min_band,max_band in bands_int ]
        return tuple(ret)
    except:
        return tuple(np.repeat(np.nan,5))


########################################### Entropy and spectral flatness
##code from features_function/entro.py
############## Utils
def embed_in_dim(signal,dim,skipping_parameter):
    array = np.asarray(signal)
    return np.array([array[i:(i+dim):skipping_parameter] for i in range(len(signal)-dim+1)])

######### Svd
from scipy.sparse.linalg import svds
def svd_entropy(signal,dim,skipping_parameter):
    u,s,v = svds(embed_in_dim(signal,dim,skipping_parameter),k=dim-1)
    return entropy(s)

############### Permutation
from itertools import permutations
from collections import Counter

def permutation_entropy(signal,dim=4,skipping_parameter=1):
    if len(signal):
        embeded_seq = embed_in_dim(signal=signal, dim=dim, skipping_parameter=skipping_parameter)
        permutations_seq = [tuple(np.argsort(seq)) for seq in embeded_seq] #Replace measures by their ranks (not exactly, but equivalent)
        return entropy(Counter(permutations_seq).values())
    else:
        return np.nan

############## Spectral
from scipy import fft

def _get_spectrum(signal): #Get Spectral power density (half of the squared fft)
    return (np.array(np.abs(fft(signal)[1:len(signal)/2]))**2)

from scipy.stats.mstats import gmean

def spectral_flatness(signal):
    if len(signal):
        spectrum = _get_spectrum(signal)
        return gmean(spectrum)/np.mean(spectrum)
    else:
        return np.nan


########################################### RQA
##code from features_function/rqa.py
def decimate_filtfilt(x, q, n=None, ftype='iir', axis=-1):
    """
    Downsample the signal by using a filter.
    By default, an order 8 Chebyshev type I filter is used.  A 30 point FIR
    filter with hamming window is used if `ftype` is 'fir'.
    Parameters
    ----------
    x : ndarray
        The signal to be downsampled, as an N-dimensional array.
    q : int
        The downsampling factor.
    n : int, optional
        The order of the filter (1 less than the length for 'fir').
    ftype : str {'iir', 'fir'}, optional
        The type of the lowpass filter.
    axis : int, optional
        The axis along which to decimate.
    Returns
    -------
    y : ndarray
        The down-sampled signal.
    See also
    --------
    resample
    """
    if not isinstance(q, int):
        raise TypeError("q must be an integer")

    if n is None:
        if ftype == 'fir':
            n = 30
        else:
            n = 8

    if ftype == 'fir':
        b = firwin(n + 1, 1. / q, window='hamming')
        a = 1.
    else:
        b, a = cheby1(n, 0.05, 0.8 / q)

    y = filtfilt(b, a, x, axis=axis)

    sl = [slice(None)] * y.ndim
    sl[axis] = slice(None, None, q)
    return y[sl]

def decimate_and_recurrence(signal, decimate_q=4, dim=1, tau=1, metric='supremum', normalize=False, threshold=0.2):
    if len(signal):
        decimated_signal = decimate_filtfilt(x=signal, q=int(decimate_q))
        rp = RecurrencePlot(decimated_signal, dim=dim, tau=tau, metric=metric,
                     normalize=normalize, threshold=threshold)
        return rp.laminarity(),rp.determinism()
    else:
        return np.nan
