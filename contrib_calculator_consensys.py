import json
import math
import random
import time
import copy
import numpy as np
import pandas as pd 
import seaborn as sns
import matplotlib.pyplot as plt



'''
    Data conversion functions, from csv to list of lists

    Args: 
        pos_name = 'csv_title.csv'
        _type = ['tech', 'media', 'health']
        _random = boolean (randomizes chronological list)

    Returns: list of lists of different grant category types 
        [[grant_id (str), user_id (str), contribution_amount (float)]]
'''
def get_data(pos_name, _type, _random=False, _seed=9):
    # read data
    df = pd.read_csv(pos_name)

    # positive categories
    tech_pos = df[df['grant_type'] == _type]
    
    # get relevant rows
    rel = ['grant_id', 'contributor_profile_id', 'amount_per_period_usdt']
    tp = tech_pos[rel]
    tp.loc[:, 'grant_id'] = tp.loc[:, 'grant_id'].astype(str)
    
    # create list of lists from dataframe
    gtp = tp.T.values.T.tolist()

    if _random:
        random.seed(_seed)
        gtp = random.sample(gtp, len(gtp))

    return gtp



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

    Returns:
        totals: total clr award by grant, normalized by the normalization factor
'''
def calculate_clr(aggregated_contributions, pair_totals, threshold=25.0, total_pot=0.0):
    totals = []
    for proj, contribz in aggregated_contributions.items():
        tot = 0
        for k1, v1 in contribz.items():
            for k2, v2 in contribz.items():
                if k2 > k1:  # removes single donations, vitalik's formula
                    tot += ((v1 * v2) ** 0.5) / (pair_totals[k1][k2] / threshold + 1)
        tot1 = 0
        numc = 0
        avg_ca = 0
        for k1, v1 in contribz.items():
            tot1 += v1
            numc += 1
        avg_ca = tot1 / numc

        totals.append({'id': proj, 'clr_amount': tot, 'one_match': tot1, 'num_contrib': numc, 'avg_ca': avg_ca})

    return totals



'''
    Calculates CLR for every incremental transaction, select bin size for data output

    Args:
        _data = local gitcoin grants r5 data
        cap = artificial cap on match amounts, but still counting txns
        bin_size = int
        threshold = threshold
        total_pot = total_pot

    Returns:
        a dataframe with six columns ['id', 'clr_amount', 'one_match', num_contrib', 'avg_ca', 'txns']
'''
def calculate_clr_by_txn(_data, cap=999999999.0, bin_size=10, threshold=25.0, total_pot=0.0):
    res = []
    # for every incremental transaction
    for x in range(0, len(_data)):
        agg_contribs, pair_tots = aggregate_contributions(_data[0: x])
        totals = calculate_clr(agg_contribs, pair_tots, threshold=threshold, total_pot=total_pot)
        
        for _res in totals:
            if _res['clr_amount'] >= cap:
                _res['clr_amount'] = cap
            if _res['one_match'] >= cap:
                _res['one_match'] = cap
            _res['txns'] = x

        # # normalization factor
        # bigtot = 0
        # for _res in totals:
        #     bigtot += x['clr_amount']
        # normalization_factor = bigtot / total_pot

        # # modify totals
        # for x in totals:
        #     x['clr_amount'] = x['clr_amount'] / normalization_factor

        # # make sure normalization factor works
        # bigtot = 0
        # for x in totals:
        #     bigtot += x['clr_amount']
        
        # # how to exclude capped ones out once they hit limit?
        # # subtract capped, then normalize on remaining?
        # # normalize totals

        res.append(totals)

    dict_list = []
    for x in res:
        for y in x:
            dict_list.append(y)
    dict_list = [d for d in dict_list if d['txns'] % bin_size == 0]

    final = pd.DataFrame.from_dict(dict_list)
    final = final.drop_duplicates()

    return final



'''
    Shows us distribution plot of clr match amount on grant by txn time.

    Args: cleaned dataset [id, clr_amount, txns]

    Returns: multiple distribution plots (facetgrid)
'''
def distribution_plot(final_data):
    g = sns.FacetGrid(final_data, col='txns', hue='txns', palette='tab20c', col_wrap=4, height=1.5)
    g.map(sns.barplot, 'id', 'clr_amount')
    for ax in g.axes.flat:
        for label in ax.get_xticklabels():
            label.set_rotation(90)
    # why are some axis labels missing?
    plt.show()



if __name__ == '__main__':

tp = get_data('r5_health.csv', 'health', _random=True, _seed=9)
f = calculate_clr_by_txn(tp, cap=9999999999.0, bin_size=100, threshold=25.0, total_pot=0.0)

f[f['txns'] == 100]
f[f['txns'] == 900]

# distribution_plot(f)

# cap clr
# no cap clr
# cap 1:1
# no cap 1:1
