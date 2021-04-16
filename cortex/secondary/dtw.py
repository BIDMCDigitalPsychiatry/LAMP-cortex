from ..feature_types import secondary_feature
from ..raw.gps import gps
import pandas as pd
import numpy as np
import similaritymeasures


@secondary_feature(
    name='cortex.feature.dtw',
    dependencies=[gps]
)