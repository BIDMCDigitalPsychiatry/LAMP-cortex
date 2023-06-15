""" Module to compute step count from raw feature steps """
import pandas as pd
import LAMP
from ..feature_types import secondary_feature
from ..raw.steps import steps
from ..raw.analytics import analytics
LAMP.connect()

MS_IN_A_DAY = 86400000
@secondary_feature(
    name='cortex.feature.step_count',
    dependencies=[steps, analytics]
)
def step_count(data_type = 'health',
               **kwargs):
    """Number of steps.

    Args:
        **kwargs:
            id (string): The participant's LAMP id. Required.
            start (int): The initial UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
            end (int): The last UNIX timestamp (in ms) of the window for which the feature
                is being generated. Required.
        data_type (string): The source from which step_count is summed. Default is 'health',
        which means steps would be summed from the phone's Health app for iPhones, or GoogleFit
        app for Androids. Other options are 'pedometer', which means steps would be summed from
        phone's pedometer, or 'watch' in which case steps would be summed from an Apple watch.

    Returns:
        A dict consisting:
            timestamp (int): The beginning of the window (same as kwargs['start']).
            value (float): The number of steps.
    """
    if data_type not in ['health', 'watch', 'pedometer']:
        raise Exception('Incorrect data type. Datatype must be health, watch, or pedometer.')
    else:
        _steps = steps(**kwargs)['data']
        if len(_steps) == 0:
            return {'timestamp': kwargs['start'], 'value': None}
        _steps = pd.DataFrame(_steps)
        if "type" not in _steps:
            # Older data, not supported
            return {'timestamp': kwargs['start'], 'value': None}
        # old versions of the app, pre steps-fixing update
        old_versions = ['1.0', '1.1', '1.1.1', '1.1.2', '1.1.3', '2021.1.20',
                        '2021.1.21', '2021.6.28', '2021.6.29',
                '2021.7.6', '2021.8.30', '2021.10.10', '2021.10.20',
                        '2022.1.13', '2022.2.28', '2022.3.30',
                '2022.4.13', '2022.4.23', '2.22.5.9', '2022.6.1',
                        '2022.6.9', '2022.6.16', '2022.6.20', '2022.6.29',
                '2022.7.13', '2022.8.4', '2022.8.9', '2022.8.24', '2022.10.6',
                        '2022.10.26', '2022.10.27', '2023.1.20',
                '2023.2.1', '2023.2.23', '2023.4.4', '2023.4.11', '2023.4.19']
        # i will equal 0 if all the data is from the newer version,
        # and 1 if all or some of the data is not from the new version.
        i = 0

        for item in LAMP.SensorEvent.all_by_participant(kwargs['id'],
                                                        origin='lamp.analytics')['data']:
            try:
                version = item['data']['user_agent'].split(';')[0]
                version = version.split(' ')[1]
                if version in old_versions:
                    i = 1
                    pre_change = item['timestamp']
                    post_change_df = _steps[_steps['timestamp'] > pre_change]
                    pre_change_df = _steps[_steps['timestamp'] <= pre_change]
                    break
            except Exception:
                pass

        if i == 0:
            post_change_df = _steps
            pre_change_df = pd.DataFrame()

        if data_type == 'health':
            # Don't need to do pre and post here because these are the same --
            # these values will still be off (too high) in pre_change_df, though.
            # Using data_type == 'pedometer' is more accurate for pre_change_df on Apple phones.
            _steps = _steps.loc[_steps["source"].str.contains('com.', na=False)]

            if len(_steps) == 0:
                return {'timestamp': kwargs['start'], 'value': None}

            else:
                try:
                    # Excluding counts from watch
                    _steps = _steps[_steps['device_model'] != 'Watch']
                except Exception:
                    pass
                return {'timestamp': kwargs['start'],
                    'value': _steps[_steps["type"] == "step_count"]["value"].sum()}

        elif data_type == 'pedometer':
            # Does not work well on Androids - no pedometer.
            _steps2 = pd.DataFrame()
            if len(post_change_df) > 0:
                _post_steps = post_change_df.loc[post_change_df["source"].str.contains('pedometer',
                                                                                       na=False)]
                _post_steps = _post_steps[_post_steps['type'] == 'step_count']
                _steps2 = pd.concat([_steps2, _post_steps])
            if len(pre_change_df) > 0:
                _pre_steps = pre_change_df[(pre_change_df["type"] == "step_count")
                        & (pre_change_df["source"] != 'null')].drop_duplicates()
                _steps2 = pd.concat([_steps2, _pre_steps])
            if len(_steps2) == 0:
                return {'timestamp': kwargs['start'], 'value': None}

            else:
                return {'timestamp': kwargs['start'],
                    'value': _steps2[_steps2["type"] == "step_count"]["value"].max()}

        elif data_type == 'watch':
            if post_change_df.empty:
                return {'timestamp': kwargs['start'], 'value': None}
            else:
                _steps = post_change_df.loc[
                    post_change_df["device_model"].str.contains('Watch', na=False)]
                return {'timestamp': kwargs['start'],'value': _steps[
                    (_steps["type"] == "step_count") & (
                        _steps["device_model"] == "Watch")]["value"].sum()}
