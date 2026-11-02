# Changelog

All notable changes to floc are documented in this file.

## [1.2.2] - 2026-10-30

### Changed
- Reverted the default `--assign-metric` from `avg` back to `query`
  (fraction of the sample's hashes found in the cluster's merged sketch), the
  behaviour of v1.1 and earlier. Average containment only improved assignment
  while clusters were small; as a cluster's merged sketch grows, the
  cluster-in-sample containment shrinks and drags the average down, so new
  samples increasingly fail to join clusters they belong to.
- When assigning new samples, each existing cluster is now represented only by
  hashes found in at least `--cluster-hash-freq` of its members (default: the
  `--min-hash-freq` value, 0.05). Previously the merged sketch kept every hash
  from every member, so it kept growing with k-mers carried by only one or a
  few members. Use `--cluster-hash-freq 0` to keep every hash.

### Added
- `--cluster-hash-freq` option (see above).
- The containments and distances behind each step are saved to the output
  directory: `assign.csv` (each new sample against each existing cluster),
  `dbscan.csv` (sample pairs clustered with DBSCAN) and, with `--plot`,
  `plot.csv` (all sample pairs used for the plots). `dbscan.csv` is added to
  by each run in the same output directory rather than replaced, so no DBSCAN
  comparison is lost; `assign.csv` and `plot.csv` are replaced each run.

### Fixed
- Samples left over after each DBSCAN batch are now assigned using
  `--assign-metric` and `--cluster-hash-freq`; previously this step always used
  `query` with every hash. It also no longer reuses distances cached for an
  earlier, smaller version of a cluster, or confuses a sample with a cluster
  that has the same name.

To reproduce v1.2.1 assignments use `--assign-metric avg --cluster-hash-freq 0`;
for v1.1 use `--cluster-hash-freq 0`.

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
