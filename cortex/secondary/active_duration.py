from ..feature_types import secondary_feature
from ..raw.accelerometer import accelerometer

@secondary_feature(
    name='cortex.feature.active_duration',
    dependencies=[accelerometer]
)