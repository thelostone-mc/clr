import json
import math
import time
import copy
import pandas as pd 



'''
    data conversion functions, from csv to list of lists

    args: 
        csv file
            'filename.csv'

    returns: 
        list of lists of grant data 
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
            [[grant_id (str), user_id (str), contribution_amount (float)]]
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
    combine previous round 1/3 contributions with current round contributions

    args: previous round contributions list of lists

    returns: list of lists of combined contributions
        [[grant_id (str), user_id (str), contribution_amount (float)]]

'''
def combine_previous_round(previous, current):
    for x in previous:
        x[2] = x[2]/3.0
    combined = current + previous

    return combined



'''
    aggregates contributions by contributor, and calculates total contributions by unique pairs

    args: 
        list of lists of grant data
            [[grant_id (str), user_id (str), contribution_amount (float)]]

    returns: 
        aggregated contributions by pair & total contributions by pair
            {grant_id (str): {user_id (str): aggregated_amount (float)}}
            {user_id (str): {user_id (str): pair_total (float)}}
'''
def aggregate_contributions(grant_contributions):
    contrib_dict = {}
    for proj, user, amount in grant_contributions:
        if proj not in contrib_dict:
            contrib_dict[proj] = {}
        contrib_dict[proj][user] = contrib_dict[proj].get(user, 0) + amount

    tot_overlap = {}
    for proj, contribz in contrib_dict.items():
        for k1, v1 in contribz.items():
            if k1 not in tot_overlap:
                tot_overlap[k1] = {}
            for k2, v2 in contribz.items():
                if k2 not in tot_overlap[k1]:
                    tot_overlap[k1][k2] = 0
                tot_overlap[k1][k2] += (v1 * v2) ** 0.5

    return contrib_dict, tot_overlap



'''
    calculates the clr amount at the given threshold and total pot

    args:
        aggregated_contributions
            {grant_id (str): {user_id (str): aggregated_amount (float)}}
        pair_totals
            {user_id (str): {user_id (str): pair_total (float)}}
        threshold
            float
        total_pot
            float

    returns:
        total clr award by grant, normalized by the normalization factor
            [{'id': proj, 'clr_amount': tot}]
        saturation point
            boolean
'''
def calculate_clr(aggregated_contributions, pair_totals, threshold=25.0, total_pot=0.0):
    saturation_point = False
    bigtot = 0
    totals = []
    for proj, contribz in aggregated_contributions.items():
        tot = 0
        for k1, v1 in contribz.items():
            for k2, v2 in contribz.items():
                if k2 > k1:  # removes single donations, vitalik's formula
                    tot += ((v1 * v2) ** 0.5) / (pair_totals[k1][k2] / threshold + 1)
        bigtot += tot
        totals.append({'id': proj, 'clr_amount': tot})

    if bigtot >= total_pot:
        saturation_point = True

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
def run_calcs(csv_file, threshold=20.0, total_pot=101000.0):
    prev_round, curr_round = get_data(csv_file)
    
    # combined round
    start_time = time.time()
    comb_round = combine_previous_round(prev_round, curr_round)
    agg_contribs, pair_tots = aggregate_contributions(comb_round)
    totals, sat_pot = calculate_clr(agg_contribs, pair_tots, threshold=threshold, total_pot=total_pot)
    print('live calc runtime --- %s seconds ---' % (time.time() - start_time))

    # curr_round only
    start_time = time.time()
    agg_contribs_c, pair_tots_c = aggregate_contributions(curr_round)
    totals_c, sat_pot_c = calculate_clr(agg_contribs_c, pair_tots_c, threshold=threshold, total_pot=total_pot)
    print('live calc runtime --- %s seconds ---' % (time.time() - start_time))
 
    return totals, totals_c



if __name__ == '__main__':
    t, tc = run_calcs('r4_r5_tech_contribs_5004_5678.csv')
