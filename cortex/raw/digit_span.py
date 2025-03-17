""" Module for raw feature digit_span """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.digit_span",
    dependencies=["lamp.digit_span"]
)
def digit_span(_limit=10000,
             cache=False,
             recursive=True,
             **kwargs):
    return