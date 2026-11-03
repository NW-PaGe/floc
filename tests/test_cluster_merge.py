import sourmash as sm

from floc.cluster import _merge_cluster, assign_to_cluster


def _mh(hashes):
    mh = sm.MinHash(n=0, ksize=31, scaled=1, track_abundance=True)
    mh.set_abundances(hashes)
    return mh.to_frozen()


CORE = {h: 1 for h in range(1, 11)}
# hash 11 is in 1/4 members, hash 12 in 2/4
MEMBERS = {
    f"m{i}": {"mh": _mh(CORE | extra)}
    for i, extra in enumerate([{11: 1, 12: 1}, {12: 1}, {}, {}], 1)
}


def test_merge_keeps_hashes_in_min_fraction_of_members():
    assert set(_merge_cluster("1", MEMBERS, 0).hashes) == set(range(1, 13))
    assert set(_merge_cluster("1", MEMBERS, 0.5).hashes) == set(range(1, 11)) | {12}
    assert set(_merge_cluster("1", MEMBERS, 0.75).hashes) == set(range(1, 11))


def test_merge_sums_abundance():
    assert _merge_cluster("1", MEMBERS, 0.5).hashes[1] == 4


def test_filter_used_in_assignment():
    # sample carries hash 12, which half the members have
    q = {"q": {"mh": _mh(CORE | {12: 1})}}
    a, _ = assign_to_cluster(dict(q), {"1": MEMBERS}, 0.05, min_member_frac=0)
    assert a
    a, _ = assign_to_cluster(dict(q), {"1": MEMBERS}, 0.05, min_member_frac=0.75)
    assert not a
