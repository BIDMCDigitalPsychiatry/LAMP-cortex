""" Module to compute bluetooth device count from raw feature bluetooth """
import numpy as np
import pandas as pd

from ..feature_types import secondary_feature
from ..raw.bluetooth import bluetooth

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.bluetooth_device_count',
    dependencies=[bluetooth]
)
def bluetooth_device_count(**kwargs):
    """Number of unique bluetooth devices that were nearby.

    Args:
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): Number of unique bluetooth devices that were nearby.
    """
    _bluetooth = pd.DataFrame(bluetooth(**kwargs)['data'])
    _device_count = None
    if len(_bluetooth) > 0:
        _device_count = len(np.unique(_bluetooth['bt_address'], return_counts=False))

    return {'timestamp': kwargs['start'], 'value': _device_count}
