# Python analysis pipeline for the LAMP Platform.

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
pip install LAMP-cortex
```

### Configuration

Ensure your `server_address` is set correctly. If using the default server, it will be `api.lamp.digital`. Keep your `access_key` (sometimes an email address) and `secret_key` (sometimes a password) private and do not share them with others.

```python
import LAMP
LAMP.connect(access_key, secret_key, server_address)
```

