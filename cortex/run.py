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
def generate_id_list():
    pass

#Check type of id
def id_check(id):
    pass



