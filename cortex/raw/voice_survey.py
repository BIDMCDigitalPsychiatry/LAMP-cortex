""" Module for raw feature voice_survey """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.voice_survey",
    dependencies=["lamp.voice_survey"]
)
def voice_survey(_limit=10000,
             cache=False,
             recursive=True,
             **kwargs):
    return