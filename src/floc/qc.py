from __future__ import annotations

import os
import csv
import math
import logging
import statistics
from typing import Dict, Any, List, Optional, Tuple
import sourmash as sm
from collections import defaultdict
from dataclasses import dataclass

from .sm_ops import DistanceCache, _merged_distance

MHMap = Dict[str, Dict[str, Any]]


@dataclass
class RawGlobal:
    """Hold per-hash sample counts and total abundances across all samples."""
    counts: Dict[int, List[int]]  # hash -> [n_samples, total_abundance]
    n_samples: int
    template: sm.MinHash          # supplies ksize, scaled, num and seed


def build_raw_global(mh_map: MHMap) -> RawGlobal:
    """Count the samples that contain each hash and its total abundance."""
    if not mh_map:
        raise ValueError("mh_map is empty; cannot build the global hash.")

    counts: Dict[int, List[int]] = defaultdict(lambda: [0, 0])
    for rec in mh_map.values():
        for hash_val, abundance in rec["mh"].hashes.items():
            counts[hash_val][0] += 1
            counts[hash_val][1] += abundance

    template = next(iter(mh_map.values()))["mh"]
    return RawGlobal(counts=dict(counts), n_samples=len(mh_map), template=template)


def filter_global(raw: RawGlobal, min_freq: float) -> Tuple[sm.MinHash, dict]:
    """
    Filter hashes not observed in more than min_freq of samples.
    Weight each kept hash by its total abundance.
    Return the filtered global MinHash and counts of total and kept hashes.
    """
    n = raw.n_samples
    kept = {h: a for h, (n_h, a) in raw.counts.items() if (n_h / n) > min_freq}

    t = raw.template
    global_mh = sm.MinHash(
        n=0 if t.scaled else t.num,
        scaled=t.scaled,
        ksize=t.ksize,
        seed=t.seed,
        track_abundance=True,
    )
    global_mh.set_abundances(kept)

    n_total = len(raw.counts)
    stats = {
        "n_total": n_total,
        "n_kept": len(kept),
        "p_kept": 100 * len(kept) / (n_total if n_total else 1),
    }
    return global_mh, stats


def _warn_low_power(n_samples: int, freq: float, option: str, purpose: str) -> None:
    """Warn when too few samples exist for freq to filter any hash."""
    # A hash in one sample has frequency 1/n, so when 1/n > freq the filter keeps every hash.
    if freq > 0 and (1 / n_samples) > freq:
        min_needed = math.ceil(1 / freq - 1e-9)
        logging.warning(
            f"{purpose} has little power with {n_samples} samples: with {option} {freq}, "
            f"floc needs at least {min_needed} samples to filter rare k-mers."
        )


def filter_to_global(raw: RawGlobal, min_freq: float, *mh_maps: MHMap) -> Tuple[MHMap, ...]:
    """
    Filter hashes in each sample not observed in more than min_freq of samples.
    Keep each original sketch in 'mh_raw' so write_sigs writes it unfiltered.
    Return a new map for each map in mh_maps; leave the inputs unchanged.
    """
    _warn_low_power(raw.n_samples, min_freq, "--global-hash-freq", "Global hash filtering")
    global_mh, stats = filter_global(raw, min_freq)
    keep = set(global_mh.hashes)

    outs: List[MHMap] = []
    n_before: List[int] = []
    n_after: List[int] = []
    for mh_map in mh_maps:
        out: MHMap = {}
        for sid, rec in mh_map.items():
            mh_raw = rec.get("mh_raw", rec["mh"])
            mh = mh_raw.copy_and_clear()
            if mh_raw.track_abundance:
                mh.set_abundances({h: a for h, a in mh_raw.hashes.items() if h in keep})
            else:
                mh.add_many([h for h in mh_raw.hashes if h in keep])
            out[sid] = {**rec, "mh": mh, "mh_raw": mh_raw}
            n_before.append(len(mh_raw))
            n_after.append(len(mh))
            if len(mh) == 0:
                logging.warning(f"id={sid} has no hashes left after global hash filtering.")
        outs.append(out)

    logging.info(
        f"Global hash filter    : threshold={min_freq}; {stats['n_total']} hashes; "
        f"kept {stats['n_kept']} ({stats['p_kept']:.2f}%)"
    )
    if n_before:
        logging.info(
            f"Hashes per sample     : before mean={statistics.mean(n_before):.1f} "
            f"range=[{min(n_before)}, {max(n_before)}]; "
            f"after mean={statistics.mean(n_after):.1f} range=[{min(n_after)}, {max(n_after)}]"
        )
    return tuple(outs)


def global_containment(
    query_map: MHMap,
    raw: RawGlobal,
    *,
    min_hash_frac: float = 0.5,
    min_hash_freq: float = 0.05,
    outfile: Optional[str] = "global_containment_results.csv",
) -> MHMap:
    """
    Filter hashes in the raw global not observed in more than min_hash_freq of samples.
    Fail queries with less than min_hash_frac of their hashes in that global.
    Write per-query results to outfile and return the queries that pass.
    """
    if not query_map:
        logging.warning("global_containment: query_map is empty.")
        return {}

    _warn_low_power(raw.n_samples, min_hash_freq, "--min-hash-freq", "QC")

    # 1) Filter the raw global for QC
    subj_global, subj_stats = filter_global(raw, min_hash_freq)
    mh_global = {"global": {"mh": subj_global}}

    # 2) Compute each query's containment in the QC global
    cache = DistanceCache()
    ids: List[str] = []
    fracs: List[float] = []
    results: List[dict] = []

    for qid, qinfo in query_map.items():
        local_map = {qid: qinfo} | mh_global
        f = 1 - _merged_distance(qid, "global", mh_map=local_map, cache=cache)
        ids.append(qid)
        fracs.append(f)
        results.append({
            "id": qid,
            "frac_hash_in_global": f,
            "within_threshold": f >= min_hash_frac
        })

    mean_f = statistics.mean(fracs) if fracs else 0.0
    sd_f = statistics.pstdev(fracs) if len(fracs) > 1 else 0.0
    min_f, max_f = min(fracs), max(fracs)
    failing = [r for r in results if not r["within_threshold"]]
    failing_ids = {r["id"] for r in failing}

    # 3) Logging summary then only failures
    start_msg = "=== Global Containment (QC): Queries vs Filtered Subject Global ==="
    logging.info(start_msg)
    logging.info(f"Queries               : {len(query_map)}")
    logging.info(f"Subjects              : {raw.n_samples}")

    logging.info(f"Global hash frequency : threshold={min_hash_freq}; {subj_stats['n_total']} hashes; kept {subj_stats['n_kept']} ({subj_stats['p_kept']:.2f}%)")
    logging.info(f"Query hash fraction   : threshold={min_hash_frac}; mean={mean_f:.4f} stdev={sd_f:.4f} range=[{min_f:.4f}, {max_f:.4f}]")

    if failing:
        logging.warning(f"Queries below threshold (frac_hash_in_global < {min_hash_frac:.4f}):")
        for r in failing:
            logging.warning(f"id={r['id']} hash_freq={r['frac_hash_in_global']:.4f}")
    else:
        logging.info("All queries are within the hash frequency threshold.")

    # 4) Save per-query results
    if outfile:
        outdir = os.path.dirname(outfile)
        if outdir and not os.path.exists(outdir):
            os.makedirs(outdir, exist_ok=True)
        with open(outfile, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["id", "frac_hash_in_global", "within_threshold"]
            )
            writer.writeheader()
            writer.writerows(results)
        logging.info(f"Saved per-query results to {outfile}")

    # 5) Return a new query_map without failing queries
    query_map_pass: MHMap = {k: v for k, v in query_map.items() if k not in failing_ids}

    logging.warning("="*len(start_msg))
    return query_map_pass