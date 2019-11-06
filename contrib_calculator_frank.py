import json

# add grant dictionary conversion here if we want to use this script

# contribs = json.loads(open('v_contribs.json').read())
# contribs = json.loads(open('v_contribs_short.json').read())

contribs = [[1.0, 1.0, 5.0], [2.0, 3.0, 20.0], [2.0, 1.0, 2.0 ], [2.0, 4.0, 2.0 ], [2.0, 5.0, 5.0 ], [2.0, 1.0, 15.0 ], [3.0, 3.0, 20.0], [3.0, 1.0, 2.0]]

# aggregating contributor contributions
contrib_dict = {}
for proj, user, amount in contribs:
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

# add threshold "binary" calculation here
lower = 0
upper = total_pot * 2
iterations = 0
threshold = lower + upper // 2
while iterations < 100:
    iterations += 1
    bigtot = 0
    totals = []
    # single donation doesn't get a match
    for proj, contribz in contrib_dict.items():
        tot = 0
        for k1, v1 in contribz.items():
            for k2, v2 in contribz.items():
                if k2 > k1:  # remove pairs
                    # pairwise matching formula
                    tot += (v1 * v2) ** 0.5 * min(1, threshold / tot_overlap[k1][k2])
                    # # vitalik's division formula
                    # tot += (v1 * v2) ** 0.5 / (tot_overlap[k1][k2] / max_contrib + 1)
        bigtot += tot
        totals.append((proj, tot))
    print('threshold', threshold)
    if bigtot == total_pot:
        print(bigtot)
    elif bigtot < total_pot:
        threshold = (threshold + upper) / 2
        print('total less than pot', bigtot)
    elif bigtot > total_pot:
        threshold = (lower + threshold) / 2
        print('total greater than pot', bigtot)
    elif iterations == 101:
        print(bigtot)

# # max_contrib = 3.4514245
# threshold = 15.46267066735667
# # max_contrib = 999999

# bigtot = 0
# totals = []
# # single donation doesn't get a match
# for proj, contribz in contrib_dict.items():
#     tot = 0
#     for k1, v1 in contribz.items():
#         for k2, v2 in contribz.items():
#             if k2 > k1:  # remove pairs
#                 # pairwise matching formula
#                 tot += (v1 * v2) ** 0.5 * min(1, threshold / tot_overlap[k1][k2])
#                 # # vitalik's division formula
#                 # tot += (v1 * v2) ** 0.5 / (tot_overlap[k1][k2] / max_contrib + 1)
#     bigtot += tot
#     totals.append((proj, tot))

# for proj, tot in sorted(totals):
#     print('{}, {}'.format(proj, tot))

# print(bigtot)
#     