""" Module to compute the data quality from raw data """
import pandas as pd
import numpy as np
import os

from ..feature_types import secondary_feature, log
import LAMP

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.data_quality',
    dependencies=[]
)
def data_quality(feature, bin_size=-1, **kwargs):
    """Compute the data quality of raw data over time.
    Args:
        feature (string): The feature to compute quality.
        bin_size (int): How to split up time in ms.
            Default: -1 will result in default settings
            for accelerometer: 1000 (1 Hz, every 1s)
            for gps: 1000 * 10 * 60 (every 10min)
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for
                which the feature is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for
                which the feature is being generated. Required.
    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The percent of the time that there was at least one
                    data point in each time window of size "bin_size".
    """
    LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'),
             os.getenv('LAMP_SERVER_ADDRESS', 'api.lamp.digital'))

    _data_quality = 0
    bin_width = bin_size
    if feature == "accelerometer":
        if bin_size == -1:
            bin_width = 1000
    elif feature == "gps":
        if bin_size == -1:
            bin_width = 1000 * 10 * 60
    else:
        log.info("This feature is not yet supported.")
        return {'timestamp':kwargs['start'], 'value': None}

    # check for the special case where there is no data
    if len(LAMP.SensorEvent.all_by_participant(participant_id=kwargs["id"],
                                               origin="lamp." + feature,
                                               _from=kwargs["start"],
                                               to=kwargs["end"],
                                               _limit=1)['data']) == 0:
        return {'timestamp':kwargs['start'], 'value': 0}

    count = 0
    total_bins = (kwargs["end"] - kwargs["start"]) / bin_width
    for i in range(kwargs["start"], kwargs["end"], bin_width):
        if len(LAMP.SensorEvent.all_by_participant(participant_id=kwargs["id"],
            origin="lamp." + feature, _from=i, to=i + bin_width,
                                        _limit=1)['data']) > 0:
            count += 1
    _data_quality = count / total_bins

    return {'timestamp':kwargs['start'], 'value': _data_quality}
