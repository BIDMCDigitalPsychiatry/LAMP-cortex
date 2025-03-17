""" Module for raw feature trails_b """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.trails_b",
    dependencies=["lamp.trails_b"]
)
def trails_b(_limit=10000,
             cache=False,
             recursive=True,
             **kwargs):
    return