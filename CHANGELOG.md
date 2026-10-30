# Changelog

All notable changes to floc are documented in this file.

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
