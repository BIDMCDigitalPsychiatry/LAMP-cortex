""" Module to compute nearby device count from raw feature nearby_device """
import numpy as np
import pandas as pd

from cortex.feature_types import secondary_feature
from cortex.raw.nearby_device import nearby_device

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.nearby_device_count',
    dependencies=[nearby_device]
)
def nearby_device_count(**kwargs):
    """Number of unique nearby devices.

    Args:
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            resolution (int): The resolution (in ms) over which to comptute features.

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): Number of unique bluetooth devices that were nearby.
    """
    _nearby_device = pd.DataFrame(nearby_device(**kwargs)['data'])
    _nearby_device_count = None
    if len(_nearby_device) > 0:
        bluetooth_devices = _nearby_device[_nearby_device['type'] == 'bluetooth']
        _nearby_device_count = len(np.unique(bluetooth_devices['address'], return_counts=False))

    return {'timestamp': kwargs['start'], 'value': _nearby_device_count}
