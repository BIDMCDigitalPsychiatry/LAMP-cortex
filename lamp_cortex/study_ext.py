import LAMP
import numpy as np
from functools import reduce

class StudyExt():
    """
    """
    def __init__(self, 
                 participants, 
                 domains=None, 
                 df_props={}):

        self.domains = domains
        self.df_props = df_props
        self.init_participants(participants)

    def __iter__(self):
        for participant in self.participants:
            yield participant

    def __len__(self):
        return len(self.participants)

    def __getitem__(self, key):
        return self.participants[key]

    @property
    def participants(self):
        return self._participants

    @property
    def domains(self):
        return self._domains

    @participants.setter
    def participants(self, value):
        self._participants = value

    @domains.setter
    def domains(self, value):
        self._domains = value

    def domain_check(self, domains):
        """
        If domains is passed in, just return it.

        Else, see if domains is set as object attribute
        """
        if domains is None:
            if not hasattr(self, 'domains'):
                raise AttributeError('Domains were not set for cohort and were not provided.')
            domains = self.domains
        return domains

    def init_participants(self, participants):
        """
        Initialize participants in cohorts. Can take either participant objects or participant ids
        """
        self.participants = []
        for participant in participants:

            if isinstance(participant, LAMP.analysis.ParticipantExt):
                #NEED TO CHECK participant MATCHES PROPS
                self.participants.append(participant)

            else:
                self.add_participant(participant)

    def get_participant(self, participant_id):
        """
        Get participant object by id.

        If it doesn't exist, will return None
        """
        for participant in self.participants:
            if participant.id == participant_id:
                return participant

        print('participant not found!')
        return None

    def add_participant(self, participant):
        self.participants.append(LAMP.analysis.ParticipantExt(id = participant, 
                                          domains=self.domains, 
                                          df_props=self.df_props))


    def mean_age(self):
        """
        Return mean, std age of participants in cohort
        """
        participant_ages = [participant.age for participant in self.participants if participant.age is not None]
        if len(participant_ages) == 0:
            return None

        return np.mean(participant_ages)


    def std_age(self):
        """
        Return std age of participants in cohort
        """
        participant_ages = [participant.age for participant in self.participants if participant.age is not None]
        if len(participant_ages) == 0:
            return None

        return np.std(participant_ages)

    def domain_mean(self, domain):
        """
        Find the mean value for particular domain in cohort
        
        :param domain (str): the specified domain
        """
        dom_values = [participant.df[domain].values for participant in self.participants if domain in participant.df.columns]
        if len(dom_values) == 0: return None
        return np.nanmean(np.concatenate(dom_values))

    def domain_stdev(self, domain):
        """
        Find the std value for particular domain in cohort
        
        :param domain (str): the specified domain
        """
        dom_values = [participant.df[domain].values for participant in self.participants if domain in participant.df.columns]
        if len(dom_values) == 0: return None
        return np.nanstd(np.concatenate(dom_values))

    def normalize(self, domains=None, dom_means={}, dom_vars={}, in_sample=False):
        """
        Normalize each domain in cohort so that values have 0 mean/unit variance

        If in_sample is true, then performs within-sample normalization
        
        :param domains (list): domains to use. Default None, in which all availble domains are used
        :param dom_means (dict): the predetermined means of specified domains
        :param dom_vars (dict): the predetermined standard deviations of specified domains
        :param in_sample (bool): Whether to perform within-sample normalization. Default False
        """
        if domains is None and self.domains is None: #Get all features from all particpants
            domains = set(np.concatenate([participant.df.columns.drop(['Date', 'id']) for participant in participants]))

        elif domains is None:
            domains = self.domains
            
        #
        if not in_sample:
            dom_means = {dom: self.domain_mean(dom) for dom in domains if self.domain_mean(dom) is not None and dom not in dom_means}
            dom_vars = {dom: self.domain_stdev(dom) for dom in domains if self.domain_stdev(dom) is not None and dom not in dom_vars}

        for participant in self.participants: participant.normalize(domains=domains, domain_means=dom_means, domain_vars=dom_vars)

    def impute(self, domains=None):
        """
        Impute every participant in cohort.
        
        :param domains (list): domains to use. Default None, in which all availble domains are used
        """
        if domains is None and self.domains is None: #Get all features from all particpants
            domains = set(np.concatenate([participant.df.columns.drop(['Date', 'id']) for participant in participants]))
        elif domains is None:
            domains = self.domains

        for participant in self: participant.impute(domains=domains)

    def bin(self, domains=None, window_size=3):
        """
        Bins all participants in cohort.
        
        :param domains (list): domains to use. Default None, in which all availble domains are used
        :param window_size (int): the number of days to use per bin
        """
        if domains is None and self.domains is None: #Get all features from all particpants
            domains = set(np.concatenate([participant.df.columns.drop(['Date', 'id']) for participant in participants]))
        elif domains is None:
            domains = self.domains

        for participant in self: participant.bin(domains=domains, window_size=window_size)
            
    def impute_bins(self, domains=None):
        """
        Impute bins
        
        :param domains (list): domains to use. Default None, in which all availble domains are used
        """
        if domains is None and self.domains is None: #Get all features from all particpants
            domains = set(np.concatenate([participant.df.columns.drop(['Date', 'id']) for participant in participants]))
        elif domains is None:
            domains = self.domains
            
        for participant in self: participant.impute_bins(domains=domains)
        

    def transition_probabilities(self, domains=None, joint_size=1):
        """
        Get cohort_wide transistion probabilities.

        :param domains (list): domains to use. Default None, in which all availble domains are used
        :param joint_size (int): the number of variables used when calculating the joint probabilities for transistion event. Defaults to 1. 
        """
        if domains is None and self.domains is None: #Get all features from all particpants
            domains = set(np.concatenate([participant.df.columns.drop(['Date', 'id']) for participant in participants]))
        elif domains is None:
            domains = self.domains

        samples_tp = [pro.get_transitions(domains = domains, joint_size = joint_size) for pro in self]

        master_dict = {}

        for sample in samples_tp:
            for cat in sample:
                if cat not in master_dict:
                    master_dict[cat] = {state: sample[cat][state] for state in sample[cat]}
                else: #merge
                    for state in sample[cat]:
                        master_dict[cat][state] = {state2: master_dict[cat][state][state2] + sample[cat][state][state2] for state2 in 
                                                                                                                        master_dict[cat][state]}
        #Convert to probabilities
        trans_dict = {}
        for cat in master_dict:
            trans_dict[cat] = {}
            for state in master_dict[cat]:
                trans_dict[cat][state] = {}
                for state2 in master_dict[cat][state]:
                    if sum(master_dict[cat][state].values()) == 0:
                        trans_dict[cat][state][state2] = None
                    else:
                        trans_dict[cat][state][state2] = float(master_dict[cat][state][state2]) / float(sum(master_dict[cat][state].values()))
        return trans_dict, master_dict

    def domain_bouts(self, domains=None):
        """
        Get elevated/sedated domain bouts in each domain
        
        :param domains (list): domains to use. Default None, in which all availble domains are used
        """
        if domains is None and self.domains is None: #Get all features from all particpants
            domains = set(np.concatenate([participant.df.columns.drop(['Date', 'id']) for participant in participants]))
        elif domains is None:
            domains = self.domains
            
        bout_dict = {}
        for participant in self: 
            participant_bout_dict = participant.domain_bouts(domains=domains)
            for dom in participant_bout_dict:
                if dom not in bout_dict: bout_dict[dom] = participant_bout_dict[dom]
                else: 
                    bout_dict[dom]['low'] += participant_bout_dict[dom]['low']
                    bout_dict[dom]['high'] += participant_bout_dict[dom]['high']
                    bout_dict[dom]['low ends'] += participant_bout_dict[dom]['low ends']
                    bout_dict[dom]['high ends'] += participant_bout_dict[dom]['high ends']

        return bout_dict



