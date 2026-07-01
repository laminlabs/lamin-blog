---
title: "Scaling anndata training to the terra-byte scale with annbatch"
date: 2026-06-25
author: felix-fischer, ilan-gold, fabian-theis, falexwolf
affiliation:
  felix-fischer: Lamin Labs, Munich
  ilan-gold: Helmholtz Munich
  fabian-theis: Helmholtz Munich
  falexwolf: Lamin Labs, Munich
---

The demand for AI in biology is accelerating at an unprecedented rate, with state-of-the-art models now routinely trained on datasets exceeding the terabyte scale. This growth has surfaced a critical bottleneck: disk-backed data loading. While `MappedCollection` was a pioneer in solving this — enabling larger-than-memory training and seamless integration with the `anndata` ecosystem — it hit a ceiling on performance. Its loading speeds often fall significantly short of the throughput required by modern GPUs, leading to extensive resource waste or GPUs that are mostly idle. To bridge this gap, we developed `annbatch`: a high-performance data loader that maintains full `anndata` integration and thereby shifting the bottleneck back to the hardware's actual processing limits.

To achieve the performance required for modern models like scVI — which demand a 50–100x speedup over the loading speed obtained by `MappedCollection` — we focused on two fundamental architectural shifts:

- **From Random to Chunked Pseudo-Random Access:** Traditional fully random access is an I/O killer for disk-backed data. By switching to a chunked pseudo-random access pattern, we significantly reduce disk seek time and overhead, allowing for much higher throughput.
- **From HDF5 to Zarr:** We moved away from the older HDF5-backed `anndata` format in favor of the Zarr backed `anndata` format. Zarr's cloud-native, chunk-based storage is designed for high-concurrency workloads, providing the parallelization needed to keep up with modern GPUs.

Combined with many low-level optimizations, these changes effectively remove the I/O bottleneck, finally allowing the hardware to run at full throttle.

But does this theoretical speed translate to the real world? Let's look at the Tahoe-100M atlas. Training an scVI model on a dataset of this magnitude is a high-throughput challenge; if the data loader can't keep up, the hardware sits idle.

![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/cuS0VjLS1upOkfzL0000.png)

**Figure 1**: Wall-clock time per iteration as a function of samples per second for training an scVI model or simple linear model. `MappedCollection` is loading-limited at ~1,195 samples/s, while `annbatch` shifts the regime to compute-limited at ~84,000 samples/s — a ~70x speedup that collapses a 24-hour training epoch to roughly 15 minutes.

![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/KfBn3sfRNJLtqMEn0000.png)

**Figure 2**: Raw dataloader throughput on the Tahoe-100M full collection across four configurations. AnnBatch (chunk=512) reaches 63,138 samples/s — a ~61x improvement over `MappedCollection` at 1,033 samples/s.

![](https://lamin-site-assets.s3.amazonaws.com/.lamindb/yoNFOJbnwdn4dNa70000.png)

**Figure 3**: Data lineage tracked by LaminDB — from raw h5ads through Zarr conversion to the benchmarking run and plot artifacts. Each arrow represents a registered transform with full input/output linkage.

Using `MappedCollection`, the bottleneck was so severe that a single training epoch required almost a full day (24 hours). By switching to `annbatch`, we slashed that time to roughly 15 minutes. By shifting the bottleneck back to the hardware's actual processing power, we've made terabyte-scale biological training not just possible, but highly efficient.

The transition from `MappedCollection` to `annbatch` represents more than just a performance patch; it is a fundamental shift in how we handle massive biological datasets. By moving to a Zarr-backed architecture and implementing chunked pseudo-random access, we have effectively ended the era of "GPU starvation." When a 24-hour training epoch shrinks to just 15 minutes, the research cycle changes. You no longer wait a week to see if a model converges — you see the results before your next coffee break.

Because `annbatch` stays native to the `anndata` ecosystem, this efficiency isn't locked into a single niche. It provides a scalable, high-performance foundation across a vast array of biological data types. To give you a sense of the scope, here are just a few examples of what you can now scale:

- 💊 **Large-scale scRNA-seq perturbations:** Model complex cellular responses across millions of cells without I/O lag.
- 🧬 **Rare-variant WGS data:** Process massive genomic arrays with the same ease as a standard expression matrix.
- 📷 **Cropped microscopy image tiles:** Train on high-throughput imaging data without abandoning your metadata structures.

These modalities are just the beginning. As biological datasets continue to grow into the tens of terabytes, `annbatch` ensures that your hardware — not your data loader — is the only limit to your discovery.

Ready to accelerate your training? Explore the code, check out the benchmarks, and read the full technical breakdown at the links below:

- **GitHub:** [github.com/scverse/annbatch](https://github.com/scverse/annbatch)
- **Read the Paper:** [arXiv:2604.01949](https://arxiv.org/abs/2604.01949)
