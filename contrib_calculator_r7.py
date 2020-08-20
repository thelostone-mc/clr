import json
import math
import time
import copy
import pandas as pd 
from pprint import pprint

CLR_PERCENTAGE_DISTRIBUTED = 0



'''
    data conversion function, from csv

    args: 
        csv file
            'filename.csv'

    returns: 
        list of lists of grant data 
            [[grant_id (str), user_id (str), sms_verification (boolean) contribution_amount (float)]]
'''
def get_data_csv(csv_file, grant_type):
    # read data
    df = pd.read_csv(csv_file)

    # select grant type
    df = df[df['grant_type']==grant_type]

    # get relevant rows
    relevant = ['grant_id', 'contributor_profile_id', 'sms_verification', 'amount_per_period_usdt']
    dr = df[relevant]

    # create list of lists from dataframe
    data_list = dr.T.values.T.tolist()

    return data_list



'''
    data conversion function, from django data structure

    args: 
        django grant data structure
            {
                'id' : str,
                'contibutions' : [
                    {
                        'id' : str, 
                        'is_verified' : boolean,
                        'sum_of_each_profiles_contributions' : int
                    }
                ]
            }

    returns: 
        list of lists of grant data 
            [[grant_id (str), user_id (str), sms_verification (boolean) contribution_amount (float)]]
'''
def get_data_django(grants_data):
    grants_list = []
    for g in grants_data:
        grant_id = g.get('id')
        for c in g.get('contributions'):
            profile_id = c.get('id')
            if profile_id:
                val = [grant_id] + [c.get('id')] + [c.get('is_verified')] + [c.get('sum_of_each_profiles_contributions')]
                grants_list.append(val)

    return grants_list



'''
    gets list of verified profile ids

    args:
        list of lists of grant data 
            [[grant_id (str), user_id (str), sms_verification (boolean) contribution_amount (float)]]

    returns:
        set list of verified user_ids
            [user_id (str)]

'''
def get_verified_list(grant_contributions):
    verified_list = []
    for _, user, ver_stat, _ in grant_contributions:
        if ver_stat and user not in verified_list:
            verified_list.append(user)

    return verified_list



'''
    aggregates contributions by contributor, and calculates total contributions by unique pairs

    args: 
        list of lists of grant data 
            [[grant_id (str), user_id (str), sms_verification (boolean) contribution_amount (float)]]

    returns: 
        aggregated contributions by pair in nested list
            {
                grant_id (str): {
                    user_id (str): aggregated_amount (float)
                }
            }
'''
def aggregate_contributions(grant_contributions):
    contrib_dict = {}
    for proj, user, ver_stat, amount in grant_contributions:
        if proj not in contrib_dict:
            contrib_dict[proj] = {}
        contrib_dict[proj][user] = contrib_dict[proj].get(user, 0) + amount

    return contrib_dict



'''
    gets pair totals between current round

    args:
        aggregated contributions by pair in nested dict
            {
                grant_id (str): {
                    user_id (str): aggregated_amount (float)
                }
            }

    returns:
        pair totals between current round
            {user_id (str): {user_id (str): pair_total (float)}}
'''
def get_totals_by_pair(contrib_dict):
    tot_overlap = {}
    
    # start pairwise match
    for proj, contribz in contrib_dict.items():
        for k1, v1 in contribz.items():
            if k1 not in tot_overlap:
                tot_overlap[k1] = {}
            
            # pairwise matches to current round
            for k2, v2 in contribz.items():
                if k2 not in tot_overlap[k1]:
                    tot_overlap[k1][k2] = 0
                tot_overlap[k1][k2] += (v1 * v2) ** 0.5

    return tot_overlap


### START HERE


'''
    calculates the clr amount at the given threshold and total pot
    
    args:
        aggregated_contributions by pair in nested dict
            {
                grant_id (str): {
                    user_id (str): aggregated_amount (float)
                }
            }
        pair_totals
            {user_id (str): {user_id (str): pair_total (float)}}
        verified_list
            [user_id (str)]
        v_threshold (verified threshold)
            float
        uv_threshold (unverified threshold)
            float
        total_pot
            float

    returns:
        total clr award by grant, normalized by the normalization factor
            [{'id': proj, 'clr_amount': tot}]
        saturation point
            boolean
'''
def calculate_clr(aggregated_contributions, pair_totals, verified_list, v_threshold=25.0, uv_threshold=5.0, total_pot=100000.0):
    saturation_point = False
    bigtot = 0
    totals = []
    for proj, contribz in aggregated_contributions.items():
        tot = 0

        # start pairwise matches
        for k1, v1 in contribz.items():

            # pairwise matches to current round
            for k2, v2 in contribz.items():
                if k2 > k1 and all(i in verified_list for i in [k2, k1]):
                    # print(f'k1:{k1}')  # testing
                    # print(f'k2:{k2}')  # testing
                    tot += ((v1 * v2) ** 0.5) / (pair_totals[k1][k2] / v_threshold + 1)
                else:
                    tot += ((v1 * v2) ** 0.5) / (pair_totals[k1][k2] / uv_threshold + 1)

        bigtot += tot
        totals.append({'id': proj, 'clr_amount': tot})

    # # normalization section
    # global CLR_PERCENTAGE_DISTRIBUTED

    # if bigtot >= total_pot: # saturation reached
    #     CLR_PERCENTAGE_DISTRIBUTED = 100
    #     for t in totals:
    #         t['clr_amount'] = ((t['clr_amount'] / bigtot) * total_pot)
    # else:
    #     CLR_PERCENTAGE_DISTRIBUTED = (bigtot / total_pot) * 100

    return totals



''' 
    run all calculation functions

    args: 
        csv_file
            'filename.csv' 
        threshold
            float
        total_pot
            float

    returns: 
        grants clr award amounts
'''
def run_calcs(csv_file, grant_type='tech', v_threshold=25.0, uv_threshold=5.0, total_pot=100000.0, prev_flag=True):
    start_time = time.time()
    curr_round = get_data_csv(csv_file, grant_type)
    vlist = get_verified_list(curr_round)
    agg = aggregate_contributions(curr_round)
    ptots = get_totals_by_pair(agg)
    totals = calculate_clr(agg, ptots, vlist, v_threshold=v_threshold, uv_threshold=uv_threshold, total_pot=total_pot)
    print('live calc runtime --- %s seconds ---' % (time.time() - start_time))
 
    return totals



if __name__ == '__main__':
    curr_round = get_data_csv('r6_contributions.csv', 'tech')
    vlist = get_verified_list(curr_round)
    agg = aggregate_contributions(curr_round)
    ptots = get_totals_by_pair(agg)
    totals = calculate_clr(agg, ptots, vlist, v_threshold=25.0, uv_threshold=5.0, total_pot=20000.0)
    totals_l = calculate_clr(agg, ptots, vlist, v_threshold=8.0, uv_threshold=2.0, total_pot=40000.0)