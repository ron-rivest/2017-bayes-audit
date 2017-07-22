# syn2.py
# Ronald L. Rivest
# July 8, 2017
# python3

"""
Routines to generate a synthetic test election dataset, 
given the following 13 parameters (defaults in brackets):
    n_cids = # number of contests [1]
    n_cids_wrong = # number of contests with wrong reported outcome [0]
    min_n_selids_per_cid = minimum number of selids per contest [2]
    max_n_selids_per_cid = maximum number of selids per contest [5]
    n_pbcids = # number of pbcids [1]
    n_pbcids_nocvr = # number of collections with no CVRs [0]
    min_n_bids_perp = minimum number of bids per pbcid [1000]
    max_n_bids_perp = maximum number of bids per pbcid [100000]
    min_pbcids_per_cid = minimum number of pbcids per contest [1]
    max_pbcids_per_cid = maximum number of pbcids per contest [1]
    dropoff = rate at which votes drop off with selection (geometric) [0.9]
    errorrate = rate at which reported votes != actual votes [0.005]
    seed = random number seed (for reproducibility) [1]
    RandomState = state for random number generator

    ### following are then computed ###
    cids = list of cids (of length n_cids)
    cids_wrong = list of cids that will have wrong output
    pbcids = list of pbcids (of length n_pbcids)
    cvr_type_p = mapping of pbcid to "CVR" or "noCVR"
    n_bids_p = mapping from pbcid to number of bids in that pbcid
    
The main data structure here, SynElection, is a subclass of 
multi.Election.  We fill in the values of the fields as if they
had been read on, or else we (optionally) output the values as csv files.
"""

import numpy as np
import os

import multi
import structure
import utils
import random 

class SynElection(multi.Election):

    def __init__(self, synseed=1):

        super(SynElection, self).__init__()
        self.n_cids = 2
        self.n_cids_wrong = 0
        self.min_n_selids_per_cid = 2
        self.max_n_selids_per_cid = 5
        self.n_pbcids = 2
        self.n_pbcids_nocvr = 0
        self.min_n_bids_per_pbcid = 10
        self.max_n_bids_per_pbcid = 20
        self.min_pbcids_per_cid = 1
        self.max_pbcids_per_cid = self.n_pbcids
        self.dropoff = 0.9
        self.error_rate = 0.005
        #self.seed = seed
        self.synseed = synseed
        self.SynRandomState = np.random.RandomState(self.synseed)
        #self.RandomState = np.random.RandomState(self.seed)


default_SynElection = SynElection()          


def geospace(start, stop, num=7):
    """
    Return a list of up to num distinct integer values,
    from start, start+1, ..., stop, inclusive, geometrically spread out.

    A bit like numpy.linspace, but geometrically spread
    out rather than linearly spread out, and only integers returned.
    >>> geospace(0,1)
    [0, 1]
    >>> geospace(0,10)
    [0, 1, 2, 3, 5, 7, 10]    
    >>> geospace(20, 10000)
    [20, 56, 159, 447, 1260, 3550, 10000]    
    >>> geospace(1, 64)
    [1, 2, 4, 8, 16, 32, 64]
    """

    answer = {start, stop}
    start = max(start, 1)
    for i in range(1, num-1):
        answer.add(int(np.rint(start*(stop/start)**(i/(num-1)))))
    return sorted(answer)


def geospace_choice(se, start, stop, num=7):
    """ 
    Return a random element from geospace(start, stop, num), 
    based on se.RandomState.
    """

    elts = geospace(start, stop, num)
    return se.SynRandomState.choice(elts)


def generate_election_structure(se=default_SynElection):
    """
    se has SynElection for the parameters noted above;
    add to se values that would be otherwise read in,
    e.g. via structure.py (read_election, read_contests,
    read_collections)
    """

    # reset RandomState from seed
    se.SynRandomState = np.random.RandomState(se.synseed)

    dts = utils.datetime_string()
    se.election_name = "TestElection-"+dts
    se.election_dirname = "TestElection-"+dts
    se.election_date = dts                     # FIX ??
    se.election_url = "None"            


def generate_contests(se):

    # check number of contests
    assert isinstance(se.n_cids, int) and se.n_cids >= 1
    # make cid for each contest
    se.cids = ["c{}".format(i+1) for i in range(se.n_cids)]

    # generate contest types as plurality and number winners = 1
    # no write-ins
    for cid in se.cids:
        se.contest_type_c[cid] = "plurality"
        se.winners_c[cid] = 1
        se.write_ins_c[cid] = "no"

    # check number of cids with wrong reported outcome
    assert isinstance(se.n_cids_wrong, int) and 0 <= se.n_cids_wrong <= se.n_cids
    # determine which cids have wrong reported outcome
    se.cids_wrong = []
    while len(se.cids_wrong) < se.n_cids_wrong:
        se.cids_wrong.append(se.SynRandomState.choice(se.cids))

    # generate selids for each cid
    se.n_selids_c = {}
    se.selids_c = {}
    for cid in se.cids:
        se.n_selids_c[cid] = geospace_choice(se,
                                             se.min_n_selids_per_cid,
                                             se.max_n_selids_per_cid)

        se.selids_c[cid] = {"s{}".format(i):True for i in range(1, se.n_selids_c[cid]+1)}


def generate_collections(se):

    # generate list of pbcids
    assert isinstance(se.n_pbcids, int) and se.n_pbcids >= 1
    se.pbcids = ["p{}".format(i) for i in range(1, se.n_pbcids+1)]

    # add managers
    for pbcid in se.pbcids:
        se.manager_p[pbcid] = "Nobody"

    # number of pbcids with no CVR
    assert isinstance(se.n_pbcids_nocvr, int) and 0 <= se.n_pbcids_nocvr <= se.n_pbcids
    # identify which pbcids have types CVR or noCVR
    se.cvr_type_p = {}
    while len(se.cvr_type_p) < se.n_pbcids_nocvr:
        se.cvr_type_p[se.SynRandomState.choice[se.pbcids]] = "noCVR"
    for pbcid in se.pbcids:
        if pbcid not in se.cvr_type_p:
            se.cvr_type_p[pbcid] = "CVR"
    
    # determine range of pbcids for each cid (always a range of consecutive pbcids)
    m = se.min_pbcids_per_cid
    M = se.max_pbcids_per_cid
    assert m >= 1
    assert M <= se.n_pbcids
    se.firstpbcidx_c = {}
    se.lastpbcidx_c = {}
    se.rel_cp = {}
    for cid in se.cids:
        s = geospace_choice(se, m, M)
        se.firstpbcidx_c[cid] = se.SynRandomState.randint(0, se.n_pbcids - s + 1)
        se.lastpbcidx_c[cid] = se.firstpbcidx_c[cid] + s - 1
        se.rel_cp[cid] = {}
        for pbcidx in range(se.firstpbcidx_c[cid], se.lastpbcidx_c[cid]+1):
            pbcid = se.pbcids[pbcidx]
            se.rel_cp[cid][pbcid] = True


def write_structure_csvs(se):

    write_11_election_csv(se)
    write_12_contests_csv(se)
    write_13_collections-csv(se)

def write_11_election_csv(se):

    dirpath = os.path.join(multi.ELECTIONS_ROOT, se.election_dirname, "1-structure")
    os.makedirs(dirpath, exist_ok=True)
    filename = os.path.join(dirpath, "11_election.csv")
    with open(filename, "w") as file:
        file.write("Attribute,Value\n")
        file.write("Election name,"+se.election_name+"\n")
        file.write("Elections dirname,"+se.election_dirname+"\n")
        file.write("Election date,"+se.election_date+"\n")
        file.write("Election URL,"+se.election_url+"\n")

def write_12_contests_csv(se):

    dirpath = os.path.join(multi.ELECTIONS_ROOT, se.election_dirname, "1-structure")
    os.makedirs(dirpath, exist_ok=True)
    filename = os.path.join(dirpath, "12_contests.csv")
    with open(filename, "w") as file:
        for fieldname in ["Contest id", "Contest type", "Winners",
                          "Write-ins", "Selections"]:
            file.write("{},".format(fieldname))
        file.write("\n")
        for cid in se.cids:
            file.write(cid+",")
            file.write("{},".format(se.contest_type_c[cid].title()))
            file.write("{},".format(se.winners_c[cid]))
            file.write("{},".format(se.write_ins_c[cid].title()))
            for selid in se.selids_c[cid]:
                file.write("{},".format(selid))
            file.write("\n")
        
def write_13_collections_csv(se):

    dirpath = os.path.join(multi.ELECTIONS_ROOT, se.election_dirname, "1-structure")
    os.makedirs(dirpath, exist_ok=True)
    filename = os.path.join(dirpath, "13_collections.csv")
    with open(filename, "w") as file:
        for fieldname in ["Collection id", "Manager", "CVR type", "Contests"]:
            file.write("{},".format(fieldname))
        file.write("\n")
        for pbcid in se.pbcids:
            file.write("{},".format(pbcid))
            file.write("{},".format(se.manager_p[pbcid]))
            file.write("{},".format(se.cvr_type_p[pbcid]))
            for cid in se.cids:
                if pbcid in se.rel_cp[cid]:
                    file.write("{},".format(cid))
            file.write("\n")

def write_14_reported_csv(se):
    dirpath = os.path.join(multi.ELECTIONS_ROOT, se.election_dirname, "2-election")
    os.makedirs(dirpath, exist_ok=True)
    for pbcid in se.pbcids:
        # handle cvr pbcids
        if se.cvr_type_p[pbcid]=="CVR": 
            filename = os.path.join(dirpath, "reported-cvrs-" + pbcid+".csv")
            with open(filename, "w") as file:
                for fieldname in ["Collection id", "Scanner", "Ballot id", "Contest", "Selections"]:
                    file.write("{},".format(fieldname))
                file.write("\n")
                for cid in se.rv_cpb:
                    if pbcid in se.rel_cp[cid]:
                        for bid in se.rv_cpb[cid][pbcid]:
                            selid = se.rv_cpb[cid][pbcid][bid]
                            if se.cvr_type_p[pbcid] == "CVR":
                                file.write("{},".format(pbcid))
                                file.write("{},".format("scanner_1"))
                                file.write("{},".format(bid))
                                file.write("{},".format(cid))
                                file.write("{},".format(selid))
                            file.write("\n")
                            # if selid has more than one "vote" 
                            """
                                for vote in list(selid):
                                    file.write("{},".format(vote))
                            """
        # handle non-cvr pbcids
        else:
            pass
    """
    go through the pbcids here .. we want the files to be in the form:

      reported-cvrs-DEN-A01-2017-11-07.csv
      reported-cvrs-DEN-A02-2017-11-07.csv
      reported-cvrs-LOG-B13-2017-11-07.csv
    """


def write_15_ballot_manifest(se):
    pass 

##############################################################################
## generate reported data

def generate_reported(se):

    # generate number of bids for each pbcid
    se.n_bids_p = {}
    for pbcid in se.pbcids:
        se.n_bids_p[pbcid] = geospace_choice(se,
                                            se.min_n_bids_per_pbcid,
                                            se.max_n_bids_per_pbcid)
    # generate list of ballot ids for each pbcid
    se.n_bids = 0
    se.bids_p = {}
    for pbcid in se.pbcids:
        se.bids_p[pbcid] = []
        for i in range(se.n_bids_p[pbcid]):
            bid = "b{}".format(se.n_bids)
            se.n_bids += 1
            se.bids_p[pbcid].append(bid)

    print('se.bids_p:', se.bids_p)

    """
    figure out what contest(s) are on the ballot for given bid and pbcid 
    figure out if contest is CVR or not 
    draw from selection 
    """

    """
    above we have the bids that correspond to the given paper ballot collections. what we want to do is assign 
    contests to those ballot ids based on what contests are in the given pbcids as well as assign selections 
    based on the possible selections for each contest
    """
    se.cids_b = {}

    # change rel_cp to rel_pc 
    rel_pc = {}
    for cid in se.cids:
        pbcids = se.rel_cp[cid]
        for pbcid in pbcids:
            if pbcid not in rel_pc:
                rel_pc[pbcid]=[cid]
            else:
                rel_pc[pbcid].append(cid)

    for pbcid in se.pbcids:
        if (se.cvr_type_p[pbcid] == 'CVR'):
            bids_pi = se.bids_p[pbcid]
            available_contests = rel_pc[pbcid]
            for i in range(len(bids_pi)):
                num_contests =  int(se.SynRandomState.uniform(1,len(available_contests)+1,1))# random.randint(1,len(available_contests)) #change to int(se.SynRandomState.uniform(low, high, size))
                contest_set = set()
                for j in range(num_contests):
                    contest = int(se.SynRandomState.uniform(0,len(available_contests),1)) # random.randint(0, len(available_contests)-1)
                    if contest not in contest_set:
                        contest_set.add(contest)
                        se.cids_b[bids_pi[i]] = available_contests[contest]
        else: # not sure what to do here if cvr_type_p[pbcid] == non-CVR 
            pass 

    # generate the selection for each contest. so basically populate rv_cpb. draw from selids_c. 
    # also keep track of ro_c
    se.rv_cpb = dict()
    for contest in se.rel_cp:
        for pbcid in se.rel_cp[contest]:
            for bid in se.bids_p[pbcid]:
                selids = list(se.selids_c[contest].keys())
                if se.contest_type_c[contest] == 'plurality':
                    selection_index = int(se.SynRandomState.uniform(0,len(selids),1)) # random.randint(0, len(selids)-1)
                    selection = selids[selection_index]
                    nested_set(se.rv_cpb, [contest, pbcid, bid], selection)

                else: # we can handle this later when its not hardcoded 
                    pass
                    

    # sum over ballot ids and pbcids to get se.ro_c
    rn_cs = dict() 
    for cid in se.cids:
        for pbcid in se.rel_cp[cid]:
            for bid in se.bids_p[pbcid]:
                selection = se.rv_cpb[cid][pbcid][bid]
                if cid not in rn_cs:
                    nested_set(rn_cs, [cid, selection], 1)
                else:
                    if selection not in rn_cs[cid]:
                        nested_set(rn_cs, [cid, selection], 1)
                    else:
                        rn_cs[cid][selection]+=1

    # get rn_p from se.rv_cpb
    se.rn_p = dict()
    for cid in se.rv_cpb:
        for pbcid in se.rv_cpb[cid]:
            for bid in se.rv_cpb[cid][pbcid]:
                if pbcid not in se.rn_p:
                    se.rn_p[pbcid]=1
                else:
                    se.rn_p[pbcid]+=1

    # sum over selection ids to get rn_c
    se.rn_c = dict()
    for cid in rn_cs:
        for selid in rn_cs[cid]:
            if cid not in se.rn_c:
                se.rn_c[cid]=rn_cs[cid][selid]
            else:
                se.rn_c[cid]+=rn_cs[cid][selid]

    # get rn_cpr
    se.rn_cpr = dict()
    for cid in se.rv_cpb:
        for pbcid in se.rv_cpb[cid]:
            for bid in se.rv_cpb[cid][pbcid]:
                selid = se.rv_cpb[cid][pbcid][bid]
                if cid in se.rn_cpr:
                    if pbcid in se.rn_cpr[cid]:
                        if selid in se.rn_cpr[cid][pbcid]:
                            se.rn_cpr[cid][pbcid][selid]+=1
                        else:
                            nested_set(se.rn_cpr,[cid,pbcid,selid], 1)
                    else:
                        nested_set(se.rn_cpr,[cid,pbcid,selid], 1)
                else:
                    nested_set(se.rn_cpr,[cid,pbcid,selid], 1)

    # sum over pbcids to get rn_cr
    se.rn_cr = dict()
    for cid in se.rn_cpr:
        for pbcid in se.rn_cpr[cid]:
            for selid in se.rn_cpr[cid][pbcid]:
                if cid in se.rn_cr:
                    if selid in se.rn_cr[cid]:
                        se.rn_cr[cid][selid]+=se.rn_cpr[cid][pbcid][selid]
                    else:
                        nested_set(se.rn_cr, [cid,selid], se.rn_cpr[cid][pbcid][selid])
                else:
                    nested_set(se.rn_cr, [cid,selid], se.rn_cpr[cid][pbcid][selid])

    se.ro_c = dict()
    for contest in rn_cs:
        outcome = max(rn_cs[contest], key=rn_cs[contest].get)
        se.ro_c[contest] = outcome

    # dropoff
    assert 0 < se.dropoff <= 1

    # error_rate
    assert 0 <= se.error_rate <= 1

    return se


def generate_ballot_manifest(se):
    """ generate everything other than location -- but what structure should we put this in? """

    n_pc = dict()
    for cid in se.rv_cpb:
        for pbcid in se.rv_cpb[cid]:
            nested_set(n_pc,[pbcid, cid],len(se.rv_cpb[cid][pbcid]))
    # the keys aren't ordered, so we need to use an ordered dictionary or something to keep track of the "first"
    # ballot before incrementing 
    # no -- just use one line per ballot; don't worry about compression/collapsing


def nested_set(dic, keys, value):

    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


##############################################################################
## Generate audit data

def generate_audit(se):

    # setup
    # generate 3/audit/31-setup/311-audit-seed.csv
    # generate 3/audit/31-setup/312-sampling-orders
    #   sampling-order-PBCID.csv
    #   (This is generated by standard audit anyway)
    # generate 3/audit/32-audited-votes
    #   audited-votes-PBCID.csv
    # (audit stages will be generated by audit itself)

    pass

def generate_actual(se):
    se.av_cpb = dict()
    for cid in se.rv_cpb:
        for pbcid in se.rv_cpb[cid]:
            for bid in se.rv_cpb[cid][pbcid]:
                for vote in se.rv_cpb[cid][pbcid][bid]:
                    if (se.SynRandomState.uniform() <= se.error_rate):
                        #then choose a different selection other than the one on reported
                        selids = list(se.selids_c[cid].keys())
                        # selids.remove(se.rv_cpb[contest][pbcid][bid])
                    else:
                        selids = list(se.selids_c[cid].keys())
                    selection = se.SynRandomState.choice(selids)
                    nested_set(se.av_cpb, [cid, pbcid, bid], selection)


def test():

    se = SynElection()
    se.seed = 9
    generate_election_structure(se)
    generate_contests(se)
    generate_collections(se)
    generate_reported(se)
    generate_actual(se)
    generate_ballot_manifest(se)
    structure.finish_election_structure(se)
    for key in sorted(vars(se)):
        print(key)
        print("    ", vars(se)[key])
    print("Checking structure:", structure.check_election_structure(se))
    
    write_11_election_csv(se)
    write_12_contests_csv(se)
    write_13_collections_csv(se)
    write_14_reported_csv(se)

if __name__=="__main__":
    test()
