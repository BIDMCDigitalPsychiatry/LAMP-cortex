#!/usr/bin/env python3 
from pprint import pprint
from cortex import significant_locations, trips, all_features

pprint(all_features())
for i in range(1583532346000, 1585363115000, 86400000):
    pprint(significant_locations(id="U26468383", start=i, end=i + 86400000))
