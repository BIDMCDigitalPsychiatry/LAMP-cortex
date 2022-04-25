""" Module for interacting with the database """
import time
from pymongo import MongoClient
import pandas as pd
import LAMP

def create_client(client_url,client):
    """ Create a MongoDB client from one of two sources, either an existing
        client or a valid mongo URL
        Args:
            client_url: a valid mongodb URL w/ login info
            client: a valid pymongo client
        Returns:
            A pymongo client.
    """
    if client_url is not None and not isinstance(client_url,str) and client is None:
        raise TypeError("client_url must be a string")
    if isinstance(client_url, str) and client is None:
        client = MongoClient(client_url)
    elif client is not None:
        try:
            client.server_info()
        except:
            raise TypeError("Passed client was not valid or could not connect.")
    elif client is None and client_url is None:
        raise TypeError("Please pass either a valid mongodb URL as a string"
                        + " to the 'client_url' param or a mongodb client to 'client'.")
    return client

def change_parent(target, original_parent, target_parent, db="LAMP",
                  client_url=None, client=None):
    """ Move a target from one parent to another - e.g. a participant from one
        study to another, or a study from one researcher to another.

        Args:
            target: the target's LAMP id
            original_parent: the LAMP id of the original parent of the target
            target_parent: the LAMP id of the parent the target should be moved to
            db: the database this will happen in (usually 'LAMP')
            client_url: a valid mongodb URL w/ login info
            client: a valid pymongo client
        Returns:
            None
    """
    client = create_client(client_url, client)
    def target_category(target, db):
        for coll in client[db].list_collection_names():
            if client[db][coll].find_one({"_id":target}) is not None:
                return coll
        return None

    # Check DB
    if db not in client.list_database_names():
        raise KeyError(f"Invalid database. Choose one of {client.list_database_names()}")
    orig_data = client[db][target_category(target, db)].find_one({"_id":target})
    # Check ID is correct
    if orig_data is None:
        raise KeyError("Couldn't find an id corresponding to the one entered. Please retry")
    # Check ID is associated with the proper parent.
    if orig_data['_parent']!=original_parent:
        raise KeyError(f"{target} is not a child of {original_parent}, "
                       + f"but of {orig_data['_parent']}. Please make sure you"
                       + " are targeting the right ID and retry.")

    orig_category = target_category(original_parent, db)
    t_category = target_category(target_parent, db)

    # If we got here, we can be reasonably sure the user has the correct target
    # Next, let's make sure the target is being switched to the correct level
    if  orig_category != t_category:
        raise TypeError(f"Original and target parents are not the "
                        + f"same category: {orig_category} vs. {t_category}.")

    # Okay, now let's try to switch
    update = { "$set": { "_parent": target_parent } }
    client[db][target_category(target, db)].find_one_and_update({'_id':target},update)
    try:
        orig_name = client[db][orig_category].find_one({"_id":original_parent})['name']
        t_name = client[db][t_category].find_one({"_id":target_parent})['name']
        print (f'{target} updated. Moved {target_category(target, db)} from'
               + f' {orig_category} {orig_name} - ({original_parent}) to'
               + f' {t_category} {t_name} - ({target_parent}).')
    except:
        print (f'{target} updated. Moved {target_category(target, db)} from'
               + f' {orig_category} {original_parent} to {t_category} {target_parent}.')

def restore_activities_manually(study_id, db="LAMP", client_url=None, client=None):
    """ Restore deleted activities to a study
        Args:
            study_id: the study_id to restore activities too
            db: the database this will happen in (usually 'LAMP')
            client_url: a valid mongodb URL w/ login info
            client: a valid pymongo client
        Returns:
            None
    """
    client = create_client(client_url, client)

    if db not in client.list_database_names():
        raise KeyError(f'Could not find the {db} database. '
                       + f'Did you mean one of {client.list_database_names()}')
    if client[db].study.find_one({'_id':study_id}) is None:
        raise KeyError(f"Could not find study {study_id}. Please double check the provided id.")

    deleted_guide = [[x['name'],x['_id']] for x in
                     client.LAMP.activity.find({'_parent':study_id,'_deleted':True})]
    if len(deleted_guide)==0:
        print("No activities are deleted")
        return
    print("The following activities are deleted")
    for idx,val in enumerate(deleted_guide):
        print(f'{idx}:{val[0]}:{val[1]}')

    print("Please input, comma-seperated, the numbers of the activity you"
          + " would like to restore. (e.g. 1,4)")
    undelete = input().split(',')
    for x in undelete:
        try:
            int(x)
        except:
            continue
        if len(deleted_guide)-1<int(x) or int(x)<0:
            continue
        update = { "$set": { "_deleted": False} }
        client.LAMP.activity.find_one_and_update({'_id':deleted_guide[int(x)][1],
                                                  '_parent':study_id},update)
    print("All done. As of now:")
    time.sleep(2)
    deleted_guide = [[x['name'],x['_id']] for x in
                     client.LAMP.activity.find({'_parent':study_id,'_deleted':True})]
    if len(deleted_guide)==0:
        print("No activities are deleted")
        return
    print("The following activities are deleted")
    for idx,val in enumerate(deleted_guide):
        print(f'{idx}:{val[0]}:{val[1]}')

def list_deleted_activities(study_id, db="LAMP", client_url=None, client=None):
    """ List all deleted activities in a study
        Args:
            study_id: the study to examine
            db: the database this will happen in (usually 'LAMP')
            client_url: a valid mongodb URL w/ login info
            client: a valid pymongo client
        Returns:
            A list of objects with id and name keys
    """
    client = create_client(client_url,client)

    if db not in client.list_database_names():
        raise KeyError(f'Could not find the {db} database. '
                       + f'Did you mean one of {client.list_database_names()}')
    if client[db].study.find_one({'_id':study_id}) is None:
        raise KeyError(f"Could not find study {study_id}. Please double check the provided id.")

    return [{'id':x['_id'],'name':x['name']} for x in
            client[db].activity.find({'_parent':study_id,'_deleted':True})]

def restore_activities(activity_id, db="LAMP", client_url=None, client=None,restore_tags=True):
    """ Restore a deleted activity, optionally restoring all tags
        Args:
            activity_id: string or list of the LAMP IDs of the activity(s) to restore
            db: the database this will happen in (usually 'LAMP')
            client_url: a valid mongodb URL w/ login info
            client: a valid pymongo client
            restore_tags: Whether to restore any tags created on a activity
        Returns:
            None
    """
    client = create_client(client_url, client)

    if db not in client.list_database_names():
        raise KeyError(f'Could not find the {db} database. '
                       + f'Did you mean one of {client.list_database_names()}')

    def restore(_id, restore_tags=restore_tags):
        update = { "$set": { "_deleted": False} }
        client[db].activity.find_one_and_update({'_id':_id}, update)
        if restore_tags:
            client[db].tag.update_many({'_parent':_id}, update)

    if not isinstance(activity_id,list):
        activity_id = [activity_id]

    for activity in activity_id:
        db_data = client[db].activity.find_one({'_id':activity})
        if db_data is None:
            print(f"Could not find activity {activity}. Please double check the provided id.")
            continue
        if not db_data['_deleted']:
            print(f"{activity} is already restored.")
            continue
        print(f'Restoring {activity}...')
        restore(str(activity))

def list_deleted_participants(study_id, db="LAMP", client_url=None, client=None):
    """ List all deleted participants in a study
        Args:
            study_id: the study to examine
            db: the database this will happen in (usually 'LAMP')
            client_url: a valid mongodb URL w/ login info
            client: a valid pymongo client
        Returns:
            a list
    """
    client = create_client(client_url, client)

    if db not in client.list_database_names():
        raise KeyError(f'Could not find the {db} database. '
                       + f'Did you mean one of {client.list_database_names()}')
    if client[db].study.find_one({'_id':study_id}) is None:
        raise KeyError(f"Could not find study {study_id}. Please double check the provided id.")

    return [{'id':x['_id']} for x in
            client[db].participant.find({'_parent':study_id,'_deleted':True})]

def restore_participant(participant_id, db="LAMP", client_url=None, client=None, restore_tags=True):
    """ Restore a deleted participant, optionally restoring all tags
        Args:
            participant_id: string or list of the LAMP IDs of the participant(s) to restore
            db: the database this will happen in (usually 'LAMP')
            client_url: a valid mongodb URL w/ login info
            client: a valid pymongo client
            restore_tags: If true, attempt to restore any tags created on a participant.
        Returns:
            None
    """
    client = create_client(client_url, client)

    if db not in client.list_database_names():
        raise KeyError(f'Could not find the {db} database. '
                       + f'Did you mean one of {client.list_database_names()}')

    def restore(_id, restore_tags=restore_tags):
        update = { "$set": { "_deleted": False} }
        client[db].participant.find_one_and_update({'_id':_id},update)
        if restore_tags:
            client[db].tag.update_many({'_parent':_id},update)

    if not isinstance(participant_id,list):
        participant_id = [participant_id]

    for participant in participant_id:
        db_data = client[db].participant.find_one({'_id':participant})
        if db_data is None:
            print(f"Could not find participant {participant}. Please double check the provided id.")
            continue
        elif not db_data['_deleted']:
            print(f"{participant} is already restored.")
            continue
        print(f'Restoring {participant}...')
        restore(str(participant))

def get_survey_names(participant_id, db="LAMP", client_url=None, client=None):
    """ Get the survey names and specs. Use the db to get deleted surveys as well.

        Args:
            participant_id: the participant id
            db: the database this will happen in (usually 'LAMP')
            client_url: a valid mongodb URL w/ login info
            client: a valid pymongo client
        Returns:
            A dataframe containing activity events and their corresponding names
    """
    client = create_client(client_url, client)

    if db not in client.list_database_names():
        raise KeyError(f'Could not find the {db} database. '
                       + f'Did you mean one of {client.list_database_names()}')

    df = LAMP.ActivityEvent.all_by_participant(participant_id, _limit=10000)["data"]
    df = pd.DataFrame(df)
    study_id = LAMP.Type.parent(participant_id)["data"]["Study"]
    survey_ids = {x["_id"]: {"name": x["name"], "spec": x["spec"]}
                  for x in client.LAMP.activity.find({"_parent": study_id})}
    df_names = []
    df_type = []
    for i in range(len(df)):
        if df.loc[i, "activity"] != "undefined":
            df_names.append(survey_ids[df.loc[i, "activity"]]["name"])
            df_type.append(survey_ids[df.loc[i, "activity"]]["spec"])
        else:
            df_names.append(None)
            df_type.append(None)
    df["name"] = df_names
    df["spec"] = df_type
    return df
