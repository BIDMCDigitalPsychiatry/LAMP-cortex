""" Module for raw feature device_motion """
from ..feature_types import raw_feature

@raw_feature(
    name="lamp.device_motion",
    dependencies=["lamp.device_motion"]
)
def device_motion(_limit=10000,
                  cache=False,
                  recursive=True,
                  **kwargs):
    """ Get all device_motion data bounded by the time interval.

    Args:
        _limit (int): The maximum number of sensor events to query for in a single request
        cache (bool): Indicates whether to save raw data locally in cache dir
        recursive (bool): if True, continue requesting data until all data is
                returned; else just one request

    Returns:
        timestamp (int): The UTC timestamp for the event.
        motion: (dict)
            x: (float) the x-component of motion
            y: (float) the y-component of motion
            z: (float) the z-component of motion
        magnetic: (dict)
            x: (float, units: micro T) the geomagnetic field strength along the
                device's x-axis, where the x-axis runs from left to right,
                across the front screen
            y: (float, units: micro T) the geomagnetic field strength along the
                device's y-axis, where the y-axis runs vertically from the
                bottom to the top of the device's screen
            z: (float, units: micro T) the geomagnetic field strength along the
                device's z-axis, where the z-axis runs towards the outside of the
                device's screen (toward the user)
        altitude: (dict)
            x: (float) the x-component of altitude
            y: (float) the x-component of altitude
            z: (float) the y-component of altitude
        gravity: (dict)
            x: (float) the force of gravity along the device's x-axis, where the
                x-axis runs from left to right, across the front screen
            y: (float) the force of gravity along the device's y-axis, where the
                y-axis runs vertically from the bottom to the top of the device's screen
            z: (float) the force of gravity along the device's z-axis, where the
                z-axis runs towards the outside of the device's screen (toward the user)
        rotation: (dict)
            x: (float) the rotation vector component around the x-axis, which
                points tangentially along the ground, to the East: x * sin(theta/2)
            y: (float) the rotation vector component around the y-axis, which
                points tangent along the ground, to the North: y * sin(theta/2)
            z: (float) the rotation vector component around the z-axis, which
                points towards the sky, perpendicular to the ground: z * sin(theta/2)


    Example:
        {
        'motion': {
          'x': -0.0017750263214111328,
          'y': 0.004897803068161009,
          'z': -0.00017660856246948242
         },
        'magnetic': {
          'x': 3.450927734375,
          'y': 8.881887435913086,
          'z': 53.096649169921875
         },
        'attitude': {
          'x': 2.9586798819128934,
          'y': 0.1373790520467436,
          'z': -0.9628289634642353
         },
        'gravity': {
           'x': 0.18018077313899994,
           'y': -0.13694733381271362,
           'z': 0.9740535616874695
          },
         'rotation': {
           'x': 0.001726057380437851,
           'y': -0.008104033768177036,
           'z': 0.004878027364611627
          }
        },
        }
    """
    return
