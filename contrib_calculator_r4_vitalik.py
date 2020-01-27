GRANTS_CSV_FILE = '/Users/fronk/MEGA/github/untracked/gitcoin-results/grants-clr-round-4/r4_grants_raw_data_new.csv'
PHANTOM_CSV_FILE = '/Users/fronk/MEGA/github/untracked/gitcoin-results/grants-clr-round-4/r4_phantom_raw_data_new.csv'

def get_raw_grants(grant_type):
    lines = ( 
        [x.split(',') for x in open(GRANTS_CSV_FILE).readlines()][1:] +
        [x.split(',') for x in open(PHANTOM_CSV_FILE).readlines()][1:]
    )
    grants = [(line[0], int(line[-4]), float(line[-1])) for line in lines if line[-5] == grant_type]
    o = {}
    for proj, user, amount in grants:
        if proj not in o:
            o[proj] = {}
        o[proj][user] = o[proj].get(user, 0) + amount

    tot_overlap = {}
    for proj, contribz in o.items():
        for k1, v1 in contribz.items():
            if k1 not in tot_overlap:
                tot_overlap[k1] = {}
            for k2, v2 in contribz.items():
                if k2 not in tot_overlap[k1]:
                    tot_overlap[k1][k2] = 0
                tot_overlap[k1][k2] += (v1 * v2) ** 0.5
    return o, tot_overlap

# get aggregated contributions and total overlap
tech, toverlap = get_raw_grants('tech')
media, moverlap = get_raw_grants('media')

def calculate_clr(aggregated_contributions, pair_totals, lower_bound=0.0, total_pot=125000.0):   
    lower = lower_bound
    upper = total_pot
    iterations = 0
    while iterations < 100:
        threshold = (lower + upper) / 2
        iterations += 1
        if iterations == 100:
            # print("--- %s seconds ---" % (time.time() - start_time))
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
            # print("--- %s seconds ---" % (time.time() - start_time))
            print(f'bigtot {bigtot} = total_pot {total_pot} with threshold {threshold}')
            # print(totals)
            break
        elif bigtot < total_pot:
            lower = threshold
        elif bigtot > total_pot:
            upper = threshold
    return bigtot, totals 

calculate_clr(tech, toverlap)
calculate_clr(media, moverlap, total_pot=75000.0)