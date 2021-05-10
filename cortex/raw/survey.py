from ..feature_types import raw_feature, log
import LAMP


@raw_feature(
    name='lamp.survey',
    dependencies=['lamp.survey']
)
def survey(replace_ids=True, limit=2147483647, cache=True, **kwargs):
    """
    Get survey events for participant

    :param replace_ids (bool): TODO.
    :param limit (int): TODO.
    :return timestamp (int): TODO.
    :return survey (str): TODO.
    :return item (str): TODO.
    :return value (any): TODO.
    :return duration (int): TODO.
    """

    # Grab the list of surveys and ALL ActivityEvents which are filtered locally.
    # TODO: Once the API Server supports filtering origin by an ActivitySpec, we won't need this.
    activities = LAMP.Activity.all_by_participant(kwargs['id'])['data']
    surveys = {x['id']: x for x in activities if x['spec'] == 'lamp.survey'}
    raw = LAMP.ActivityEvent.all_by_participant(kwargs['id'],
                                                # origin="lamp.survey" TODO: backend not implemented
                                                _from=kwargs['start'],
                                                to=kwargs['end'],
                                                _limit=limit)['data']

    # Unpack the temporal slices and flatten the dict, including the timestamp and survey.
    # Computing a per-event survey score requires a `groupby('timestamp', 'survey')` call.
    return [
        {
            'timestamp': x['timestamp'],
            'survey': surveys[x['activity']]['name'] if replace_ids else x['activity'],
            **y
        }
        for x in raw
        if 'activity' in x
            and x['activity'] in surveys
            and len(x['temporal_slices']) > 0
        for y in x['temporal_slices']
    ]
