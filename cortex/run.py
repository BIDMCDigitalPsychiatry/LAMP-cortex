# import raw
# import primary
# import secondary

# from functools import reduce
# import LAMP



# main fxn
def run(id, feature_dict, start, end):
    #1. Check id to generate list of participants (put into "generate_id_list"?)
#     if isinstance(id, str):
#         if len(LAMP.Participant.view(id)['data']) > 0: 
#             id = [id]
#         elif len(LAMP.Study.view(id)['data']) > 0:
#             id = [p['id'] for p in LAMP.Participant.all_by_study(id)['data']]
#         elif len(LAMP.Researcher.view(_id)['data']) > 0:
#             id = reduce(lambda x, y: x + [part['id'] for part in lamp.Participant.all_by_study(y)['data']], 
#                                 studies[1:], 
#                                 [part['id'] for part in lamp.Participant.all_by_study(studies[0])['data']])
            
    #2. Of zipped list (id, feature), execute
    pass
    
    
#Helper function to get list of all participant ids from "id" of type {LAMP.Researcher, LAMP.Study, LAMP.Participant}
def generate_ids(id_set):
    
    """
    This function takes either a single id of type Researcher, Study, or
    Participant,or a list of participant ids, and returns a list of all
    associated participant ids.
    
    Args:
        id_set(str/list) - A Researcher, Study, or Participant id, or a list of Participant ids
    
    Returns:
        list - A list of all associated participant ids
    """
    if isinstance(id_set, str):
        # Use LAMP.Type.parent to determine if this id is associated with
        # a Researcher, Study, or Participant
        parents = LAMP.Type.parent(id_set)["data"]

        # If we find a "Study" parent, this must be a Participant
        if "Study" in parents:
            # We return a list of exactly the one Participant ID.
            return [id_set]

        # If we do NOT find a Study parent, it cannot be a participant,
        # but the presence of a "Researcher" parent means it is a Study.
        elif "Researcher" in parents:
            # We return a list of Participant ids.
            return [val['id'] for val in LAMP.Participant.all_by_study(id_set)['data']]
            pass

        # Researchers have no parents.
        # Therefore, an empty parent dictionary means this id is associated
        # with a Researcher.
        elif not bool(parents):
            # First, we get all study ids associated with this researcher
            study_ids = [val['id'] for val in LAMP.Study.all_by_researcher(id_set)["data"]]
            # Then, we loop through the list of study ids and concatenate all associated
            # participant ids into a single list, which we then return.
            participant_ids = []
            for study_id in study_ids:
                participant_ids += [val['id'] for val in LAMP.Participant.all_by_study(study_id)['data']]
            return participant_ids
        # If we reached this condition, the parent array is not empty, but it does not
        # contain Study OR Researcher parents. This is unlikely but we log the unknown
        # parents and return an empty list.
        else:
            #log.info("Unknown parent"+str(parents))
            return []

    # If a list was passed in, we assume it was a list of participant ids.
    # We then return it unchanged.
    elif isinstance(id_set, list):
        return id_set

#Check type of id
def id_check(id):
    pass



