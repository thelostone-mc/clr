import json
import math
import time
import copy
import pandas as pd 



# GRANT_CONTRIBUTIONS = [
#     {
#         'id': '4',
#         'contributions': [
#             { '1': 10.0 },
#             { '2': 5.0 },
#             { '2': 10.0 },
#             { '3': 7.0 },
#             { '5': 5.0 },
#             { '4': -10.0 },
#             { '5': -5.0 },
#             { '5': -5.0 }
#         ]
#     }
# ]

# POSITIVE_CONTRIBUTIONS = [
#     {
#         'id': '4',
#         'contributions': [
#             { '1': 10.0 },
#             { '2': 5.0 },
#             { '2': 10.0 },
#             { '3': 7.0 },
#             { '5': 5.0 }
#         ]
#     },
#     # {
#     #     'id': '5',
#     #     'contributions': [
#     #         { '1': 7.0 },
#     #         { '2': 10.0 },
#     #         { '3': 3.0 },
#     #         { '3': 7.0 }
#     #     ]
#     # }
# ]

# NEGATIVE_CONTRIBUTIONS = [
#     {
#         'id': '4',
#         'contributions': [
#             { '4': -10.0 },
#             { '5': -5.0 },
#             { '5': -5.0 }
#         ]
#     },
#     # {
#     #     'id': '5',
#     #     'contributions': [
#     #         { '7': -15.0 }
#     #     ]
#     # }
# ]

# POSITIVE_CONTRIBUTIONS_1000 = [
#     {
#         'id': '4',
#         'contributions': [
#             {str(x): 1.0} for x in range(1, 1001)
#         ]
#     }
# ]

# POSITIVE_CONTRIBUTIONS_50 = [    
#     {
#         'id': '4',
#         'contributions': [
#             { '1': 25.0 },
#             { '2': 25.0 }
#         ]
#     }
# ]

# POSITIVE_CONTRIBUTIONS_51 = [    
#     {
#         'id': '4',
#         'contributions': [
#             { '1': 25.0 },
#             { '2': 25.0 },
#             { '3': 1.0  }
#         ]
#     }
# ]

# POSITIVE_CONTRIBUTIONS_25 = [    
#     {
#         'id': '4',
#         'contributions': [
#             { '1': 25.0 }
#         ]
#     }
# ]

# NEGATIVE_CONTRIBUTIONS_2 = [    
#     {
#         'id': '4',
#         'contributions': [
#             { '1002': -1.0 },
#             { '1003': -1.0 }
#         ]
#     }
# ]

# NEGATIVE_CONTRIBUTIONS_1 = [    
#     {
#         'id': '4',
#         'contributions': [
#             { '1002': -1.0 }
#         ]
#     }
# ]

# NEGATIVE_CONTRIBUTIONS_1 = [    
#     {
#         'id': '4',
#         'contributions': [
#             { '1002': -1.0 }
#         ]
#     }
# ]



'''
    Data conversion functions, from csv to list of lists

    Args: csv title
    Returns: list of lists of different grant category types 
        [[grant_id (str), user_id (str), contribution_amount (float)]]
'''
def get_data(pos_name, neg_name):
    # read data
    df = pd.read_csv(pos_name)
    dfn = pd.read_csv(neg_name)
    
    # positive categories
    tech_pos = df[df['grant_type'] == 'tech']
    media_pos = df[df['grant_type'] == 'media']
    health_pos = df[df['grant_type'] == 'health']

    # negative categories
    tech_neg = dfn[dfn['grant_type'] == 'tech']
    media_neg = dfn[dfn['grant_type'] == 'media']
    health_neg = dfn[dfn['grant_type'] == 'health']
    
    # get relevant rows
    relevant = ['grant_id', 'contributor_profile_id', 'amount_per_period_usdt']
    tp = tech_pos[relevant]
    mp = media_pos[relevant]
    hp = health_pos[relevant]
    tn = tech_neg[relevant]
    mn = media_neg[relevant]
    hn = health_neg[relevant]
    
    # create list of lists from dataframe
    gtp = tp.T.values.T.tolist()
    gmp = mp.T.values.T.tolist()
    ghp = hp.T.values.T.tolist()
    gtn = tn.T.values.T.tolist()
    gmn = mn.T.values.T.tolist()
    ghn = hn.T.values.T.tolist()

    return gtp, gmp, ghp, gtn, gmn, ghn



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
def calculate_new_clr(aggregated_contributions, pair_totals, threshold=25.0, total_pot=0.0, positive=True):
    bigtot = 0
    totals = []
    if positive:
        for proj, contribz in aggregated_contributions.items():
            tot = 0
            for k1, v1 in contribz.items():
                for k2, v2 in contribz.items():
                    if k2 > k1:  # removes single donations, vitalik's formula
                        tot += ((v1 * v2) ** 0.5) / (pair_totals[k1][k2] / threshold + 1)
            bigtot += tot
            totals.append({'id': proj, 'clr_amount': tot})
    
    if not positive:
        for proj, contribz in aggregated_contributions.items():
            tot = 0
            for k1, v1 in contribz.items():
                for k2, v2 in contribz.items():
                    if k2 > k1:  # removes single donations but adds it in below, vitalik's formula
                        tot += ((v1 * v2) ** 0.5) / (pair_totals[k1][k2] / threshold + 1)
                    if k2 == k1:  # negative vote will count less if single, but will count
                        # tot += ((v1 * v2) ** 0.5) / (pair_totals[k1][k2] / 1 + 1)
                        tot += ((v1 * v2) ** 0.5)
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
def calculate_new_clr_final(totals_pos, totals_neg, total_pot=0.0):
    neg_ids = [y['id'] for y in totals_neg]
    [totals_neg.append({'id': x['id'], 'clr_amount': 0}) for x in totals_pos if x['id'] not in neg_ids]

    pos_ids = [x['id'] for x in totals_pos]
    [totals_pos.append({'id': y['id'], 'clr_amount': 0}) for y in totals_neg if y['id'] not in pos_ids]

    totals = []
    for x in totals_pos:
        for y in totals_neg:
            if x['id'] == y['id'] and (x['clr_amount'] == 0 or x['clr_amount'] < y['clr_amount']):
                totals.append({'id': x['id'], 'clr_amount': 0})
            elif x['id'] == y['id']:
                totals.append({'id': x['id'], 'clr_amount': (math.sqrt(x['clr_amount']) - math.sqrt(y['clr_amount']))**2})

    # find normalization factor
    bigtot = 0
    for x in totals:
        bigtot += x['clr_amount']
    normalization_factor = bigtot / total_pot
    # print(normalization_factor)
    
    # modify totals
    for x in totals:
        x['clr_amount'] = x['clr_amount'] / normalization_factor
    
    # make sure normalization factor works
    bigtot = 0
    for x in totals:
        bigtot += x['clr_amount']
    # print(bigtot)  # should equal total pot
    
    return bigtot, totals



''' 
    Meta function that runs combined positive & negative voting mechanisms, case 2

    Args: none

    Returns: grants clr award amounts
'''
def run_r5_clr(positive_contributions, negative_contributions=None, threshold=25.0, total_pot=0.0):
    start_time = time.time()
    
    # positive
    # p_contributions = translate_data(positive_contributions)
    p_, tp_ = aggregate_contributions(positive_contributions)
    totals_pos_ = calculate_new_clr(p_, tp_, threshold=threshold, total_pot=total_pot)
    
    # negative
    # n_contributions = translate_data(negative_contributions)
    n_, tn_ = aggregate_contributions(negative_contributions)
    totals_neg_ = calculate_new_clr(n_, tn_, threshold=threshold, total_pot=total_pot, positive=False)
    
    # final
    t_ = calculate_new_clr_final(totals_pos_, totals_neg_, total_pot=total_pot)
    print('live calc runtime --- %s seconds ---' % (time.time() - start_time))
    
    return t_, totals_pos_, totals_neg_



if __name__ == '__main__':
    tech_pos, media_pos, health_pos, tech_neg, media_neg, health_neg = get_data('r5_pos.csv', 'r5_neg.csv')

    t, tp, tn = run_r5_clr(tech_pos, tech_neg, total_pot = 101000.0)
    m, mp, mn = run_r5_clr(media_pos, media_neg, total_pot = 50000.0)
    h, hp, hn = run_r5_clr(health_pos, health_neg, total_pot = 100000.0)



    # # testing examples
    # print('all examples run in a 1 grant scenario with 125,000 pot & 25.0 treshhold')

    # print('\n')
    # e2, ep2, en2 = run_r5_clr(POSITIVE_CONTRIBUTIONS_1000, NEGATIVE_CONTRIBUTIONS_2)
    # e1, ep1, en1 = run_r5_clr(POSITIVE_CONTRIBUTIONS_1000, NEGATIVE_CONTRIBUTIONS_1)
    # difference = ((e1[0]['clr_amount'] - ep1[0]['clr_amount']) / e1[0]['clr_amount']) / ((e2[0]['clr_amount'] - ep2[0]['clr_amount']) / e2[0]['clr_amount'])
    # print("1000 people put 1 dai positive votes, then a single person making a 1 dai negative vote should have ~50% as much impact as two people each making a 1 dai negative vote, if it's 4x more, or if the first case gives no decrease at all, then it's wrong")  
    # print(f'Tp for 2 negatives: {ep2}')
    # print(f'Tn for 2 negatives: {en2}')
    # print(f'T for 2 negatives: {e2}')
    # print(f'Tp for 1 negative: {ep1}')
    # print(f'Tn for 1 negative: {en1}')
    # print(f'T for 1 negative: {e1}')
    # print(f'negative impact of 2: {en2}')
    # print(f'negative impact of 1: {en1}')
    # print(f'difference in impact on clr, 1n / 2n: {difference}')

    # print('\n')
    # e25, ep25, en25 = run_r5_clr(POSITIVE_CONTRIBUTIONS_25)
    # print('A donates $25 (positive)')
    # print(f'Tp: {ep25}')
    # print(f'Tn: {en25}')
    # print(f'T: {e25}')

    # print('\n')
    # e251, ep251, en251 = run_r5_clr(POSITIVE_CONTRIBUTIONS_25, NEGATIVE_CONTRIBUTIONS_1)
    # print('A donates $25 (positive), B donates $1 (negative)')
    # print(f'Tp: {ep251}')
    # print(f'Tn: {en251}')
    # print(f'T: {e251}')

    # print('\n')
    # e252, ep252, en252 = run_r5_clr(POSITIVE_CONTRIBUTIONS_25, NEGATIVE_CONTRIBUTIONS_2)
    # print('A donates $25 (positive), B donates $1 (negative), C donates $1 (negative)')
    # print(f'Tp: {ep252}')
    # print(f'Tn: {en252}')
    # print(f'T: {e252}')

    # print('\n')
    # e50, ep50, en50 = run_r5_clr(POSITIVE_CONTRIBUTIONS_50, threshold=999999999999999.0)
    # print('A donates $25 (positive), B donates $25 (positive)')
    # print(f'Tp: {ep50}')
    # print(f'Tn: {en50}')
    # print(f'T: {e50}')

    # print('\n')
    # e51, ep51, en51 = run_r5_clr(POSITIVE_CONTRIBUTIONS_51, threshold=999999999999999.0)
    # print('A donates $25 (positive), B donates $25 (positive), C donates $1 (positive)')
    # print(f'Tp: {ep51}')
    # print(f'Tn: {en51}')
    # print(f'T: {e51}')

    # print('\n')
    # e501, ep501, en501 = run_r5_clr(POSITIVE_CONTRIBUTIONS_50, NEGATIVE_CONTRIBUTIONS_1, threshold=999999999999999.0)
    # print('A donates $25 (positive), B donates $25 (positive), C donates $1 (negative)')
    # print(f'Tp: {ep501}')
    # print(f'Tn: {en501}')
    # print(f'T: {e501}')

    # print('\n')
    # e502, ep502, en502 = run_r5_clr(POSITIVE_CONTRIBUTIONS_50, NEGATIVE_CONTRIBUTIONS_2, threshold=999999999999999.0)
    # print('A donates $25 (positive), B donates $25 (positive), C donates $1 (negative), D donates $1 (negative)')
    # print(f'Tp: {ep502}')
    # print(f'Tn: {en502}')
    # print(f'T: {e502}')

    # print('\n')
    # e511, ep511, en511 = run_r5_clr(POSITIVE_CONTRIBUTIONS_51, NEGATIVE_CONTRIBUTIONS_1, threshold=999999999999999.0)
    # print('A donates $25 (positive), B donates $25 (positive), C donates $1 (positive), D donates $1 (negative)')
    # print(f'Tp: {ep511}')
    # print(f'Tn: {en511}')
    # print(f'T: {e511}')
