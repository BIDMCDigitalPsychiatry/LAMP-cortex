""" Module to compute the data quality from raw data """
import pandas as pd
import numpy as np

from ..feature_types import secondary_feature, log
from ..raw.accelerometer import accelerometer
from ..raw.gps import gps

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.data_quality',
    dependencies=[accelerometer, gps]
)
def data_quality(feature, bin_size=-1, **kwargs):
    """ Compute the data quality of raw data over time.

        Args:
            feature - the feature to compute quality as a string
            bin_size - how to split up time in ms
                default: -1 will result in default settings
                    for accelerometer: 1000 (1 Hz, every 1s)
                    for gps: 1000 * 10 * 60 (every 10min)
        Returns:
            the percent of the time that there was at least one
            data point in each time window of size bin_size
        Supported features: accelerometer, gps
    """
    _data_quality = 0
    bin_width = bin_size
    if feature == "accelerometer":
        _data = accelerometer(**kwargs)['data']
        if bin_size == -1:
            bin_width = 1000
    elif feature == "gps":
        _data = gps(**kwargs)['data']
        if bin_size == -1:
            bin_width = 1000 * 10 * 60
    else:
        log.info("This feature is not yet supported.")
        return {'timestamp':kwargs['start'], 'value': None}

    if len(_data) == 0:
        return {'timestamp':kwargs['start'], 'value': 0}

    _data_quality = _get_quality(pd.DataFrame(_data)[["timestamp"]],
                                bin_width,
                                kwargs["start"],
                                kwargs["end"])

    return {'timestamp':kwargs['start'], 'value': _data_quality}

def _get_quality(_data, bin_size, start, end):
    """ Returns the data quality (percent of bins with one or more data points).

        Args:
            _data - the timestamps
            bin_size - the size of the bins in ms
            start - the start time in ms
            end - the end time in ms
        Returns:
            the data quality
    """
    count = 0
    total_bins = (end - start) / bin_size
    for i in range(start, end, bin_size):
        arr = _data["timestamp"].to_numpy()
        if np.any((arr < i + bin_size) & (arr >= i)):
            count += 1
    return count / total_bins
