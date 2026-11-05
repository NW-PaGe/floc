import gzip
import random

import sourmash as sm

from floc.cli import main
from floc.qc import build_raw_global, filter_global, filter_to_global


def _mh(hashes, abund=True):
    mh = sm.MinHash(n=0, scaled=1, ksize=31, track_abundance=abund)
    if abund:
        mh.set_abundances({h: 2 for h in hashes})
    else:
        mh.add_many(hashes)
    return mh


def _map(sets, abund=True):
    return {f"s{i}": {"mh": _mh(h, abund), "cluster": None} for i, h in enumerate(sets)}


def test_raw_global_counts_samples_and_abundance():
    raw = build_raw_global(_map([{1, 2}, {2, 3}, {2}]))
    assert raw.n_samples == 3
    assert raw.counts[2] == [3, 6]
    assert raw.counts[1] == [1, 2]


def test_filter_global_is_strict():
    raw = build_raw_global(_map([{1, 2}, {2, 3}, {2}, {2}]))
    gmh, stats = filter_global(raw, 0.25)  # hash 1 and 3 are in exactly 25%
    assert set(gmh.hashes) == {2}
    assert gmh.hashes[2] == 8
    assert stats == {"n_total": 3, "n_kept": 1, "p_kept": 100 / 3}
    gmh, _ = filter_global(raw, 0)
    assert set(gmh.hashes) == {1, 2, 3}


def test_filter_to_global_keeps_raw_and_leaves_input():
    for abund in (True, False):
        fx = _map([{1, 2}, {2, 3}], abund)
        sig = {"db": {"mh": _mh({2, 4}, abund), "cluster": "1"}}
        raw = build_raw_global(fx | sig)
        fx_f, sig_f = filter_to_global(raw, 0.5, fx, sig)
        assert set(fx_f["s0"]["mh"].hashes) == {2}
        assert set(fx_f["s0"]["mh_raw"].hashes) == {1, 2}
        assert set(sig_f["db"]["mh"].hashes) == {2}
        assert sig_f["db"]["cluster"] == "1"
        assert set(fx["s0"]["mh"].hashes) == {1, 2}  # input unchanged
        assert "mh_raw" not in fx["s0"]
        assert fx_f["s0"]["mh"].track_abundance == abund


def _write_fasta(path, seq):
    path.write_text(f">{path.stem}\n{seq}\n")


def test_cli_writes_unfiltered_sigs(tmp_path):
    rng = random.Random(1)
    core = "".join(rng.choice("ACGT") for _ in range(20000))
    indir = tmp_path / "in"
    indir.mkdir()
    for i in range(10):
        acc = "".join(rng.choice("ACGT") for _ in range(3000))
        _write_fasta(indir / f"g{i}.fa", core + acc)
    out = tmp_path / "out"
    assert main([str(indir), "-o", str(out), "--scaled", "10", "--skip-qc"]) == 0

    for i in range(10):
        with gzip.open(out / "sigs" / f"g{i}.sig.gz", "rt") as fp:
            stored = sm.load_one_signature(fp.read()).minhash
        fresh = sm.MinHash(n=0, scaled=10, ksize=31)
        fresh.add_sequence((indir / f"g{i}.fa").read_text().split("\n")[1])
        assert set(stored.hashes) == set(fresh.hashes)
