# reported.py
# Ronald L. Rivest (with Karim Husayn Karimi)
# July 8, 2017
# python3

"""
Code that works with multi.py for post-election audit support.
This code reads and checks the "reported" results: votes
and reported outcomes.

The directory format is illustrated by this example from
README.md:

    2-election
       21-reported-votes
          reported-cvrs-DEN-A01-2017-11-07.csv
          reported-cvrs-DEN-A02-2017-11-07.csv
          reported-cvrs-LOG-B13-2017-11-07.csv
       22-ballot-manifests
          manifest-DEN-A01-2017-11-07.csv
          manifest-DEN-A01-2017-11-07.csv
          manifest-LOG-B13-2017-11-07.csv
       23-reported-outcomes-2017-11-07.csv

The 2-election directory is a subdirectory of the main
directory for the election.

There are three file types here:
   reported-cvrs
   ballot-manifests
   reported-outcomes

Here is an example of a reported-cvrs file, from
the README.md file:

Collection id   , Source , Ballot id   , Contest     , Selections
DEN-A01         , L      , B-231       , DEN-prop-1  , Yes       
DEN-A01         , L      , B-231       , DEN-prop-2  
DEN-A01         , L      , B-231       , US-Senate-1 , Rhee Pub       , Sarah Day
DEN-A01         , L      , B-777       , DEN-prop-1  , No            
DEN-A01         , L      , B-777       , DEN-prop-2  , Yes           
DEN-A01         , L      , B-777       , US-Senate-1 , +Tom Cruz     
DEN-A01         , L      , B-888       , US-Senate-1 , -Invalid      

If the collection is noCVR, then the format is slightly different:

Collection id   , Source , Tally       , Contest     , Selections 
LOG-B13         , L      , 2034        , LOG-mayor   , Susan Hat  
LOG-B13         , L      , 1156        , LOG-mayor   , Barry Su   
LOG-B13         , L      , 987         , LOG-mayor   , Benton Liu 
LOG-B13         , L      , 3           , LOG-mayor   , -Invalid   
LOG-B13         , L      , 1           , LOG-mayor   , +Lizard People
LOG-B13         , L      , 3314        , US-Senate-1 , Rhee Pub      
LOG-B13         , L      , 542         , US-Senate-1 , Deb O'Crat    
LOG-B13         , L      , 216         , US-Senate-1 , Val Green     
LOG-B13         , L      , 99          , US-Senate-1 , Sarah Day     
LOG-B13         , L      , 9           , US-Senate-1 , +Tom Cruz     
LOG-B13         , L      , 1           , US-Senate-1 , -Invalid      


Here is an example of a ballot-manifests file, from the README.md file:

Collection id , Original index , Ballot id , Location       
LOG-B13       , 1              , B-0001    , Box 001 no 0001
LOG-B13       , 2              , B-0002    , Box 001 no 0002
LOG-B13       , 3              , B-0003    , Box 001 no 0003
LOG-B13       , 4              , B-0004    , Box 001 no 0004
LOG-B13       , 5              , C-0001    , Box 002 no 0001

Here is an example of a reported outcomes file, from the README.md file:

Contest id      , Winner(s)
DEN-prop-1      , Yes      
DEN-mayor       , John Smith 
Boulder-council , Dave Diddle, Ben Borg   , Sue Mee   , Jill Snead

"""

##############################################################################
# Election data I/O and validation (stuff that depends on cast votes)
##############################################################################


def is_writein(selid):

    return len(selid) > 0 and selid[0] == "+"


def is_error_selid(selid):

    return len(selid) > 0 and selid[0] == "-"


def get_election_data(e):

    # next line needs to be replaced!
    load_part_from_json(e, "data.js")
    for cid in e.rn_cpr:
        unpack_json_keys(e.syn_rn_cr[cid])
        for pbcid in e.rn_cpr[cid]:
            unpack_json_keys(e.rn_cpr[cid][pbcid])
    finish_election_data(e)
    check_election_data(e)
    show_election_data(e)


def finish_election_data(e):
    """ 
    Compute election data attributes that are derivative from others. 
    or that need conversion (e.g. strings-->tuples from json keys).
    """

    # make sure e.selids_c contains all +/- selids seen in reported votes
    # and that e.votes_c[cid] contains all reported votes
    for cid in e.cids:
        for pbcid in e.rel_cp[cid]:
            for bid in e.bids_p[pbcid]:
                r = e.rv_cpb[cid][pbcid][bid]
                e.votes_c[r] = True
                for selid in r:
                    if is_writein(selid) or is_error_selid(selid):
                        e.selids_c[cid][selid] = True

    # set e.rn_cpr[cid][pbcid][r] to number in pbcid with reported vote r:
    for cid in e.cids:
        e.rn_cpr[cid] = {}
        for pbcid in e.rel_cp[cid]:
            e.rn_cpr[cid][pbcid] = {}
            for r in e.votes_c[cid]:
                e.rn_cpr[cid][pbcid][r] = len([bid for bid in e.bids_p[pbcid]
                                               if e.rv_cpb[cid][pbcid][bid] == r])

    # e.rn_c[cid] is reported number of votes cast in contest cid
    for cid in e.cids:
        e.rn_c[cid] = sum([e.rn_cpr[cid][pbcid][vote]
                           for pbcid in e.rn_cpr[cid]
                           for vote in e.votes_c[cid]])

    # e.rn_cr[cid][vote] is reported number cast for vote in cid
    for cid in e.cids:
        e.rn_cr[cid] = {}
        for pbcid in e.rn_cpr[cid]:
            for vote in e.votes_c[cid]:
                if vote not in e.rn_cr[cid]:
                    e.rn_cr[cid][vote] = 0
                if vote not in e.rn_cpr[cid][pbcid]:
                    e.rn_cpr[cid][pbcid][vote] = 0
                e.rn_cr[cid][vote] += e.rn_cpr[cid][pbcid][vote]


def check_election_data(e):

    if not isinstance(e.rn_cpr, dict):
        myerror("e.rn_cpr is not a dict.")
    for cid in e.rn_cpr:
        if cid not in e.cids:
            mywarning("cid `{}` not in e.cids.".format(cid))
        for pbcid in e.rn_cpr[cid]:
            if pbcid not in e.pbcids:
                mywarning("pbcid `{}` is not in e.pbcids.".format(pbcid))
            for vote in e.rn_cpr[cid][pbcid]:
                for selid in vote:
                    if selid not in e.selids_c[cid] and selid[0].isalnum():
                        mywarning(
                            "selid `{}` is not in e.selids_c[{}]."
                            .format(selid, cid))
                if not isinstance(e.rn_cpr[cid][pbcid][vote], int):
                    mywarning("value `e.rn_cpr[{}][{}][{}] = `{}` is not an integer."
                              .format(cid, pbcid, vote, e.rn_cpr[cid][pbcid][vote]))
                if not (0 <= e.rn_cpr[cid][pbcid][vote] <= e.rn_p[pbcid]):
                    mywarning("value `e.rn_cpr[{}][{}][{}] = `{}` is out of range 0:{}."
                              .format(cid, pbcid, vote, e.rn_cpr[cid][pbcid][vote],
                                      e.rn_p[pbcid]))
                if e.rn_cr[cid][vote] != \
                        sum([e.rn_cpr[cid][pbcid][vote]
                             for pbcid in e.rel_cp[cid]]):
                    mywarning("sum of e.rn_cpr[{}][*][{}] is not e.rn_cr[{}][{}]."
                              .format(cid, vote, cid, vote))
    for cid in e.cids:
        if cid not in e.rn_cpr:
            mywarning("cid `{}` is not a key for e.rn_cpr".format(cid))
        for pbcid in e.rel_cp[cid]:
            if pbcid not in e.rn_cpr[cid]:
                mywarning(
                    "pbcid {} is not a key for e.rn_cpr[{}].".format(pbcid, cid))
            # for selid in e.selids_c[cid]:
            #     assert selid in e.rn_cpr[cid][pbcid], (cid, pbcid, selid)
            # ## not necessary, since missing selids have assumed count of 0

    if not isinstance(e.rn_c, dict):
        myerror("e.rn_c is not a dict.")
    for cid in e.rn_c:
        if cid not in e.cids:
            mywarning("e.rn_c key `{}` is not in e.cids.".format(cid))
        if not isinstance(e.rn_c[cid], int):
            mywarning("e.rn_c[{}] = {}  is not an integer.".format(
                cid, e.rn_c[cid]))
    for cid in e.cids:
        if cid not in e.rn_c:
            mywarning("cid `{}` is not a key for e.rn_c".format(cid))

    if not isinstance(e.rn_cr, dict):
        myerror("e.rn_cr is not a dict.")
    for cid in e.rn_cr:
        if cid not in e.cids:
            mywarning("e.rn_cr key cid `{}` is not in e.cids".format(cid))
        for vote in e.rn_cr[cid]:
            for selid in vote:
                if (not is_writein(selid) and not is_error_selid(selid)) \
                   and not selid in e.selids_c[cid]:
                    mywarning("e.rn_cr[{}] key `{}` is not in e.selids_c[{}]"
                              .format(cid, selid, cid))
            if not isinstance(e.rn_cr[cid][vote], int):
                mywarning("e.rn_cr[{}][{}] = {} is not an integer."
                          .format(cid, vote, e.rn_cr[cid][vote]))
    for cid in e.cids:
        if cid not in e.rn_cr:
            mywarning("cid `{}` is not a key for e.rn_cr".format(cid))

    if not isinstance(e.bids_p, dict):
        myerror("e.bids_p is not a dict.")
    for pbcid in e.pbcids:
        if not isinstance(e.bids_p[pbcid], list):
            myerror("e.bids_p[{}] is not a list.".format(pbcid))

    if not isinstance(e.av_cpb, dict):
        myerror("e.av_cpb is not a dict.")
    for cid in e.av_cpb:
        if cid not in e.cids:
            mywarning("e.av_cpb key {} is not in e.cids.".format(cid))
        for pbcid in e.av_cpb[cid]:
            if pbcid not in e.pbcids:
                mywarning("e.av_cpb[{}] key `{}` is not in e.pbcids"
                          .format(cid, pbcid))
            if not isinstance(e.av_cpb[cid][pbcid], dict):
                myerror("e.av_cpb[{}][{}] is not a dict.".format(cid, pbcid))
            bidsset = set(e.bids_p[pbcid])
            for bid in e.av_cpb[cid][pbcid]:
                if bid not in bidsset:
                    mywarning("bid `{}` from e.av_cpb[{}][{}] is not in e.bids_p[{}]."
                              .format(bid, cid, pbcid, pbcid))

    for cid in e.cids:
        if cid not in e.av_cpb:
            mywarning("cid `{}` is not a key for e.av_cpb.".format(cid))
        for pbcid in e.rel_cp[cid]:
            if pbcid not in e.av_cpb[cid]:
                mywarning("pbcid `{}` is not in e.av_cpb[{}]."
                          .format(pbcid, cid))

    if not isinstance(e.rv_cpb, dict):
        myerror("e.rv_cpb is not a dict.")
    for cid in e.rv_cpb:
        if cid not in e.cids:
            mywarning("e.rv_cpb key `{}` is not in e.cids.".format(cid))
        for pbcid in e.rv_cpb[cid]:
            if pbcid not in e.pbcids:
                mywarning("e.rv_cpb[{}] key `{}` is not in e.pbcids."
                          .format(cid, pbcid))
            if not isinstance(e.rv_cpb[cid][pbcid], dict):
                myerror("e.rv_cpb[{}][{}] is not a dict.".format(cid, pbcid))
            bidsset = set(e.bids_p[pbcid])
            for bid in e.rv_cpb[cid][pbcid]:
                if bid not in bidsset:
                    mywarning("bid `{}` from e.rv_cpb[{}][{}] is not in e.bids_p[{}]."
                              .format(bid, cid, pbcid, pbcid))
    for cid in e.cids:
        if cid not in e.rv_cpb:
            mywarning("cid `{}` is not a key in e.rv_cpb.".format(cid))
        for pbcid in e.rel_cp[cid]:
            if pbcid not in e.rv_cpb[cid]:
                mywarning("pbcid `{}` from e.rel_cp[{}] is not a key for e.rv_cpb[{}]."
                          .format(pbcid, cid, cid))

    if not isinstance(e.ro_c, dict):
        myerror("e.ro_c is not a dict.")
    for cid in e.ro_c:
        if cid not in e.cids:
            mywarning("cid `{}` from e.rv_cpb is not in e.cids".format(cid))
    for cid in e.cids:
        if cid not in e.ro_c:
            mywarning("cid `{}` is not a key for e.ro_c.".format(cid))

    if warnings_given > 0:
        myerror("Too many errors; terminating.")


def show_election_data(e):

    myprint("====== Reported election data ======")

    myprint("e.rn_cpr (total reported votes for each vote by cid and pbcid):")
    for cid in e.cids:
        for pbcid in sorted(e.rel_cp[cid]):
            myprint("    {}.{}: ".format(cid, pbcid), end='')
            for vote in sorted(e.rn_cpr[cid][pbcid]):
                myprint("{}:{} ".format(
                    vote, e.rn_cpr[cid][pbcid][vote]), end='')
            myprint()

    myprint("e.rn_c (total votes cast for each cid):")
    for cid in e.cids:
        myprint("    {}: {}".format(cid, e.rn_c[cid]))

    myprint("e.rn_cr (total cast for each vote for each cid):")
    for cid in e.cids:
        myprint("    {}: ".format(cid), end='')
        for vote in sorted(e.rn_cr[cid]):
            myprint("{}:{} ".format(vote, e.rn_cr[cid][vote]), end='')
        myprint()

    myprint("e.av_cpb (first five or so actual votes cast for each cid and pbcid):")
    for cid in e.cids:
        for pbcid in sorted(e.rel_cp[cid]):
            myprint("    {}.{}:".format(cid, pbcid), end='')
            for j in range(min(5, len(e.bids_p[pbcid]))):
                bid = e.bids_p[pbcid][j]
                myprint(e.av_cpb[cid][pbcid][bid], end=' ')
            myprint()

    myprint("e.ro_c (reported outcome for each cid):")
    for cid in e.cids:
        myprint("    {}:{}".format(cid, e.ro_c[cid]))
