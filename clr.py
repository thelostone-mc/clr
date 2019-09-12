from itertools import combinations
import math

import json

grant_contributions = [
    {
        'id': '1',
        'contributions': [
            { '1': 5 },
            { '2': 10 },
            { '3': 25 }
        ]
    },
    {
        'id': '2',
        'contributions': [
            { '3': 20 },
            { '1': 2 },
            { '4': 2 },
            { '5': 5 },
            { '1': 15 }
        ]
    }
]


def calculate_grant_lr(threshold, grant):
    grant_id = grant.get('id')
    grant_contributions = grant.get('contributions')
    unique_contributions = {}

    for contribution in grant_contributions:
        for profile, amount in contribution.items():
            if unique_contributions.get(profile):
                donation = unique_contributions[profile] + amount
                unique_contributions[profile] = donation
            else:
                unique_contributions[profile] = amount

    print(f'Grant Contributions: {grant_contributions}')
    print(f'Unique Contributions: {unique_contributions}')

    profile_pairs = list(combinations(unique_contributions.keys(), 2))
    contribution_pairs = list(combinations(unique_contributions.values(), 2))

    sqrt_of_product_pairs = []
    for contribution_1, contribution_2 in contribution_pairs:
        sqrt_of_product = round(math.sqrt(contribution_1 * contribution_2))
        sqrt_of_product_pairs.append(sqrt_of_product)


    grant = {
        'id': grant_id,
        'profile_pairs': profile_pairs,
        'contribution_pairs': contribution_pairs,
        'sqrt_of_product_pairs': sqrt_of_product_pairs
    }

    print(f'Grant ID: {grant["id"]}')
    print(f'Profile Pairs: {grant["profile_pairs"]}')
    print(f'Contribution Pairs: {grant["contribution_pairs"]}')
    print(f'Sqrt Of Product Pairs: {grant["sqrt_of_product_pairs"]}')

    print('=================\n')

    return grant

def calculate_clr(threshold, grant_contributions):
    grants = []
    group_by_pair = {}

    total_clr = 0

    for grant_contribution in grant_contributions:
        grant = calculate_grant_lr(threshold, grant_contribution)

        grants.append(grant)

        for index, profile_pair in enumerate(grant['profile_pairs']):
            pair = str('&'.join(profile_pair))
            pair_reversed = str('&'.join(profile_pair[::-1]))

            if group_by_pair.get(pair):
                group_by_pair[pair] += grant['sqrt_of_product_pairs'][index]
            elif group_by_pair.get(pair_reversed):
                group_by_pair[pair_reversed] += grant['sqrt_of_product_pairs'][index]
            else:
                group_by_pair[pair] = grant['sqrt_of_product_pairs'][index]

    print(f'SUM OF GROUPED BY PAIRS {group_by_pair} \n=================\n')

    for grant in grants:
        grant_clr = 0
        lr_contributions = []
        print(grant['profile_pairs'])
        for index, profile_pair in enumerate(grant['profile_pairs']):
            pair = str('&'.join(profile_pair))
            pair_reversed = str('&'.join(profile_pair[::-1]))
            _pair = None
            if group_by_pair.get(pair):
                _pair = pair
            elif group_by_pair.get(pair_reversed):
                _pair = pair_reversed

            lr_contribution = 0
            sqrt_of_product_pair = grant["sqrt_of_product_pairs"][index]
            # print(f'THRESHOLD {threshold} | PAIR {profile_pair} | SQRT {sqrt_of_product_pair} ')

            if threshold >= sqrt_of_product_pair:
                lr_contribution = sqrt_of_product_pair
            else:
                lr_contribution = threshold * (sqrt_of_product_pair / group_by_pair.get(_pair))

            lr_contributions.append(lr_contribution)
            grant_clr += lr_contribution
            total_clr += lr_contribution
            print(f'LR CONTRIBUTION {lr_contribution} | PAIR {profile_pair}')

        print(f'\n+++++\nGRANT {grant["id"]} - CLR CONTRIBUTION {grant_clr} \n+++++')

    print(f'\n\n============ \nTOTAL CLR {total_clr} \n=============')

    return total_clr


def grants_clr_calculate (total_pot, grant_contributions, min_threshold, max_threshold, iterations = 0):
    iterations += 1
    threshold = (max_threshold + min_threshold) / 2
    total_clr = calculate_clr(threshold, grant_contributions)

    print(f'\n\n\n************ \nPOT:  {total_pot} | Calculated CLR:  {total_clr} | Threshold {threshold} | Iterations {iterations}')
    print(f'\nMIN {min_threshold} MAX {max_threshold} threshold {threshold}')

    if total_clr > total_pot:
        max_threshold = threshold
        print(f'\n++ MIN {min_threshold} NEW MAX {max_threshold}\n************\n\n')
    elif total_clr < total_pot:
        min_threshold = threshold
        print(f'\n-- NEW MIN {min_threshold} MAX {max_threshold}\n************\n\n')
    else:
        return threshold, total_clr, iterations

    return grants_clr_calculate(total_pot, grant_contributions, min_threshold, max_threshold, iterations)

total_pot = 50
max_threshold = total_pot
min_threshold= 0

threshold, total_clr, iterations = grants_clr_calculate(total_pot, grant_contributions, min_threshold, max_threshold)

print(f'\n\n\n=============== \nFINAL \nPOT:  {total_pot} | Calculated CLR:  {total_clr} | Threshold {threshold} | Iterations {iterations}\n===============')

# calculate_clr(10, grant_contributions)