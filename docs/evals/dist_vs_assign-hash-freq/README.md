# Evaluation: distance vs. assign hash frequency
When samples are added to an existing floc database, each new sample is compared with one merged sketch per cluster rather than with every sample. `--assign-hash-freq` sets which hashes go into that merged sketch: only hashes found in at least that fraction of the cluster's members. A value of 0 keeps every hash from every member (the union), while 0.6 keeps the hashes shared by most members (a consensus).

This evaluation tests whether that setting changes how consistent the clusters are when the same samples are added in batches of different sizes, at three distance thresholds.

## Summary
- **Recommended for consistent clustering: `--distance 0.1 --assign-hash-freq 0.6`.** No pair of samples within 100 SNPs was separated in any run, and at most 2 samples per run were placed differently from the reference. Every _A. baumannii_ and _S. aureus_ run matched its reference exactly.
- **For smaller clusters: `--distance 0.075 --assign-hash-freq 0.6`.** No close pairs were separated, and at most 5 samples per run were placed differently from the reference. The most diverse _E. coli_ cluster held 2,168 SNPs, compared with 4,134 at 0.1.
- **Do not use an assign hash frequency of 0.** At every distance it separated identical _A. baumannii_ samples (0 SNPs apart), separating up to 579 of the 1,140 close pairs. It reassigned up to 58 samples in a single run.
- **Avoid a distance of 0.05** at either assign hash frequency. Even at 0.6, it separated up to 75 close _A. baumannii_ pairs, including identical samples.

Pairs that floc separated were judged by their SNP distance. Separating samples within 10 SNPs of each other rules a combination out. Separating samples within 100 SNPs is a major penalty. The table combines all three organisms; worst run means the run (batch size 1, 10, 50 or the reference) with the most separated pairs or reassigned samples.

|Distance|Assign hash freq|Closest separated pair (SNPs)|Close pairs separated (worst run)|Samples reassigned (worst run)|Max SNPs within a cluster, reference (_E. coli_ / _A. baumannii_ / _S. aureus_)|Verdict|
|-|-|-|-|-|-|-|
|0.05|0|**0**|**570**|58|1,113 / 1,655 / 1,528|Ruled out|
|0.05|0.6|**0**|**75**|30|1,113 / 1,655 / 1,528|Ruled out|
|0.075|0|**0**|**579**|50|2,168 / 3,359 / 1,528|Ruled out|
|0.075|0.6|none|0|5|2,168 / 3,359 / 1,528|**Recommended for smaller clusters**|
|0.10|0|**0**|**569**|42|4,134 / 3,359 / 1,528|Ruled out|
|0.10|0.6|none|0|2|4,134 / 3,359 / 1,528|**Recommended for consistency**|

"None" means no pair within 100 SNPs was separated in any run. See [Metrics](#metrics) for definitions.

### Why an assign hash frequency of 0 fails
The assign hash frequency is only used when new samples are added to existing clusters; samples clustered together in one batch are compared with each other directly. That is why the reference run (all 100 samples in one batch) is identical at both values, and why only the smaller batch sizes differ.

With a value of 0, a cluster's merged sketch is the union of every member's hashes, so it grows with each member and with the cluster's diversity. The default assign metric (`avg`) averages two containments: how much of the sample is in the cluster sketch, and how much of the cluster sketch is in the sample. The second shrinks as the union grows, so a large or diverse cluster looks farther away from a new sample, even when the new sample is identical to one of its members. New samples then start new clusters instead of joining the one they belong in. This hits _A. baumannii_ hardest because most of its samples belong to one large, closely related group.

A value of 0.6 keeps the merged sketch close to the size of one genome, so the distance to a cluster does not depend on how large or diverse it has become.

## Datasets
The same 100 samples per organism were used for every combination.

|Organism|Assemblies|Source|Selection|
|-|-|-|-|
|_Escherichia coli_|100|Clinical isolates sequenced at the Washington State Public Health Laboratory (WAPHL), BioProject [PRJNA288601](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA288601)|Randomly selected by floc_val|
|_Acinetobacter baumannii_|100|Clinical isolates sequenced at WAPHL, BioProject [PRJNA288601](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA288601)|Randomly selected by floc_val|
|_Staphylococcus aureus_|100|BioProject [PRJNA533550](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA533550)|Randomly selected from the BioProject's assembly list with `tail -n +2 assemblies.tsv \| shuf \| head -n 100`|

## Design
Each combination was run with [floc_val](https://github.com/DOH-JDJ0303/floc_val), a Nextflow pipeline that runs floc on the same assemblies at several batch sizes and compares the final clusters with each other and with pairwise SNP distances from [SKA2](https://github.com/bacpop/ska.rust). Samples are added in the same seeded random order at every batch size. The run that adds all samples in a single batch (batch size 100) is the reference.

|Setting|Values|
|-|-|
|floc version|v1.2.4|
|Batch sizes|1, 10, 50 and 100 (100 = all samples at once, the reference)|
|Distance thresholds (`--distance`)|0.05, 0.075 and 0.10|
|Assign hash frequency (`--assign-hash-freq`)|0 and 0.6|
|Other floc options|floc v1.2.4 defaults (including `--assign-metric avg`)|

Output files are named `<organism>_<distance>_<assign hash frequency × 100>`. For example, `abaumanii_05_0` is a distance of 0.05 with an assign hash frequency of 0, and `abaumanii_07_5_60` is a distance of 0.075 with an assign hash frequency of 0.6.

## Metrics
|Metric|Meaning|
|-|-|
|Clusters|Number of clusters, including singletons|
|Max SNPs within a cluster|Largest SNP distance between two samples in the same cluster; shows how diverse the clusters are|
|Median SNPs within a cluster|Median SNP distance between pairs of samples in the same cluster|
|Samples reassigned|Fewest samples that would have to move to another cluster to reproduce the reference clusters; 0 means the run matches the reference exactly|
|Close pairs separated|Sample pairs within 100 SNPs of each other that were placed in different clusters; 0 means no closely related samples were separated|
|Min SNPs between clusters|Smallest SNP distance between two samples in different clusters; below 100 means closely related samples were separated, and 10 or less rules the combination out|

Samples reassigned was calculated from the cluster assignments in each tree file. The other statistics for each run are in the linked metrics files.

### Reading the plots
Each plot is a neighbor-joining tree of pairwise SNP distances with one column of tiles per batch size. Each tile is colored to match the reference cluster it overlaps most. New colors are clusters with no match in the reference, and light gray tiles are singletons. The plots are interactive HTML files, which GitHub does not display; download the linked `tree` file and open it in a browser to hover over tiles.

## Results: _E. coli_
31 pairs of samples are within 100 SNPs of each other.

|Distance|Assign hash freq|Clusters (reference)|Max SNPs within a cluster (reference)|Median SNPs within a cluster (reference)|Samples reassigned (batch size 1 / 10 / 50)|Close pairs separated (worst run)|Min SNPs between clusters (lowest run)|Files|
|-|-|-|-|-|-|-|-|-|
|0.05|0|65|1,113|280|6/5/2|**4 (12.9%)**|**18**|[tree](data/ecoli_05_0.nj_tree_clusters.html), [metrics](data/ecoli_05_0.run_metrics.tsv)|
|0.05|0.6|65|1,113|280|4/3/0|0|138|[tree](data/ecoli_05_60.nj_tree_clusters.html), [metrics](data/ecoli_05_60.run_metrics.tsv)|
|0.075|0|44|2,168|776|14/13/7|0|492|[tree](data/ecoli_07_5_0.nj_tree_clusters.html), [metrics](data/ecoli_07_5_0.run_metrics.tsv)|
|0.075|0.6|44|2,168|776|3/5/3|0|1,266|[tree](data/ecoli_07_5_60.nj_tree_clusters.html), [metrics](data/ecoli_07_5_60.run_metrics.tsv)|
|0.10|0|37|4,134|1,205|18/16/11|0|138|[tree](data/ecoli_10_0.nj_tree_clusters.html), [metrics](data/ecoli_10_0.run_metrics.tsv)|
|0.10|0.6|37|4,134|1,205|2/2/2|0|1,602|[tree](data/ecoli_10_60.nj_tree_clusters.html), [metrics](data/ecoli_10_60.run_metrics.tsv)|

- **Assign hash frequency 0.6:** no close pairs were separated at any distance, and at most 5 samples were reassigned in a run.
- **Assign hash frequency 0:** batch size 1 at 0.05 separated 4 close pairs (closest 18 SNPs). At 0.075 and 0.10, no close pairs were separated, but up to 14 and 18 samples were reassigned, and the batch runs had more clusters than the reference (up to 53 vs. 44, and 46 vs. 37).

## Results: _A. baumannii_
1,140 pairs of samples are within 100 SNPs of each other. Most of these samples belong to one large, closely related group, so this dataset is the strictest test of keeping close pairs together.

|Distance|Assign hash freq|Clusters (reference)|Max SNPs within a cluster (reference)|Median SNPs within a cluster (reference)|Samples reassigned (batch size 1 / 10 / 50)|Close pairs separated (worst run)|Min SNPs between clusters (lowest run)|Files|
|-|-|-|-|-|-|-|-|-|
|0.05|0|16|1,655|493|36/43/37|**570 (50.0%)**|**0**|[tree](data/abaumanii_05_0.nj_tree_clusters.html), [metrics](data/abaumanii_05_0.run_metrics.tsv)|
|0.05|0.6|16|1,655|493|30/26/9|**75 (6.6%)**|**0**|[tree](data/abaumanii_05_60.nj_tree_clusters.html), [metrics](data/abaumanii_05_60.run_metrics.tsv)|
|0.075|0|9|3,359|539|50/46/43|**579 (50.8%)**|**0**|[tree](data/abaumanii_07_5_0.nj_tree_clusters.html), [metrics](data/abaumanii_07_5_0.run_metrics.tsv)|
|0.075|0.6|9|3,359|539|1/1/0|0|2,437|[tree](data/abaumanii_07_5_60.nj_tree_clusters.html), [metrics](data/abaumanii_07_5_60.run_metrics.tsv)|
|0.10|0|8|3,359|544|22/30/42|**569 (49.9%)**|**0**|[tree](data/abaumanii_10_0.nj_tree_clusters.html), [metrics](data/abaumanii_10_0.run_metrics.tsv)|
|0.10|0.6|8|3,359|544|0/0/0|0|3,540|[tree](data/abaumanii_10_60.nj_tree_clusters.html), [metrics](data/abaumanii_10_60.run_metrics.tsv)|

- **Assign hash frequency 0.6:** at 0.075 and 0.10, no close pairs were separated, and at most 1 sample was reassigned. At 0.10, every batch size matched the reference exactly. At 0.05, smaller batch sizes divided the large group, separating up to 75 close pairs, including identical samples.
- **Assign hash frequency 0:** every distance separated identical samples. At 0.075 and 0.10, between 344 and 579 close pairs were separated at each batch size below 100; at 0.05, up to 570. Up to 50 samples were reassigned in a run.

## Results: _S. aureus_
4 pairs of samples are within 100 SNPs of each other, so this dataset says less about keeping close pairs together than the other two.

|Distance|Assign hash freq|Clusters (reference)|Max SNPs within a cluster (reference)|Median SNPs within a cluster (reference)|Samples reassigned (batch size 1 / 10 / 50)|Close pairs separated (worst run)|Min SNPs between clusters (lowest run)|Files|
|-|-|-|-|-|-|-|-|-|
|0.05|0|16|1,528|389|58/51/25|**1 (25.0%)**|**60**|[tree](data/staph_05_0.nj_tree_clusters.html), [metrics](data/staph_05_0.run_metrics.tsv)|
|0.05|0.6|16|1,528|389|1/1/1|0|412|[tree](data/staph_05_60.nj_tree_clusters.html), [metrics](data/staph_05_60.run_metrics.tsv)|
|0.075|0|16|1,528|389|43/39/14|**1 (25.0%)**|**60**|[tree](data/staph_07_5_0.nj_tree_clusters.html), [metrics](data/staph_07_5_0.run_metrics.tsv)|
|0.075|0.6|16|1,528|389|0/0/0|0|6,194|[tree](data/staph_07_5_60.nj_tree_clusters.html), [metrics](data/staph_07_5_60.run_metrics.tsv)|
|0.10|0|16|1,528|389|21/14/4|0|141|[tree](data/staph_10_0.nj_tree_clusters.html), [metrics](data/staph_10_0.run_metrics.tsv)|
|0.10|0.6|16|1,528|389|0/0/0|0|6,194|[tree](data/staph_10_60.nj_tree_clusters.html), [metrics](data/staph_10_60.run_metrics.tsv)|

- **Assign hash frequency 0.6:** at 0.075 and 0.10, every batch size matched the reference exactly. At 0.05, one sample left the largest reference cluster at every batch size below 100.
- **Assign hash frequency 0:** at 0.05 and 0.075, a pair 60 SNPs apart was separated, and up to 58 samples were reassigned. At 0.10, no close pairs were separated, but up to 21 samples were reassigned.
