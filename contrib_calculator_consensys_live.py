import json
import math
import random
import time
import copy
import numpy as np
import pandas as pd 



'''
    input: csv, grant type, randomization, random seed, number of grants, txns
    output: list of lists data by grant type, number of grants, txns
'''
def get_data(pos_name, _type, _random=False, _seed=9, num_grants=8, txns=5000):
    # read data
    df = pd.read_csv(pos_name)

    # positive categories
    tech_pos = df[df['grant_type'] == _type]

    # add selection of number of grants
    if _random:
        random.seed(_seed)
        # tech_pos_set = list(set(tech_pos['grant_id']))
        selected_ids = random.sample(range(100), num_grants)
    
    # get relevant rows & columns
    rel = ['grant_id', 'contributor_profile_id', 'amount_per_period_usdt']
    tp = tech_pos[rel]
    tp = tp.iloc[0:txns]

    # randomly populate grant ids
    tp['grant_id'] = np.random.choice(selected_ids, size=len(tp))

    # numeric to str
    tp.loc[:, 'grant_id'] = tp.loc[:, 'grant_id'].astype(str)
    
    # create list of lists from dataframe
    gtp = tp.T.values.T.tolist()

    if _random:
        random.seed(_seed)
        gtp = random.sample(gtp, len(gtp))

    return gtp



'''
    input: list of list contribution data, grant ids involved, new user id
    output: aggregate & total overlap by donation prediction for each grant
        {'147': <zip at 0x1d3a19280>,
         '180': <zip at 0x1ded8ddc0>,
         '56': <zip at 0x1ea23e960>,
         '378': <zip at 0x1f5700500>,
         '540': <zip at 0x200bde0a0>,
         '413': <zip at 0x20bf3dbe0>,
         '514': <zip at 0x21747b780>,
         '194': <zip at 0x22293b320>}
'''
def aggregate_contributions(grant_contributions, ids, live_user=999999999.0):

    contrib_dict = {}
    for proj, user, amount in grant_contributions:
        if proj not in contrib_dict:
            contrib_dict[proj] = {}
        contrib_dict[proj][user] = contrib_dict[proj].get(user, 0) + amount

    final_list = {}
    for i in ids:
        contrib_dict_list = []
        tot_overlap_list = []
        for amount in [0, 1, 10, 25, 100]:
            contrib_dict_copy = copy.deepcopy(contrib_dict)
            contrib_dict_copy[i][live_user] = contrib_dict_copy[i].get(live_user, 0) + amount
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
        final_list[i] = zip(contrib_dict_list, tot_overlap_list)
    return final_list



'''
    input: aggregated contributions, pair totals
    output: normalized clr match amount
'''
def calculate_clr(aggregated_contributions, pair_totals, threshold=999999999.0, total_pot=0.0):
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

    # find normalization factor
    normalization_factor = bigtot / total_pot

    # modify totals
    for result in totals:
        result['clr_amount'] = result['clr_amount'] / normalization_factor

    return totals, bigtot



if __name__ == '__main__':
    d = get_data('r5_raw_tech_media_7712.csv', 'tech', _random=True, _seed=9, num_grants=8, txns=200)
    selected_ids = list(set([str(x[0]) for x in d]))

    aggregated_pair_zipped = aggregate_contributions(d, selected_ids)
    clr_curve = {}
    for k, v in aggregated_pair_zipped.items():
        total_list = []
        for x, y in v:
            clr_rewards, _ = calculate_clr(x, y, threshold=999999999.0, total_pot=25000.0)
            total_list.append(clr_rewards)
        clr_curve[k] = total_list    

    final = {}
    for k, v in clr_curve.items():
        pred = []
        for el in v:
            grab = list(filter(lambda x: x['id'] == k, el))[0]['clr_amount']
            pred.append(grab)
        pred = [pred[0]-pred[0]] + [x - pred[0] for x in pred[1:]]
        final[k] = pred

    clr_matches = pd.DataFrame(clr_curve[selected_ids[0]][0])
    clr_predictions = pd.DataFrame(final).set_index(pd.Index([0, 1, 10, 25, 100])).reset_index()
