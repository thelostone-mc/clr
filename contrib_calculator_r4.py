import json
import time
import pandas as pd 



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
        from translate_data:
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

        set variables:
        lower_bound: set at 0.0
        total_pot: set at 100000.0
        
        from the helper function aggregate_contributions:
        aggregated_contributions: {grant_id (str): {user_id (str): aggregated_amount (float)}}
        pair_totals: {user_id (str): {user_id (str): pair_total (float)}}

    Returns:
        bigtot: should equal total pot
        totals:
'''
def calculate_clr(aggregated_contributions, pair_totals, lower_bound=0.0, total_pot=125000.0):   
    lower = lower_bound
    upper = total_pot
    iterations = 0
    while iterations < 100:
        threshold = (lower + upper) / 2
        iterations += 1
        if iterations == 100:
            print("--- %s seconds ---" % (time.time() - start_time))
            print(f'iterations reached, bigtot at {bigtot} with threshold {threshold}')
            # print totals
            break
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
            # totals.append((proj, tot))
            totals.append({'id': proj, 'clr_amount': tot})
        # print(f'threshold {threshold} yields bigtot {bigtot} vs totalpot {total_pot} at iteration {iterations}')
        if bigtot == total_pot:
            print("--- %s seconds ---" % (time.time() - start_time))
            print(f'bigtot {bigtot} = total_pot {total_pot} with threshold {threshold}')
            # print(totals)
            break
        elif bigtot < total_pot:
            lower = threshold
        elif bigtot > total_pot:
            upper = threshold
    return bigtot, totals 



# testing the code
start_time = time.time()
# grants_data = json.loads(open('v_contribs.json').read())
# grants_list = translate_data(grants_data)
tech, media = get_data()
aggregated_contributions, pair_totals = aggregate_contributions(tech)
aggregated_contributions_m, pair_totals_m = aggregate_contributions(media)
calculate_clr(aggregated_contributions, pair_totals)
calculate_clr(aggregated_contributions_m, pair_totals_m, total_pot=75000.0)





