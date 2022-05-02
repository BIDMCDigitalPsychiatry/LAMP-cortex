""" Module for raw feature survey """
import LAMP
from ..feature_types import raw_feature

MAX_RETURN_SIZE = 10000

@raw_feature(
    name='lamp.survey',
    dependencies=['lamp.survey']
)
def survey(replace_ids=True,
           _limit=10000,
           cache=False,
           recursive=True,
           **kwargs):
    """ Get all survey data bounded by time interval.

        Args:
            _limit (int): The maximum number of sensor events to query for in a single request
            cache (bool): Indicates whether to save raw data locally in cache dir
            recursive (bool): if True, continue requesting data until all data is
                    returned; else just one request

        Returns:
            timestamp (int): The UTC timestamp for the steps event.
            survey (str): The name of the survey.
            item (str): the question string.
            value (str): the participant response.
            type (str): the type if applicable (currently None).
            level (str): the level if applicable (currently None).
            duration (int): the amount spent on the question.

        Example:
            {
                'timestamp': 1650460127684,
                'survey': 'Morning Daily Survey',
                'item': 'What time did you fall asleep last night?',
                'value': '11:30AM',
                'type': None,
                'level': None,
                'duration': 34095
            },
            {
                'timestamp': 1650460127684,
                'survey': 'Morning Daily Survey',
                'item': 'Today I have trouble relaxing.',
                'value': 'Not at all',
                'type': None,
                'level': None,
                'duration': 19401
            },
    """
    # Grab the list of surveys and ALL ActivityEvents which are filtered locally.
    # Once the API Server supports filtering origin by an ActivitySpec, we won't need this.
    activities = LAMP.Activity.all_by_participant(kwargs['id'])['data']
    surveys = {x['id']: x for x in activities if x['spec'] == 'lamp.survey'}

    data_next = []
    raw = LAMP.ActivityEvent.all_by_participant(kwargs['id'],
                                                _from=kwargs['start'],
                                                to=kwargs['end'],
                                                _limit=_limit)['data']
    while (recursive and
           (len(raw) == MAX_RETURN_SIZE or len(data_next) == MAX_RETURN_SIZE)):
        to = raw[-1]['timestamp']
        data_next = LAMP.ActivityEvent.all_by_participant(kwargs['id'],
                                                _from=kwargs['start'],
                                                to=int(to),
                                                _limit=_limit)['data']
        raw += data_next

    def remove_duplicate_activity_events(raw_data):
        # Here, we remove any duplicates from raw data
        # by generating a new list, then replacing the old one.
        raw_minus_duplicates = []
        for _, event in enumerate(raw_data):
            #get a list of all duplicate elements
            duplicates = list(filter(
                lambda x: x['temporal_slices'] == event['temporal_slices'], raw_minus_duplicates))
            #if we find a duplicate
            if not len(duplicates)==0:
                # we choose the event with a longer duration to be the true event
                true_event = (duplicates[0]
                              if duplicates[0]['duration'] >= event['duration'] else event)
                # and replace the old event with the new one
                raw_minus_duplicates[raw_minus_duplicates.index(duplicates[0])] =  true_event
            else:
                # if we didn't find a duplicate, we just add the new event to the growing list
                raw_minus_duplicates.append(event)
        return raw_minus_duplicates

    raw = remove_duplicate_activity_events(raw)

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
