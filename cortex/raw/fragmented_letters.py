""" Module for raw feature fragmented_letters """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.fragmented_letters",
    dependencies=["lamp.fragmented_letters"]
)
def fragmented_letters(_limit=10000,
             cache=False,
             recursive=True,
             **kwargs):
    return