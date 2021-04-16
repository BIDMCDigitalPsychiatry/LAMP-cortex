from ..feature_types import secondary_feature
from ..raw.calls import calls

import numpy as np

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.call_frequency',
    dependencies=[calls]
)
def call_frequency():
    pass
