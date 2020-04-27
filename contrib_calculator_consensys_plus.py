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
def calculate_clr_by_txn(_data, threshold=25.0, upper_pot=30000, pot_by=10000, cap_by=5, txns=1100, bin_size=100):
    poss_total_pots = [x for x in range(10000, upper_pot, pot_by)]
    poss_caps = [(x / 100) for x in range(5, 60, cap_by)] + [99999999]
    res = []
    for total_pot in poss_total_pots:
        for cap in poss_caps:
            # for every incremental transaction, calculate clr
            for x in range(0, txns + bin_size, bin_size):
                agg_contribs, pair_tots = aggregate_contributions(_data[0: x])
                totals = calculate_clr(agg_contribs, pair_tots, threshold=threshold, total_pot=total_pot)

                # add txn, pot, caps identifier
                for _res in totals:
                    _res['txns'] = x
                    _res['total_pot'] = total_pot 
                    _res['cap_pct'] = cap
                    _res['cap_amt'] = cap * total_pot

                # # post normalization factor (locks cap)
                # # for earlier iterations normalizing may cause > cap values
                # _temp_total = copy.deepcopy(total_pot)
                # for _res in totals:
                #     if _res['clr_amount'] == cap:
                #         _temp_total -= cap
                # _bigtot = 0 
                # for _res in totals:
                #     if _res['clr_amount'] < cap:
                #         _bigtot += _res['clr_amount']
                #     _normalization_factor = _bigtot / _temp_total

                # # modify totals using post normalization factor
                # for _res in totals:
                #     if _res['clr_amount'] < cap and _normalization_factor != 0:
                #         _res['clr_amount'] = _res['clr_amount'] / _normalization_factor

                # find normalization factor
                bigtot = 0
                for _res in totals:
                    bigtot += _res['clr_amount']
                normalization_factor = bigtot / total_pot

                # modify totals
                for _res in totals:
                    if normalization_factor !=0:
                        _res['clr_amount'] = _res['clr_amount'] / normalization_factor

                # for every clr result, implement cap if necessary
                for _res in totals:
                    if _res['clr_amount'] >= cap * total_pot:
                        _res['clr_amount'] = cap * total_pot
                    if _res['one_match'] >= cap * total_pot:
                        _res['one_match'] = cap * total_pot

                # fill in missing data
                all_ids = set([h[0] for h in _data])
                # for _res in totals:
                _temp_ids = [y['id'] for y in totals]
                _missing_ids = list(set(all_ids) - set(_temp_ids))
                for z in _missing_ids:
                    totals.append({'id': z, 'clr_amount': 0, 'one_match': 0, 'num_contrib': 0, 'avg_ca': 0, 'txns': x, 'total_pot': total_pot, 'cap_pct': cap, 'cap_amt': cap * total_pot})

                res.append(totals)

    # flatten list
    dict_list = []
    for x in res:
        for y in x:
            dict_list.append(y)
    # dict_list = [d for d in dict_list if d['txns'] % bin_size == 0 and d['txns'] != 0]

    final = pd.DataFrame.from_dict(dict_list)
    final = final.drop_duplicates()

    return final



'''
    Shows us distribution plot of clr match amount on grant by txn time.

    Args: 
        fdata = cleaned dataset [id, clr_amount, txns]
        y_value = (clr_amount or one_match)
        _title = (title of graph)

    Returns: multiple distribution plots (facetgrid)
'''
def distribution_plot(fdata, pot, cap, y_val):
    g = sns.FacetGrid(fdata[(fdata['total_pot']==pot) & (fdata['cap_pct']==cap/100)], col='txns', palette='tab20c', col_wrap=2, height=2, sharey=True, sharex=True)
    g.map(sns.barplot, 'id', y_val)
    for ax in g.axes.flat:
        _ = ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    g.fig.suptitle(f'total_pot_{pot}_cap_{cap}_{y_val}')
    # plt.show()
    g.fig.set_size_inches(20, 10)
    g.savefig(f'total_pot_{pot}_cap_{cap}_{y_val}', bbox_inches='tight')



if __name__ == '__main__':


    distribution_plot(ff, 20000, 10, 'clr_amount')
    distribution_plot(ff, 20000, 10, 'one_match')
    distribution_plot(ff, 20000, 9999999900, 'clr_amount')
    distribution_plot(ff, 20000, 9999999900, 'one_match')
    distribution_plot(ff, 20000, 9999999900, 'num_contrib')
    distribution_plot(ff, 20000, 9999999900, 'avg_ca')



    # # playing around with bokeh sliders

    # from bokeh.plotting import figure, output_file, show, ColumnDataSource, curdoc
    # from bokeh.layouts import column, row
    # from bokeh.models import TextInput

    # fff = ff[ff['txns'].isin([500, 600])]
    # fff = ff[ff['txns'] == 500]

    # output_file('text_input_barplot.html')

    # source = ColumnDataSource(data=fff)

    # plot = figure(
    #     x_range=fff['id'],
    #     x_axis_label='project_id',
    #     y_axis_label='matching_donation'
    # )
    # plot.xaxis.major_label_orientation = 'vertical'
    # plot.vbar(x='id', top='clr_amount', width=0.9, source=source)

    # # insert js callback statement here

    # # txn slider (number of users), filters on final dataframe
    # text_input_txns = TextInput(value='num_txns/users', title='num_txns')
    # # cap size, recalculates calculate_clr_by_txn (cap)
    # text_input_cap = TextInput(value='cap_size', title='cap_size')
    # # round size, reclaculates calculate_clr_by_txn (total_pot)
    # text_input_round = TextInput(value='round_size', title='round_size')

    # layout = row(
    #     plot, 
    #     column(text_input_txns, text_input_cap, text_input_round)
    # )

    # show(layout)
