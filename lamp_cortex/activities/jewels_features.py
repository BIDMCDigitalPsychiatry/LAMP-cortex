import datetime
import pandas as pd
import numpy as np
from functools import reduce
import LAMP
    

def jewels_featurize(results, times, resolution, key):
    assert key in ['lamp.jewels_a', 'lamp.jewels_b']

    if key not in results:
        return pd.DataFrame({'Date':times})

    traildat = results[key]
    stat = pd.DataFrame(traildat.static_data.tolist())
    sel_jewels_data = traildat.join(stat)

    column_labels = traildat.static_data.tolist()

    return sel_jewels_data


def tempfunc(results, date_list, resolution):
    jewels_a, jewels_b = jewels_featurize(results, date_list, resolution=resolution, key='lamp.jewels_a'), jewels_featurize(results, date_list, resolution=resolution, key='lamp.jewels_b')
    df_list = [jewels_a, jewels_b]
    allDfs = reduce(lambda left, right: pd.merge(left, right, on=["Date"], how='left'), df_list)
    
    return allDfs


    
    
