""" Module for raw feature funny_memory """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.funny_memory",
    dependencies=["lamp.funny_memory"]
)
def funny_memory(_limit=10000,
             cache=False,
             recursive=True,
             **kwargs):
    return