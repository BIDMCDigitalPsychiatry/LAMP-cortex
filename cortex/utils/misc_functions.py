""" Module for miscellaneous useful functions """
from statistics import mode
import LAMP

def get_os_version(participant_id):
    """ Get OS / Device version from lamp.analytics data.

        Args:
            participant_id: the participant id
        Returns:
            A dictionary with "device_type", "os_version", and "phone_type"
            if they are found in the analytics data. Otherwise, the
            dictionary will be filled with None
        Note: These new login strings are found in data from Spring 2022 or
            later. This will not work with older data.
    """
    analytics_data = LAMP.SensorEvent.all_by_participant(participant_id,
                                        origin="lamp.analytics")["data"]
    login_data = [x["data"]["device_type"] +"; "+ x["data"]['user_agent']
                  for x in analytics_data
                  if (("action" in x["data"]) and (x['data']["action"] == "login") or
                     'type' in x['data'] and x['data']['type'] == 'login') and
                     ("device_type" in x['data'] and x['data']['user_agent'].count(';')>=2) and
                     (x["data"]["device_type"] != 'Dashboard')]
    if len(login_data) > 0:
        user_str = mode(login_data).split("; ")
        if len(user_str) >= 4:
            return {
                "device_type": user_str[0],
                "os_version": user_str[2],
                "phone_type": user_str[3],
            }
    return {"device_type": None, "os_version": None, "phone_type": None}
