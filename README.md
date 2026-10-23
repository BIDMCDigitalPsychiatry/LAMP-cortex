# Cortex data analysis pipeline for the LAMP Platform.

## Overview

This API client is used to process and featurize data collected in LAMP. [Visit our documentation](https://docs.lamp.digital/data_science/cortex/getting-started) for more information about using cortex and the LAMP API.

### Jump to:

- [Setting up Cortex](#setting_up_cortex)
- [Cortex example](#example_cortex_query)
- [Binary sensor streams](#binary_sensor_stream)
- [Find a bug?](#bug_report)
- [Developing Cortex](#cortex_dev)
- [Command-line usage](#advanced)

<a name="setting_up_cortex"></a>
# Setting up Cortex

You will need Python 3.8+ and `pip` installed in order to use Cortex. 
  - You may need root permissions, using `sudo`.
  - Alternatively, to install locally, use `pip --user`.
  - If `pip` is not recognized as a command, use `python3 -m pip`.

If you meet the prerequisites, install Cortex:

```sh
pip install git+https://github.com/BIDMCDigitalPsychiatry/LAMP-cortex.git@master
```

If you do not have your environment variables set up you will need to perform the initial server credentials configuraton below:

```python
import os
os.environ['LAMP_ACCESS_KEY'] = 'YOUR_EMAIL_ADDRESS'
os.environ['LAMP_SECRET_KEY'] = 'YOUR_PASSWORD'
os.environ['LAMP_SERVER_ADDRESS'] = 'YOUR_SERVER_ADDRESS'
```

<a name="example_cortex_query"></a>
## Example: Passive data features from Cortex
The primary function of Cortex is to provide a set of features derived from pasive data. Data can be pulled either by calling Cortex functions directly, or by using the `cortex.run()` function to parse multiple participants or features simultaneously. For example, one feature of interest is screen_duration or the time spent with the phone "on".

First, we can pull this data using the Cortex function. Let's say we want to compute the amount of time spent by
participant: "U1234567890" from 11/15/21 (epoch time: 1636952400000) to 11/30/21 (epoch time: 1638248400000) each day (resolution = miliseconds in a day = 86400000):

```python
import cortex
screen_dur = cortex.secondary.screen_duration.screen_duration("U1234567890", start=1636952400000, end=1638248400000, resolution=86400000)
```

The output would look something like this:
```
{'timestamp': 1636952400000,
 'duration': 1296000000,
 'resolution': 86400000,
 'data': [{'timestamp': 1636952400000, 'value': 0.0},
  {'timestamp': 1637038800000, 'value': 0.0},
  {'timestamp': 1637125200000, 'value': 0.0},
  {'timestamp': 1637211600000, 'value': 0.0},
  {'timestamp': 1637298000000, 'value': 0.0},
  {'timestamp': 1637384400000, 'value': 0.0},
  {'timestamp': 1637470800000, 'value': 8425464},
  {'timestamp': 1637557200000, 'value': 54589034},
  {'timestamp': 1637643600000, 'value': 50200716},
  {'timestamp': 1637730000000, 'value': 38500923},
  {'timestamp': 1637816400000, 'value': 38872835},
  {'timestamp': 1637902800000, 'value': 46796405},
  {'timestamp': 1637989200000, 'value': 42115755},
  {'timestamp': 1638075600000, 'value': 44383154}]}
 ```
The 'data' in the dictionary holds the start timestamps (of each day from 11/15/21 to 11/29/21) and the screen duration for each of these days.
 
Second, we could have pulled this same data using the `cortex.run` function. Note that `resolution` is automatically set to a day in `cortex.run`. To invoke `cortex.run`, you must provide a specific ID or a `list` of IDs (only `Researcher`, `Study`, or `Participant` IDs are supported). Then, you specify the behavioral features to generate and extract. Once Cortex finishes running, you will be provided a `dict` where each key is the behavioral feature name, and the value is a dataframe. You can use this dataframe to save your output to a CSV file, for example, or continue data processing and visualization. This function call would look like this:

 ```python
import cortex
screen_dur = cortex.run("U1234567890", ['screen_duration'], start=1636952400000, end=1638248400000)
```
And the output might look like:
```
{'screen_duration':              id           timestamp       value
 0   U1234567890 2021-11-15 05:00:00         0.0
 1   U1234567890 2021-11-16 05:00:00         0.0
 2   U1234567890 2021-11-17 05:00:00         0.0
 3   U1234567890 2021-11-18 05:00:00         0.0
 4   U1234567890 2021-11-19 05:00:00         0.0
 5   U1234567890 2021-11-20 05:00:00         0.0
 6   U1234567890 2021-11-21 05:00:00   8425464.0
 7   U1234567890 2021-11-22 05:00:00  54589034.0
 8   U1234567890 2021-11-23 05:00:00  50200716.0
 9   U1234567890 2021-11-24 05:00:00  38500923.0
 10  U1234567890 2021-11-25 05:00:00  38872835.0
 11  U1234567890 2021-11-26 05:00:00  46796405.0
 12  U1234567890 2021-11-27 05:00:00  42115755.0
 13  U1234567890 2021-11-28 05:00:00  44383154.0}
 ```
The output is the same as above, except the 'data' has been transformed into a Pandas DataFrame. Additionally, the dictionary is indexed by feature -- this way you can add to the list of features processed at once. Finally, a column "id" has been added so that multiple participants can be processed simultaneously. 

<a name="binary_sensor_stream"></a>
## Binary sensor streams: high-rate accelerometer

The high-rate accelerometer sensors (`lamp.accelerometer10hz`, `lamp.accelerometer20hz`,
`lamp.accelerometer50hz`, and `lamp.accelerometer100hz`) don't use `sensor_event`. Devices upload
compressed binary frames to `/participant/{id}/sensor-stream` instead, so you read them with
`cortex.utils.sensor_stream.load_sensor_stream`, not with a `cortex.raw` feature. The wire format
is defined in the LAMP-protocol sensor-stream contract (`docs/sensor-stream.md`).

Install the `binary` extra, which adds the `openzl` (0.3.0) and `zstandard` decoders:

```sh
pip install "LAMP-cortex[binary] @ git+https://github.com/BIDMCDigitalPsychiatry/LAMP-cortex.git@master"
```

The read routes authenticate with an API key, sent as the `x-api-key` header. Set it in
`LAMP_API_KEY`, next to your other credentials. `LAMP_SERVER_ADDRESS` can include a scheme
(`http://localhost:3000`); without one, Cortex uses `https://`.

```python
import os
os.environ['LAMP_API_KEY'] = 'YOUR_API_KEY'

from cortex.utils.sensor_stream import load_sensor_stream
df = load_sensor_stream("U1234567890", "lamp.accelerometer50hz",
                        start=1790000100000, end=1790000400000)
```

The result is a DataFrame with exactly four columns: `timestamp` (int64, Unix epoch ms) and `x`,
`y`, and `z` (float32, m/s², in the Android axis convention: face up on a table reads about
`(0, 0, 9.81)`).

- `start` and `end` are both inclusive.
- Rows are newest first, like `cortex.raw` features. Pass `ascending=True` for oldest first.
- Two rows can share a timestamp, and identical rows inside one frame are kept: they're real
  samples that share a millisecond. A window can hold several frames (after an app restart or a
  late batch); Cortex merges them and drops a row only when an identical row (all four columns
  equal) appears in a different frame, as after a re-sent partial frame.
- Every frame is checked before it's used: its `sha256`, then the contract's decoder checks
  (one OpenZL output, a length that's a multiple of 20 bytes, `sample_count` records, the OpenZL
  format version, and the first and last timestamps). A failed check raises
  `cortex.utils.sensor_stream.SensorStreamError`.

To decode a frame you already have, call `decode_frame(blob, codec, sample_count=...,
codec_format_version=...)`. It returns a NumPy structured array with dtype `ACCEL_DTYPE`.

`lamp.gps1m` (one GPS fix per minute) stays on `sensor_event`, so it's an ordinary raw feature:
`cortex.raw.gps1m.gps1m(id=..., start=..., end=...)`. Its data has the same shape as `lamp.gps`.

The tests for this module (`tests/binary_sensor_tests.py`) run offline against golden vectors
and a fake server:

```sh
LAMP_ACCESS_KEY=x LAMP_SECRET_KEY=x python -m unittest tests/binary_sensor_tests.py
```

<a name="bug_report"></a>
### Find a bug?

Our forum has many answers to common questions. If you find a bug, need help with working with Cortex, or have a suggestion for how the code can be improved please make a post [on the forum] (https://mindlamp.discourse.group/).

<a name="cortex_dev"></a>
### Adding features to Cortex
If you are interesting in developing new features for Cortex, please check out our docs [here] (https://docs.lamp.digital/data_science/cortex/developing_cortex). Note that the unittests in this repository will fail for users outside of BIDMC since you do not have access to our data.

<a name="advanced"></a>
### Advanced Configuration

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
