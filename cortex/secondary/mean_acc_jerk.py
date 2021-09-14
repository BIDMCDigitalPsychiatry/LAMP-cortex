""" Module for computing jerk from raw accelerometer data """
import pandas as pd

from ..feature_types import secondary_feature
from ..primary.acc_jerk import acc_jerk

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.mean_acc_jerk',
    dependencies=[acc_jerk]
)
def mean_acc_jerk(threshold=500, **kwargs):
    """ Computes the jerk of the accelerometer data.
        Jerk is the squared differences in accelerometer.

        params:
            threshold - the max difference between points to be computed in the sum
                (ie if there is too large of a gap in time between accelerometer
                points, jerk has little meaning)
    """
    _acc_jerk = pd.DataFrame(acc_jerk(threshold=threshold,
                                      id=kwargs['id'],
                                      start=kwargs['start'],
                                      end=kwargs['end'])["data"])
    jerk = None
    if len(_acc_jerk) > 0:
        jerk = _acc_jerk["acc_jerk"].mean()
    return {'timestamp': kwargs['start'], 'mean_acc_jerk': jerk}
