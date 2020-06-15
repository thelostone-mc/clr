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
    pr = df[df['clr_round'] == 4]
    cr = df[df['clr_round'] == 5]
    
    # get relevant rows
    relevant = ['grant_id', 'contributor_profile_id', 'amount_per_period_usdt']
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
    ### NEED TO CHANGE TRANSLATE DATA TO OUTPUT VERIFICATION STATUS

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
        if ver_stat == 'verified' and user not in verified_list:
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
            
            # pairwise matches to last round
            if contrib_dict['previous'].get(proj):
                for x1, y1 in contrib_dict['previous'][proj].items():
                    if x1 not in tot_overlap[k1]:
                        tot_overlap[k1][x1] = 0
                    tot_overlap[k1][x1] += (v1 * y1) ** 0.5

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
                    print(f'k1:{k1}')  # testing
                    print(f'k2:{k2}')  # testing
                    tot += ((v1 * v2) ** 0.5) / (pair_totals[k1][k2] / v_threshold + 1)
                else:
                    tot += ((v1 * v2) ** 0.5) / (pair_totals[k1][k2] / uv_threshold + 1)

            # pairwise matches to last round
            if aggregated_contributions['previous'].get(proj):
                for x1, y1 in aggregated_contributions['previous'][proj].items():
                    if x1 != k1 and all(i in verified_list for i in [x1, k1]):
                        print(f'x1:{x1}')  # testing
                        print(f'k1:{k1}')  # testing
                        tot += ((v1 * y1) ** 0.5) / (pair_totals[k1][x1] / v_threshold + 1)
                    else:
                        tot += ((v1 * y1) ** 0.5) / (pair_totals[k1][x1] / uv_threshold + 1)

        bigtot += tot
        totals.append({'id': proj, 'clr_amount': tot})

    if bigtot >= total_pot:
        saturation_point = True

    if saturation_point == True:
        # find normalization factor
        normalization_factor = bigtot / total_pot
        # modify totals
        for result in totals:
            result['clr_amount'] = result['clr_amount'] / normalization_factor

    return totals, saturation_point



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
    # vlist = get_verified_list = prev_round + curr_round
    agg6 = aggregate_contributions(curr_round, 'current')
    agg5 = aggregate_contributions(prev_round, 'previous')
    combinedagg = {**agg5, **agg6}
    ptots= get_totals_by_pair(combinedagg)
    totals = calculate_clr(combinedagg, ptots, vlist, v_threshold=v_threshold, uv_threshold=uv_threshold, total_pot=total_pot)
    print('live calc runtime --- %s seconds ---' % (time.time() - start_time))
 
    return totals



if __name__ == '__main__':
    t = run_calcs('r4_r5_tech_contribs_5004_5678.csv')
    pprint(t)



####################################################

# # TESTING

# # zero contributions to a grant in r6 = 0 match
# # first contribution to a grant in r6 pairwise match 
# #     include all permutations in r6 and between r6 and r5
# #     exclude diagonals (r6a, r6a) and (r6a, r5a)
# #     exclude permutations in r5 1/3 contributors


# # can't combine at this level because it would aggregate prev & curr rounds
# # combined = curr_round_res + prev_round_res

# # separate aggregate contributions otherwise it'll all be counted as one
# # you can't have dual keys in dicts, nest again or list of lists

# # curr_round_res = [x for x in curr_round if x[0] in [490.0, 86.0, 526.0]]
# # curr_round_set = list(set([x[0] for x in curr_round_res]))
# # prev_round_res = [x for x in prev_round if x[0] in curr_round_set]

# agg6 = aggregate_contributions(curr_round_res, 'current')
# agg5 = aggregate_contributions(prev_round_res, 'previous')

# # use nested dictionary
# combinedagg = {**agg5, **agg6}

# # combinedagg smaller version
# combinedaggsmall = {
#     'previous': {
#         86.0: {
#             73120.0: 1.0,
#             72055.0: 5.0,
#             28361.0: 10.0,
#             8899.0: 10
#         }
#         90.0: {
#             100.0: 50.0,
#             200.0: 50.0
#         }
#     },
#     'current': {
#         86.0: {
#             7766.0: 5.0,
#             8899.0: 10
#         },
#         90.0: {
#             1.0: 5.0,
#             10.0: 50.0
#         }
#     }
# }

# # the end result is still by project because of the for loop proj
# # get pairs between current and previous and add on to tot_overlap?
# ptots_curr_small = get_totals_by_pair(combinedaggsmall)

# # calculate clr with current & previous pairs
# res = calculate_clr(combinedagg, ptots_curr, threshold=25.0, total_pot=100000.0)

####################################################

# all unverified

prev = [
    [100.0, 1.0, 'unverified', 9.0],
    [100.0, 2.0, 'unverified', 16.0],
    [100.0, 3.0, 'unverified', 25.0],
    [100.0, 4.0, 'unverified', 36.0],
    [200.0, 5.0, 'unverified', 9.0],
    [200.0, 6.0, 'unverified', 9.0]
]
curr = [
    [100.0, 4.0, 'unverified', 36.0],
    [100.0, 10.0, 'unverified', 49.0],
    [200.0, 9.0, 'unverified', 9.0],
    [200.0, 8.0, 'unverified', 16.0]
]

vlist = get_verified_list(curr + prev)
agg_curr = aggregate_contributions(curr, 'current')
agg_prev = aggregate_contributions(prev, 'previous')
combinedagg = {**agg_prev, **agg_curr}
ptots = get_totals_by_pair(combinedagg)
res = calculate_clr(combinedagg, ptots, vlist, v_threshold=25.0, uv_threshold=5.0, total_pot=10000.0)

'''
([{'id': 100.0, 'clr_amount': 40.546726309791495},
  {'id': 200.0, 'clr_amount': 24.98707633278265}],
 False)
'''

####################################################

# all verified

prev = [
    [100.0, 1.0, 'verified', 9.0],
    [100.0, 2.0, 'verified', 16.0],
    [100.0, 3.0, 'verified', 25.0],
    [100.0, 4.0, 'verified', 36.0],
    [200.0, 5.0, 'verified', 9.0],
    [200.0, 6.0, 'verified', 9.0]
]
curr = [
    [100.0, 4.0, 'verified', 36.0],
    [100.0, 10.0, 'verified', 49.0],
    [200.0, 9.0, 'verified', 9.0],
    [200.0, 8.0, 'verified', 16.0]
]

vlist = get_verified_list(curr + prev)
agg_curr = aggregate_contributions(curr, 'current')
agg_prev = aggregate_contributions(prev, 'previous')
combinedagg = {**agg_prev, **agg_curr}
ptots = get_totals_by_pair(combinedagg)
res = calculate_clr(combinedagg, ptots, vlist, v_threshold=25.0, uv_threshold=5.0, total_pot=10000.0)

'''
k1:4.0
k2:10.0
x1:1.0
k1:4.0
x1:2.0
k1:4.0
x1:3.0
k1:4.0
x1:1.0
k1:10.0
x1:2.0
k1:10.0
x1:3.0
k1:10.0
x1:4.0
k1:10.0
x1:5.0
k1:9.0
x1:6.0
k1:9.0
k1:8.0
k2:9.0
x1:5.0
k1:8.0
x1:6.0
k1:8.0

([{'id': 100.0, 'clr_amount': 90.03969680182165},
  {'id': 200.0, 'clr_amount': 38.11498731327261}],
 False)
'''

####################################################

# mix of verified & unverified

prev = [
    [100.0, 1.0, 'unverified', 9.0],
    [100.0, 2.0, 'verified', 16.0],
    [100.0, 3.0, 'unverified', 25.0],
    [100.0, 4.0, 'verified', 36.0],
    [200.0, 5.0, 'unverified', 9.0],
    [200.0, 6.0, 'verified', 9.0]
]
curr = [
    [100.0, 4.0, 'verified', 36.0],
    [100.0, 10.0, 'unverified', 49.0],
    [200.0, 9.0, 'unverified', 9.0],
    [200.0, 8.0, 'unverified', 16.0]
]

vlist = get_verified_list(curr + prev)
agg_curr = aggregate_contributions(curr, 'current')
agg_prev = aggregate_contributions(prev, 'previous')
combinedagg = {**agg_prev, **agg_curr}
ptots = get_totals_by_pair(combinedagg)
res = calculate_clr(combinedagg, ptots, vlist, v_threshold=25.0, uv_threshold=5.0, total_pot=10000.0)

'''
x1:2.0
k1:4.0

([{'id': 100.0, 'clr_amount': 45.78767200623433},
  {'id': 200.0, 'clr_amount': 24.98707633278265}],
 False)
'''
