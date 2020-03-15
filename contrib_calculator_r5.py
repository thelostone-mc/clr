import json
import math
import time
import copy
import pandas as pd 



GRANT_CONTRIBUTIONS = [
    {
        'id': '4',
        'contributions': [
            { '1': 10.0 },
            { '2': 5.0 },
            { '2': 10.0 },
            { '3': 7.0 },
            { '5': 5.0 },
            { '4': -10.0 },
            { '5': -5.0 },
            { '5': -5.0 }
        ]
    }
]

POSITIVE_CONTRIBUTIONS = [
    {
        'id': '4',
        'contributions': [
            { '1': 10.0 },
            { '2': 5.0 },
            { '2': 10.0 },
            { '3': 7.0 },
            { '5': 5.0 }
        ]
    },
    # {
    #     'id': '5',
    #     'contributions': [
    #         { '1': 7.0 },
    #         { '2': 10.0 },
    #         { '3': 3.0 },
    #         { '3': 7.0 }
    #     ]
    # }
]

NEGATIVE_CONTRIBUTIONS = [
    {
        'id': '4',
        'contributions': [
            { '4': -10.0 },
            { '5': -5.0 },
            { '5': -5.0 }
        ]
    },
    # {
    #     'id': '5',
    #     'contributions': [
    #         { '7': -15.0 }
    #     ]
    # }
]



'''
    Some data conversion functions.
'''
def get_data():
    # read data
    grants = pd.read_csv('r4_grants_raw_data_new.csv')
    phantom = pd.read_csv('r4_phantom_raw_data_new.csv')
    
    # concat grant and phantom data
    df = pd.concat([grants, phantom], axis=0)
    
    # use tech or media grants only
    tech = df[df['grant_type'] == 'tech']
    media = df[df['grant_type'] == 'media']
    
    # get relevant rows
    relevant = ['grant_id', 'contributor_profile_id', 'amount_per_period_usdt']
    t = tech[relevant]
    m = media[relevant]
    
    # create list of lists from dataframe
    gdt = t.T.values.T.tolist()
    gdm = m.T.values.T.tolist()

    return gdt, gdm



'''
    Helper function that translates existing grant data structure to a list of lists.

    Args:
        {
            'id': (string) ,
            'contibutions' : [
                {
                    contributor_profile (str) : contribution_amount (int)
                }
            ]
        }

    Returns:
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
    Helper function that aggregates contributions by contributor, and then uses the aggregated contributors by contributor and calculates total contributions by unique pairs.

    Args:
        from get_data or translate_data:
        [[grant_id (str), user_id (str), contribution_amount (float)]]

    Returns:
        {grant_id (str): {user_id (str): aggregated_amount (float)}}

        and

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
    Helper function that aggregates contributions by contributor, and then uses the aggregated contributors by contributor and calculates total contributions by unique pairs.

    Args:
        from get_data or translate_data:
        [[grant_id (str), user_id (str), contribution_amount (float)]]

    Returns:
        {grant_id (str): {user_id (str): aggregated_amount (float)}}

        and

        {user_id (str): {user_id (str): pair_total (float)}}
'''
def aggregate_contributions_combined(grant_contributions):
    
    # separate positives and negatives
    contrib_dict_pos = {}
    contrib_dict_neg = {}
    for proj, user, amount in grant_contributions:
        if proj not in contrib_dict_pos and amount > 0:
            contrib_dict_pos[proj] = {}
        if proj not in contrib_dict_neg and amount < 0:
            contrib_dict_neg[proj] = {}
        if amount > 0:
            contrib_dict_pos[proj][user] = contrib_dict_pos[proj].get(user, 0) + amount
        if amount < 0:
            contrib_dict_neg[proj][user] = contrib_dict_neg[proj].get(user, 0) + amount

    # positive
    tot_overlap_pos = {}
    for proj, contribz in contrib_dict_pos.items():
        for k1, v1 in contribz.items():
            if k1 not in tot_overlap_pos:
                tot_overlap_pos[k1] = {}
            for k2, v2 in contribz.items():
                if k2 not in tot_overlap_pos[k1]:
                    tot_overlap_pos[k1][k2] = 0
                tot_overlap_pos[k1][k2] += (v1 * v2) ** 0.5

    # negative
    tot_overlap_neg = {}
    for proj, contribz in contrib_dict_neg.items():
        for k1, v1 in contribz.items():
            if k1 not in tot_overlap_neg:
                tot_overlap_neg[k1] = {}
            for k2, v2 in contribz.items():
                if k2 not in tot_overlap_neg[k1]:
                    tot_overlap_neg[k1][k2] = 0
                tot_overlap_neg[k1][k2] += (v1 * v2) ** 0.5
    return contrib_dict_pos, contrib_dict_neg, tot_overlap_pos, tot_overlap_neg



'''
    Helper function that aggregates contributions by contributor, and then uses the aggregated contributors by contributor and calculates total contributions by unique pairs.

    Args:
        from get_data or translate_data: [[grant_id (str), user_id (str), contribution_amount (float)]]

        grant_id: grant being donated to

        live_user: user doing the donation

    Returns:
        {grant_id (str): {user_id (str): aggregated_amount (float)}}

        and

        {user_id (str): {user_id (str): pair_total (float)}}
'''
def aggregate_contributions_live(grant_contributions, grant_id=86.0, live_user=99999999.0):
    contrib_dict = {}
    for proj, user, amount in grant_contributions:
        if proj not in contrib_dict:
            contrib_dict[proj] = {}
        contrib_dict[proj][user] = contrib_dict[proj].get(user, 0) + amount
    contrib_dict_list = []
    tot_overlap_list = []
    for amount in [0, 1, 10, 100, 1000]:  # multiple case
    # for amount in [0.00001]:  # singular case
        contrib_dict_copy = copy.deepcopy(contrib_dict)
        contrib_dict_copy[grant_id][live_user] = contrib_dict_copy[grant_id].get(live_user, 0) + amount
        contrib_dict_list.append(contrib_dict_copy)
        tot_overlap = {}
        for proj, contribz in contrib_dict_copy.items():
            for k1, v1 in contribz.items():
                if k1 not in tot_overlap:
                    tot_overlap[k1] = {}
                for k2, v2 in contribz.items():
                    if k2 not in tot_overlap[k1]:
                        tot_overlap[k1][k2] = 0
                    tot_overlap[k1][k2] += (v1 * v2) ** 0.5
        tot_overlap_list.append(tot_overlap)
        # print(f'finished predicting {amount}')
    return contrib_dict_list, tot_overlap_list



'''
    Helper function that runs the pairwise clr formula while "binary" searching for the correct threshold.

    Args:
    
        aggregated_contributions: {grant_id (str): {user_id (str): aggregated_amount (float)}}
        pair_totals: {user_id (str): {user_id (str): pair_total (float)}}
        threshold: pairwise coefficient
        total_pot: total pot for the tech or media round, default tech

    Returns:
        totals: total clr award by grant, normalized by the normalization factor
'''
def calculate_new_clr(aggregated_contributions, pair_totals, threshold=25.0, total_pot=125000.0):
    bigtot = 0
    totals = []
    # single donation doesn't get a match
    for proj, contribz in aggregated_contributions.items():
        tot = 0
        for k1, v1 in contribz.items():
            for k2, v2 in contribz.items():
                if k2 > k1:  # remove pairs
                    # # pairwise matching formula
                    # tot += (v1 * v2) ** 0.5 * min(1, threshold / pair_totals[k1][k2])
                    # vitalik's division formula
                    tot += ((v1 * v2) ** 0.5) / (pair_totals[k1][k2] / threshold + 1)
        bigtot += tot
        totals.append({'id': proj, 'clr_amount': tot})
    # find normalization factor
    normalization_factor = bigtot / total_pot
    # modify totals
    for result in totals:
        result['clr_amount'] = result['clr_amount'] / normalization_factor
    # # check total = pot
    # print(f'total pot check = {sum([x["clr_amount"] for x in totals])}')
    return totals 



'''
    Helper function that runs the pairwise clr formula while "binary" searching for the correct threshold.

    Args:
    
        aggregated_contributions: {grant_id (str): {user_id (str): aggregated_amount (float)}}
        pair_totals: {user_id (str): {user_id (str): pair_total (float)}}
        threshold: pairwise coefficient
        total_pot: total pot for the tech or media round, default tech,
        positive: positive or negative contributions

    Returns:
        totals: total clr award by grant, normalized by the normalization factor
'''
def calculate_new_clr_separate(aggregated_contributions, pair_totals, threshold=25.0, total_pot=125000.0, positive=True):
    bigtot = 0
    totals = []
    if positive:  # positive
        for proj, contribz in aggregated_contributions.items():
            tot = 0
            for k1, v1 in contribz.items():
                for k2, v2 in contribz.items():
                    if k2 > k1:  # removes single donations, vitalik's formula
                        tot += ((v1 * v2) ** 0.5) / (pair_totals[k1][k2] / threshold + 1)
            bigtot += tot
            totals.append({'id': proj, 'clr_amount': tot})
    
    if not positive:  # negative
        for proj, contribz in aggregated_contributions.items():
            tot = 0
            for k1, v1 in contribz.items():
                for k2, v2 in contribz.items():
                    if k2 > k1:  # removes single donations but adds it in below, vitalik's formula
                        tot += ((v1 * v2) ** 0.5) / (pair_totals[k1][k2] / threshold + 1)
                    if k2 == k1:  # negative vote will count less if single, but will count
                        tot += ((v1 * v2) ** 0.5) / (pair_totals[k1][k2] / 1 + 1)
            bigtot += tot
            totals.append({'id': proj, 'clr_amount': tot})

    return totals



'''
    Helper function that calculates the final difference between positive and negative totals and finds the final clr reward amount

    Args:
        
        totals_pos: [{'id': proj, 'clr_amount': tot}]
        totals_neg: [{'id': proj, 'clr_amount': tot}]
        total_pot: 125000.0 default

    Returns:
        totals: total clr award by grant pos less neg, normalized by the normalization factor
'''
def calculate_new_clr_separate_final(totals_pos, totals_neg, total_pot=125000.0):
    # calculate final totals
    totals = [{'id': x['id'], 'clr_amount': (math.sqrt(x['clr_amount']) - math.sqrt(y['clr_amount']))**2} for x in totals_pos for y in totals_neg if x['id'] == y['id']]
    for x in totals:
        if x['clr_amount'] < 0:
            x['clr_amount'] = 0
    
    # # find normalization factor
    # bigtot = 0 
    # for x in totals:
    #     bigtot += x['clr_amount']
    # normalization_factor = bigtot / total_pot

    # # modify totals
    # for x in totals:
    #     x['clr_amount'] = x['clr_amount'] / normalization_factor

    return totals



'''
    Helper function that runs the pairwise clr formula while "binary" searching for the correct threshold.

    Args:
    
        aggregated_contributions: {grant_id (str): {user_id (str): aggregated_amount (float)}}
        pair_totals: {user_id (str): {user_id (str): pair_total (float)}}
        threshold: pairwise coefficient
        total_pot: total pot for the tech or media round, default tech

    Returns:
        totals: total clr award by grant, normalized by the normalization factor
'''
def calculate_new_clr_combined(aggregated_contributions_pos, pair_totals_pos, aggregated_contributions_neg, pair_totals_neg, threshold=25.0, total_pot=125000.0):
    
    # positive
    bigtot_pos = 0
    totals_pos = []
    for proj, contribz in aggregated_contributions_pos.items():
        tot = 0
        for k1, v1 in contribz.items():
            for k2, v2 in contribz.items():
                if k2 > k1:  # removes single donations, vitalik's formula
                    tot += ((v1 * v2) ** 0.5) / (pair_totals_pos[k1][k2] / threshold + 1)
        bigtot_pos += tot
        totals_pos.append({'id': proj, 'clr_amount': tot})
    
    # negative
    bigtot_neg = 0
    totals_neg = []
    for proj, contribz in aggregated_contributions_neg.items():
        tot = 0
        for k1, v1 in contribz.items():
            for k2, v2 in contribz.items():
                if k2 > k1:  # removes single donations but adds it in below, vitalik's formula
                    tot += ((v1 * v2) ** 0.5) / (pair_totals_neg[k1][k2] / threshold + 1)
                if k2 == k1:  # negative vote will count less if single, but will count
                    tot += ((v1 * v2) ** 0.5) / (pair_totals_neg[k1][k2] / 1 + 1)
        bigtot_neg += tot
        totals_neg.append({'id': proj, 'clr_amount': tot})

    # calculate final totals
    totals = [{'id': x['id'], 'clr_amount': (math.sqrt(x['clr_amount']) - math.sqrt(y['clr_amount']))**2} for x in totals_pos for y in totals_neg if x['id'] == y['id']]
    for x in totals:
        if x['clr_amount'] < 0:
            x['clr_amount'] = 0
    
    # # find normalization factor
    # bigtot = 0 
    # for x in totals:
    #     bigtot += x['clr_amount']
    # normalization_factor = bigtot / total_pot

    # # modify totals
    # for x in totals:
    #     x['clr_amount'] = x['clr_amount'] / normalization_factor

    return totals_pos, totals_neg, totals



'''
    Runs final tech grants calculations

    Args: none

    Returns: tech grants clr award amounts 
'''
def run_tech_calc():
    start_time = time.time()
    tech, media = get_data()
    aggregated_contributions, pair_totals = aggregate_contributions(tech)
    res = calculate_new_clr(aggregated_contributions, pair_totals)
    print('tech final calc runtime --- %s seconds ---' % (time.time() - start_time))
    return res



'''
    Runs final media grants calculations

    Args: none

    Returns: media grants clr award amounts 
'''
def run_media_calc():
    start_time = time.time()
    tech, media = get_data()
    aggregated_contributions_m, pair_totals_m = aggregate_contributions(media)
    res = calculate_new_clr(aggregated_contributions_m, pair_totals_m, total_pot=75000.0)
    print('media final calc runtime --- %s seconds ---' % (time.time() - start_time))
    return res



'''
    Runs live donation incremental calculations

    Args: live grant being donated to, live user doing the donation

    Returns: live donation incremental clr award amounts 
'''
def run_live_calc(grant_id=86.0, live_user=99999999.0, threshold=25.0, total_pot=125000.0):
    start_time = time.time()
    tech, media = get_data()
    aggregated_contributions_list, pair_totals_list = aggregate_contributions_live(tech, grant_id=grant_id, live_user=live_user)
    clr_curve = []
    for x, y in zip(aggregated_contributions_list, pair_totals_list):
        res = calculate_new_clr(x, y, threshold=threshold, total_pot=total_pot)
        pred = list(filter(lambda x: x['id'] == grant_id, res))[0]['clr_amount']
        clr_curve.append(pred)
    clr_curve = [clr_curve[0]] + [x - clr_curve[0] for x in clr_curve[1:]]
    print('live calc runtime --- %s seconds ---' % (time.time() - start_time))
    print(clr_curve)
    return clr_curve



''' 
    Meta function that runs combined positive & negative voting mechanisms, case 1

    Args: none

    Returns: grants clr award amounts
'''
def run_combined_clr():
    start_time = time.time()
    # combined calculations
    grant_contributions = translate_data(GRANT_CONTRIBUTIONS)
    p, n, tp, tn = aggregate_contributions_combined(grant_contributions)
    totals_pos, totals_neg, t = calculate_new_clr_combined(p, tp, n, tn)
    print('live calc runtime --- %s seconds ---' % (time.time() - start_time))
    return t



''' 
    Meta function that runs combined positive & negative voting mechanisms, case 2

    Args: none

    Returns: grants clr award amounts
'''
def run_separate_clr():
    start_time = time.time()
    # positive
    positive_contributions = translate_data(POSITIVE_CONTRIBUTIONS)
    p_, tp_ = aggregate_contributions(positive_contributions)
    totals_pos_ = calculate_new_clr_separate(p_, tp_)
    # negative
    negative_contributions = translate_data(NEGATIVE_CONTRIBUTIONS)
    n_, tn_ = aggregate_contributions(negative_contributions)
    totals_neg_ = calculate_new_clr_separate(n_, tn_, positive=False)
    # final
    t_ = calculate_new_clr_separate_final(totals_pos, totals_neg)
    print('live calc runtime --- %s seconds ---' % (time.time() - start_time))
    return t_


if __name__ == '__main__':
    # run_tech_calc()
    # run_media_calc()
    # run_live_calc()
    # run_live_calc(99, 63424)
    run_combined_clr()
    run_separate_clr()       
