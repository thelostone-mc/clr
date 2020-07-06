import json
import math
import time
import copy
import pandas as pd 
from pprint import pprint



'''
    data conversion functions, from csv to list of lists

    args: 
        csv file
            'filename.csv'

    returns: 
        list of lists of grant data x 2
            [[grant_id (str), user_id (str), contribution_amount (float)]]
'''
def get_data(csv_file):
    # read data
    df = pd.read_csv(csv_file)
    
    # round information
    pr = df[df['clr_round'] == 5]
    cr = df[df['clr_round'] == 6]
    
    # get relevant rows
    relevant = ['grant_id', 'contributor_profile_id', 'sms_verification', 'amount_per_period_usdt']
    pr = pr[relevant]
    cr = cr[relevant]

    # create list of lists from dataframe
    prl = pr.T.values.T.tolist()
    crl = cr.T.values.T.tolist()

    return prl, crl



'''
    translates django grant data structure to a list of lists

    args: 
        django grant data structure
            {
                'id': (string) ,
                'contibutions' : [
                    {
                        contributor_profile (str) : contribution_amount (int)
                    }
                ]
            }

    returns: 
        list of lists of grant data 
            [[grant_id (str), user_id (str), verification_status (str), contribution_amount (float)]]
'''
def translate_data(grants_data):
    grants_list = []
    for g in grants_data:
        grant_id = g.get('id')
        for c in g.get('contributions'):
            val = [grant_id] + [list(c.keys())[0], list(c.values())[0]]
            grants_list.append(val)

    return grants_list



'''
    gets list of verified profile ids

    args:
        list of lists of grant data 
        [[grant_id (str), user_id (str), verification_status (str), contribution_amount (float)]]

    returns:
        set list of verified user_ids
            [user_id (str)]

'''
def get_verified_list(grant_contributions):
    verified_list = []
    for proj, user, ver_stat, amount in grant_contributions:
        if ver_stat is True and user not in verified_list:
            verified_list.append(user)

    return verified_list



'''
    aggregates contributions by contributor, and calculates total contributions by unique pairs

    args: 
        list of lists of grant data 
            [[grant_id (str), user_id (str), verification_status (str), contribution_amount (float)]]
        round
            str ('current' or 'previous') only

    returns: 
        aggregated contributions by pair in nested list
            {
                round: {
                    grant_id (str): {
                        user_id (str): aggregated_amount (float)
                    }
                }
            }
'''
def aggregate_contributions(grant_contributions, _round='current'):
    round_dict = {}
    contrib_dict = {}
    for proj, user, ver_stat, amount in grant_contributions:
        if _round == 'previous':
            amount = amount / 3
        if proj not in contrib_dict:
            contrib_dict[proj] = {}
        contrib_dict[proj][user] = contrib_dict[proj].get(user, 0) + amount
    round_dict[_round] = contrib_dict

    return round_dict



'''
    gets pair totals between current round, current and previous round

    args:
        aggregated contributions by pair in nested dict
            {
                round: {
                    grant_id (str): {
                        user_id (str): aggregated_amount (float)
                    }
                }
            }

    returns:
        pair totals between current round, current and previous round
            {user_id (str): {user_id (str): pair_total (float)}}

'''
def get_totals_by_pair(contrib_dict):
    tot_overlap = {}
    
    # start pairwise match
    for proj, contribz in contrib_dict['current'].items():
        for k1, v1 in contribz.items():
            if k1 not in tot_overlap:
                tot_overlap[k1] = {}
            
            # pairwise matches to current round
            for k2, v2 in contribz.items():
                if k2 not in tot_overlap[k1]:
                    tot_overlap[k1][k2] = 0
                tot_overlap[k1][k2] += (v1 * v2) ** 0.5
            
            # # pairwise matches to last round
            # if contrib_dict['previous'].get(proj):
            #     for x1, y1 in contrib_dict['previous'][proj].items():
            #         if x1 not in tot_overlap[k1]:
            #             tot_overlap[k1][x1] = 0
            #         tot_overlap[k1][x1] += (v1 * y1) ** 0.5

    return tot_overlap



'''
    calculates the clr amount at the given threshold and total pot
    args:
        aggregated_contributions by pair in nested dict
            {
                round: {
                    grant_id (str): {
                        user_id (str): aggregated_amount (float)
                    }
                }
            }
        pair_totals
            {user_id (str): {user_id (str): pair_total (float)}}
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
    for proj, contribz in aggregated_contributions['current'].items():
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

            # # pairwise matches to last round
            # if aggregated_contributions['previous'].get(proj):
            #     for x1, y1 in aggregated_contributions['previous'][proj].items():
            #         if x1 != k1 and all(i in verified_list for i in [x1, k1]):
            #             # print(f'x1:{x1}')  # testing
            #             # print(f'k1:{k1}')  # testing
            #             tot += ((v1 * y1) ** 0.5) / (pair_totals[k1][x1] / v_threshold + 1)
            #         else:
            #             tot += ((v1 * y1) ** 0.5) / (pair_totals[k1][x1] / uv_threshold + 1)

        bigtot += tot
        totals.append({'id': proj, 'clr_amount': tot})

    bigtot_normalized_cap = 0
    for t in totals:    
        clr_amount = t['clr_amount']

        # 1. normalize
        if bigtot >= total_pot:
            t['clr_amount'] = ((clr_amount / bigtot) * total_pot) 

        # # 2. cap clr amount
        # if clr_amount >= _cap:
        #     t['clr_amount'] = _cap

        # 3. calculate the total clr to be distributed
        bigtot_normalized_cap += t['clr_amount']

    if bigtot_normalized_cap >= total_pot:
        saturation_point = True

    return totals, bigtot_normalized_cap, saturation_point



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
def run_calcs(csv_file, v_threshold=25.0, uv_threshold=5.0, total_pot=100000.0):
    start_time = time.time()
    prev_round, curr_round = get_data(csv_file)
    vlist = get_verified_list(prev_round + curr_round)
    agg6 = aggregate_contributions(curr_round, 'current')
    agg5 = aggregate_contributions(prev_round, 'previous')
    combinedagg = {**agg5, **agg6}
    ptots= get_totals_by_pair(combinedagg)
    totals, normalized_cap, saturation_point = calculate_clr(combinedagg, ptots, vlist, v_threshold=v_threshold, uv_threshold=uv_threshold, total_pot=total_pot)
    print('live calc runtime --- %s seconds ---' % (time.time() - start_time))
 
    return totals



if __name__ == '__main__':
    # # both r5 & r6, no run_calcs
    # prev_round, curr_round = get_data('r5_r6_contributions.csv')
    # vlist = get_verified_list(prev_round + curr_round)
    # agg6 = aggregate_contributions(curr_round, 'current')
    # agg5 = aggregate_contributions(prev_round, 'previous')
    # combinedagg = {**agg5, **agg6}
    # ptots = get_totals_by_pair(combinedagg)
    # totals, normalized_cap, saturation_point = calculate_clr(combinedagg, ptots, vlist, v_threshold=25.0, uv_threshold=9.0, total_pot=175000.0)

    # both r5 & r6
    t = run_calcs('r5_r6_contributions.csv', v_threshold=25.0, uv_threshold=9.0, total_pot=175000.0)

    # only r6
    prev_round, curr_round = get_data('r5_r6_contributions.csv')
    vlist = get_verified_list(prev_round + curr_round)
    agg6 = aggregate_contributions(curr_round, 'current')
    ptots = get_totals_by_pair(agg6)
    totals, normalized_cap, saturation_point = calculate_clr(agg6, ptots, vlist, v_threshold=25.0, uv_threshold=9.0, total_pot=175000.0)

    # final diffs
    r56 = pd.DataFrame(t)
    r6 = pd.DataFrame(totals)
    rf = r56.merge(r6, how='inner', on='id')
    rf = rf.rename(columns={'clr_amount_x': 'r5_r6_contribs', 'clr_amount_y': 'r6_contribs_only'})
    rf.to_csv('r6_grants_comparison_results.csv')