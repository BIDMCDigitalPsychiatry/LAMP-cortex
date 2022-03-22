import sys
import os
import LAMP
from functools import reduce
LAMP.connect(os.getenv('LAMP_ACCESS_KEY'), os.getenv('LAMP_SECRET_KEY'), os.getenv('LAMP_SERVER_ADDRESS'))

# TODO