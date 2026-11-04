# Changelog

All notable changes to floc are documented in this file.

## [1.2.4] - 2026-11-03

### Changed
- Default `--distance` raised from 0.03 to 0.075, so samples up to about 7.5%
  apart (1 - containment) are now clustered together. In batch-size validation
  on 100 assemblies each of _E. coli_, _A. baumannii_ and _S. aureus_, 0.075
  was the lowest threshold tested at which samples within 100 SNPs of each
  other always ended up in the same cluster, however samples were added (see
  `docs/validation.md`). Cluster assignments may differ from v1.2.3 on the
  same inputs; use `--distance 0.03` to reproduce the previous behaviour.
- Default `--assign-hash-freq` raised from 0.5 to 0.6, so each existing
  cluster is represented by hashes found in at least 60% of its members when
  new samples are assigned. Use `--assign-hash-freq 0.5` for the previous
  behaviour.

## [1.2.3] - 2026-11-02

### Changed
- When assigning new samples, each existing cluster is now represented only by
  hashes found in at least `--assign-hash-freq` of its members (default 0.5).
  Previously the cluster's merged sketch kept every hash from every member, so
  it kept growing with k-mers carried by only one or a few members.
- The default `--assign-metric` is `avg` again. With the merged sketch limited
  to hashes most members share, the cluster-in-sample containment falls much
  less as clusters grow, which is what made `avg` unreliable in v1.2.1.
- Samples left over after each DBSCAN batch are now assigned using
  `--assign-metric` and `--assign-hash-freq`; previously this step always used
  `query` with every hash. This only affects runs with more new samples than
  `--batch`.

### Added
- `--assign-hash-freq` option (see above). `0` keeps every hash.
- `--dbscan-metric {avg,min,max}` sets how the containments in both directions
  between two samples are combined into the distance used by DBSCAN
  (default `avg`, the previous behaviour). The same distances are used for
  `--pairwise` and `--plot`.
- The containments and distances behind each step are saved to the output
  directory, with the columns `id1,id2,id1_in_id2,id2_in_id1,distance`:
  - `assign.csv`: each new sample against each existing cluster (replaced
    each run);
  - `dbscan.csv`: sample pairs compared by DBSCAN. Each run in the same output
    directory adds to this file, so no comparison is lost;
  - `plot.csv`: every sample pair used for the plots, with `--plot` (replaced
    each run).

### Fixed
- Between-batch assignment no longer reuses distances cached for an earlier,
  smaller version of a cluster, or confuses a sample with a cluster of the
  same name.

### Removed
- Committed build artifacts (`build/`, `src/floc.egg-info/`). A stale `build/`
  folder could be installed in place of the current source; both are now
  ignored via `.gitignore`.

To reproduce v1.2.2 assignments use `--assign-metric query --assign-hash-freq 0`;
for v1.2.1 use `--assign-hash-freq 0`.

## [1.2.2] - 2026-10-30

### Changed
- Reverted the default `--assign-metric` from `avg` back to `query`
  (fraction of the sample's hashes found in the cluster's merged sketch), the
  behaviour of v1.1 and earlier. Average containment only improved assignment
  while clusters were small; as a cluster's merged sketch grows, the
  cluster-in-sample containment shrinks and drags the average down, so new
  samples increasingly fail to join clusters they belong to.
  Use `--assign-metric avg` to get the v1.2.1 behaviour.

## [1.2.1] - 2026-10-30

### Changed
- New samples are now assigned to existing clusters using the **average** of the
  sample-in-cluster and cluster-in-sample containment against each cluster's
  merged sketch. Previously only sample-in-cluster containment was used.
  Cluster assignments may differ from v1.1 on the same inputs; use
  `--assign-metric query` to reproduce the previous behaviour.

### Added
- `--assign-metric {query,min,max,avg}` option to choose the containment used
  for cluster assignment (default: `avg`).
- QC warning when there are too few samples for `--min-hash-freq` to filter
  rare k-mers (in which case no sample can fail QC).

### Fixed
- Samples are now assigned to the *closest* cluster within the distance
  threshold. Previously a sample could be assigned to the first matching
  cluster rather than the nearest one.
- Ties between equally close clusters are broken deterministically by taking
  the cluster label that sorts first alphabetically.
- floc now exits with status 1 (instead of 0) when samples fail QC and
  `--ignore-qc` is not set.
- `floc --version` reported `1.0`; the version is now defined once in
  `floc/__init__.py` and read by both the CLI and the package metadata.
- Clarified the QC failure message (`frac_hash_in_global < threshold`).
- README examples used a non-existent `-i` flag and the wrong signature
  directory name (`sig/` instead of `sigs/`).

### Removed
- Committed build artifacts (`build/`, `src/floc.egg-info/`); these are now
  ignored via `.gitignore`.

## Earlier releases

See the `v1.1`, `v1.0.1` and `v1.0.0` tags on GitHub.
