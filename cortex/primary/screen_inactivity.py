import numpy as np
import pandas as pd

from ..feature_types import primary_feature
from ..raw.screen_state import screen_state

@primary_feature(
    name="cortex.screen_inactivity",
    dependencies=[screen_state],
    attach=False
)
def screen_inactivity(**kwargs):
    """ Returns periods of inactivity from screen_state activity
        params:
        returns:
            Screen inactivity periods, sorted by duration. The timestamp key is the 
    """
    _ss = screen_state(**kwargs)['data']
    if not _ss:
        return {'data': [], 'has_raw_data': 0}
    else:
        if len(_ss) > 0:
            has_raw_data = 1
            _ss = pd.DataFrame.from_dict(list(reversed(_ss)))
            _ss = _ss[_ss.timestamp != _ss.timestamp.shift()]
            _ss = _ss.reset_index(drop=True)
            _ss['screen_inactivity'] = _ss.timestamp - _ss.timestamp.shift()
            _ss = _ss[_ss.value == 0].sort_values(by='screen_inactivity', ascending=False).dropna()
            _ret = list(_ss[["timestamp", "screen_inactivity"]].T.to_dict().values())
        else:
            _ret = []
    
    return {'data': _ret, 'has_raw_data': has_raw_data}