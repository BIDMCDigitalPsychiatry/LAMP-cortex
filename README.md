# Cortex data analysis pipeline for the LAMP Platform.

## Overview

This API client is used to process and featurize data collected in LAMP. [Visit our documentation for more information about the LAMP Platform.](https://docs.lamp.digital/)

## Installation
### Prerequisites

Python 3.4+ and `pip`. 
  - You may need root permissions, using `sudo`.
  - Alternatively, to install locally, use `pip --user`.
  - If `pip` is not recognized as a command, use `python3 -m pip`.

### Installation

```sh
pip install git+https://github.com/BIDMCDigitalPsychiatry/LAMP-cortex.git@master
```

Alternatively, instead of `pip install`, you may need to use `python3 -m pip install --user`.

### Configuration

Ensure your `server_address` is set correctly. If using the default server, it will be `api.lamp.digital`. Keep your `access_key` (sometimes an email address) and `secret_key` (sometimes a password) private and do not share them with others. While you are able to set these parameters as arguments to the `cortex` executable, it is preferred to set them as session-wide environment variables. You can also run the script from the command line:

```bash
LAMP_SERVER_ADDRESS=api.lamp.digital LAMP_ACCESS_KEY=XXX LAMP_SECRET_KEY=XXX python3 -m \
  cortex significant_locations \
    --id=U26468383 \
    --start=1583532346000 \
    --end=1583618746000 \
    --k_max=9
```

Or another example using the CLI arguments instead of environment variables (and outputting to a file):

```bash
python3 -m \
  cortex --format=csv --server-address=api.lamp.digital --access-key=XXX --secret-key=XXX \
    survey --id=U26468383 --start=1583532346000 --end=1583618746000 \
    2>/dev/null 1>./my_cortex_output.csv
```

### Example

```python
# environment variables must already contain LAMP configuration info
from pprint import pprint
from cortex import all_features, significant_locations, trips
pprint(all_features())
for i in range(1583532346000, 1585363115000, 86400000):
    pprint(significant_locations(id="U26468383", start=i, end=i + 86400000))
```
