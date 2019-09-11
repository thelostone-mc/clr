from itertools import combinations
import math

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
            { '1': 2 },
            { '4': 2 },
            { '5': 5 },
            { '1': 15 },
            { '3': 20 }
        ]
    }
]


def calculate_grant_lr(threshold, grant_contributions):
    unique_contributions = {}

    for contribution in grant_contributions: 
        for profile, amount in contribution.items():
            if unique_contributions.get(profile):
                donation = unique_contributions[profile] + amount
                unique_contributions[profile] = donation
            else:
                unique_contributions[profile] = amount

    print(f'Unique Contributions: {unique_contributions}')

    contribution_pairs = list(combinations(unique_contributions.values(), 2))
    print(f'Contribution Pairs: {list(contribution_pairs)}')

    grant_lr_contribution = 0
    lr_contributions = []
    for contribution_1, contribution_2 in contribution_pairs:
        lr_contribution = math.sqrt(contribution_1 * contribution_2)
        lr_contributions.append(lr_contribution)
        grant_lr_contribution += lr_contribution
    
    print(f'Grant LR contribution: {grant_lr_contribution}')
    print(f'Pairwise LR contribution: {lr_contributions}')
    print('=================\n')

    return (grant_lr_contribution, lr_contributions)

def calculate_clr(threshold, grant_contributions):
    total_grants_lr = 0
    grants = []
    for index, grant_contribution in enumerate(grant_contributions):
        (grant_lr, lr_contributions) = calculate_grant_lr(threshold, grant_contribution.get('contributions'))
        total_grants_lr += grant_lr
        grants.append({
            'id': grant_contributions[index]['id'],
            'grant_lr': grant_lr,
            'lr_contributions': lr_contributions
        })

    total_clr = 0
    for index, grant in enumerate(grants):
        grant_lr = grant['grant_lr']
        
        for contribution in grant['lr_contributions']:
            grant_clr = 0

            if contribution > threshold:
                lr_contribution = contribution / threshold
                print(f'Grant Id: {grant["id"]}, LR contribution > Threshold. LR contibution {contribution} -> {lr_contribution}')
            else:
                lr_contribution = contribution
                print(f'Grant Id: {grant["id"]}, LR contribution < Threshold. LR contibution {lr_contribution}')

            grant_clr += lr_contribution

        grants[index]['clr'] = grant_clr
        total_clr += grant_clr

    return ( grants, total_clr )

def grants_clr_calculate(total_pot, grant_contributions):
    threshold = 15
    grants, total_clr = calculate_clr(threshold, grant_contributions)
    print(f'================= \n\nTHRESHOLD CLR:  {total_clr} \nCalculated CLR:  {total_clr}')

total_pot = 50
grants_clr_calculate(total_pot, grant_contributions)
