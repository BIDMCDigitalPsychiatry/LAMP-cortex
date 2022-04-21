import os
import pandas as pd
import numpy as np
import LAMP

def get_os_version(participant_id):
    """ Get OS / Device version from lamp.analytics data.

        Args:
            participant_id: the participant id
        Returns:
            None if there is no analytics data.
            Else, a dictionary with "device_type", "os_version", and "phone_type"
            if they are found in the analytics data
    """
    analytics_data = LAMP.SensorEvent.all_by_participant(participant_id, origin="lamp.analytics")["data"]
    df = [x for x in analytics_data if ("action" in x["data"])]
    df = [x for x in df if ("login" == x['data']["action"])]

    df_2 = [x for x in analytics_data if ("user_agent" in x["data"])]
    df_2 = [x for x in df_2 if 'LAMP-dashboard' in x["data"]["user_agent"]]
    if len(df) > 0:
        device_type = df[0]["data"]["device_type"]
        os_version = None
        phone_type = None
        os_info = df[0]["data"]["user_agent"]
        split = True
        try:
            os_info.split(",")
        except:
            split = False
        if split:
            if ";" in os_info:
                os_info = os_info.split('; ')
                if device_type == 'Android':
                    pass
                else:
                    os_version = os_info[1].split(" ")[1]
                    phone_type = os_info[2].split(" ")[1]
            else:
                os_info = os_info.split(",")
                if device_type == "Android":
                    if len(df_2) > 0:
                        os_version = df_2[0]["data"]["user_agent"].split("(")[1].split(")")[0].split("; ")[1]
                    phone_type = os_info[2]
                else:
                    pass
        return {
            "device_type": device_type,
            "os_version": os_version,
            "phone_type": phone_type
        }
    return None
