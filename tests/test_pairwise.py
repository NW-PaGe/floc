import csv

import sourmash as sm

from floc.io_ops import write_pairwise
from floc.sm_ops import DistanceCache, _distance


def _mh(hashes):
    mh = sm.MinHash(n=0, ksize=31, scaled=1)
    mh.add_many(hashes)
    return mh


def test_cache_keeps_containment_direction():
    c = DistanceCache()
    c.set("b", "a", 0.3, a_in_b=0.6, b_in_a=0.8)  # here a="b", b="a"
    assert c.get_containments("b", "a") == (0.6, 0.8)
    assert c.get_containments("a", "b") == (0.8, 0.6)


def test_write_pairwise(tmp_path):
    m = {"x": {"mh": _mh(range(1, 11))}, "y": {"mh": _mh(range(1, 6))}}
    cache = DistanceCache()
    d = _distance("x", "y", mh_map=m, cache=cache)
    path = tmp_path / "p.csv"
    assert write_pairwise(str(path), [("x", "y"), ("x", "z")], cache) == 1  # z never compared
    write_pairwise(str(path), [("y", "x")], cache)  # appends without a second header
    rows = list(csv.DictReader(open(path)))
    assert [(r["id1"], r["id2"]) for r in rows] == [("x", "y"), ("y", "x")]
    assert float(rows[0]["id1_in_id2"]) == 0.5 and float(rows[0]["id2_in_id1"]) == 1.0
    assert float(rows[0]["distance"]) == d == 0.25
