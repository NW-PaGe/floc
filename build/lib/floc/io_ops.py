from typing import List, Tuple, Dict, Optional, Any
import logging, os, csv, sys

SEQ_EXTS = {'.fa', '.fasta', '.fna', '.fq', '.fastq'}

# Pairwise comparison files written to the output directory
PAIR_FILES = {"assign": "assign.csv", "dbscan": "dbscan.csv", "plot": "plot.csv"}
PAIR_FIELDS = ["id1", "id2", "id1_in_id2", "id2_in_id1", "distance"]


def write_pairwise(path: str, pairs, cache) -> int:
    """Append one row per (id1, id2) pair to the CSV at `path`, taking the
    distance and both containments from `cache` (a sm_ops.DistanceCache).

    The header is written when the file is new, so repeated calls during a run
    (e.g. one per DBSCAN batch) build up a single file. Pairs that were never
    compared are skipped. Returns the number of rows written.
    """
    new = not os.path.exists(path) or os.path.getsize(path) == 0
    n = 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(PAIR_FIELDS)
        for a, b in pairs:
            d = cache.get(a, b)
            c = cache.get_containments(a, b)
            if d is None or c is None:
                continue
            w.writerow([a, b, c[0], c[1], d])
            n += 1
    return n


def clear_pairwise(outdir: str) -> None:
    """Remove pairwise files left by a previous run in `outdir`."""
    for name in PAIR_FILES.values():
        p = os.path.join(outdir, name)
        if os.path.exists(p):
            os.remove(p)

def drop_ext(filepath: str) -> str:
    """
    Return basename without compression and primary extension.
    Handles names like: sample.R1.fastq.gz -> sample.R1
    Also: sample.sig.gz -> sample, sample.fa -> sample
    """
    base = os.path.basename(filepath)
    # strip one compression layer if present
    if base.lower().endswith('.gz'):
        base = os.path.splitext(base)[0]
    # strip primary extension (e.g., .fastq, .fa, .sig)
    base = os.path.splitext(base)[0]
    return base

def _is_sig(path: str) -> bool:
    low = path.lower()
    return low.endswith('.sig') or low.endswith('.sig.gz')

def _is_seq(path: str) -> bool:
    """
    Checks for (fa|fasta|fna|fq|fastq) with or without .gz
    """
    low = path.lower()
    if low.endswith('.gz'):
        low = low[:-3]  # remove .gz
    _, ext = os.path.splitext(low)
    return ext in SEQ_EXTS

def parse_input(inputs: List[str], overwrite: bool) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Scan a list of directories (or files) and build:
      fx   : {basename -> seq file path} for FASTA/FASTQ
      sigs : {basename -> signature file path} for .sig/.sig.gz

    Rules:
      - Basenames must be unique within each category.
      - If both seq and sig exist for the same basename:
          * overwrite=True  -> keep the seq; drop the existing sig (it will be regenerated)
          * overwrite=False -> error out with guidance
    """
    files: List[str] = []
    for p in inputs:
        if os.path.isdir(p):
            for f in os.listdir(p):
                fp = os.path.join(p, f)
                if os.path.isfile(fp):
                    files.append(fp)
        elif os.path.isfile(p):
            files.append(p)
        else:
            logging.warning(f"Skipping non-existent path: {p}")

    fx: Dict[str, str] = {}
    sigs: Dict[str, str] = {}

    # Classify
    for f in files:
        name = drop_ext(f)
        if _is_sig(f):
            if name in sigs:
                logging.error(f"Error: Signature files must have unique basenames ({name})")
                sys.exit(1)
            sigs[name] = f
        elif _is_seq(f):
            if name in fx:
                logging.error(f"Error: FASTA/FASTQ files must have unique basenames ({name})")
                sys.exit(1)
            fx[name] = f
        else:
            # Not a recognized seq or sig; ignore quietly or log debug
            logging.debug(f"Ignoring non-seq/non-sig file: {f}")

    # Resolve conflicts & keep non-conflicting signatures
    sigs_checked: Dict[str, str] = {}
    for k, v in sigs.items():
        if k in fx:
            msg = f"Multiple files (FASTA/FASTQ and signature) provided for {k}. "
            if overwrite:
                logging.warning(msg + "The signature file will be overwritten.")
                # Intentionally drop the signature entry so it can be regenerated.
                continue
            else:
                logging.error(msg + "Remove the FASTA/FASTQ or re-run with '--overwrite'.")
                sys.exit(1)
        # No conflict → keep this signature
        sigs_checked[k] = v

    return fx, sigs_checked

def write_cluster_csv(mh_clust: Dict[str, Dict[str, Any]], outdir: str, filename: str = "clusters.csv") -> str:
    """
    Write a CSV summarizing the final clusters.

    Parameters
    ----------
    mh_clust : dict
        Dictionary of clusters in the form:
            { cluster_label: { sid: {'mh': MinHash, 'cluster': cluster_label, ...}, ... }, ... }

    outdir : str
        Directory where the CSV will be written.

    filename : str, optional
        Output CSV filename (default: 'clusters.csv').

    Returns
    -------
    str
        Path to the written CSV file.
    """
    if not mh_clust:
        logging.warning("No clusters found — skipping CSV export.")
        return ""

    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, filename)

    rows = []
    for cluster_label, members in mh_clust.items():
        for sid in sorted(members.keys()):
            rows.append({"sid": sid, "cluster": cluster_label})

    # Sort by cluster then sid for clean reproducibility
    rows.sort(key=lambda r: (r["cluster"], r["sid"]))

    with open(outpath, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["sid", "cluster"])
        writer.writeheader()
        writer.writerows(rows)

    logging.info(f"Wrote cluster summary CSV with {len(rows)} entries → {outpath}")