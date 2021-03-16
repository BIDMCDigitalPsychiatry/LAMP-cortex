from ..feature_types import primary_feature
from ..raw.accelerometer import accelerometer

@primary_feature(
    name="cortex.survey_scores",
    dependencies=[accelerometer]
)
def survey_scores(**kwargs):
    """
    TODO
    """
    return []
