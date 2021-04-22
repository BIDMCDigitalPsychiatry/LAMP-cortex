from ..feature_types import secondary_feature
from ..raw.accelerometer import accelerometer

@secondary_feature(
    name='cortex.feature.sedentary_duration',
    dependencies=[accelerometer]
)
def sedentary_duration():
    pass