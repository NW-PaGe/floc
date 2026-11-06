# Floc :beer:
Floc is an iterative genome clustering tool. Genome assemblies are placed into new or existing clusters based on pairwise genetic distances. Genetic distance is estimated using the Sourmash k-mer containment method.

:rainbow: **Fun Fact:** Floc is short for _flocculate_, which is a term often used in fermentation (like a **sourmash**!) to describe the coalescence of suspended particles (yeast, protein, etc.,)!

## Installation
### From source
```
git clone https://github.com/NW-PaGe/floc
conda create -n floc python=3.11
conda activate floc
pip install "setuptools<70" wheel
pip install --no-build-isolation floc/
```

### With Docker
```
docker run --rm -v "$PWD":/work -w /work \
    public.ecr.aws/o8h2f0o1/floc:1.2.4 \
    floc --help
```

## Usage
```
usage: floc [-h] [-o OUTDIR] [-d DISTANCE] [--ksize KSIZE] [--scaled SCALED] [--batch BATCH] [--ignore-qc] [--skip-qc]
            [--min-hash-freq MIN_HASH_FREQ] [--min-hash-frac MIN_HASH_FRAC] [--overwrite] [--plot] [--pairwise]
            [--assign-metric {avg,min,max,query}] [--assign-hash-freq ASSIGN_HASH_FREQ]
            [--dbscan-metric {avg,min,max}] [--version]
            input [input ...]

floc: Genomic clustering tool for population-level surveillance

positional arguments:
  input                 Files or directories containing input files (FASTA, FASTQ, or Sourmash signatures)

options:
  -h, --help            show this help message and exit
  -o OUTDIR, --outdir OUTDIR
                        Output directory
  -d DISTANCE, --distance DISTANCE
                        Distance threshold used to create clusters (default: 0.1)
  --ksize KSIZE         k-mer size
  --scaled SCALED       Scaling factor for signatures
  --batch BATCH         Number of sequences to cluster per batch
  --ignore-qc           Remove samples that fail QC without failing
  --skip-qc             Skip QC
  --min-hash-freq MIN_HASH_FREQ
                        QC: build the global hash from k-mers found in more than this fraction of all samples
                        (default: 0.05)
  --min-hash-frac MIN_HASH_FRAC
                        QC: a sample fails if less than this fraction of its k-mers are in the global hash built with
                        --min-hash-freq (default: 0.5)
  --overwrite           Overwrite existing signature files
  --plot                Create PCoA and NJ tree plots. Can take a long time with many samples.
  --pairwise            Compute pairwise distance matrix for each cluster with a new sample.
  --assign-metric {avg,min,max,query}
                        Containment metric used to assign new samples to existing clusters: avg, min, max, or query
                        (default: avg)
  --assign-hash-freq ASSIGN_HASH_FREQ
                        When assigning new samples, represent each existing cluster only by hashes found in at least
                        this fraction of its members; 0 uses every hash (default: 0.6)
  --dbscan-metric {avg,min,max}
                        How the containments in both directions between two samples are combined into the distance
                        used by DBSCAN; also used for --pairwise and --plot (default: avg)
  --version             show program's version number and exit
```

## Outputs
|File / Directory|Description|
|-|-|
|`clusters.csv`|Cluster results for each sample in input|
|`sigs/*`|Sourmash signature files. These contain cluster information in the `filename` field and can be re-used for iterative clustering|
|`pcoa.html`|PCoA plot generated from all pairwise distances. Only created if run with `--plot`|
|`nj_tree.html` & `nj_tree.nwk`|Neighbor-joining tree plot and newick file generated from all pairwise distances. Only created if run with `--plot`|
|`global_containment.csv`|Per-sample summary of minhash global containment|
|`assign.csv`|Each new sample compared with the merged sketch of each existing cluster during assignment (`id2` is the cluster label)|
|`dbscan.csv`|Pairwise comparisons between samples clustered with DBSCAN. New runs add to this file rather than replacing it, so it keeps a record of every DBSCAN comparison made in this output directory|
|`plot.csv`|Pairwise comparisons between all samples used for the plots. Only created if run with `--plot`|

`assign.csv`, `dbscan.csv` and `plot.csv` share the columns `id1,id2,id1_in_id2,id2_in_id1,distance`: the fraction of `id1`'s hashes found in `id2`, the reverse, and the distance floc used (set by `--assign-metric` for `assign.csv` and by `--dbscan-metric` for `dbscan.csv` and `plot.csv`). Each file is only written when that step runs. `assign.csv` and `plot.csv` are replaced on each run; `dbscan.csv` is added to.

## Example
### 1. Running for the first time
```
floc assemblies/ -o db/
```

### 2. Running any time after
```
floc new_assemblies/ db/sigs/ -o db/
```