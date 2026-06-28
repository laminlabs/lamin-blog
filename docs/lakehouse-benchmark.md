---
title: "Lakehouse Engineering: Benchmarking Metadata-Driven Query Optimization"
date: 2026-06-25
author: Koncopd, falexwolf
affiliation:
  Koncopd: Lamin Labs, Munich
  falexwolf: Lamin Labs, Munich
db: https://lamin.ai/laminlabs/lakehouse-benchmarks
---
Every genomics data scientist eventually hits the same wall. The biology is worked out. The pipeline is written. And then — before a single query can run — comes the decision of how to actually get at the data: which engine to use, whether to ingest or read in place, how to handle six Parquet files that need to behave like one table.

This report compares five query approaches over a shared LaminDB collection of 1000 Genomes CNV calls — 8,929 rows across six DRAGEN Parquet shards — running the same six-step user journey in each: access, per-sample statistics, recurrent region detection, filtered query, sample append, and schema change. The five approaches are PyArrow, Polars, DuckDB, Apache Iceberg, and LanceDB. All timing results are single-run measurements on SageMaker (ml.t3.medium) in store mode unless otherwise stated; they are provided as indicative comparisons on a small dataset, not rigorous benchmarks.

## Background and motivation

A copy-number variant analysis typically involves per-sample statistics, recurrent region identification across samples, filtered positional queries, incremental sample appends, and schema evolution. These operations are routine in genomics but span the full read-write surface of a query engine. Choosing an engine commits a team to a specific answer for all of them simultaneously: an engine that makes querying concise may make schema changes ephemeral; an engine that provides durable writes may require an upfront ingestion step; an engine that copies data into its own format removes it from the source lineage graph.

This report measures all six operations end-to-end across five engines to make those tradeoffs explicit.

## One shared dataset

All five approaches read from the same collection of parquet files:

```python
import lamindb as ln
collection = ln.Collection.get("K6X8Ejk3fjgAZT6h0000")  # 1000 Genomes CNV calls
```

Three engines — PyArrow, Polars, and DuckDB — read the source Parquet files in place. Two — Iceberg and LanceDB — ingest the data into their own format before querying.

---

## Setup

::::::{tab-set}
:::::{tab-item} PyArrow
`collection.open()` returns a lazy PyArrow dataset backed by S3. No data is read until a query is issued.

```python
dataset = collection.open()   # lazy PyArrow dataset over the 6 shards
```
:::::

:::::{tab-item} Polars
`collection.open(engine="polars")` returns a context manager yielding a Polars LazyFrame backed by S3. No data is read until `.collect()` is called.

```python
with collection.open(engine="polars") as lazy_df:
    ...   # lazy_df is a Polars LazyFrame backed by S3
```
:::::

:::::{tab-item} DuckDB
DuckDB registers a view over the collection's S3 paths via `httpfs`. The view is lazy — nothing is read until a SQL query is issued.

```python
import duckdb
con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute("CREATE OR REPLACE SECRET s3 (TYPE s3, PROVIDER credential_chain);")

s3_paths = [str(a.path) for a in collection.ordered_artifacts.all()]
con.execute(f"CREATE OR REPLACE VIEW cnv_vcf AS SELECT * FROM read_parquet({s3_paths})")
```
:::::

:::::{tab-item} Iceberg
Iceberg requires a full materialisation of the LaminDB collection before ingestion into a catalog-managed table on S3.

```python
from pyiceberg.catalog.sql import SqlCatalog

arrow = collection.open().to_table()   # 7.3s — full S3 read

catalog = SqlCatalog("local", uri="sqlite:///iceberg_catalog.db", warehouse=WAREHOUSE)
catalog.create_namespace("genomics")
table = catalog.create_table("genomics.cnv_vcf", schema=arrow.schema)
table.overwrite(arrow)   # 1.36s — writes Parquet + metadata to S3
```

:::::

:::::{tab-item} LanceDB
LanceDB requires a full materialisation of the LaminDB collection and ingestion into Lance columnar format on S3. LanceDB is the only engine in this comparison that copies data out of the source Parquet files.

```python
import lancedb

arrow = collection.open().to_table()   # 7.4s — full S3 read
db = lancedb.connect(WAREHOUSE)
table = db.create_table("cnv_vcf", data=arrow, mode="overwrite")   # 0.15s
```
:::::
::::::

**Setup summary:**

| Engine | Lines | Time | Ingest required |
|---|---|---|---|
| PyArrow | 1 | ~0s | No |
| Polars | 1 | ~0s | No |
| DuckDB | 5 | ~1s | No |
| Iceberg | ~20 | ~8.7s | No (wraps source Parquet) |
| LanceDB | 3 | ~7.6s | Yes (copies to Lance format) |

<!-- PLOT: setup_cost.svg -->
<?xml version="1.0" encoding="utf-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns:xlink="http://www.w3.org/1999/xlink" width="568.243437pt" height="352.558984pt" viewBox="0 0 568.243437 352.558984" xmlns="http://www.w3.org/2000/svg" version="1.1">
 <metadata>
  <rdf:RDF xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:cc="http://creativecommons.org/ns#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
   <cc:Work>
    <dc:type rdf:resource="http://purl.org/dc/dcmitype/StillImage"/>
    <dc:date>2026-06-25T14:37:50.742270</dc:date>
    <dc:format>image/svg+xml</dc:format>
    <dc:creator>
     <cc:Agent>
      <dc:title>Matplotlib v3.11.0, https://matplotlib.org/</dc:title>
     </cc:Agent>
    </dc:creator>
   </cc:Work>
  </rdf:RDF>
 </metadata>
 <defs>
  <style type="text/css">*{stroke-linejoin: round; stroke-linecap: butt}</style>
 </defs>
 <g id="figure_1">
  <g id="patch_1">
   <path d="M 0 352.558984 
L 568.243437 352.558984 
L 568.243437 0 
L 0 0 
z
" style="fill: #ffffff"/>
  </g>
  <g id="axes_1">
   <g id="patch_2">
    <path d="M 40.925781 327.358125 
L 561.043437 327.358125 
L 561.043437 28.318125 
L 40.925781 28.318125 
z
" style="fill: #ffffff"/>
   </g>
   <g id="patch_3">
    <path d="M 64.567493 327.358125 
L 117.10463 327.358125 
L 117.10463 327.358086 
L 64.567493 327.358086 
z
" clip-path="url(#p843ab579ba)" style="fill: #4c72b0; opacity: 0.9"/>
   </g>
   <g id="patch_4">
    <path d="M 169.641767 327.358125 
L 222.178904 327.358125 
L 222.178904 327.358078 
L 169.641767 327.358078 
z
" clip-path="url(#p843ab579ba)" style="fill: #8b5cf6; opacity: 0.9"/>
   </g>
   <g id="patch_5">
    <path d="M 274.716041 327.358125 
L 327.253178 327.358125 
L 327.253178 302.506622 
L 274.716041 302.506622 
z
" clip-path="url(#p843ab579ba)" style="fill: #dd8452; opacity: 0.9"/>
   </g>
   <g id="patch_6">
    <path d="M 379.790315 327.358125 
L 432.327452 327.358125 
L 432.327452 124.759316 
L 379.790315 124.759316 
z
" clip-path="url(#p843ab579ba)" style="fill: #55a868; opacity: 0.9"/>
   </g>
   <g id="patch_7">
    <path d="M 484.864589 327.358125 
L 537.401726 327.358125 
L 537.401726 130.577656 
L 484.864589 130.577656 
z
" clip-path="url(#p843ab579ba)" style="fill: #c44e52; opacity: 0.9"/>
   </g>
   <g id="patch_8">
    <path d="M 64.567493 327.358086 
L 117.10463 327.358086 
L 117.10463 327.358086 
L 64.567493 327.358086 
z
" clip-path="url(#p843ab579ba)" style="fill: #4c72b0; opacity: 0.4"/>
   </g>
   <g id="patch_9">
    <path d="M 169.641767 327.358078 
L 222.178904 327.358078 
L 222.178904 327.358078 
L 169.641767 327.358078 
z
" clip-path="url(#p843ab579ba)" style="fill: #8b5cf6; opacity: 0.4"/>
   </g>
   <g id="patch_10">
    <path d="M 274.716041 302.506622 
L 327.253178 302.506622 
L 327.253178 302.506622 
L 274.716041 302.506622 
z
" clip-path="url(#p843ab579ba)" style="fill: #dd8452; opacity: 0.4"/>
   </g>
   <g id="patch_11">
    <path d="M 379.790315 124.759316 
L 432.327452 124.759316 
L 432.327452 88.126125 
L 379.790315 88.126125 
z
" clip-path="url(#p843ab579ba)" style="fill: url(#ha18f562144); opacity: 0.4"/>
   </g>
   <g id="patch_12">
    <path d="M 484.864589 130.577656 
L 537.401726 130.577656 
L 537.401726 126.527563 
L 484.864589 126.527563 
z
" clip-path="url(#p843ab579ba)" style="fill: url(#hf5b8d32bc1); opacity: 0.4"/>
   </g>
   <g id="matplotlib.axis_1">
    <g id="xtick_1">
     <g id="line2d_1">
      <defs>
       <path id="mf52e499059" d="M 0 0 
L 0 3.5 
" style="stroke: #000000; stroke-width: 0.8"/>
      </defs>
      <g>
       <use xlink:href="#mf52e499059" x="90.836061" y="327.358125" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_1">
      <!-- PyArrow -->
      <g transform="translate(48.440515 342.716406) scale(0.11 -0.11)">
       <defs>
        <path id="DejaVuSans-39" d="M 1831 0 
L 50 4666 
L 709 4666 
L 2188 738 
L 3669 4666 
L 4325 4666 
L 2547 0 
L 1831 0 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-44" d="M 2194 1759 
Q 1497 1759 1228 1600 
Q 959 1441 959 1056 
Q 959 750 1161 570 
Q 1363 391 1709 391 
Q 2188 391 2477 730 
Q 2766 1069 2766 1631 
L 2766 1759 
L 2194 1759 
z
M 3341 1997 
L 3341 0 
L 2766 0 
L 2766 531 
Q 2569 213 2275 61 
Q 1981 -91 1556 -91 
Q 1019 -91 701 211 
Q 384 513 384 1019 
Q 384 1609 779 1909 
Q 1175 2209 1959 2209 
L 2766 2209 
L 2766 2266 
Q 2766 2663 2505 2880 
Q 2244 3097 1772 3097 
Q 1472 3097 1187 3025 
Q 903 2953 641 2809 
L 641 3341 
Q 956 3463 1253 3523 
Q 1550 3584 1831 3584 
Q 2591 3584 2966 3190 
Q 3341 2797 3341 1997 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-51" d="M 3513 2113 
L 3513 0 
L 2938 0 
L 2938 2094 
Q 2938 2591 2744 2837 
Q 2550 3084 2163 3084 
Q 1697 3084 1428 2787 
Q 1159 2491 1159 1978 
L 1159 0 
L 581 0 
L 581 3500 
L 1159 3500 
L 1159 2956 
Q 1366 3272 1645 3428 
Q 1925 3584 2291 3584 
Q 2894 3584 3203 3211 
Q 3513 2838 3513 2113 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-4c" d="M 603 3500 
L 1178 3500 
L 1178 0 
L 603 0 
L 603 3500 
z
M 603 4863 
L 1178 4863 
L 1178 4134 
L 603 4134 
L 603 4863 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-4f" d="M 603 4863 
L 1178 4863 
L 1178 0 
L 603 0 
L 603 4863 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-3" transform="scale(0.015625)"/>
        <path id="DejaVuSans-33" d="M 1259 4147 
L 1259 2394 
L 2053 2394 
Q 2494 2394 2734 2622 
Q 2975 2850 2975 3272 
Q 2975 3691 2734 3919 
Q 2494 4147 2053 4147 
L 1259 4147 
z
M 628 4666 
L 2053 4666 
Q 2838 4666 3239 4311 
Q 3641 3956 3641 3272 
Q 3641 2581 3239 2228 
Q 2838 1875 2053 1875 
L 1259 1875 
L 1259 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-5c" d="M 2059 -325 
Q 1816 -950 1584 -1140 
Q 1353 -1331 966 -1331 
L 506 -1331 
L 506 -850 
L 844 -850 
Q 1081 -850 1212 -737 
Q 1344 -625 1503 -206 
L 1606 56 
L 191 3500 
L 800 3500 
L 1894 763 
L 2988 3500 
L 3597 3500 
L 2059 -325 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-24" d="M 2188 4044 
L 1331 1722 
L 3047 1722 
L 2188 4044 
z
M 1831 4666 
L 2547 4666 
L 4325 0 
L 3669 0 
L 3244 1197 
L 1141 1197 
L 716 0 
L 50 0 
L 1831 4666 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-55" d="M 2631 2963 
Q 2534 3019 2420 3045 
Q 2306 3072 2169 3072 
Q 1681 3072 1420 2755 
Q 1159 2438 1159 1844 
L 1159 0 
L 581 0 
L 581 3500 
L 1159 3500 
L 1159 2956 
Q 1341 3275 1631 3429 
Q 1922 3584 2338 3584 
Q 2397 3584 2469 3576 
Q 2541 3569 2628 3553 
L 2631 2963 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-52" d="M 1959 3097 
Q 1497 3097 1228 2736 
Q 959 2375 959 1747 
Q 959 1119 1226 758 
Q 1494 397 1959 397 
Q 2419 397 2687 759 
Q 2956 1122 2956 1747 
Q 2956 2369 2687 2733 
Q 2419 3097 1959 3097 
z
M 1959 3584 
Q 2709 3584 3137 3096 
Q 3566 2609 3566 1747 
Q 3566 888 3137 398 
Q 2709 -91 1959 -91 
Q 1206 -91 779 398 
Q 353 888 353 1747 
Q 353 2609 779 3096 
Q 1206 3584 1959 3584 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-5a" d="M 269 3500 
L 844 3500 
L 1563 769 
L 2278 3500 
L 2956 3500 
L 3675 769 
L 4391 3500 
L 4966 3500 
L 4050 0 
L 3372 0 
L 2619 2869 
L 1863 0 
L 1184 0 
L 269 3500 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-39"/>
       <use xlink:href="#DejaVuSans-44" transform="translate(60.640625 0)"/>
       <use xlink:href="#DejaVuSans-51" transform="translate(121.921875 0)"/>
       <use xlink:href="#DejaVuSans-4c" transform="translate(185.296875 0)"/>
       <use xlink:href="#DejaVuSans-4f" transform="translate(213.078125 0)"/>
       <use xlink:href="#DejaVuSans-4f" transform="translate(240.859375 0)"/>
       <use xlink:href="#DejaVuSans-44" transform="translate(268.640625 0)"/>
       <use xlink:href="#DejaVuSans-3" transform="translate(329.921875 0)"/>
       <use xlink:href="#DejaVuSans-33" transform="translate(361.703125 0)"/>
       <use xlink:href="#DejaVuSans-5c" transform="translate(422 0)"/>
       <use xlink:href="#DejaVuSans-24" transform="translate(481.1875 0)"/>
       <use xlink:href="#DejaVuSans-55" transform="translate(549.59375 0)"/>
       <use xlink:href="#DejaVuSans-55" transform="translate(588.953125 0)"/>
       <use xlink:href="#DejaVuSans-52" transform="translate(627.859375 0)"/>
       <use xlink:href="#DejaVuSans-5a" transform="translate(689.046875 0)"/>
      </g>
     </g>
    </g>
    <g id="xtick_2">
     <g id="line2d_2">
      <g>
       <use xlink:href="#mf52e499059" x="195.910335" y="327.358125" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_2">
      <!-- Polars -->
      <g transform="translate(179.400023 342.716406) scale(0.11 -0.11)">
       <defs>
        <path id="DejaVuSans-56" d="M 2834 3397 
L 2834 2853 
Q 2591 2978 2328 3040 
Q 2066 3103 1784 3103 
Q 1356 3103 1142 2972 
Q 928 2841 928 2578 
Q 928 2378 1081 2264 
Q 1234 2150 1697 2047 
L 1894 2003 
Q 2506 1872 2764 1633 
Q 3022 1394 3022 966 
Q 3022 478 2636 193 
Q 2250 -91 1575 -91 
Q 1294 -91 989 -36 
Q 684 19 347 128 
L 347 722 
Q 666 556 975 473 
Q 1284 391 1588 391 
Q 1994 391 2212 530 
Q 2431 669 2431 922 
Q 2431 1156 2273 1281 
Q 2116 1406 1581 1522 
L 1381 1569 
Q 847 1681 609 1914 
Q 372 2147 372 2553 
Q 372 3047 722 3315 
Q 1072 3584 1716 3584 
Q 2034 3584 2315 3537 
Q 2597 3491 2834 3397 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-33"/>
       <use xlink:href="#DejaVuSans-52" transform="translate(56.734375 0)"/>
       <use xlink:href="#DejaVuSans-4f" transform="translate(117.921875 0)"/>
       <use xlink:href="#DejaVuSans-44" transform="translate(145.703125 0)"/>
       <use xlink:href="#DejaVuSans-55" transform="translate(206.984375 0)"/>
       <use xlink:href="#DejaVuSans-56" transform="translate(248.09375 0)"/>
      </g>
     </g>
    </g>
    <g id="xtick_3">
     <g id="line2d_3">
      <g>
       <use xlink:href="#mf52e499059" x="300.984609" y="327.358125" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_3">
      <!-- DuckDB -->
      <g transform="translate(279.046484 342.716406) scale(0.11 -0.11)">
       <defs>
        <path id="DejaVuSans-27" d="M 1259 4147 
L 1259 519 
L 2022 519 
Q 2988 519 3436 956 
Q 3884 1394 3884 2338 
Q 3884 3275 3436 3711 
Q 2988 4147 2022 4147 
L 1259 4147 
z
M 628 4666 
L 1925 4666 
Q 3281 4666 3915 4102 
Q 4550 3538 4550 2338 
Q 4550 1131 3912 565 
Q 3275 0 1925 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-58" d="M 544 1381 
L 544 3500 
L 1119 3500 
L 1119 1403 
Q 1119 906 1312 657 
Q 1506 409 1894 409 
Q 2359 409 2629 706 
Q 2900 1003 2900 1516 
L 2900 3500 
L 3475 3500 
L 3475 0 
L 2900 0 
L 2900 538 
Q 2691 219 2414 64 
Q 2138 -91 1772 -91 
Q 1169 -91 856 284 
Q 544 659 544 1381 
z
M 1991 3584 
L 1991 3584 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-46" d="M 3122 3366 
L 3122 2828 
Q 2878 2963 2633 3030 
Q 2388 3097 2138 3097 
Q 1578 3097 1268 2742 
Q 959 2388 959 1747 
Q 959 1106 1268 751 
Q 1578 397 2138 397 
Q 2388 397 2633 464 
Q 2878 531 3122 666 
L 3122 134 
Q 2881 22 2623 -34 
Q 2366 -91 2075 -91 
Q 1284 -91 818 406 
Q 353 903 353 1747 
Q 353 2603 823 3093 
Q 1294 3584 2113 3584 
Q 2378 3584 2631 3529 
Q 2884 3475 3122 3366 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-4e" d="M 581 4863 
L 1159 4863 
L 1159 1991 
L 2875 3500 
L 3609 3500 
L 1753 1863 
L 3688 0 
L 2938 0 
L 1159 1709 
L 1159 0 
L 581 0 
L 581 4863 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-25" d="M 1259 2228 
L 1259 519 
L 2272 519 
Q 2781 519 3026 730 
Q 3272 941 3272 1375 
Q 3272 1813 3026 2020 
Q 2781 2228 2272 2228 
L 1259 2228 
z
M 1259 4147 
L 1259 2741 
L 2194 2741 
Q 2656 2741 2882 2914 
Q 3109 3088 3109 3444 
Q 3109 3797 2882 3972 
Q 2656 4147 2194 4147 
L 1259 4147 
z
M 628 4666 
L 2241 4666 
Q 2963 4666 3353 4366 
Q 3744 4066 3744 3513 
Q 3744 3084 3544 2831 
Q 3344 2578 2956 2516 
Q 3422 2416 3680 2098 
Q 3938 1781 3938 1306 
Q 3938 681 3513 340 
Q 3088 0 2303 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-27"/>
       <use xlink:href="#DejaVuSans-58" transform="translate(77 0)"/>
       <use xlink:href="#DejaVuSans-46" transform="translate(140.375 0)"/>
       <use xlink:href="#DejaVuSans-4e" transform="translate(195.359375 0)"/>
       <use xlink:href="#DejaVuSans-27" transform="translate(253.265625 0)"/>
       <use xlink:href="#DejaVuSans-25" transform="translate(330.265625 0)"/>
      </g>
     </g>
    </g>
    <g id="xtick_4">
     <g id="line2d_4">
      <g>
       <use xlink:href="#mf52e499059" x="406.058883" y="327.358125" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_4">
      <!-- Iceberg -->
      <g transform="translate(385.495758 342.716406) scale(0.11 -0.11)">
       <defs>
        <path id="DejaVuSans-2c" d="M 628 4666 
L 1259 4666 
L 1259 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-48" d="M 3597 1894 
L 3597 1613 
L 953 1613 
Q 991 1019 1311 708 
Q 1631 397 2203 397 
Q 2534 397 2845 478 
Q 3156 559 3463 722 
L 3463 178 
Q 3153 47 2828 -22 
Q 2503 -91 2169 -91 
Q 1331 -91 842 396 
Q 353 884 353 1716 
Q 353 2575 817 3079 
Q 1281 3584 2069 3584 
Q 2775 3584 3186 3129 
Q 3597 2675 3597 1894 
z
M 3022 2063 
Q 3016 2534 2758 2815 
Q 2500 3097 2075 3097 
Q 1594 3097 1305 2825 
Q 1016 2553 972 2059 
L 3022 2063 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-45" d="M 3116 1747 
Q 3116 2381 2855 2742 
Q 2594 3103 2138 3103 
Q 1681 3103 1420 2742 
Q 1159 2381 1159 1747 
Q 1159 1113 1420 752 
Q 1681 391 2138 391 
Q 2594 391 2855 752 
Q 3116 1113 3116 1747 
z
M 1159 2969 
Q 1341 3281 1617 3432 
Q 1894 3584 2278 3584 
Q 2916 3584 3314 3078 
Q 3713 2572 3713 1747 
Q 3713 922 3314 415 
Q 2916 -91 2278 -91 
Q 1894 -91 1617 61 
Q 1341 213 1159 525 
L 1159 0 
L 581 0 
L 581 4863 
L 1159 4863 
L 1159 2969 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-4a" d="M 2906 1791 
Q 2906 2416 2648 2759 
Q 2391 3103 1925 3103 
Q 1463 3103 1205 2759 
Q 947 2416 947 1791 
Q 947 1169 1205 825 
Q 1463 481 1925 481 
Q 2391 481 2648 825 
Q 2906 1169 2906 1791 
z
M 3481 434 
Q 3481 -459 3084 -895 
Q 2688 -1331 1869 -1331 
Q 1566 -1331 1297 -1286 
Q 1028 -1241 775 -1147 
L 775 -588 
Q 1028 -725 1275 -790 
Q 1522 -856 1778 -856 
Q 2344 -856 2625 -561 
Q 2906 -266 2906 331 
L 2906 616 
Q 2728 306 2450 153 
Q 2172 0 1784 0 
Q 1141 0 747 490 
Q 353 981 353 1791 
Q 353 2603 747 3093 
Q 1141 3584 1784 3584 
Q 2172 3584 2450 3431 
Q 2728 3278 2906 2969 
L 2906 3500 
L 3481 3500 
L 3481 434 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-2c"/>
       <use xlink:href="#DejaVuSans-46" transform="translate(29.5 0)"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(84.484375 0)"/>
       <use xlink:href="#DejaVuSans-45" transform="translate(146.015625 0)"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(209.5 0)"/>
       <use xlink:href="#DejaVuSans-55" transform="translate(271.03125 0)"/>
       <use xlink:href="#DejaVuSans-4a" transform="translate(310.390625 0)"/>
      </g>
     </g>
    </g>
    <g id="xtick_5">
     <g id="line2d_5">
      <g>
       <use xlink:href="#mf52e499059" x="511.133157" y="327.358125" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_5">
      <!-- LanceDB -->
      <g transform="translate(486.795657 342.715547) scale(0.11 -0.11)">
       <defs>
        <path id="DejaVuSans-2f" d="M 628 4666 
L 1259 4666 
L 1259 531 
L 3531 531 
L 3531 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-2f"/>
       <use xlink:href="#DejaVuSans-44" transform="translate(55.71875 0)"/>
       <use xlink:href="#DejaVuSans-51" transform="translate(117 0)"/>
       <use xlink:href="#DejaVuSans-46" transform="translate(180.375 0)"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(235.359375 0)"/>
       <use xlink:href="#DejaVuSans-27" transform="translate(296.890625 0)"/>
       <use xlink:href="#DejaVuSans-25" transform="translate(373.890625 0)"/>
      </g>
     </g>
    </g>
   </g>
   <g id="matplotlib.axis_2">
    <g id="ytick_1">
     <g id="line2d_6">
      <defs>
       <path id="m7354247fea" d="M 0 0 
L -3.5 0 
" style="stroke: #000000; stroke-width: 0.8"/>
      </defs>
      <g>
       <use xlink:href="#m7354247fea" x="40.925781" y="327.358125" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_6">
      <!-- 0 -->
      <g transform="translate(27.563281 331.156953) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-13" d="M 2034 4250 
Q 1547 4250 1301 3770 
Q 1056 3291 1056 2328 
Q 1056 1369 1301 889 
Q 1547 409 2034 409 
Q 2525 409 2770 889 
Q 3016 1369 3016 2328 
Q 3016 3291 2770 3770 
Q 2525 4250 2034 4250 
z
M 2034 4750 
Q 2819 4750 3233 4129 
Q 3647 3509 3647 2328 
Q 3647 1150 3233 529 
Q 2819 -91 2034 -91 
Q 1250 -91 836 529 
Q 422 1150 422 2328 
Q 422 3509 836 4129 
Q 1250 4750 2034 4750 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-13"/>
      </g>
     </g>
    </g>
    <g id="ytick_2">
     <g id="line2d_7">
      <g>
       <use xlink:href="#m7354247fea" x="40.925781" y="274.284404" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_7">
      <!-- 2 -->
      <g transform="translate(27.563281 278.083233) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-15" d="M 1228 531 
L 3431 531 
L 3431 0 
L 469 0 
L 469 531 
Q 828 903 1448 1529 
Q 2069 2156 2228 2338 
Q 2531 2678 2651 2914 
Q 2772 3150 2772 3378 
Q 2772 3750 2511 3984 
Q 2250 4219 1831 4219 
Q 1534 4219 1204 4116 
Q 875 4013 500 3803 
L 500 4441 
Q 881 4594 1212 4672 
Q 1544 4750 1819 4750 
Q 2544 4750 2975 4387 
Q 3406 4025 3406 3419 
Q 3406 3131 3298 2873 
Q 3191 2616 2906 2266 
Q 2828 2175 2409 1742 
Q 1991 1309 1228 531 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-15"/>
      </g>
     </g>
    </g>
    <g id="ytick_3">
     <g id="line2d_8">
      <g>
       <use xlink:href="#m7354247fea" x="40.925781" y="221.210684" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_8">
      <!-- 4 -->
      <g transform="translate(27.563281 225.009512) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-17" d="M 2419 4116 
L 825 1625 
L 2419 1625 
L 2419 4116 
z
M 2253 4666 
L 3047 4666 
L 3047 1625 
L 3713 1625 
L 3713 1100 
L 3047 1100 
L 3047 0 
L 2419 0 
L 2419 1100 
L 313 1100 
L 313 1709 
L 2253 4666 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-17"/>
      </g>
     </g>
    </g>
    <g id="ytick_4">
     <g id="line2d_9">
      <g>
       <use xlink:href="#m7354247fea" x="40.925781" y="168.136963" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_9">
      <!-- 6 -->
      <g transform="translate(27.563281 171.935792) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-19" d="M 2113 2584 
Q 1688 2584 1439 2293 
Q 1191 2003 1191 1497 
Q 1191 994 1439 701 
Q 1688 409 2113 409 
Q 2538 409 2786 701 
Q 3034 994 3034 1497 
Q 3034 2003 2786 2293 
Q 2538 2584 2113 2584 
z
M 3366 4563 
L 3366 3988 
Q 3128 4100 2886 4159 
Q 2644 4219 2406 4219 
Q 1781 4219 1451 3797 
Q 1122 3375 1075 2522 
Q 1259 2794 1537 2939 
Q 1816 3084 2150 3084 
Q 2853 3084 3261 2657 
Q 3669 2231 3669 1497 
Q 3669 778 3244 343 
Q 2819 -91 2113 -91 
Q 1303 -91 875 529 
Q 447 1150 447 2328 
Q 447 3434 972 4092 
Q 1497 4750 2381 4750 
Q 2619 4750 2861 4703 
Q 3103 4656 3366 4563 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-19"/>
      </g>
     </g>
    </g>
    <g id="ytick_5">
     <g id="line2d_10">
      <g>
       <use xlink:href="#m7354247fea" x="40.925781" y="115.063243" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_10">
      <!-- 8 -->
      <g transform="translate(27.563281 118.862071) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-1b" d="M 2034 2216 
Q 1584 2216 1326 1975 
Q 1069 1734 1069 1313 
Q 1069 891 1326 650 
Q 1584 409 2034 409 
Q 2484 409 2743 651 
Q 3003 894 3003 1313 
Q 3003 1734 2745 1975 
Q 2488 2216 2034 2216 
z
M 1403 2484 
Q 997 2584 770 2862 
Q 544 3141 544 3541 
Q 544 4100 942 4425 
Q 1341 4750 2034 4750 
Q 2731 4750 3128 4425 
Q 3525 4100 3525 3541 
Q 3525 3141 3298 2862 
Q 3072 2584 2669 2484 
Q 3125 2378 3379 2068 
Q 3634 1759 3634 1313 
Q 3634 634 3220 271 
Q 2806 -91 2034 -91 
Q 1263 -91 848 271 
Q 434 634 434 1313 
Q 434 1759 690 2068 
Q 947 2378 1403 2484 
z
M 1172 3481 
Q 1172 3119 1398 2916 
Q 1625 2713 2034 2713 
Q 2441 2713 2670 2916 
Q 2900 3119 2900 3481 
Q 2900 3844 2670 4047 
Q 2441 4250 2034 4250 
Q 1625 4250 1398 4047 
Q 1172 3844 1172 3481 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-1b"/>
      </g>
     </g>
    </g>
    <g id="ytick_6">
     <g id="line2d_11">
      <g>
       <use xlink:href="#m7354247fea" x="40.925781" y="61.989522" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_11">
      <!-- 10 -->
      <g transform="translate(21.200781 65.78835) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-14" d="M 794 531 
L 1825 531 
L 1825 4091 
L 703 3866 
L 703 4441 
L 1819 4666 
L 2450 4666 
L 2450 531 
L 3481 531 
L 3481 0 
L 794 0 
L 794 531 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-14"/>
       <use xlink:href="#DejaVuSans-13" transform="translate(63.625 0)"/>
      </g>
     </g>
    </g>
    <g id="text_12">
     <!-- Time (seconds) -->
     <g transform="translate(14.798438 216.002187) rotate(-90) scale(0.1 -0.1)">
      <defs>
       <path id="DejaVuSans-37" d="M -19 4666 
L 3928 4666 
L 3928 4134 
L 2272 4134 
L 2272 0 
L 1638 0 
L 1638 4134 
L -19 4134 
L -19 4666 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-50" d="M 3328 2828 
Q 3544 3216 3844 3400 
Q 4144 3584 4550 3584 
Q 5097 3584 5394 3201 
Q 5691 2819 5691 2113 
L 5691 0 
L 5113 0 
L 5113 2094 
Q 5113 2597 4934 2840 
Q 4756 3084 4391 3084 
Q 3944 3084 3684 2787 
Q 3425 2491 3425 1978 
L 3425 0 
L 2847 0 
L 2847 2094 
Q 2847 2600 2669 2842 
Q 2491 3084 2119 3084 
Q 1678 3084 1418 2786 
Q 1159 2488 1159 1978 
L 1159 0 
L 581 0 
L 581 3500 
L 1159 3500 
L 1159 2956 
Q 1356 3278 1631 3431 
Q 1906 3584 2284 3584 
Q 2666 3584 2933 3390 
Q 3200 3197 3328 2828 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-b" d="M 1984 4856 
Q 1566 4138 1362 3434 
Q 1159 2731 1159 2009 
Q 1159 1288 1364 580 
Q 1569 -128 1984 -844 
L 1484 -844 
Q 1016 -109 783 600 
Q 550 1309 550 2009 
Q 550 2706 781 3412 
Q 1013 4119 1484 4856 
L 1984 4856 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-47" d="M 2906 2969 
L 2906 4863 
L 3481 4863 
L 3481 0 
L 2906 0 
L 2906 525 
Q 2725 213 2448 61 
Q 2172 -91 1784 -91 
Q 1150 -91 751 415 
Q 353 922 353 1747 
Q 353 2572 751 3078 
Q 1150 3584 1784 3584 
Q 2172 3584 2448 3432 
Q 2725 3281 2906 2969 
z
M 947 1747 
Q 947 1113 1208 752 
Q 1469 391 1925 391 
Q 2381 391 2643 752 
Q 2906 1113 2906 1747 
Q 2906 2381 2643 2742 
Q 2381 3103 1925 3103 
Q 1469 3103 1208 2742 
Q 947 2381 947 1747 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-c" d="M 513 4856 
L 1013 4856 
Q 1481 4119 1714 3412 
Q 1947 2706 1947 2009 
Q 1947 1309 1714 600 
Q 1481 -109 1013 -844 
L 513 -844 
Q 928 -128 1133 580 
Q 1338 1288 1338 2009 
Q 1338 2731 1133 3434 
Q 928 4138 513 4856 
z
" transform="scale(0.015625)"/>
      </defs>
      <use xlink:href="#DejaVuSans-37"/>
      <use xlink:href="#DejaVuSans-4c" transform="translate(58 0)"/>
      <use xlink:href="#DejaVuSans-50" transform="translate(85.78125 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(183.1875 0)"/>
      <use xlink:href="#DejaVuSans-3" transform="translate(244.71875 0)"/>
      <use xlink:href="#DejaVuSans-b" transform="translate(276.5 0)"/>
      <use xlink:href="#DejaVuSans-56" transform="translate(315.515625 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(367.609375 0)"/>
      <use xlink:href="#DejaVuSans-46" transform="translate(429.140625 0)"/>
      <use xlink:href="#DejaVuSans-52" transform="translate(484.125 0)"/>
      <use xlink:href="#DejaVuSans-51" transform="translate(545.3125 0)"/>
      <use xlink:href="#DejaVuSans-47" transform="translate(608.6875 0)"/>
      <use xlink:href="#DejaVuSans-56" transform="translate(672.171875 0)"/>
      <use xlink:href="#DejaVuSans-c" transform="translate(724.265625 0)"/>
     </g>
    </g>
   </g>
   <g id="patch_13">
    <path d="M 40.925781 327.358125 
L 40.925781 28.318125 
" style="fill: none; stroke: #000000; stroke-width: 0.8; stroke-linejoin: miter; stroke-linecap: square"/>
   </g>
   <g id="patch_14">
    <path d="M 40.925781 327.358125 
L 561.043437 327.358125 
" style="fill: none; stroke: #000000; stroke-width: 0.8; stroke-linejoin: miter; stroke-linecap: square"/>
   </g>
   <g id="text_13">
    <!-- 0.00s -->
    <g transform="translate(77.055515 321.215448) scale(0.09 -0.09)">
     <defs>
      <path id="DejaVuSans-Bold-13" d="M 2944 2338 
Q 2944 3213 2780 3570 
Q 2616 3928 2228 3928 
Q 1841 3928 1675 3570 
Q 1509 3213 1509 2338 
Q 1509 1453 1675 1090 
Q 1841 728 2228 728 
Q 2613 728 2778 1090 
Q 2944 1453 2944 2338 
z
M 4147 2328 
Q 4147 1169 3647 539 
Q 3147 -91 2228 -91 
Q 1306 -91 806 539 
Q 306 1169 306 2328 
Q 306 3491 806 4120 
Q 1306 4750 2228 4750 
Q 3147 4750 3647 4120 
Q 4147 3491 4147 2328 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-11" d="M 653 1209 
L 1778 1209 
L 1778 0 
L 653 0 
L 653 1209 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-56" d="M 3272 3391 
L 3272 2541 
Q 2913 2691 2578 2766 
Q 2244 2841 1947 2841 
Q 1628 2841 1473 2761 
Q 1319 2681 1319 2516 
Q 1319 2381 1436 2309 
Q 1553 2238 1856 2203 
L 2053 2175 
Q 2913 2066 3209 1816 
Q 3506 1566 3506 1031 
Q 3506 472 3093 190 
Q 2681 -91 1863 -91 
Q 1516 -91 1145 -36 
Q 775 19 384 128 
L 384 978 
Q 719 816 1070 734 
Q 1422 653 1784 653 
Q 2113 653 2278 743 
Q 2444 834 2444 1013 
Q 2444 1163 2330 1236 
Q 2216 1309 1875 1350 
L 1678 1375 
Q 931 1469 631 1722 
Q 331 1975 331 2491 
Q 331 3047 712 3315 
Q 1094 3584 1881 3584 
Q 2191 3584 2531 3537 
Q 2872 3491 3272 3391 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-Bold-13"/>
     <use xlink:href="#DejaVuSans-Bold-11" transform="translate(69.578125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-13" transform="translate(107.5625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-13" transform="translate(177.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(246.71875 0)"/>
    </g>
   </g>
   <g id="text_14">
    <!-- 0.00s -->
    <g transform="translate(182.129789 321.21544) scale(0.09 -0.09)">
     <use xlink:href="#DejaVuSans-Bold-13"/>
     <use xlink:href="#DejaVuSans-Bold-11" transform="translate(69.578125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-13" transform="translate(107.5625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-13" transform="translate(177.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(246.71875 0)"/>
    </g>
   </g>
   <g id="text_15">
    <!-- 0.94s -->
    <g transform="translate(287.204062 296.363984) scale(0.09 -0.09)">
     <defs>
      <path id="DejaVuSans-Bold-1c" d="M 641 103 
L 641 966 
Q 928 831 1190 764 
Q 1453 697 1709 697 
Q 2247 697 2547 995 
Q 2847 1294 2900 1881 
Q 2688 1725 2447 1647 
Q 2206 1569 1925 1569 
Q 1209 1569 770 1986 
Q 331 2403 331 3084 
Q 331 3838 820 4291 
Q 1309 4744 2131 4744 
Q 3044 4744 3544 4128 
Q 4044 3513 4044 2388 
Q 4044 1231 3459 570 
Q 2875 -91 1856 -91 
Q 1528 -91 1228 -42 
Q 928 6 641 103 
z
M 2125 2350 
Q 2441 2350 2600 2554 
Q 2759 2759 2759 3169 
Q 2759 3575 2600 3781 
Q 2441 3988 2125 3988 
Q 1809 3988 1650 3781 
Q 1491 3575 1491 3169 
Q 1491 2759 1650 2554 
Q 1809 2350 2125 2350 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-17" d="M 2356 3675 
L 1038 1722 
L 2356 1722 
L 2356 3675 
z
M 2156 4666 
L 3494 4666 
L 3494 1722 
L 4159 1722 
L 4159 850 
L 3494 850 
L 3494 0 
L 2356 0 
L 2356 850 
L 288 850 
L 288 1881 
L 2156 4666 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-Bold-13"/>
     <use xlink:href="#DejaVuSans-Bold-11" transform="translate(69.578125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-1c" transform="translate(107.5625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-17" transform="translate(177.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(246.71875 0)"/>
    </g>
   </g>
   <g id="text_16">
    <!-- read -->
    <g style="fill: #ffffff" transform="translate(291.376992 312.380176) scale(0.075 -0.075)">
     <defs>
      <path id="DejaVuSans-Bold-55" d="M 3138 2547 
Q 2991 2616 2845 2648 
Q 2700 2681 2553 2681 
Q 2122 2681 1889 2404 
Q 1656 2128 1656 1613 
L 1656 0 
L 538 0 
L 538 3500 
L 1656 3500 
L 1656 2925 
Q 1872 3269 2151 3426 
Q 2431 3584 2822 3584 
Q 2878 3584 2943 3579 
Q 3009 3575 3134 3559 
L 3138 2547 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-48" d="M 4031 1759 
L 4031 1441 
L 1416 1441 
Q 1456 1047 1700 850 
Q 1944 653 2381 653 
Q 2734 653 3104 758 
Q 3475 863 3866 1075 
L 3866 213 
Q 3469 63 3072 -14 
Q 2675 -91 2278 -91 
Q 1328 -91 801 392 
Q 275 875 275 1747 
Q 275 2603 792 3093 
Q 1309 3584 2216 3584 
Q 3041 3584 3536 3087 
Q 4031 2591 4031 1759 
z
M 2881 2131 
Q 2881 2450 2695 2645 
Q 2509 2841 2209 2841 
Q 1884 2841 1681 2658 
Q 1478 2475 1428 2131 
L 2881 2131 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-44" d="M 2106 1575 
Q 1756 1575 1579 1456 
Q 1403 1338 1403 1106 
Q 1403 894 1545 773 
Q 1688 653 1941 653 
Q 2256 653 2472 879 
Q 2688 1106 2688 1447 
L 2688 1575 
L 2106 1575 
z
M 3816 1997 
L 3816 0 
L 2688 0 
L 2688 519 
Q 2463 200 2181 54 
Q 1900 -91 1497 -91 
Q 953 -91 614 226 
Q 275 544 275 1050 
Q 275 1666 698 1953 
Q 1122 2241 2028 2241 
L 2688 2241 
L 2688 2328 
Q 2688 2594 2478 2717 
Q 2269 2841 1825 2841 
Q 1466 2841 1156 2769 
Q 847 2697 581 2553 
L 581 3406 
Q 941 3494 1303 3539 
Q 1666 3584 2028 3584 
Q 2975 3584 3395 3211 
Q 3816 2838 3816 1997 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-47" d="M 2919 2988 
L 2919 4863 
L 4044 4863 
L 4044 0 
L 2919 0 
L 2919 506 
Q 2688 197 2409 53 
Q 2131 -91 1766 -91 
Q 1119 -91 703 423 
Q 288 938 288 1747 
Q 288 2556 703 3070 
Q 1119 3584 1766 3584 
Q 2128 3584 2408 3439 
Q 2688 3294 2919 2988 
z
M 2181 722 
Q 2541 722 2730 984 
Q 2919 1247 2919 1747 
Q 2919 2247 2730 2509 
Q 2541 2772 2181 2772 
Q 1825 2772 1636 2509 
Q 1447 2247 1447 1747 
Q 1447 1247 1636 984 
Q 1825 722 2181 722 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-Bold-55"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(49.3125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-44" transform="translate(117.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-47" transform="translate(184.625 0)"/>
    </g>
    <!-- 0.94s -->
    <g style="fill: #ffffff" transform="translate(289.50082 321.381641) scale(0.075 -0.075)">
     <use xlink:href="#DejaVuSans-Bold-13"/>
     <use xlink:href="#DejaVuSans-Bold-11" transform="translate(69.578125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-1c" transform="translate(107.5625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-17" transform="translate(177.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(246.71875 0)"/>
    </g>
   </g>
   <g id="text_17">
    <!-- 9.02s -->
    <g transform="translate(392.278336 81.983487) scale(0.09 -0.09)">
     <defs>
      <path id="DejaVuSans-Bold-15" d="M 1844 884 
L 3897 884 
L 3897 0 
L 506 0 
L 506 884 
L 2209 2388 
Q 2438 2594 2547 2791 
Q 2656 2988 2656 3200 
Q 2656 3528 2436 3728 
Q 2216 3928 1850 3928 
Q 1569 3928 1234 3808 
Q 900 3688 519 3450 
L 519 4475 
Q 925 4609 1322 4679 
Q 1719 4750 2100 4750 
Q 2938 4750 3402 4381 
Q 3866 4013 3866 3353 
Q 3866 2972 3669 2642 
Q 3472 2313 2841 1759 
L 1844 884 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-Bold-1c"/>
     <use xlink:href="#DejaVuSans-Bold-11" transform="translate(69.578125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-13" transform="translate(107.5625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-15" transform="translate(177.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(246.71875 0)"/>
    </g>
   </g>
   <g id="text_18">
    <!-- read -->
    <g style="fill: #ffffff" transform="translate(396.451266 223.506523) scale(0.075 -0.075)">
     <use xlink:href="#DejaVuSans-Bold-55"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(49.3125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-44" transform="translate(117.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-47" transform="translate(184.625 0)"/>
    </g>
    <!-- 7.63s -->
    <g style="fill: #ffffff" transform="translate(394.575094 232.507988) scale(0.075 -0.075)">
     <defs>
      <path id="DejaVuSans-Bold-1a" d="M 428 4666 
L 3944 4666 
L 3944 3988 
L 2125 0 
L 953 0 
L 2675 3781 
L 428 3781 
L 428 4666 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-19" d="M 2316 2303 
Q 2000 2303 1842 2098 
Q 1684 1894 1684 1484 
Q 1684 1075 1842 870 
Q 2000 666 2316 666 
Q 2634 666 2792 870 
Q 2950 1075 2950 1484 
Q 2950 1894 2792 2098 
Q 2634 2303 2316 2303 
z
M 3803 4544 
L 3803 3681 
Q 3506 3822 3243 3889 
Q 2981 3956 2731 3956 
Q 2194 3956 1894 3657 
Q 1594 3359 1544 2772 
Q 1750 2925 1990 3001 
Q 2231 3078 2516 3078 
Q 3231 3078 3670 2659 
Q 4109 2241 4109 1563 
Q 4109 813 3618 361 
Q 3128 -91 2303 -91 
Q 1394 -91 895 523 
Q 397 1138 397 2266 
Q 397 3422 980 4083 
Q 1563 4744 2578 4744 
Q 2900 4744 3203 4694 
Q 3506 4644 3803 4544 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-16" d="M 2981 2516 
Q 3453 2394 3698 2092 
Q 3944 1791 3944 1325 
Q 3944 631 3412 270 
Q 2881 -91 1863 -91 
Q 1503 -91 1142 -33 
Q 781 25 428 141 
L 428 1069 
Q 766 900 1098 814 
Q 1431 728 1753 728 
Q 2231 728 2486 893 
Q 2741 1059 2741 1369 
Q 2741 1688 2480 1852 
Q 2219 2016 1709 2016 
L 1228 2016 
L 1228 2791 
L 1734 2791 
Q 2188 2791 2409 2933 
Q 2631 3075 2631 3366 
Q 2631 3634 2415 3781 
Q 2200 3928 1806 3928 
Q 1516 3928 1219 3862 
Q 922 3797 628 3669 
L 628 4550 
Q 984 4650 1334 4700 
Q 1684 4750 2022 4750 
Q 2931 4750 3382 4451 
Q 3834 4153 3834 3553 
Q 3834 3144 3618 2883 
Q 3403 2622 2981 2516 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-Bold-1a"/>
     <use xlink:href="#DejaVuSans-Bold-11" transform="translate(69.578125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-19" transform="translate(107.5625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-16" transform="translate(177.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(246.71875 0)"/>
    </g>
   </g>
   <g id="text_19">
    <!-- ingest -->
    <g style="fill: #ffffff" transform="translate(393.732321 104.06067) scale(0.07 -0.07)">
     <defs>
      <path id="DejaVuSans-Bold-4c" d="M 538 3500 
L 1656 3500 
L 1656 0 
L 538 0 
L 538 3500 
z
M 538 4863 
L 1656 4863 
L 1656 3950 
L 538 3950 
L 538 4863 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-51" d="M 4056 2131 
L 4056 0 
L 2931 0 
L 2931 347 
L 2931 1631 
Q 2931 2084 2911 2256 
Q 2891 2428 2841 2509 
Q 2775 2619 2662 2680 
Q 2550 2741 2406 2741 
Q 2056 2741 1856 2470 
Q 1656 2200 1656 1722 
L 1656 0 
L 538 0 
L 538 3500 
L 1656 3500 
L 1656 2988 
Q 1909 3294 2193 3439 
Q 2478 3584 2822 3584 
Q 3428 3584 3742 3212 
Q 4056 2841 4056 2131 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-4a" d="M 2919 594 
Q 2688 288 2409 144 
Q 2131 0 1766 0 
Q 1125 0 706 504 
Q 288 1009 288 1791 
Q 288 2575 706 3076 
Q 1125 3578 1766 3578 
Q 2131 3578 2409 3434 
Q 2688 3291 2919 2981 
L 2919 3500 
L 4044 3500 
L 4044 353 
Q 4044 -491 3511 -936 
Q 2978 -1381 1966 -1381 
Q 1638 -1381 1331 -1331 
Q 1025 -1281 716 -1178 
L 716 -306 
Q 1009 -475 1290 -558 
Q 1572 -641 1856 -641 
Q 2406 -641 2662 -400 
Q 2919 -159 2919 353 
L 2919 594 
z
M 2181 2772 
Q 1834 2772 1640 2515 
Q 1447 2259 1447 1791 
Q 1447 1309 1634 1061 
Q 1822 813 2181 813 
Q 2531 813 2725 1069 
Q 2919 1325 2919 1791 
Q 2919 2259 2725 2515 
Q 2531 2772 2181 2772 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-57" d="M 1759 4494 
L 1759 3500 
L 2913 3500 
L 2913 2700 
L 1759 2700 
L 1759 1216 
Q 1759 972 1856 886 
Q 1953 800 2241 800 
L 2816 800 
L 2816 0 
L 1856 0 
Q 1194 0 917 276 
Q 641 553 641 1216 
L 641 2700 
L 84 2700 
L 84 3500 
L 641 3500 
L 641 4494 
L 1759 4494 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-Bold-4c"/>
     <use xlink:href="#DejaVuSans-Bold-51" transform="translate(34.28125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4a" transform="translate(105.46875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(177.046875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(244.875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-57" transform="translate(304.390625 0)"/>
    </g>
    <!-- 1.380s -->
    <g style="fill: #ffffff" transform="translate(392.905446 112.462037) scale(0.07 -0.07)">
     <defs>
      <path id="DejaVuSans-Bold-14" d="M 750 831 
L 1813 831 
L 1813 3847 
L 722 3622 
L 722 4441 
L 1806 4666 
L 2950 4666 
L 2950 831 
L 4013 831 
L 4013 0 
L 750 0 
L 750 831 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-1b" d="M 2228 2088 
Q 1891 2088 1709 1903 
Q 1528 1719 1528 1375 
Q 1528 1031 1709 848 
Q 1891 666 2228 666 
Q 2563 666 2741 848 
Q 2919 1031 2919 1375 
Q 2919 1722 2741 1905 
Q 2563 2088 2228 2088 
z
M 1350 2484 
Q 925 2613 709 2878 
Q 494 3144 494 3541 
Q 494 4131 934 4440 
Q 1375 4750 2228 4750 
Q 3075 4750 3515 4442 
Q 3956 4134 3956 3541 
Q 3956 3144 3739 2878 
Q 3522 2613 3097 2484 
Q 3572 2353 3814 2058 
Q 4056 1763 4056 1313 
Q 4056 619 3595 264 
Q 3134 -91 2228 -91 
Q 1319 -91 855 264 
Q 391 619 391 1313 
Q 391 1763 633 2058 
Q 875 2353 1350 2484 
z
M 1631 3419 
Q 1631 3141 1786 2991 
Q 1941 2841 2228 2841 
Q 2509 2841 2662 2991 
Q 2816 3141 2816 3419 
Q 2816 3697 2662 3845 
Q 2509 3994 2228 3994 
Q 1941 3994 1786 3844 
Q 1631 3694 1631 3419 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-Bold-14"/>
     <use xlink:href="#DejaVuSans-Bold-11" transform="translate(69.578125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-16" transform="translate(107.5625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-1b" transform="translate(177.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-13" transform="translate(246.71875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(316.296875 0)"/>
    </g>
   </g>
   <g id="text_20">
    <!-- 7.57s -->
    <g transform="translate(497.35261 120.384925) scale(0.09 -0.09)">
     <defs>
      <path id="DejaVuSans-Bold-18" d="M 678 4666 
L 3669 4666 
L 3669 3781 
L 1638 3781 
L 1638 3059 
Q 1775 3097 1914 3117 
Q 2053 3138 2203 3138 
Q 3056 3138 3531 2711 
Q 4006 2284 4006 1522 
Q 4006 766 3489 337 
Q 2972 -91 2053 -91 
Q 1656 -91 1267 -14 
Q 878 63 494 219 
L 494 1166 
Q 875 947 1217 837 
Q 1559 728 1863 728 
Q 2300 728 2551 942 
Q 2803 1156 2803 1522 
Q 2803 1891 2551 2103 
Q 2300 2316 1863 2316 
Q 1603 2316 1309 2248 
Q 1016 2181 678 2041 
L 678 4666 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-Bold-1a"/>
     <use xlink:href="#DejaVuSans-Bold-11" transform="translate(69.578125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-18" transform="translate(107.5625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-1a" transform="translate(177.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(246.71875 0)"/>
    </g>
   </g>
   <g id="text_21">
    <!-- read -->
    <g style="fill: #ffffff" transform="translate(501.52554 226.415693) scale(0.075 -0.075)">
     <use xlink:href="#DejaVuSans-Bold-55"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(49.3125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-44" transform="translate(117.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-47" transform="translate(184.625 0)"/>
    </g>
    <!-- 7.42s -->
    <g style="fill: #ffffff" transform="translate(499.649368 235.417158) scale(0.075 -0.075)">
     <use xlink:href="#DejaVuSans-Bold-1a"/>
     <use xlink:href="#DejaVuSans-Bold-11" transform="translate(69.578125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-17" transform="translate(107.5625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-15" transform="translate(177.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(246.71875 0)"/>
    </g>
   </g>
   <g id="text_22">
    <!-- ingest -->
    <g style="fill: #ffffff" transform="translate(498.806595 126.170559) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-Bold-4c"/>
     <use xlink:href="#DejaVuSans-Bold-51" transform="translate(34.28125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4a" transform="translate(105.46875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(177.046875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(244.875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-57" transform="translate(304.390625 0)"/>
    </g>
    <!-- 0.153s -->
    <g style="fill: #ffffff" transform="translate(497.97972 134.571926) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-Bold-13"/>
     <use xlink:href="#DejaVuSans-Bold-11" transform="translate(69.578125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-14" transform="translate(107.5625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-18" transform="translate(177.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-16" transform="translate(246.71875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(316.296875 0)"/>
    </g>
   </g>
   <g id="text_23">
    <!-- Setup cost: read from LaminDB + ingest into engine store -->
    <g transform="translate(104.422734 16.318125) scale(0.12 -0.12)">
     <defs>
      <path id="DejaVuSans-Bold-36" d="M 3834 4519 
L 3834 3531 
Q 3450 3703 3084 3790 
Q 2719 3878 2394 3878 
Q 1963 3878 1756 3759 
Q 1550 3641 1550 3391 
Q 1550 3203 1689 3098 
Q 1828 2994 2194 2919 
L 2706 2816 
Q 3484 2659 3812 2340 
Q 4141 2022 4141 1434 
Q 4141 663 3683 286 
Q 3225 -91 2284 -91 
Q 1841 -91 1394 -6 
Q 947 78 500 244 
L 500 1259 
Q 947 1022 1364 901 
Q 1781 781 2169 781 
Q 2563 781 2772 912 
Q 2981 1044 2981 1288 
Q 2981 1506 2839 1625 
Q 2697 1744 2272 1838 
L 1806 1941 
Q 1106 2091 782 2419 
Q 459 2747 459 3303 
Q 459 4000 909 4375 
Q 1359 4750 2203 4750 
Q 2588 4750 2994 4692 
Q 3400 4634 3834 4519 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-58" d="M 500 1363 
L 500 3500 
L 1625 3500 
L 1625 3150 
Q 1625 2866 1622 2436 
Q 1619 2006 1619 1863 
Q 1619 1441 1641 1255 
Q 1663 1069 1716 984 
Q 1784 875 1895 815 
Q 2006 756 2150 756 
Q 2500 756 2700 1025 
Q 2900 1294 2900 1772 
L 2900 3500 
L 4019 3500 
L 4019 0 
L 2900 0 
L 2900 506 
Q 2647 200 2364 54 
Q 2081 -91 1741 -91 
Q 1134 -91 817 281 
Q 500 653 500 1363 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-53" d="M 1656 506 
L 1656 -1331 
L 538 -1331 
L 538 3500 
L 1656 3500 
L 1656 2988 
Q 1888 3294 2169 3439 
Q 2450 3584 2816 3584 
Q 3463 3584 3878 3070 
Q 4294 2556 4294 1747 
Q 4294 938 3878 423 
Q 3463 -91 2816 -91 
Q 2450 -91 2169 54 
Q 1888 200 1656 506 
z
M 2400 2772 
Q 2041 2772 1848 2508 
Q 1656 2244 1656 1747 
Q 1656 1250 1848 986 
Q 2041 722 2400 722 
Q 2759 722 2948 984 
Q 3138 1247 3138 1747 
Q 3138 2247 2948 2509 
Q 2759 2772 2400 2772 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-3" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-46" d="M 3366 3391 
L 3366 2478 
Q 3138 2634 2908 2709 
Q 2678 2784 2431 2784 
Q 1963 2784 1702 2511 
Q 1441 2238 1441 1747 
Q 1441 1256 1702 982 
Q 1963 709 2431 709 
Q 2694 709 2930 787 
Q 3166 866 3366 1019 
L 3366 103 
Q 3103 6 2833 -42 
Q 2563 -91 2291 -91 
Q 1344 -91 809 395 
Q 275 881 275 1747 
Q 275 2613 809 3098 
Q 1344 3584 2291 3584 
Q 2566 3584 2833 3536 
Q 3100 3488 3366 3391 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-52" d="M 2203 2784 
Q 1831 2784 1636 2517 
Q 1441 2250 1441 1747 
Q 1441 1244 1636 976 
Q 1831 709 2203 709 
Q 2569 709 2762 976 
Q 2956 1244 2956 1747 
Q 2956 2250 2762 2517 
Q 2569 2784 2203 2784 
z
M 2203 3584 
Q 3106 3584 3614 3096 
Q 4122 2609 4122 1747 
Q 4122 884 3614 396 
Q 3106 -91 2203 -91 
Q 1297 -91 786 396 
Q 275 884 275 1747 
Q 275 2609 786 3096 
Q 1297 3584 2203 3584 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-1d" d="M 716 3500 
L 1844 3500 
L 1844 2291 
L 716 2291 
L 716 3500 
z
M 716 1209 
L 1844 1209 
L 1844 0 
L 716 0 
L 716 1209 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-49" d="M 2841 4863 
L 2841 4128 
L 2222 4128 
Q 1984 4128 1890 4042 
Q 1797 3956 1797 3744 
L 1797 3500 
L 2753 3500 
L 2753 2700 
L 1797 2700 
L 1797 0 
L 678 0 
L 678 2700 
L 122 2700 
L 122 3500 
L 678 3500 
L 678 3744 
Q 678 4316 997 4589 
Q 1316 4863 1984 4863 
L 2841 4863 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-50" d="M 3781 2919 
Q 3994 3244 4286 3414 
Q 4578 3584 4928 3584 
Q 5531 3584 5847 3212 
Q 6163 2841 6163 2131 
L 6163 0 
L 5038 0 
L 5038 1825 
Q 5041 1866 5042 1909 
Q 5044 1953 5044 2034 
Q 5044 2406 4934 2573 
Q 4825 2741 4581 2741 
Q 4263 2741 4089 2478 
Q 3916 2216 3909 1719 
L 3909 0 
L 2784 0 
L 2784 1825 
Q 2784 2406 2684 2573 
Q 2584 2741 2328 2741 
Q 2006 2741 1831 2477 
Q 1656 2213 1656 1722 
L 1656 0 
L 531 0 
L 531 3500 
L 1656 3500 
L 1656 2988 
Q 1863 3284 2130 3434 
Q 2397 3584 2719 3584 
Q 3081 3584 3359 3409 
Q 3638 3234 3781 2919 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-2f" d="M 588 4666 
L 1791 4666 
L 1791 909 
L 3903 909 
L 3903 0 
L 588 0 
L 588 4666 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-27" d="M 1791 3756 
L 1791 909 
L 2222 909 
Q 2959 909 3348 1275 
Q 3738 1641 3738 2338 
Q 3738 3031 3350 3393 
Q 2963 3756 2222 3756 
L 1791 3756 
z
M 588 4666 
L 1856 4666 
Q 2919 4666 3439 4514 
Q 3959 4363 4331 4000 
Q 4659 3684 4818 3271 
Q 4978 2859 4978 2338 
Q 4978 1809 4818 1395 
Q 4659 981 4331 666 
Q 3956 303 3431 151 
Q 2906 0 1856 0 
L 588 0 
L 588 4666 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-25" d="M 2456 2859 
Q 2741 2859 2887 2984 
Q 3034 3109 3034 3353 
Q 3034 3594 2887 3720 
Q 2741 3847 2456 3847 
L 1791 3847 
L 1791 2859 
L 2456 2859 
z
M 2497 819 
Q 2859 819 3042 972 
Q 3225 1125 3225 1434 
Q 3225 1738 3044 1889 
Q 2863 2041 2497 2041 
L 1791 2041 
L 1791 819 
L 2497 819 
z
M 3616 2497 
Q 4003 2384 4215 2081 
Q 4428 1778 4428 1338 
Q 4428 663 3972 331 
Q 3516 0 2584 0 
L 588 0 
L 588 4666 
L 2394 4666 
Q 3366 4666 3802 4372 
Q 4238 4078 4238 3431 
Q 4238 3091 4078 2852 
Q 3919 2613 3616 2497 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-e" d="M 3053 4013 
L 3053 2375 
L 4684 2375 
L 4684 1638 
L 3053 1638 
L 3053 0 
L 2309 0 
L 2309 1638 
L 678 1638 
L 678 2375 
L 2309 2375 
L 2309 4013 
L 3053 4013 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-Bold-36"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(72.015625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-57" transform="translate(139.84375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-58" transform="translate(187.640625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-53" transform="translate(258.828125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(330.40625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-46" transform="translate(365.21875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-52" transform="translate(424.5 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(493.203125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-57" transform="translate(552.71875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-1d" transform="translate(600.515625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(640.5 0)"/>
     <use xlink:href="#DejaVuSans-Bold-55" transform="translate(675.3125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(724.625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-44" transform="translate(792.453125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-47" transform="translate(859.9375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(931.515625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-49" transform="translate(966.328125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-55" transform="translate(1009.828125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-52" transform="translate(1059.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-50" transform="translate(1127.84375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(1232.046875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-2f" transform="translate(1266.859375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-44" transform="translate(1330.578125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-50" transform="translate(1398.0625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4c" transform="translate(1502.265625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-51" transform="translate(1536.546875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-27" transform="translate(1607.734375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-25" transform="translate(1690.75 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(1766.96875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-e" transform="translate(1801.78125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(1885.578125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4c" transform="translate(1920.390625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-51" transform="translate(1954.671875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4a" transform="translate(2025.859375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(2097.4375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(2165.265625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-57" transform="translate(2224.78125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(2272.578125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4c" transform="translate(2307.390625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-51" transform="translate(2341.671875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-57" transform="translate(2412.859375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-52" transform="translate(2460.65625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(2529.359375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(2564.171875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-51" transform="translate(2632 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4a" transform="translate(2703.1875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4c" transform="translate(2774.765625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-51" transform="translate(2809.046875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(2880.234375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(2948.0625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(2982.875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-57" transform="translate(3042.390625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-52" transform="translate(3090.1875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-55" transform="translate(3158.890625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(3208.203125 0)"/>
    </g>
   </g>
   <g id="legend_1">
    <g id="patch_15">
     <path d="M 46.525781 58.719375 
L 170.978281 58.719375 
Q 172.578281 58.719375 172.578281 57.119375 
L 172.578281 33.918125 
Q 172.578281 32.318125 170.978281 32.318125 
L 46.525781 32.318125 
Q 44.925781 32.318125 44.925781 33.918125 
L 44.925781 57.119375 
Q 44.925781 58.719375 46.525781 58.719375 
z
" style="fill: #ffffff; opacity: 0.9; stroke: #cccccc; stroke-linejoin: miter"/>
    </g>
    <g id="patch_16">
     <path d="M 48.125781 41.596875 
L 64.125781 41.596875 
L 64.125781 35.996875 
L 48.125781 35.996875 
z
" style="fill: #888888; opacity: 0.9; stroke: #888888; stroke-linejoin: miter"/>
    </g>
    <g id="text_24">
     <!-- Read from LaminDB (S3) -->
     <g transform="translate(70.525781 41.596875) scale(0.08 -0.08)">
      <defs>
       <path id="DejaVuSans-35" d="M 2841 2188 
Q 3044 2119 3236 1894 
Q 3428 1669 3622 1275 
L 4263 0 
L 3584 0 
L 2988 1197 
Q 2756 1666 2539 1819 
Q 2322 1972 1947 1972 
L 1259 1972 
L 1259 0 
L 628 0 
L 628 4666 
L 2053 4666 
Q 2853 4666 3247 4331 
Q 3641 3997 3641 3322 
Q 3641 2881 3436 2590 
Q 3231 2300 2841 2188 
z
M 1259 4147 
L 1259 2491 
L 2053 2491 
Q 2509 2491 2742 2702 
Q 2975 2913 2975 3322 
Q 2975 3731 2742 3939 
Q 2509 4147 2053 4147 
L 1259 4147 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-49" d="M 2375 4863 
L 2375 4384 
L 1825 4384 
Q 1516 4384 1395 4259 
Q 1275 4134 1275 3809 
L 1275 3500 
L 2222 3500 
L 2222 3053 
L 1275 3053 
L 1275 0 
L 697 0 
L 697 3053 
L 147 3053 
L 147 3500 
L 697 3500 
L 697 3744 
Q 697 4328 969 4595 
Q 1241 4863 1831 4863 
L 2375 4863 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-36" d="M 3425 4513 
L 3425 3897 
Q 3066 4069 2747 4153 
Q 2428 4238 2131 4238 
Q 1616 4238 1336 4038 
Q 1056 3838 1056 3469 
Q 1056 3159 1242 3001 
Q 1428 2844 1947 2747 
L 2328 2669 
Q 3034 2534 3370 2195 
Q 3706 1856 3706 1288 
Q 3706 609 3251 259 
Q 2797 -91 1919 -91 
Q 1588 -91 1214 -16 
Q 841 59 441 206 
L 441 856 
Q 825 641 1194 531 
Q 1563 422 1919 422 
Q 2459 422 2753 634 
Q 3047 847 3047 1241 
Q 3047 1584 2836 1778 
Q 2625 1972 2144 2069 
L 1759 2144 
Q 1053 2284 737 2584 
Q 422 2884 422 3419 
Q 422 4038 858 4394 
Q 1294 4750 2059 4750 
Q 2388 4750 2728 4690 
Q 3069 4631 3425 4513 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-16" d="M 2597 2516 
Q 3050 2419 3304 2112 
Q 3559 1806 3559 1356 
Q 3559 666 3084 287 
Q 2609 -91 1734 -91 
Q 1441 -91 1130 -33 
Q 819 25 488 141 
L 488 750 
Q 750 597 1062 519 
Q 1375 441 1716 441 
Q 2309 441 2620 675 
Q 2931 909 2931 1356 
Q 2931 1769 2642 2001 
Q 2353 2234 1838 2234 
L 1294 2234 
L 1294 2753 
L 1863 2753 
Q 2328 2753 2575 2939 
Q 2822 3125 2822 3475 
Q 2822 3834 2567 4026 
Q 2313 4219 1838 4219 
Q 1578 4219 1281 4162 
Q 984 4106 628 3988 
L 628 4550 
Q 988 4650 1302 4700 
Q 1616 4750 1894 4750 
Q 2613 4750 3031 4423 
Q 3450 4097 3450 3541 
Q 3450 3153 3228 2886 
Q 3006 2619 2597 2516 
z
" transform="scale(0.015625)"/>
      </defs>
      <use xlink:href="#DejaVuSans-35"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(65 0)"/>
      <use xlink:href="#DejaVuSans-44" transform="translate(126.53125 0)"/>
      <use xlink:href="#DejaVuSans-47" transform="translate(187.8125 0)"/>
      <use xlink:href="#DejaVuSans-3" transform="translate(251.296875 0)"/>
      <use xlink:href="#DejaVuSans-49" transform="translate(283.078125 0)"/>
      <use xlink:href="#DejaVuSans-55" transform="translate(318.28125 0)"/>
      <use xlink:href="#DejaVuSans-52" transform="translate(357.1875 0)"/>
      <use xlink:href="#DejaVuSans-50" transform="translate(418.375 0)"/>
      <use xlink:href="#DejaVuSans-3" transform="translate(515.78125 0)"/>
      <use xlink:href="#DejaVuSans-2f" transform="translate(547.5625 0)"/>
      <use xlink:href="#DejaVuSans-44" transform="translate(603.28125 0)"/>
      <use xlink:href="#DejaVuSans-50" transform="translate(664.5625 0)"/>
      <use xlink:href="#DejaVuSans-4c" transform="translate(761.96875 0)"/>
      <use xlink:href="#DejaVuSans-51" transform="translate(789.75 0)"/>
      <use xlink:href="#DejaVuSans-27" transform="translate(853.125 0)"/>
      <use xlink:href="#DejaVuSans-25" transform="translate(930.125 0)"/>
      <use xlink:href="#DejaVuSans-3" transform="translate(998.734375 0)"/>
      <use xlink:href="#DejaVuSans-b" transform="translate(1030.515625 0)"/>
      <use xlink:href="#DejaVuSans-36" transform="translate(1069.53125 0)"/>
      <use xlink:href="#DejaVuSans-16" transform="translate(1133.015625 0)"/>
      <use xlink:href="#DejaVuSans-c" transform="translate(1196.640625 0)"/>
     </g>
    </g>
    <g id="patch_17">
     <path d="M 48.125781 53.5975 
L 64.125781 53.5975 
L 64.125781 47.9975 
L 48.125781 47.9975 
z
" style="fill: url(#hc42b5eeeea); opacity: 0.4; stroke: #888888; stroke-linejoin: miter"/>
    </g>
    <g id="text_25">
     <!-- Ingest into engine store -->
     <g transform="translate(70.525781 53.5975) scale(0.08 -0.08)">
      <defs>
       <path id="DejaVuSans-57" d="M 1172 4494 
L 1172 3500 
L 2356 3500 
L 2356 3053 
L 1172 3053 
L 1172 1153 
Q 1172 725 1289 603 
Q 1406 481 1766 481 
L 2356 481 
L 2356 0 
L 1766 0 
Q 1100 0 847 248 
Q 594 497 594 1153 
L 594 3053 
L 172 3053 
L 172 3500 
L 594 3500 
L 594 4494 
L 1172 4494 
z
" transform="scale(0.015625)"/>
      </defs>
      <use xlink:href="#DejaVuSans-2c"/>
      <use xlink:href="#DejaVuSans-51" transform="translate(29.5 0)"/>
      <use xlink:href="#DejaVuSans-4a" transform="translate(92.875 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(156.359375 0)"/>
      <use xlink:href="#DejaVuSans-56" transform="translate(217.890625 0)"/>
      <use xlink:href="#DejaVuSans-57" transform="translate(269.984375 0)"/>
      <use xlink:href="#DejaVuSans-3" transform="translate(309.1875 0)"/>
      <use xlink:href="#DejaVuSans-4c" transform="translate(340.96875 0)"/>
      <use xlink:href="#DejaVuSans-51" transform="translate(368.75 0)"/>
      <use xlink:href="#DejaVuSans-57" transform="translate(432.125 0)"/>
      <use xlink:href="#DejaVuSans-52" transform="translate(471.328125 0)"/>
      <use xlink:href="#DejaVuSans-3" transform="translate(532.515625 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(564.296875 0)"/>
      <use xlink:href="#DejaVuSans-51" transform="translate(625.828125 0)"/>
      <use xlink:href="#DejaVuSans-4a" transform="translate(689.203125 0)"/>
      <use xlink:href="#DejaVuSans-4c" transform="translate(752.6875 0)"/>
      <use xlink:href="#DejaVuSans-51" transform="translate(780.46875 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(843.84375 0)"/>
      <use xlink:href="#DejaVuSans-3" transform="translate(905.375 0)"/>
      <use xlink:href="#DejaVuSans-56" transform="translate(937.15625 0)"/>
      <use xlink:href="#DejaVuSans-57" transform="translate(989.25 0)"/>
      <use xlink:href="#DejaVuSans-52" transform="translate(1028.453125 0)"/>
      <use xlink:href="#DejaVuSans-55" transform="translate(1089.640625 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(1128.546875 0)"/>
     </g>
    </g>
   </g>
  </g>
 </g>
 <defs>
  <clipPath id="p843ab579ba">
   <rect x="40.925781" y="28.318125" width="520.117656" height="299.04"/>
  </clipPath>
 </defs>
 <defs>
  <pattern id="ha18f562144" patternUnits="userSpaceOnUse" x="0" y="0" width="72" height="72">
   <rect x="0" y="0" width="73" height="73" fill="#55a868"/>
   <path d="M -36 36 
L 36 -36 
M -30 42 
L 42 -30 
M -24 48 
L 48 -24 
M -18 54 
L 54 -18 
M -12 60 
L 60 -12 
M -6 66 
L 66 -6 
M 0 72 
L 72 0 
M 6 78 
L 78 6 
M 12 84 
L 84 12 
M 18 90 
L 90 18 
M 24 96 
L 96 24 
M 30 102 
L 102 30 
M 36 108 
L 108 36 
M -36 36 
L 36 108 
M -30 30 
L 42 102 
M -24 24 
L 48 96 
M -18 18 
L 54 90 
M -12 12 
L 60 84 
M -6 6 
L 66 78 
M 0 0 
L 72 72 
M 6 -6 
L 78 66 
M 12 -12 
L 84 60 
M 18 -18 
L 90 54 
M 24 -24 
L 96 48 
M 30 -30 
L 102 42 
M 36 -36 
L 108 36 
" style="fill: #000000; stroke: #000000; stroke-width: 1.0; stroke-linecap: butt; stroke-linejoin: miter"/>
  </pattern>
  <pattern id="hf5b8d32bc1" patternUnits="userSpaceOnUse" x="0" y="0" width="72" height="72">
   <rect x="0" y="0" width="73" height="73" fill="#c44e52"/>
   <path d="M -36 36 
L 36 -36 
M -30 42 
L 42 -30 
M -24 48 
L 48 -24 
M -18 54 
L 54 -18 
M -12 60 
L 60 -12 
M -6 66 
L 66 -6 
M 0 72 
L 72 0 
M 6 78 
L 78 6 
M 12 84 
L 84 12 
M 18 90 
L 90 18 
M 24 96 
L 96 24 
M 30 102 
L 102 30 
M 36 108 
L 108 36 
M -36 36 
L 36 108 
M -30 30 
L 42 102 
M -24 24 
L 48 96 
M -18 18 
L 54 90 
M -12 12 
L 60 84 
M -6 6 
L 66 78 
M 0 0 
L 72 72 
M 6 -6 
L 78 66 
M 12 -12 
L 84 60 
M 18 -18 
L 90 54 
M 24 -24 
L 96 48 
M 30 -30 
L 102 42 
M 36 -36 
L 108 36 
" style="fill: #000000; stroke: #000000; stroke-width: 1.0; stroke-linecap: butt; stroke-linejoin: miter"/>
  </pattern>
  <pattern id="hc42b5eeeea" patternUnits="userSpaceOnUse" x="0" y="0" width="72" height="72">
   <rect x="0" y="0" width="73" height="73" fill="#888888"/>
   <path d="M -36 36 
L 36 -36 
M -30 42 
L 42 -30 
M -24 48 
L 48 -24 
M -18 54 
L 54 -18 
M -12 60 
L 60 -12 
M -6 66 
L 66 -6 
M 0 72 
L 72 0 
M 6 78 
L 78 6 
M 12 84 
L 84 12 
M 18 90 
L 90 18 
M 24 96 
L 96 24 
M 30 102 
L 102 30 
M 36 108 
L 108 36 
M -36 36 
L 36 108 
M -30 30 
L 42 102 
M -24 24 
L 48 96 
M -18 18 
L 54 90 
M -12 12 
L 60 84 
M -6 6 
L 66 78 
M 0 0 
L 72 72 
M 6 -6 
L 78 66 
M 12 -12 
L 84 60 
M 18 -18 
L 90 54 
M 24 -24 
L 96 48 
M 30 -30 
L 102 42 
M 36 -36 
L 108 36 
" style="fill: #888888; stroke: #888888; stroke-width: 1.0; stroke-linecap: butt; stroke-linejoin: miter; stroke-opacity: 0.4"/>
  </pattern>
 </defs>
</svg>

---

## Queries

Three queries were run against all five engines. The computation logic is equivalent across engines; differences in timing reflect S3 read strategy and whether data has been pre-ingested.

### Caveats on timing

All timings are single-run measurements on 8,929 rows. At this scale, results are dominated by fixed overheads (connection setup, S3 round-trips) rather than computational throughput. Iceberg and LanceDB query times reflect reads from their own pre-ingested S3 store, not from the source Parquet — their setup time should be amortised across queries when comparing total cost.

### Query 1 — per-sample CNV statistics

For each sample: total CNV count, deletion count, median deletion size, homozygous count, heterozygous count.

::::::{tab-set}
:::::{tab-item} PyArrow
```python
df = dataset.to_table().to_pandas()

stats = df.groupby("SAMPLE_NAME").agg(
    Total_CNVs=("INFO_SVLEN", "count"),
    Deletions=("INFO_SVLEN", lambda x: (x < 0).sum()),
    Median_Deletion_Size=("INFO_SVLEN", lambda x: abs(x[x < 0]).median()),
    Homozygous_CNVs=("SAMPLE_GT", lambda x: (x == "1/1").sum()),
    Heterozygous_CNVs=("SAMPLE_GT", lambda x: (x == "0/1").sum()),
).reset_index()
```
:::::

:::::{tab-item} Polars
```python
df = lazy_df.collect().to_pandas()

stats = df.groupby("SAMPLE_NAME").agg(
    Total_CNVs=("INFO_SVLEN", "count"),
    Deletions=("INFO_SVLEN", lambda x: (x < 0).sum()),
    Median_Deletion_Size=("INFO_SVLEN", lambda x: abs(x[x < 0]).median()),
    Homozygous_CNVs=("SAMPLE_GT", lambda x: (x == "1/1").sum()),
    Heterozygous_CNVs=("SAMPLE_GT", lambda x: (x == "0/1").sum()),
).reset_index()
```
:::::

:::::{tab-item} DuckDB
```python
stats = con.execute("""
    SELECT
        SAMPLE_NAME,
        COUNT(*)                                               AS Total_CNVs,
        COUNT(*) FILTER (WHERE INFO_SVLEN < 0)                 AS Deletions,
        MEDIAN(ABS(INFO_SVLEN)) FILTER (WHERE INFO_SVLEN < 0)  AS Median_Deletion_Size,
        COUNT(*) FILTER (WHERE SAMPLE_GT = '1/1')              AS Homozygous_CNVs,
        COUNT(*) FILTER (WHERE SAMPLE_GT = '0/1')              AS Heterozygous_CNVs
    FROM cnv_vcf
    GROUP BY SAMPLE_NAME
""").df()
```
:::::

:::::{tab-item} Iceberg
```python
df = table.scan().to_arrow().to_pandas()

stats = df.groupby("SAMPLE_NAME").agg(
    Total_CNVs=("INFO_SVLEN", "count"),
    Deletions=("INFO_SVLEN", lambda x: (x < 0).sum()),
    Median_Deletion_Size=("INFO_SVLEN", lambda x: abs(x[x < 0]).median()),
    Homozygous_CNVs=("SAMPLE_GT", lambda x: (x == "1/1").sum()),
    Heterozygous_CNVs=("SAMPLE_GT", lambda x: (x == "0/1").sum()),
).reset_index()
```
:::::

:::::{tab-item} LanceDB
```python
df = table.to_arrow().to_pandas()

stats = df.groupby("SAMPLE_NAME").agg(
    Total_CNVs=("INFO_SVLEN", "count"),
    Deletions=("INFO_SVLEN", lambda x: (x < 0).sum()),
    Median_Deletion_Size=("INFO_SVLEN", lambda x: abs(x[x < 0]).median()),
    Homozygous_CNVs=("SAMPLE_GT", lambda x: (x == "1/1").sum()),
    Heterozygous_CNVs=("SAMPLE_GT", lambda x: (x == "0/1").sum()),
).reset_index()
```
:::::
::::::

### Query 2 — recurrent region detection

Genomic positions are binned into 1 kbp windows. Bins containing CNVs from two or more distinct samples are identified as recurrent regions. All five engines produced 1,903 recurrent regions.

::::::{tab-set}
:::::{tab-item} PyArrow
```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]   # 1,903 recurrent regions
```
:::::

:::::{tab-item} Polars
```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]   # 1,903 recurrent regions
```
:::::

:::::{tab-item} DuckDB
```python
recurrent = con.execute("""
    SELECT
        CHROM || ':' || CAST((POS // 1000) * 1000 AS VARCHAR) AS region_key,
        COUNT(DISTINCT SAMPLE_NAME) AS sample_count
    FROM cnv_vcf
    GROUP BY region_key
    HAVING COUNT(DISTINCT SAMPLE_NAME) >= 2
    ORDER BY sample_count DESC
""").df()   # 1,903 recurrent regions
```
:::::

:::::{tab-item} Iceberg
```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]   # 1,903 recurrent regions
```
:::::

:::::{tab-item} LanceDB
```python
df["region_key"] = df["CHROM"] + ":" + ((df["POS"] // 1000) * 1000).astype(str)
recurrent = df.groupby("region_key")["SAMPLE_NAME"].nunique()
recurrent = recurrent[recurrent >= 2]   # 1,903 recurrent regions
```
:::::
::::::

### Query 3 — filtered query

Variants on the most prevalent chromosome within the 10th–90th percentile position band. Each engine pushes the predicate into the storage layer. All five returned 589 variants.

::::::{tab-set}
:::::{tab-item} PyArrow
```python
import pyarrow.compute as pc
expr = ((pc.field("CHROM") == chrom)
        & (pc.field("POS") >= lo) & (pc.field("POS") <= hi))
filtered = dataset.to_table(filter=expr)   # predicate pushdown into Parquet row groups
```
:::::

:::::{tab-item} Polars
```python
filtered = lazy_df.filter(
    (pl.col("CHROM") == chrom) & (pl.col("POS") >= lo) & (pl.col("POS") <= hi)
).collect()
```
:::::

:::::{tab-item} DuckDB
```python
filtered = con.execute(
    "SELECT * FROM cnv_vcf WHERE CHROM = ? AND POS BETWEEN ? AND ?",
    [chrom, lo, hi],
).df()
```
:::::

:::::{tab-item} Iceberg
```python
from pyiceberg.expressions import And, EqualTo, GreaterThanOrEqual, LessThanOrEqual
row_filter = And(EqualTo("CHROM", chrom),
             And(GreaterThanOrEqual("POS", lo), LessThanOrEqual("POS", hi)))
filtered = table.scan(row_filter=row_filter).to_arrow()
```
:::::

:::::{tab-item} LanceDB
```python
filtered = table.to_lance().to_table(
    filter=f"CHROM = '{chrom}' AND POS BETWEEN {lo} AND {hi}"
).to_pandas()
```
:::::
::::::

<!-- PLOT: query_times.svg -->
<?xml version="1.0" encoding="utf-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns:xlink="http://www.w3.org/1999/xlink" width="640.541562pt" height="351.915pt" viewBox="0 0 640.541562 351.915" xmlns="http://www.w3.org/2000/svg" version="1.1">
 <metadata>
  <rdf:RDF xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:cc="http://creativecommons.org/ns#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
   <cc:Work>
    <dc:type rdf:resource="http://purl.org/dc/dcmitype/StillImage"/>
    <dc:date>2026-06-25T14:37:50.926411</dc:date>
    <dc:format>image/svg+xml</dc:format>
    <dc:creator>
     <cc:Agent>
      <dc:title>Matplotlib v3.11.0, https://matplotlib.org/</dc:title>
     </cc:Agent>
    </dc:creator>
   </cc:Work>
  </rdf:RDF>
 </metadata>
 <defs>
  <style type="text/css">*{stroke-linejoin: round; stroke-linecap: butt}</style>
 </defs>
 <g id="figure_1">
  <g id="patch_1">
   <path d="M 0 351.915 
L 640.541562 351.915 
L 640.541562 0 
L 0 0 
z
" style="fill: #ffffff"/>
  </g>
  <g id="axes_1">
   <g id="patch_2">
    <path d="M 44.103906 313.709531 
L 633.341562 313.709531 
L 633.341562 28.318125 
L 44.103906 28.318125 
z
" style="fill: #ffffff"/>
   </g>
   <g id="patch_3">
    <path d="M 70.887436 313.709531 
L 104.135956 313.709531 
L 104.135956 41.908192 
L 70.887436 41.908192 
z
" clip-path="url(#pff3e02fd7d)" style="fill: #4c72b0; opacity: 0.85"/>
   </g>
   <g id="patch_4">
    <path d="M 255.601435 313.709531 
L 288.849955 313.709531 
L 288.849955 93.647671 
L 255.601435 93.647671 
z
" clip-path="url(#pff3e02fd7d)" style="fill: #4c72b0; opacity: 0.85"/>
   </g>
   <g id="patch_5">
    <path d="M 440.315434 313.709531 
L 473.563954 313.709531 
L 473.563954 136.838746 
L 440.315434 136.838746 
z
" clip-path="url(#pff3e02fd7d)" style="fill: #4c72b0; opacity: 0.85"/>
   </g>
   <g id="patch_6">
    <path d="M 104.135956 313.709531 
L 137.384476 313.709531 
L 137.384476 238.100947 
L 104.135956 238.100947 
z
" clip-path="url(#pff3e02fd7d)" style="fill: #8b5cf6; opacity: 0.85"/>
   </g>
   <g id="patch_7">
    <path d="M 288.849955 313.709531 
L 322.098474 313.709531 
L 322.098474 240.372688 
L 288.849955 240.372688 
z
" clip-path="url(#pff3e02fd7d)" style="fill: #8b5cf6; opacity: 0.85"/>
   </g>
   <g id="patch_8">
    <path d="M 473.563954 313.709531 
L 506.812473 313.709531 
L 506.812473 253.178953 
L 473.563954 253.178953 
z
" clip-path="url(#pff3e02fd7d)" style="fill: #8b5cf6; opacity: 0.85"/>
   </g>
   <g id="patch_9">
    <path d="M 137.384476 313.709531 
L 170.632995 313.709531 
L 170.632995 177.380475 
L 137.384476 177.380475 
z
" clip-path="url(#pff3e02fd7d)" style="fill: #dd8452; opacity: 0.85"/>
   </g>
   <g id="patch_10">
    <path d="M 322.098474 313.709531 
L 355.346994 313.709531 
L 355.346994 180.245971 
L 322.098474 180.245971 
z
" clip-path="url(#pff3e02fd7d)" style="fill: #dd8452; opacity: 0.85"/>
   </g>
   <g id="patch_11">
    <path d="M 506.812473 313.709531 
L 540.060993 313.709531 
L 540.060993 174.791807 
L 506.812473 174.791807 
z
" clip-path="url(#pff3e02fd7d)" style="fill: #dd8452; opacity: 0.85"/>
   </g>
   <g id="patch_12">
    <path d="M 170.632995 313.709531 
L 203.881515 313.709531 
L 203.881515 282.614181 
L 170.632995 282.614181 
z
" clip-path="url(#pff3e02fd7d)" style="fill: #55a868; opacity: 0.85"/>
   </g>
   <g id="patch_13">
    <path d="M 355.346994 313.709531 
L 388.595514 313.709531 
L 388.595514 287.787608 
L 355.346994 287.787608 
z
" clip-path="url(#pff3e02fd7d)" style="fill: #55a868; opacity: 0.85"/>
   </g>
   <g id="patch_14">
    <path d="M 540.060993 313.709531 
L 573.309513 313.709531 
L 573.309513 289.633315 
L 540.060993 289.633315 
z
" clip-path="url(#pff3e02fd7d)" style="fill: #55a868; opacity: 0.85"/>
   </g>
   <g id="patch_15">
    <path d="M 203.881515 313.709531 
L 237.130035 313.709531 
L 237.130035 283.832055 
L 203.881515 283.832055 
z
" clip-path="url(#pff3e02fd7d)" style="fill: #c44e52; opacity: 0.85"/>
   </g>
   <g id="patch_16">
    <path d="M 388.595514 313.709531 
L 421.844034 313.709531 
L 421.844034 303.753107 
L 388.595514 303.753107 
z
" clip-path="url(#pff3e02fd7d)" style="fill: #c44e52; opacity: 0.85"/>
   </g>
   <g id="patch_17">
    <path d="M 573.309513 313.709531 
L 606.558033 313.709531 
L 606.558033 254.763 
L 573.309513 254.763 
z
" clip-path="url(#pff3e02fd7d)" style="fill: #c44e52; opacity: 0.85"/>
   </g>
   <g id="matplotlib.axis_1">
    <g id="xtick_1">
     <g id="line2d_1">
      <defs>
       <path id="m9672ed2363" d="M 0 0 
L 0 3.5 
" style="stroke: #000000; stroke-width: 0.8"/>
      </defs>
      <g>
       <use xlink:href="#m9672ed2363" x="154.008736" y="313.709531" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_1">
      <!-- Per-sample -->
      <g transform="translate(126.376704 329.308945) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-33" d="M 1259 4147 
L 1259 2394 
L 2053 2394 
Q 2494 2394 2734 2622 
Q 2975 2850 2975 3272 
Q 2975 3691 2734 3919 
Q 2494 4147 2053 4147 
L 1259 4147 
z
M 628 4666 
L 2053 4666 
Q 2838 4666 3239 4311 
Q 3641 3956 3641 3272 
Q 3641 2581 3239 2228 
Q 2838 1875 2053 1875 
L 1259 1875 
L 1259 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-48" d="M 3597 1894 
L 3597 1613 
L 953 1613 
Q 991 1019 1311 708 
Q 1631 397 2203 397 
Q 2534 397 2845 478 
Q 3156 559 3463 722 
L 3463 178 
Q 3153 47 2828 -22 
Q 2503 -91 2169 -91 
Q 1331 -91 842 396 
Q 353 884 353 1716 
Q 353 2575 817 3079 
Q 1281 3584 2069 3584 
Q 2775 3584 3186 3129 
Q 3597 2675 3597 1894 
z
M 3022 2063 
Q 3016 2534 2758 2815 
Q 2500 3097 2075 3097 
Q 1594 3097 1305 2825 
Q 1016 2553 972 2059 
L 3022 2063 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-55" d="M 2631 2963 
Q 2534 3019 2420 3045 
Q 2306 3072 2169 3072 
Q 1681 3072 1420 2755 
Q 1159 2438 1159 1844 
L 1159 0 
L 581 0 
L 581 3500 
L 1159 3500 
L 1159 2956 
Q 1341 3275 1631 3429 
Q 1922 3584 2338 3584 
Q 2397 3584 2469 3576 
Q 2541 3569 2628 3553 
L 2631 2963 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-10" d="M 313 2009 
L 1997 2009 
L 1997 1497 
L 313 1497 
L 313 2009 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-56" d="M 2834 3397 
L 2834 2853 
Q 2591 2978 2328 3040 
Q 2066 3103 1784 3103 
Q 1356 3103 1142 2972 
Q 928 2841 928 2578 
Q 928 2378 1081 2264 
Q 1234 2150 1697 2047 
L 1894 2003 
Q 2506 1872 2764 1633 
Q 3022 1394 3022 966 
Q 3022 478 2636 193 
Q 2250 -91 1575 -91 
Q 1294 -91 989 -36 
Q 684 19 347 128 
L 347 722 
Q 666 556 975 473 
Q 1284 391 1588 391 
Q 1994 391 2212 530 
Q 2431 669 2431 922 
Q 2431 1156 2273 1281 
Q 2116 1406 1581 1522 
L 1381 1569 
Q 847 1681 609 1914 
Q 372 2147 372 2553 
Q 372 3047 722 3315 
Q 1072 3584 1716 3584 
Q 2034 3584 2315 3537 
Q 2597 3491 2834 3397 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-44" d="M 2194 1759 
Q 1497 1759 1228 1600 
Q 959 1441 959 1056 
Q 959 750 1161 570 
Q 1363 391 1709 391 
Q 2188 391 2477 730 
Q 2766 1069 2766 1631 
L 2766 1759 
L 2194 1759 
z
M 3341 1997 
L 3341 0 
L 2766 0 
L 2766 531 
Q 2569 213 2275 61 
Q 1981 -91 1556 -91 
Q 1019 -91 701 211 
Q 384 513 384 1019 
Q 384 1609 779 1909 
Q 1175 2209 1959 2209 
L 2766 2209 
L 2766 2266 
Q 2766 2663 2505 2880 
Q 2244 3097 1772 3097 
Q 1472 3097 1187 3025 
Q 903 2953 641 2809 
L 641 3341 
Q 956 3463 1253 3523 
Q 1550 3584 1831 3584 
Q 2591 3584 2966 3190 
Q 3341 2797 3341 1997 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-50" d="M 3328 2828 
Q 3544 3216 3844 3400 
Q 4144 3584 4550 3584 
Q 5097 3584 5394 3201 
Q 5691 2819 5691 2113 
L 5691 0 
L 5113 0 
L 5113 2094 
Q 5113 2597 4934 2840 
Q 4756 3084 4391 3084 
Q 3944 3084 3684 2787 
Q 3425 2491 3425 1978 
L 3425 0 
L 2847 0 
L 2847 2094 
Q 2847 2600 2669 2842 
Q 2491 3084 2119 3084 
Q 1678 3084 1418 2786 
Q 1159 2488 1159 1978 
L 1159 0 
L 581 0 
L 581 3500 
L 1159 3500 
L 1159 2956 
Q 1356 3278 1631 3431 
Q 1906 3584 2284 3584 
Q 2666 3584 2933 3390 
Q 3200 3197 3328 2828 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-53" d="M 1159 525 
L 1159 -1331 
L 581 -1331 
L 581 3500 
L 1159 3500 
L 1159 2969 
Q 1341 3281 1617 3432 
Q 1894 3584 2278 3584 
Q 2916 3584 3314 3078 
Q 3713 2572 3713 1747 
Q 3713 922 3314 415 
Q 2916 -91 2278 -91 
Q 1894 -91 1617 61 
Q 1341 213 1159 525 
z
M 3116 1747 
Q 3116 2381 2855 2742 
Q 2594 3103 2138 3103 
Q 1681 3103 1420 2742 
Q 1159 2381 1159 1747 
Q 1159 1113 1420 752 
Q 1681 391 2138 391 
Q 2594 391 2855 752 
Q 3116 1113 3116 1747 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-4f" d="M 603 4863 
L 1178 4863 
L 1178 0 
L 603 0 
L 603 4863 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-33"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(56.734375 0)"/>
       <use xlink:href="#DejaVuSans-55" transform="translate(118.265625 0)"/>
       <use xlink:href="#DejaVuSans-10" transform="translate(152.984375 0)"/>
       <use xlink:href="#DejaVuSans-56" transform="translate(189.0625 0)"/>
       <use xlink:href="#DejaVuSans-44" transform="translate(241.15625 0)"/>
       <use xlink:href="#DejaVuSans-50" transform="translate(302.4375 0)"/>
       <use xlink:href="#DejaVuSans-53" transform="translate(399.84375 0)"/>
       <use xlink:href="#DejaVuSans-4f" transform="translate(463.328125 0)"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(491.109375 0)"/>
      </g>
      <!-- statistics -->
      <g transform="translate(131.722798 341.31168) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-57" d="M 1172 4494 
L 1172 3500 
L 2356 3500 
L 2356 3053 
L 1172 3053 
L 1172 1153 
Q 1172 725 1289 603 
Q 1406 481 1766 481 
L 2356 481 
L 2356 0 
L 1766 0 
Q 1100 0 847 248 
Q 594 497 594 1153 
L 594 3053 
L 172 3053 
L 172 3500 
L 594 3500 
L 594 4494 
L 1172 4494 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-4c" d="M 603 3500 
L 1178 3500 
L 1178 0 
L 603 0 
L 603 3500 
z
M 603 4863 
L 1178 4863 
L 1178 4134 
L 603 4134 
L 603 4863 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-46" d="M 3122 3366 
L 3122 2828 
Q 2878 2963 2633 3030 
Q 2388 3097 2138 3097 
Q 1578 3097 1268 2742 
Q 959 2388 959 1747 
Q 959 1106 1268 751 
Q 1578 397 2138 397 
Q 2388 397 2633 464 
Q 2878 531 3122 666 
L 3122 134 
Q 2881 22 2623 -34 
Q 2366 -91 2075 -91 
Q 1284 -91 818 406 
Q 353 903 353 1747 
Q 353 2603 823 3093 
Q 1294 3584 2113 3584 
Q 2378 3584 2631 3529 
Q 2884 3475 3122 3366 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-56"/>
       <use xlink:href="#DejaVuSans-57" transform="translate(52.09375 0)"/>
       <use xlink:href="#DejaVuSans-44" transform="translate(91.296875 0)"/>
       <use xlink:href="#DejaVuSans-57" transform="translate(152.578125 0)"/>
       <use xlink:href="#DejaVuSans-4c" transform="translate(191.78125 0)"/>
       <use xlink:href="#DejaVuSans-56" transform="translate(219.5625 0)"/>
       <use xlink:href="#DejaVuSans-57" transform="translate(271.65625 0)"/>
       <use xlink:href="#DejaVuSans-4c" transform="translate(310.859375 0)"/>
       <use xlink:href="#DejaVuSans-46" transform="translate(338.640625 0)"/>
       <use xlink:href="#DejaVuSans-56" transform="translate(393.625 0)"/>
      </g>
     </g>
    </g>
    <g id="xtick_2">
     <g id="line2d_2">
      <g>
       <use xlink:href="#m9672ed2363" x="338.722734" y="313.709531" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_2">
      <!-- Recurrent -->
      <g transform="translate(314.359453 329.308164) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-35" d="M 2841 2188 
Q 3044 2119 3236 1894 
Q 3428 1669 3622 1275 
L 4263 0 
L 3584 0 
L 2988 1197 
Q 2756 1666 2539 1819 
Q 2322 1972 1947 1972 
L 1259 1972 
L 1259 0 
L 628 0 
L 628 4666 
L 2053 4666 
Q 2853 4666 3247 4331 
Q 3641 3997 3641 3322 
Q 3641 2881 3436 2590 
Q 3231 2300 2841 2188 
z
M 1259 4147 
L 1259 2491 
L 2053 2491 
Q 2509 2491 2742 2702 
Q 2975 2913 2975 3322 
Q 2975 3731 2742 3939 
Q 2509 4147 2053 4147 
L 1259 4147 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-58" d="M 544 1381 
L 544 3500 
L 1119 3500 
L 1119 1403 
Q 1119 906 1312 657 
Q 1506 409 1894 409 
Q 2359 409 2629 706 
Q 2900 1003 2900 1516 
L 2900 3500 
L 3475 3500 
L 3475 0 
L 2900 0 
L 2900 538 
Q 2691 219 2414 64 
Q 2138 -91 1772 -91 
Q 1169 -91 856 284 
Q 544 659 544 1381 
z
M 1991 3584 
L 1991 3584 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-51" d="M 3513 2113 
L 3513 0 
L 2938 0 
L 2938 2094 
Q 2938 2591 2744 2837 
Q 2550 3084 2163 3084 
Q 1697 3084 1428 2787 
Q 1159 2491 1159 1978 
L 1159 0 
L 581 0 
L 581 3500 
L 1159 3500 
L 1159 2956 
Q 1366 3272 1645 3428 
Q 1925 3584 2291 3584 
Q 2894 3584 3203 3211 
Q 3513 2838 3513 2113 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-35"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(65 0)"/>
       <use xlink:href="#DejaVuSans-46" transform="translate(126.53125 0)"/>
       <use xlink:href="#DejaVuSans-58" transform="translate(181.515625 0)"/>
       <use xlink:href="#DejaVuSans-55" transform="translate(244.890625 0)"/>
       <use xlink:href="#DejaVuSans-55" transform="translate(284.25 0)"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(323.15625 0)"/>
       <use xlink:href="#DejaVuSans-51" transform="translate(384.6875 0)"/>
       <use xlink:href="#DejaVuSans-57" transform="translate(448.0625 0)"/>
      </g>
      <!-- regions -->
      <g transform="translate(320.304766 341.310898) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-4a" d="M 2906 1791 
Q 2906 2416 2648 2759 
Q 2391 3103 1925 3103 
Q 1463 3103 1205 2759 
Q 947 2416 947 1791 
Q 947 1169 1205 825 
Q 1463 481 1925 481 
Q 2391 481 2648 825 
Q 2906 1169 2906 1791 
z
M 3481 434 
Q 3481 -459 3084 -895 
Q 2688 -1331 1869 -1331 
Q 1566 -1331 1297 -1286 
Q 1028 -1241 775 -1147 
L 775 -588 
Q 1028 -725 1275 -790 
Q 1522 -856 1778 -856 
Q 2344 -856 2625 -561 
Q 2906 -266 2906 331 
L 2906 616 
Q 2728 306 2450 153 
Q 2172 0 1784 0 
Q 1141 0 747 490 
Q 353 981 353 1791 
Q 353 2603 747 3093 
Q 1141 3584 1784 3584 
Q 2172 3584 2450 3431 
Q 2728 3278 2906 2969 
L 2906 3500 
L 3481 3500 
L 3481 434 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-52" d="M 1959 3097 
Q 1497 3097 1228 2736 
Q 959 2375 959 1747 
Q 959 1119 1226 758 
Q 1494 397 1959 397 
Q 2419 397 2687 759 
Q 2956 1122 2956 1747 
Q 2956 2369 2687 2733 
Q 2419 3097 1959 3097 
z
M 1959 3584 
Q 2709 3584 3137 3096 
Q 3566 2609 3566 1747 
Q 3566 888 3137 398 
Q 2709 -91 1959 -91 
Q 1206 -91 779 398 
Q 353 888 353 1747 
Q 353 2609 779 3096 
Q 1206 3584 1959 3584 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-55"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(38.90625 0)"/>
       <use xlink:href="#DejaVuSans-4a" transform="translate(100.4375 0)"/>
       <use xlink:href="#DejaVuSans-4c" transform="translate(163.921875 0)"/>
       <use xlink:href="#DejaVuSans-52" transform="translate(191.703125 0)"/>
       <use xlink:href="#DejaVuSans-51" transform="translate(252.890625 0)"/>
       <use xlink:href="#DejaVuSans-56" transform="translate(316.265625 0)"/>
      </g>
     </g>
    </g>
    <g id="xtick_3">
     <g id="line2d_3">
      <g>
       <use xlink:href="#m9672ed2363" x="523.436733" y="313.709531" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_3">
      <!-- Filtered query -->
      <g transform="translate(488.890639 329.308945) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-29" d="M 628 4666 
L 3309 4666 
L 3309 4134 
L 1259 4134 
L 1259 2759 
L 3109 2759 
L 3109 2228 
L 1259 2228 
L 1259 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-47" d="M 2906 2969 
L 2906 4863 
L 3481 4863 
L 3481 0 
L 2906 0 
L 2906 525 
Q 2725 213 2448 61 
Q 2172 -91 1784 -91 
Q 1150 -91 751 415 
Q 353 922 353 1747 
Q 353 2572 751 3078 
Q 1150 3584 1784 3584 
Q 2172 3584 2448 3432 
Q 2725 3281 2906 2969 
z
M 947 1747 
Q 947 1113 1208 752 
Q 1469 391 1925 391 
Q 2381 391 2643 752 
Q 2906 1113 2906 1747 
Q 2906 2381 2643 2742 
Q 2381 3103 1925 3103 
Q 1469 3103 1208 2742 
Q 947 2381 947 1747 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-3" transform="scale(0.015625)"/>
        <path id="DejaVuSans-54" d="M 947 1747 
Q 947 1113 1208 752 
Q 1469 391 1925 391 
Q 2381 391 2643 752 
Q 2906 1113 2906 1747 
Q 2906 2381 2643 2742 
Q 2381 3103 1925 3103 
Q 1469 3103 1208 2742 
Q 947 2381 947 1747 
z
M 2906 525 
Q 2725 213 2448 61 
Q 2172 -91 1784 -91 
Q 1150 -91 751 415 
Q 353 922 353 1747 
Q 353 2572 751 3078 
Q 1150 3584 1784 3584 
Q 2172 3584 2448 3432 
Q 2725 3281 2906 2969 
L 2906 3500 
L 3481 3500 
L 3481 -1331 
L 2906 -1331 
L 2906 525 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-5c" d="M 2059 -325 
Q 1816 -950 1584 -1140 
Q 1353 -1331 966 -1331 
L 506 -1331 
L 506 -850 
L 844 -850 
Q 1081 -850 1212 -737 
Q 1344 -625 1503 -206 
L 1606 56 
L 191 3500 
L 800 3500 
L 1894 763 
L 2988 3500 
L 3597 3500 
L 2059 -325 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-29"/>
       <use xlink:href="#DejaVuSans-4c" transform="translate(50.234375 0)"/>
       <use xlink:href="#DejaVuSans-4f" transform="translate(78.015625 0)"/>
       <use xlink:href="#DejaVuSans-57" transform="translate(105.796875 0)"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(145 0)"/>
       <use xlink:href="#DejaVuSans-55" transform="translate(206.53125 0)"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(245.4375 0)"/>
       <use xlink:href="#DejaVuSans-47" transform="translate(306.96875 0)"/>
       <use xlink:href="#DejaVuSans-3" transform="translate(370.453125 0)"/>
       <use xlink:href="#DejaVuSans-54" transform="translate(402.234375 0)"/>
       <use xlink:href="#DejaVuSans-58" transform="translate(465.71875 0)"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(529.09375 0)"/>
       <use xlink:href="#DejaVuSans-55" transform="translate(590.625 0)"/>
       <use xlink:href="#DejaVuSans-5c" transform="translate(631.734375 0)"/>
      </g>
      <!-- (native pushdown) -->
      <g transform="translate(476.720327 341.31168) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-b" d="M 1984 4856 
Q 1566 4138 1362 3434 
Q 1159 2731 1159 2009 
Q 1159 1288 1364 580 
Q 1569 -128 1984 -844 
L 1484 -844 
Q 1016 -109 783 600 
Q 550 1309 550 2009 
Q 550 2706 781 3412 
Q 1013 4119 1484 4856 
L 1984 4856 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-59" d="M 191 3500 
L 800 3500 
L 1894 563 
L 2988 3500 
L 3597 3500 
L 2284 0 
L 1503 0 
L 191 3500 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-4b" d="M 3513 2113 
L 3513 0 
L 2938 0 
L 2938 2094 
Q 2938 2591 2744 2837 
Q 2550 3084 2163 3084 
Q 1697 3084 1428 2787 
Q 1159 2491 1159 1978 
L 1159 0 
L 581 0 
L 581 4863 
L 1159 4863 
L 1159 2956 
Q 1366 3272 1645 3428 
Q 1925 3584 2291 3584 
Q 2894 3584 3203 3211 
Q 3513 2838 3513 2113 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-5a" d="M 269 3500 
L 844 3500 
L 1563 769 
L 2278 3500 
L 2956 3500 
L 3675 769 
L 4391 3500 
L 4966 3500 
L 4050 0 
L 3372 0 
L 2619 2869 
L 1863 0 
L 1184 0 
L 269 3500 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-c" d="M 513 4856 
L 1013 4856 
Q 1481 4119 1714 3412 
Q 1947 2706 1947 2009 
Q 1947 1309 1714 600 
Q 1481 -109 1013 -844 
L 513 -844 
Q 928 -128 1133 580 
Q 1338 1288 1338 2009 
Q 1338 2731 1133 3434 
Q 928 4138 513 4856 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-b"/>
       <use xlink:href="#DejaVuSans-51" transform="translate(39.015625 0)"/>
       <use xlink:href="#DejaVuSans-44" transform="translate(102.390625 0)"/>
       <use xlink:href="#DejaVuSans-57" transform="translate(163.671875 0)"/>
       <use xlink:href="#DejaVuSans-4c" transform="translate(202.875 0)"/>
       <use xlink:href="#DejaVuSans-59" transform="translate(230.65625 0)"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(289.84375 0)"/>
       <use xlink:href="#DejaVuSans-3" transform="translate(351.375 0)"/>
       <use xlink:href="#DejaVuSans-53" transform="translate(383.15625 0)"/>
       <use xlink:href="#DejaVuSans-58" transform="translate(446.640625 0)"/>
       <use xlink:href="#DejaVuSans-56" transform="translate(510.015625 0)"/>
       <use xlink:href="#DejaVuSans-4b" transform="translate(562.109375 0)"/>
       <use xlink:href="#DejaVuSans-47" transform="translate(625.484375 0)"/>
       <use xlink:href="#DejaVuSans-52" transform="translate(688.96875 0)"/>
       <use xlink:href="#DejaVuSans-5a" transform="translate(750.15625 0)"/>
       <use xlink:href="#DejaVuSans-51" transform="translate(831.9375 0)"/>
       <use xlink:href="#DejaVuSans-c" transform="translate(895.3125 0)"/>
      </g>
     </g>
    </g>
   </g>
   <g id="matplotlib.axis_2">
    <g id="ytick_1">
     <g id="line2d_4">
      <defs>
       <path id="m2e127e819e" d="M 0 0 
L -3.5 0 
" style="stroke: #000000; stroke-width: 0.8"/>
      </defs>
      <g>
       <use xlink:href="#m2e127e819e" x="44.103906" y="313.709531" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_4">
      <!-- 0.0 -->
      <g transform="translate(21.200781 317.508359) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-13" d="M 2034 4250 
Q 1547 4250 1301 3770 
Q 1056 3291 1056 2328 
Q 1056 1369 1301 889 
Q 1547 409 2034 409 
Q 2525 409 2770 889 
Q 3016 1369 3016 2328 
Q 3016 3291 2770 3770 
Q 2525 4250 2034 4250 
z
M 2034 4750 
Q 2819 4750 3233 4129 
Q 3647 3509 3647 2328 
Q 3647 1150 3233 529 
Q 2819 -91 2034 -91 
Q 1250 -91 836 529 
Q 422 1150 422 2328 
Q 422 3509 836 4129 
Q 1250 4750 2034 4750 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-11" d="M 684 794 
L 1344 794 
L 1344 0 
L 684 0 
L 684 794 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-13"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-13" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_2">
     <g id="line2d_5">
      <g>
       <use xlink:href="#m2e127e819e" x="44.103906" y="278.419273" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_5">
      <!-- 0.2 -->
      <g transform="translate(21.200781 282.218101) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-15" d="M 1228 531 
L 3431 531 
L 3431 0 
L 469 0 
L 469 531 
Q 828 903 1448 1529 
Q 2069 2156 2228 2338 
Q 2531 2678 2651 2914 
Q 2772 3150 2772 3378 
Q 2772 3750 2511 3984 
Q 2250 4219 1831 4219 
Q 1534 4219 1204 4116 
Q 875 4013 500 3803 
L 500 4441 
Q 881 4594 1212 4672 
Q 1544 4750 1819 4750 
Q 2544 4750 2975 4387 
Q 3406 4025 3406 3419 
Q 3406 3131 3298 2873 
Q 3191 2616 2906 2266 
Q 2828 2175 2409 1742 
Q 1991 1309 1228 531 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-13"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-15" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_3">
     <g id="line2d_6">
      <g>
       <use xlink:href="#m2e127e819e" x="44.103906" y="243.129015" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_6">
      <!-- 0.4 -->
      <g transform="translate(21.200781 246.927843) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-17" d="M 2419 4116 
L 825 1625 
L 2419 1625 
L 2419 4116 
z
M 2253 4666 
L 3047 4666 
L 3047 1625 
L 3713 1625 
L 3713 1100 
L 3047 1100 
L 3047 0 
L 2419 0 
L 2419 1100 
L 313 1100 
L 313 1709 
L 2253 4666 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-13"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-17" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_4">
     <g id="line2d_7">
      <g>
       <use xlink:href="#m2e127e819e" x="44.103906" y="207.838757" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_7">
      <!-- 0.6 -->
      <g transform="translate(21.200781 211.637585) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-19" d="M 2113 2584 
Q 1688 2584 1439 2293 
Q 1191 2003 1191 1497 
Q 1191 994 1439 701 
Q 1688 409 2113 409 
Q 2538 409 2786 701 
Q 3034 994 3034 1497 
Q 3034 2003 2786 2293 
Q 2538 2584 2113 2584 
z
M 3366 4563 
L 3366 3988 
Q 3128 4100 2886 4159 
Q 2644 4219 2406 4219 
Q 1781 4219 1451 3797 
Q 1122 3375 1075 2522 
Q 1259 2794 1537 2939 
Q 1816 3084 2150 3084 
Q 2853 3084 3261 2657 
Q 3669 2231 3669 1497 
Q 3669 778 3244 343 
Q 2819 -91 2113 -91 
Q 1303 -91 875 529 
Q 447 1150 447 2328 
Q 447 3434 972 4092 
Q 1497 4750 2381 4750 
Q 2619 4750 2861 4703 
Q 3103 4656 3366 4563 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-13"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-19" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_5">
     <g id="line2d_8">
      <g>
       <use xlink:href="#m2e127e819e" x="44.103906" y="172.548499" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_8">
      <!-- 0.8 -->
      <g transform="translate(21.200781 176.347327) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-1b" d="M 2034 2216 
Q 1584 2216 1326 1975 
Q 1069 1734 1069 1313 
Q 1069 891 1326 650 
Q 1584 409 2034 409 
Q 2484 409 2743 651 
Q 3003 894 3003 1313 
Q 3003 1734 2745 1975 
Q 2488 2216 2034 2216 
z
M 1403 2484 
Q 997 2584 770 2862 
Q 544 3141 544 3541 
Q 544 4100 942 4425 
Q 1341 4750 2034 4750 
Q 2731 4750 3128 4425 
Q 3525 4100 3525 3541 
Q 3525 3141 3298 2862 
Q 3072 2584 2669 2484 
Q 3125 2378 3379 2068 
Q 3634 1759 3634 1313 
Q 3634 634 3220 271 
Q 2806 -91 2034 -91 
Q 1263 -91 848 271 
Q 434 634 434 1313 
Q 434 1759 690 2068 
Q 947 2378 1403 2484 
z
M 1172 3481 
Q 1172 3119 1398 2916 
Q 1625 2713 2034 2713 
Q 2441 2713 2670 2916 
Q 2900 3119 2900 3481 
Q 2900 3844 2670 4047 
Q 2441 4250 2034 4250 
Q 1625 4250 1398 4047 
Q 1172 3844 1172 3481 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-13"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-1b" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_6">
     <g id="line2d_9">
      <g>
       <use xlink:href="#m2e127e819e" x="44.103906" y="137.25824" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_9">
      <!-- 1.0 -->
      <g transform="translate(21.200781 141.057069) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-14" d="M 794 531 
L 1825 531 
L 1825 4091 
L 703 3866 
L 703 4441 
L 1819 4666 
L 2450 4666 
L 2450 531 
L 3481 531 
L 3481 0 
L 794 0 
L 794 531 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-14"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-13" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_7">
     <g id="line2d_10">
      <g>
       <use xlink:href="#m2e127e819e" x="44.103906" y="101.967982" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_10">
      <!-- 1.2 -->
      <g transform="translate(21.200781 105.76681) scale(0.1 -0.1)">
       <use xlink:href="#DejaVuSans-14"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-15" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_8">
     <g id="line2d_11">
      <g>
       <use xlink:href="#m2e127e819e" x="44.103906" y="66.677724" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_11">
      <!-- 1.4 -->
      <g transform="translate(21.200781 70.476552) scale(0.1 -0.1)">
       <use xlink:href="#DejaVuSans-14"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-17" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_9">
     <g id="line2d_12">
      <g>
       <use xlink:href="#m2e127e819e" x="44.103906" y="31.387466" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_12">
      <!-- 1.6 -->
      <g transform="translate(21.200781 35.186294) scale(0.1 -0.1)">
       <use xlink:href="#DejaVuSans-14"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-19" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="text_13">
     <!-- Time (seconds) -->
     <g transform="translate(14.798438 209.177891) rotate(-90) scale(0.1 -0.1)">
      <defs>
       <path id="DejaVuSans-37" d="M -19 4666 
L 3928 4666 
L 3928 4134 
L 2272 4134 
L 2272 0 
L 1638 0 
L 1638 4134 
L -19 4134 
L -19 4666 
z
" transform="scale(0.015625)"/>
      </defs>
      <use xlink:href="#DejaVuSans-37"/>
      <use xlink:href="#DejaVuSans-4c" transform="translate(58 0)"/>
      <use xlink:href="#DejaVuSans-50" transform="translate(85.78125 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(183.1875 0)"/>
      <use xlink:href="#DejaVuSans-3" transform="translate(244.71875 0)"/>
      <use xlink:href="#DejaVuSans-b" transform="translate(276.5 0)"/>
      <use xlink:href="#DejaVuSans-56" transform="translate(315.515625 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(367.609375 0)"/>
      <use xlink:href="#DejaVuSans-46" transform="translate(429.140625 0)"/>
      <use xlink:href="#DejaVuSans-52" transform="translate(484.125 0)"/>
      <use xlink:href="#DejaVuSans-51" transform="translate(545.3125 0)"/>
      <use xlink:href="#DejaVuSans-47" transform="translate(608.6875 0)"/>
      <use xlink:href="#DejaVuSans-56" transform="translate(672.171875 0)"/>
      <use xlink:href="#DejaVuSans-c" transform="translate(724.265625 0)"/>
     </g>
    </g>
   </g>
   <g id="patch_18">
    <path d="M 44.103906 313.709531 
L 44.103906 28.318125 
" style="fill: none; stroke: #000000; stroke-width: 0.8; stroke-linejoin: miter; stroke-linecap: square"/>
   </g>
   <g id="patch_19">
    <path d="M 44.103906 313.709531 
L 633.341562 313.709531 
" style="fill: none; stroke: #000000; stroke-width: 0.8; stroke-linejoin: miter; stroke-linecap: square"/>
   </g>
   <g id="text_14">
    <!-- 1.54s -->
    <g transform="translate(81.997755 38.95458) rotate(-45) scale(0.07 -0.07)">
     <defs>
      <path id="DejaVuSans-18" d="M 691 4666 
L 3169 4666 
L 3169 4134 
L 1269 4134 
L 1269 2991 
Q 1406 3038 1543 3061 
Q 1681 3084 1819 3084 
Q 2600 3084 3056 2656 
Q 3513 2228 3513 1497 
Q 3513 744 3044 326 
Q 2575 -91 1722 -91 
Q 1428 -91 1123 -41 
Q 819 9 494 109 
L 494 744 
Q 775 591 1075 516 
Q 1375 441 1709 441 
Q 2250 441 2565 725 
Q 2881 1009 2881 1497 
Q 2881 1984 2565 2268 
Q 2250 2553 1709 2553 
Q 1456 2553 1204 2497 
Q 953 2441 691 2322 
L 691 4666 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-14"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-18" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-17" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_15">
    <!-- 1.25s -->
    <g transform="translate(266.711753 90.694059) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-14"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-15" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-18" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_16">
    <!-- 1.00s -->
    <g transform="translate(451.425752 133.885133) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-14"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-13" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-13" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_17">
    <!-- 0.43s -->
    <g transform="translate(115.246274 235.147334) rotate(-45) scale(0.07 -0.07)">
     <defs>
      <path id="DejaVuSans-16" d="M 2597 2516 
Q 3050 2419 3304 2112 
Q 3559 1806 3559 1356 
Q 3559 666 3084 287 
Q 2609 -91 1734 -91 
Q 1441 -91 1130 -33 
Q 819 25 488 141 
L 488 750 
Q 750 597 1062 519 
Q 1375 441 1716 441 
Q 2309 441 2620 675 
Q 2931 909 2931 1356 
Q 2931 1769 2642 2001 
Q 2353 2234 1838 2234 
L 1294 2234 
L 1294 2753 
L 1863 2753 
Q 2328 2753 2575 2939 
Q 2822 3125 2822 3475 
Q 2822 3834 2567 4026 
Q 2313 4219 1838 4219 
Q 1578 4219 1281 4162 
Q 984 4106 628 3988 
L 628 4550 
Q 988 4650 1302 4700 
Q 1616 4750 1894 4750 
Q 2613 4750 3031 4423 
Q 3450 4097 3450 3541 
Q 3450 3153 3228 2886 
Q 3006 2619 2597 2516 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-17" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-16" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_18">
    <!-- 0.42s -->
    <g transform="translate(299.960273 237.419076) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-17" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-15" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_19">
    <!-- 0.34s -->
    <g transform="translate(484.674272 250.22534) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-16" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-17" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_20">
    <!-- 0.77s -->
    <g transform="translate(148.494794 174.426863) rotate(-45) scale(0.07 -0.07)">
     <defs>
      <path id="DejaVuSans-1a" d="M 525 4666 
L 3525 4666 
L 3525 4397 
L 1831 0 
L 1172 0 
L 2766 4134 
L 525 4134 
L 525 4666 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-1a" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-1a" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_21">
    <!-- 0.76s -->
    <g transform="translate(333.208793 177.292358) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-1a" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-19" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_22">
    <!-- 0.79s -->
    <g transform="translate(517.922792 171.838194) rotate(-45) scale(0.07 -0.07)">
     <defs>
      <path id="DejaVuSans-1c" d="M 703 97 
L 703 672 
Q 941 559 1184 500 
Q 1428 441 1663 441 
Q 2288 441 2617 861 
Q 2947 1281 2994 2138 
Q 2813 1869 2534 1725 
Q 2256 1581 1919 1581 
Q 1219 1581 811 2004 
Q 403 2428 403 3163 
Q 403 3881 828 4315 
Q 1253 4750 1959 4750 
Q 2769 4750 3195 4129 
Q 3622 3509 3622 2328 
Q 3622 1225 3098 567 
Q 2575 -91 1691 -91 
Q 1453 -91 1209 -44 
Q 966 3 703 97 
z
M 1959 2075 
Q 2384 2075 2632 2365 
Q 2881 2656 2881 3163 
Q 2881 3666 2632 3958 
Q 2384 4250 1959 4250 
Q 1534 4250 1286 3958 
Q 1038 3666 1038 3163 
Q 1038 2656 1286 2365 
Q 1534 2075 1959 2075 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-1a" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-1c" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_23">
    <!-- 0.18s -->
    <g transform="translate(181.743314 279.660569) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-14" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-1b" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_24">
    <!-- 0.15s -->
    <g transform="translate(366.457313 284.833996) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-14" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-18" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_25">
    <!-- 0.14s -->
    <g transform="translate(551.171312 286.679702) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-14" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-17" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_26">
    <!-- 0.17s -->
    <g transform="translate(214.991834 280.878443) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-14" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-1a" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_27">
    <!-- 0.056s -->
    <g transform="translate(398.131194 300.799495) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-13" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-18" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-19" transform="translate(222.65625 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(286.28125 0)"/>
    </g>
   </g>
   <g id="text_28">
    <!-- 0.33s -->
    <g transform="translate(584.419831 251.809388) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-16" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-16" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_29">
    <!-- Query times by engine — all on S3 -->
    <g transform="translate(222.680859 16.318125) scale(0.12 -0.12)">
     <defs>
      <path id="DejaVuSans-Bold-34" d="M 2847 -84 
L 2753 -84 
Q 1600 -84 959 553 
Q 319 1191 319 2328 
Q 319 3463 958 4106 
Q 1597 4750 2719 4750 
Q 3853 4750 4486 4112 
Q 5119 3475 5119 2328 
Q 5119 1541 4783 972 
Q 4447 403 3816 116 
L 4756 -934 
L 3609 -934 
L 2847 -84 
z
M 2719 3878 
Q 2169 3878 1866 3472 
Q 1563 3066 1563 2328 
Q 1563 1578 1859 1179 
Q 2156 781 2719 781 
Q 3272 781 3575 1187 
Q 3878 1594 3878 2328 
Q 3878 3066 3575 3472 
Q 3272 3878 2719 3878 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-58" d="M 500 1363 
L 500 3500 
L 1625 3500 
L 1625 3150 
Q 1625 2866 1622 2436 
Q 1619 2006 1619 1863 
Q 1619 1441 1641 1255 
Q 1663 1069 1716 984 
Q 1784 875 1895 815 
Q 2006 756 2150 756 
Q 2500 756 2700 1025 
Q 2900 1294 2900 1772 
L 2900 3500 
L 4019 3500 
L 4019 0 
L 2900 0 
L 2900 506 
Q 2647 200 2364 54 
Q 2081 -91 1741 -91 
Q 1134 -91 817 281 
Q 500 653 500 1363 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-48" d="M 4031 1759 
L 4031 1441 
L 1416 1441 
Q 1456 1047 1700 850 
Q 1944 653 2381 653 
Q 2734 653 3104 758 
Q 3475 863 3866 1075 
L 3866 213 
Q 3469 63 3072 -14 
Q 2675 -91 2278 -91 
Q 1328 -91 801 392 
Q 275 875 275 1747 
Q 275 2603 792 3093 
Q 1309 3584 2216 3584 
Q 3041 3584 3536 3087 
Q 4031 2591 4031 1759 
z
M 2881 2131 
Q 2881 2450 2695 2645 
Q 2509 2841 2209 2841 
Q 1884 2841 1681 2658 
Q 1478 2475 1428 2131 
L 2881 2131 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-55" d="M 3138 2547 
Q 2991 2616 2845 2648 
Q 2700 2681 2553 2681 
Q 2122 2681 1889 2404 
Q 1656 2128 1656 1613 
L 1656 0 
L 538 0 
L 538 3500 
L 1656 3500 
L 1656 2925 
Q 1872 3269 2151 3426 
Q 2431 3584 2822 3584 
Q 2878 3584 2943 3579 
Q 3009 3575 3134 3559 
L 3138 2547 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-5c" d="M 78 3500 
L 1197 3500 
L 2138 1125 
L 2938 3500 
L 4056 3500 
L 2584 -331 
Q 2363 -916 2067 -1148 
Q 1772 -1381 1288 -1381 
L 641 -1381 
L 641 -647 
L 991 -647 
Q 1275 -647 1404 -556 
Q 1534 -466 1606 -231 
L 1638 -134 
L 78 3500 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-3" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-57" d="M 1759 4494 
L 1759 3500 
L 2913 3500 
L 2913 2700 
L 1759 2700 
L 1759 1216 
Q 1759 972 1856 886 
Q 1953 800 2241 800 
L 2816 800 
L 2816 0 
L 1856 0 
Q 1194 0 917 276 
Q 641 553 641 1216 
L 641 2700 
L 84 2700 
L 84 3500 
L 641 3500 
L 641 4494 
L 1759 4494 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-4c" d="M 538 3500 
L 1656 3500 
L 1656 0 
L 538 0 
L 538 3500 
z
M 538 4863 
L 1656 4863 
L 1656 3950 
L 538 3950 
L 538 4863 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-50" d="M 3781 2919 
Q 3994 3244 4286 3414 
Q 4578 3584 4928 3584 
Q 5531 3584 5847 3212 
Q 6163 2841 6163 2131 
L 6163 0 
L 5038 0 
L 5038 1825 
Q 5041 1866 5042 1909 
Q 5044 1953 5044 2034 
Q 5044 2406 4934 2573 
Q 4825 2741 4581 2741 
Q 4263 2741 4089 2478 
Q 3916 2216 3909 1719 
L 3909 0 
L 2784 0 
L 2784 1825 
Q 2784 2406 2684 2573 
Q 2584 2741 2328 2741 
Q 2006 2741 1831 2477 
Q 1656 2213 1656 1722 
L 1656 0 
L 531 0 
L 531 3500 
L 1656 3500 
L 1656 2988 
Q 1863 3284 2130 3434 
Q 2397 3584 2719 3584 
Q 3081 3584 3359 3409 
Q 3638 3234 3781 2919 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-56" d="M 3272 3391 
L 3272 2541 
Q 2913 2691 2578 2766 
Q 2244 2841 1947 2841 
Q 1628 2841 1473 2761 
Q 1319 2681 1319 2516 
Q 1319 2381 1436 2309 
Q 1553 2238 1856 2203 
L 2053 2175 
Q 2913 2066 3209 1816 
Q 3506 1566 3506 1031 
Q 3506 472 3093 190 
Q 2681 -91 1863 -91 
Q 1516 -91 1145 -36 
Q 775 19 384 128 
L 384 978 
Q 719 816 1070 734 
Q 1422 653 1784 653 
Q 2113 653 2278 743 
Q 2444 834 2444 1013 
Q 2444 1163 2330 1236 
Q 2216 1309 1875 1350 
L 1678 1375 
Q 931 1469 631 1722 
Q 331 1975 331 2491 
Q 331 3047 712 3315 
Q 1094 3584 1881 3584 
Q 2191 3584 2531 3537 
Q 2872 3491 3272 3391 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-45" d="M 2400 722 
Q 2759 722 2948 984 
Q 3138 1247 3138 1747 
Q 3138 2247 2948 2509 
Q 2759 2772 2400 2772 
Q 2041 2772 1848 2508 
Q 1656 2244 1656 1747 
Q 1656 1250 1848 986 
Q 2041 722 2400 722 
z
M 1656 2988 
Q 1888 3294 2169 3439 
Q 2450 3584 2816 3584 
Q 3463 3584 3878 3070 
Q 4294 2556 4294 1747 
Q 4294 938 3878 423 
Q 3463 -91 2816 -91 
Q 2450 -91 2169 54 
Q 1888 200 1656 506 
L 1656 0 
L 538 0 
L 538 4863 
L 1656 4863 
L 1656 2988 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-51" d="M 4056 2131 
L 4056 0 
L 2931 0 
L 2931 347 
L 2931 1631 
Q 2931 2084 2911 2256 
Q 2891 2428 2841 2509 
Q 2775 2619 2662 2680 
Q 2550 2741 2406 2741 
Q 2056 2741 1856 2470 
Q 1656 2200 1656 1722 
L 1656 0 
L 538 0 
L 538 3500 
L 1656 3500 
L 1656 2988 
Q 1909 3294 2193 3439 
Q 2478 3584 2822 3584 
Q 3428 3584 3742 3212 
Q 4056 2841 4056 2131 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-4a" d="M 2919 594 
Q 2688 288 2409 144 
Q 2131 0 1766 0 
Q 1125 0 706 504 
Q 288 1009 288 1791 
Q 288 2575 706 3076 
Q 1125 3578 1766 3578 
Q 2131 3578 2409 3434 
Q 2688 3291 2919 2981 
L 2919 3500 
L 4044 3500 
L 4044 353 
Q 4044 -491 3511 -936 
Q 2978 -1381 1966 -1381 
Q 1638 -1381 1331 -1331 
Q 1025 -1281 716 -1178 
L 716 -306 
Q 1009 -475 1290 -558 
Q 1572 -641 1856 -641 
Q 2406 -641 2662 -400 
Q 2919 -159 2919 353 
L 2919 594 
z
M 2181 2772 
Q 1834 2772 1640 2515 
Q 1447 2259 1447 1791 
Q 1447 1309 1634 1061 
Q 1822 813 2181 813 
Q 2531 813 2725 1069 
Q 2919 1325 2919 1791 
Q 2919 2259 2725 2515 
Q 2531 2772 2181 2772 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-af6" d="M 344 2156 
L 6056 2156 
L 6056 1350 
L 344 1350 
L 344 2156 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-44" d="M 2106 1575 
Q 1756 1575 1579 1456 
Q 1403 1338 1403 1106 
Q 1403 894 1545 773 
Q 1688 653 1941 653 
Q 2256 653 2472 879 
Q 2688 1106 2688 1447 
L 2688 1575 
L 2106 1575 
z
M 3816 1997 
L 3816 0 
L 2688 0 
L 2688 519 
Q 2463 200 2181 54 
Q 1900 -91 1497 -91 
Q 953 -91 614 226 
Q 275 544 275 1050 
Q 275 1666 698 1953 
Q 1122 2241 2028 2241 
L 2688 2241 
L 2688 2328 
Q 2688 2594 2478 2717 
Q 2269 2841 1825 2841 
Q 1466 2841 1156 2769 
Q 847 2697 581 2553 
L 581 3406 
Q 941 3494 1303 3539 
Q 1666 3584 2028 3584 
Q 2975 3584 3395 3211 
Q 3816 2838 3816 1997 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-4f" d="M 538 4863 
L 1656 4863 
L 1656 0 
L 538 0 
L 538 4863 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-52" d="M 2203 2784 
Q 1831 2784 1636 2517 
Q 1441 2250 1441 1747 
Q 1441 1244 1636 976 
Q 1831 709 2203 709 
Q 2569 709 2762 976 
Q 2956 1244 2956 1747 
Q 2956 2250 2762 2517 
Q 2569 2784 2203 2784 
z
M 2203 3584 
Q 3106 3584 3614 3096 
Q 4122 2609 4122 1747 
Q 4122 884 3614 396 
Q 3106 -91 2203 -91 
Q 1297 -91 786 396 
Q 275 884 275 1747 
Q 275 2609 786 3096 
Q 1297 3584 2203 3584 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-36" d="M 3834 4519 
L 3834 3531 
Q 3450 3703 3084 3790 
Q 2719 3878 2394 3878 
Q 1963 3878 1756 3759 
Q 1550 3641 1550 3391 
Q 1550 3203 1689 3098 
Q 1828 2994 2194 2919 
L 2706 2816 
Q 3484 2659 3812 2340 
Q 4141 2022 4141 1434 
Q 4141 663 3683 286 
Q 3225 -91 2284 -91 
Q 1841 -91 1394 -6 
Q 947 78 500 244 
L 500 1259 
Q 947 1022 1364 901 
Q 1781 781 2169 781 
Q 2563 781 2772 912 
Q 2981 1044 2981 1288 
Q 2981 1506 2839 1625 
Q 2697 1744 2272 1838 
L 1806 1941 
Q 1106 2091 782 2419 
Q 459 2747 459 3303 
Q 459 4000 909 4375 
Q 1359 4750 2203 4750 
Q 2588 4750 2994 4692 
Q 3400 4634 3834 4519 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-16" d="M 2981 2516 
Q 3453 2394 3698 2092 
Q 3944 1791 3944 1325 
Q 3944 631 3412 270 
Q 2881 -91 1863 -91 
Q 1503 -91 1142 -33 
Q 781 25 428 141 
L 428 1069 
Q 766 900 1098 814 
Q 1431 728 1753 728 
Q 2231 728 2486 893 
Q 2741 1059 2741 1369 
Q 2741 1688 2480 1852 
Q 2219 2016 1709 2016 
L 1228 2016 
L 1228 2791 
L 1734 2791 
Q 2188 2791 2409 2933 
Q 2631 3075 2631 3366 
Q 2631 3634 2415 3781 
Q 2200 3928 1806 3928 
Q 1516 3928 1219 3862 
Q 922 3797 628 3669 
L 628 4550 
Q 984 4650 1334 4700 
Q 1684 4750 2022 4750 
Q 2931 4750 3382 4451 
Q 3834 4153 3834 3553 
Q 3834 3144 3618 2883 
Q 3403 2622 2981 2516 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-Bold-34"/>
     <use xlink:href="#DejaVuSans-Bold-58" transform="translate(85.015625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(156.203125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-55" transform="translate(224.03125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-5c" transform="translate(273.34375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(338.53125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-57" transform="translate(373.34375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4c" transform="translate(421.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-50" transform="translate(455.421875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(559.625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(627.453125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(686.96875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-45" transform="translate(721.78125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-5c" transform="translate(793.359375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(858.546875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(893.359375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-51" transform="translate(961.1875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4a" transform="translate(1032.375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4c" transform="translate(1103.953125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-51" transform="translate(1138.234375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(1209.421875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(1277.25 0)"/>
     <use xlink:href="#DejaVuSans-Bold-af6" transform="translate(1312.0625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(1412.0625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-44" transform="translate(1446.875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4f" transform="translate(1514.359375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4f" transform="translate(1548.640625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(1582.921875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-52" transform="translate(1617.734375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-51" transform="translate(1686.4375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(1757.625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-36" transform="translate(1792.4375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-16" transform="translate(1864.453125 0)"/>
    </g>
   </g>
   <g id="legend_1">
    <g id="patch_20">
     <path d="M 528.867031 103.021641 
L 627.041562 103.021641 
Q 628.841562 103.021641 628.841562 101.221641 
L 628.841562 34.618125 
Q 628.841562 32.818125 627.041562 32.818125 
L 528.867031 32.818125 
Q 527.067031 32.818125 527.067031 34.618125 
L 527.067031 101.221641 
Q 527.067031 103.021641 528.867031 103.021641 
z
" style="fill: #ffffff; opacity: 0.9; stroke: #cccccc; stroke-linejoin: miter"/>
    </g>
    <g id="patch_21">
     <path d="M 530.667031 43.256719 
L 548.667031 43.256719 
L 548.667031 36.956719 
L 530.667031 36.956719 
z
" style="fill: #4c72b0; opacity: 0.85"/>
    </g>
    <g id="text_30">
     <!-- PyArrow -->
     <g transform="translate(555.867031 43.256719) scale(0.09 -0.09)">
      <defs>
       <path id="DejaVuSans-39" d="M 1831 0 
L 50 4666 
L 709 4666 
L 2188 738 
L 3669 4666 
L 4325 4666 
L 2547 0 
L 1831 0 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-24" d="M 2188 4044 
L 1331 1722 
L 3047 1722 
L 2188 4044 
z
M 1831 4666 
L 2547 4666 
L 4325 0 
L 3669 0 
L 3244 1197 
L 1141 1197 
L 716 0 
L 50 0 
L 1831 4666 
z
" transform="scale(0.015625)"/>
      </defs>
      <use xlink:href="#DejaVuSans-39"/>
      <use xlink:href="#DejaVuSans-44" transform="translate(60.640625 0)"/>
      <use xlink:href="#DejaVuSans-51" transform="translate(121.921875 0)"/>
      <use xlink:href="#DejaVuSans-4c" transform="translate(185.296875 0)"/>
      <use xlink:href="#DejaVuSans-4f" transform="translate(213.078125 0)"/>
      <use xlink:href="#DejaVuSans-4f" transform="translate(240.859375 0)"/>
      <use xlink:href="#DejaVuSans-44" transform="translate(268.640625 0)"/>
      <use xlink:href="#DejaVuSans-3" transform="translate(329.921875 0)"/>
      <use xlink:href="#DejaVuSans-33" transform="translate(361.703125 0)"/>
      <use xlink:href="#DejaVuSans-5c" transform="translate(422 0)"/>
      <use xlink:href="#DejaVuSans-24" transform="translate(481.1875 0)"/>
      <use xlink:href="#DejaVuSans-55" transform="translate(549.59375 0)"/>
      <use xlink:href="#DejaVuSans-55" transform="translate(588.953125 0)"/>
      <use xlink:href="#DejaVuSans-52" transform="translate(627.859375 0)"/>
      <use xlink:href="#DejaVuSans-5a" transform="translate(689.046875 0)"/>
     </g>
    </g>
    <g id="patch_22">
     <path d="M 530.667031 56.757422 
L 548.667031 56.757422 
L 548.667031 50.457422 
L 530.667031 50.457422 
z
" style="fill: #8b5cf6; opacity: 0.85"/>
    </g>
    <g id="text_31">
     <!-- Polars -->
     <g transform="translate(555.867031 56.757422) scale(0.09 -0.09)">
      <use xlink:href="#DejaVuSans-33"/>
      <use xlink:href="#DejaVuSans-52" transform="translate(56.734375 0)"/>
      <use xlink:href="#DejaVuSans-4f" transform="translate(117.921875 0)"/>
      <use xlink:href="#DejaVuSans-44" transform="translate(145.703125 0)"/>
      <use xlink:href="#DejaVuSans-55" transform="translate(206.984375 0)"/>
      <use xlink:href="#DejaVuSans-56" transform="translate(248.09375 0)"/>
     </g>
    </g>
    <g id="patch_23">
     <path d="M 530.667031 70.258125 
L 548.667031 70.258125 
L 548.667031 63.958125 
L 530.667031 63.958125 
z
" style="fill: #dd8452; opacity: 0.85"/>
    </g>
    <g id="text_32">
     <!-- DuckDB -->
     <g transform="translate(555.867031 70.258125) scale(0.09 -0.09)">
      <defs>
       <path id="DejaVuSans-27" d="M 1259 4147 
L 1259 519 
L 2022 519 
Q 2988 519 3436 956 
Q 3884 1394 3884 2338 
Q 3884 3275 3436 3711 
Q 2988 4147 2022 4147 
L 1259 4147 
z
M 628 4666 
L 1925 4666 
Q 3281 4666 3915 4102 
Q 4550 3538 4550 2338 
Q 4550 1131 3912 565 
Q 3275 0 1925 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-4e" d="M 581 4863 
L 1159 4863 
L 1159 1991 
L 2875 3500 
L 3609 3500 
L 1753 1863 
L 3688 0 
L 2938 0 
L 1159 1709 
L 1159 0 
L 581 0 
L 581 4863 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-25" d="M 1259 2228 
L 1259 519 
L 2272 519 
Q 2781 519 3026 730 
Q 3272 941 3272 1375 
Q 3272 1813 3026 2020 
Q 2781 2228 2272 2228 
L 1259 2228 
z
M 1259 4147 
L 1259 2741 
L 2194 2741 
Q 2656 2741 2882 2914 
Q 3109 3088 3109 3444 
Q 3109 3797 2882 3972 
Q 2656 4147 2194 4147 
L 1259 4147 
z
M 628 4666 
L 2241 4666 
Q 2963 4666 3353 4366 
Q 3744 4066 3744 3513 
Q 3744 3084 3544 2831 
Q 3344 2578 2956 2516 
Q 3422 2416 3680 2098 
Q 3938 1781 3938 1306 
Q 3938 681 3513 340 
Q 3088 0 2303 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
      </defs>
      <use xlink:href="#DejaVuSans-27"/>
      <use xlink:href="#DejaVuSans-58" transform="translate(77 0)"/>
      <use xlink:href="#DejaVuSans-46" transform="translate(140.375 0)"/>
      <use xlink:href="#DejaVuSans-4e" transform="translate(195.359375 0)"/>
      <use xlink:href="#DejaVuSans-27" transform="translate(253.265625 0)"/>
      <use xlink:href="#DejaVuSans-25" transform="translate(330.265625 0)"/>
     </g>
    </g>
    <g id="patch_24">
     <path d="M 530.667031 83.758828 
L 548.667031 83.758828 
L 548.667031 77.458828 
L 530.667031 77.458828 
z
" style="fill: #55a868; opacity: 0.85"/>
    </g>
    <g id="text_33">
     <!-- Iceberg -->
     <g transform="translate(555.867031 83.758828) scale(0.09 -0.09)">
      <defs>
       <path id="DejaVuSans-2c" d="M 628 4666 
L 1259 4666 
L 1259 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-45" d="M 3116 1747 
Q 3116 2381 2855 2742 
Q 2594 3103 2138 3103 
Q 1681 3103 1420 2742 
Q 1159 2381 1159 1747 
Q 1159 1113 1420 752 
Q 1681 391 2138 391 
Q 2594 391 2855 752 
Q 3116 1113 3116 1747 
z
M 1159 2969 
Q 1341 3281 1617 3432 
Q 1894 3584 2278 3584 
Q 2916 3584 3314 3078 
Q 3713 2572 3713 1747 
Q 3713 922 3314 415 
Q 2916 -91 2278 -91 
Q 1894 -91 1617 61 
Q 1341 213 1159 525 
L 1159 0 
L 581 0 
L 581 4863 
L 1159 4863 
L 1159 2969 
z
" transform="scale(0.015625)"/>
      </defs>
      <use xlink:href="#DejaVuSans-2c"/>
      <use xlink:href="#DejaVuSans-46" transform="translate(29.5 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(84.484375 0)"/>
      <use xlink:href="#DejaVuSans-45" transform="translate(146.015625 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(209.5 0)"/>
      <use xlink:href="#DejaVuSans-55" transform="translate(271.03125 0)"/>
      <use xlink:href="#DejaVuSans-4a" transform="translate(310.390625 0)"/>
     </g>
    </g>
    <g id="patch_25">
     <path d="M 530.667031 97.259531 
L 548.667031 97.259531 
L 548.667031 90.959531 
L 530.667031 90.959531 
z
" style="fill: #c44e52; opacity: 0.85"/>
    </g>
    <g id="text_34">
     <!-- LanceDB -->
     <g transform="translate(555.867031 97.259531) scale(0.09 -0.09)">
      <defs>
       <path id="DejaVuSans-2f" d="M 628 4666 
L 1259 4666 
L 1259 531 
L 3531 531 
L 3531 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
      </defs>
      <use xlink:href="#DejaVuSans-2f"/>
      <use xlink:href="#DejaVuSans-44" transform="translate(55.71875 0)"/>
      <use xlink:href="#DejaVuSans-51" transform="translate(117 0)"/>
      <use xlink:href="#DejaVuSans-46" transform="translate(180.375 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(235.359375 0)"/>
      <use xlink:href="#DejaVuSans-27" transform="translate(296.890625 0)"/>
      <use xlink:href="#DejaVuSans-25" transform="translate(373.890625 0)"/>
     </g>
    </g>
   </g>
  </g>
 </g>
 <defs>
  <clipPath id="pff3e02fd7d">
   <rect x="44.103906" y="28.318125" width="589.237656" height="285.391406"/>
  </clipPath>
 </defs>
</svg>

### Notes on query timing

**Polars vs. PyArrow.** Polars is ~4× faster than PyArrow across all three queries in store mode. Both engines run equivalent pandas aggregations after materialisation; the timing difference is attributable to the S3 read step. Polars reads the six shards concurrently; PyArrow's dataset API reads them more sequentially. In memory mode (data materialised once and held in RAM), the difference between the two engines is negligible. These results are single-run measurements; the magnitude of the difference may vary with shard count and network conditions.

**Iceberg and LanceDB post-ingest query times.** The low query times for Iceberg (0.15–0.19s) and LanceDB (0.06–0.33s) reflect reads from their own pre-ingested S3 stores, not from the source Parquet files. Their per-query times exclude the one-time setup cost of 8.7s and 7.6s respectively. When amortised across ten queries, the total cost per query for Iceberg is approximately 1.1s and for LanceDB approximately 1.1s — comparable to PyArrow and DuckDB.

---

## Writes

Three write operations were tested: appending a new sample (1,536 rows), adding a `QC_PASS` boolean column, and querying a historical state.

### Append

::::::{tab-set}
:::::{tab-item} PyArrow
The append saves a new artifact to LaminDB with schema validation and creates a new versioned collection. The operation includes an S3 upload, metadata registration, and lineage recording.

```python
new_art = ln.Artifact.from_dataframe(
    new_sample_df,
    key=f"lakehouse-benchmarks/append_batch_{ln.context.run.uid}.parquet",
    description="benchmark append batch (new sample)",
).save()

new_collection = ln.Collection(
    [*original_arts, new_art],
    key=collection.key, revises=collection,
).save()
```
:::::

:::::{tab-item} Polars
Identical to PyArrow — the append uses LaminDB's artifact and collection APIs regardless of which query engine opened the data.

```python
new_art = ln.Artifact.from_dataframe(
    new_sample_df,
    key=f"lakehouse-benchmarks/append_batch_{ln.context.run.uid}.parquet",
    description="benchmark append batch (new sample)",
).save()

new_collection = ln.Collection(
    [*original_arts, new_art],
    key=collection.key, revises=collection,
).save()
```
:::::

:::::{tab-item} DuckDB
The view is redefined to union in the new rows from an in-memory relation. No data is written to S3.

```python
con.register("append_batch", new_sample_arrow)
con.execute(
    f"CREATE OR REPLACE VIEW cnv_vcf AS "
    f"{base_select} UNION ALL SELECT * FROM append_batch"
)
```
:::::

:::::{tab-item} Iceberg
The append is atomic and snapshot-isolated. New Parquet files and a snapshot manifest are written to S3; concurrent readers see a consistent state throughout.

```python
table.append(new_sample_arrow)
```
:::::

:::::{tab-item} LanceDB
`add()` writes new rows to S3 and automatically increments the table version.

```python
table.add(new_sample_arrow)
# table.version == 2, table.count_rows() == 10,465
```
:::::
::::::

### Schema change

::::::{tab-set}
:::::{tab-item} PyArrow
A `QC_PASS` feature is registered in the LaminDB schema registry. All future artifacts saved against this schema — across the entire instance — are validated to include this feature.

```python
schema = ln.Schema.get(name="1000 Genomes CNV VCF")
feat = ln.Feature(name="QC_PASS", dtype=bool).save()
schema.add_optional_features([feat])
```
:::::

:::::{tab-item} Polars
Identical to PyArrow.

```python
schema = ln.Schema.get(name="1000 Genomes CNV VCF")
feat = ln.Feature(name="QC_PASS", dtype=bool).save()
schema.add_optional_features([feat])
```
:::::

:::::{tab-item} DuckDB
The view is redefined to include a virtual `NULL` column. No data is written to S3; the change exists only in the current session.

```python
con.execute(
    f"CREATE OR REPLACE VIEW cnv_vcf AS "
    f"SELECT *, CAST(NULL AS BOOLEAN) AS QC_PASS FROM ({base_select}) t"
)
```
:::::

:::::{tab-item} Iceberg
A new metadata file is written to S3 recording the updated schema. Existing Parquet files are not modified; reads of old files return `null` for the new column.

```python
from pyiceberg.types import BooleanType
with table.update_schema() as update:
    update.add_column("QC_PASS", BooleanType())
```
:::::

:::::{tab-item} LanceDB
A new column is added via SQL expression. All existing rows receive `null` for the new column.

```python
table.add_columns({"QC_PASS": "CAST(NULL AS BOOLEAN)"})
```
:::::
::::::

### Time travel

::::::{tab-set}
:::::{tab-item} PyArrow
The pre-append collection version is addressable by UID. LaminDB retains all prior collection versions.

```python
original = ln.Collection.get("K6X8Ejk3fjgAZT6h0000")
rows_v1 = original.open().count_rows()   # 8,929
```
:::::

:::::{tab-item} Polars
Same as PyArrow — collection versioning via LaminDB.

```python
original = ln.Collection.get("K6X8Ejk3fjgAZT6h0000")
with original.open(engine="polars") as lazy_v1:
    rows_v1 = lazy_v1.select(pl.len()).collect().item()   # 8,929
```
:::::

:::::{tab-item} DuckDB
Not supported. DuckDB maintains no snapshot history; the view redefinition used for append is also session-scoped.

```python
# not available
```
:::::

:::::{tab-item} Iceberg
Any historical snapshot is queryable by snapshot ID. Snapshots are retained until explicitly expired.

```python
first_snapshot = table.history()[0].snapshot_id
historical = table.scan(snapshot_id=first_snapshot).to_arrow()
historical.num_rows   # 8,929
```
:::::

:::::{tab-item} LanceDB
A specific version is checked out by integer version number and restored with `checkout_latest()`.

```python
table.checkout(1)             # version 1 = pre-append state
table.count_rows()            # 8,929
table.checkout_latest()       # restore current version
```
:::::
::::::

<!-- PLOT: write_path.svg -->
<?xml version="1.0" encoding="utf-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns:xlink="http://www.w3.org/1999/xlink" width="640.541562pt" height="351.915pt" viewBox="0 0 640.541562 351.915" xmlns="http://www.w3.org/2000/svg" version="1.1">
 <metadata>
  <rdf:RDF xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:cc="http://creativecommons.org/ns#" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
   <cc:Work>
    <dc:type rdf:resource="http://purl.org/dc/dcmitype/StillImage"/>
    <dc:date>2026-06-25T14:37:51.116090</dc:date>
    <dc:format>image/svg+xml</dc:format>
    <dc:creator>
     <cc:Agent>
      <dc:title>Matplotlib v3.11.0, https://matplotlib.org/</dc:title>
     </cc:Agent>
    </dc:creator>
   </cc:Work>
  </rdf:RDF>
 </metadata>
 <defs>
  <style type="text/css">*{stroke-linejoin: round; stroke-linecap: butt}</style>
 </defs>
 <g id="figure_1">
  <g id="patch_1">
   <path d="M 0 351.915 
L 640.541562 351.915 
L 640.541562 0 
L 0 0 
z
" style="fill: #ffffff"/>
  </g>
  <g id="axes_1">
   <g id="patch_2">
    <path d="M 44.103906 313.709531 
L 633.341562 313.709531 
L 633.341562 28.318125 
L 44.103906 28.318125 
z
" style="fill: #ffffff"/>
   </g>
   <g id="patch_3">
    <path d="M 70.887436 313.709531 
L 104.135956 313.709531 
L 104.135956 41.908192 
L 70.887436 41.908192 
z
" clip-path="url(#p70d12b2a08)" style="fill: #4c72b0; opacity: 0.85"/>
   </g>
   <g id="patch_4">
    <path d="M 255.601435 313.709531 
L 288.849955 313.709531 
L 288.849955 77.93551 
L 255.601435 77.93551 
z
" clip-path="url(#p70d12b2a08)" style="fill: #4c72b0; opacity: 0.85"/>
   </g>
   <g id="patch_5">
    <path d="M 440.315434 313.709531 
L 473.563954 313.709531 
L 473.563954 313.709531 
L 440.315434 313.709531 
z
" clip-path="url(#p70d12b2a08)" style="fill: #4c72b0; opacity: 0.85"/>
   </g>
   <g id="patch_6">
    <path d="M 104.135956 313.709531 
L 137.384476 313.709531 
L 137.384476 46.676035 
L 104.135956 46.676035 
z
" clip-path="url(#p70d12b2a08)" style="fill: #8b5cf6; opacity: 0.85"/>
   </g>
   <g id="patch_7">
    <path d="M 288.849955 313.709531 
L 322.098474 313.709531 
L 322.098474 81.378514 
L 288.849955 81.378514 
z
" clip-path="url(#p70d12b2a08)" style="fill: #8b5cf6; opacity: 0.85"/>
   </g>
   <g id="patch_8">
    <path d="M 473.563954 313.709531 
L 506.812473 313.709531 
L 506.812473 313.709531 
L 473.563954 313.709531 
z
" clip-path="url(#p70d12b2a08)" style="fill: #8b5cf6; opacity: 0.85"/>
   </g>
   <g id="patch_9">
    <path d="M 137.384476 313.709531 
L 170.632995 313.709531 
L 170.632995 298.171821 
L 137.384476 298.171821 
z
" clip-path="url(#p70d12b2a08)" style="fill: #dd8452; opacity: 0.85"/>
   </g>
   <g id="patch_10">
    <path d="M 322.098474 313.709531 
L 355.346994 313.709531 
L 355.346994 297.698464 
L 322.098474 297.698464 
z
" clip-path="url(#p70d12b2a08)" style="fill: #dd8452; opacity: 0.85"/>
   </g>
   <g id="patch_11">
    <path d="M 506.812473 313.709531 
L 540.060993 313.709531 
L 540.060993 313.709531 
L 506.812473 313.709531 
z
" clip-path="url(#p70d12b2a08)" style="fill: #dd8452; opacity: 0.85"/>
   </g>
   <g id="patch_12">
    <path d="M 170.632995 313.709531 
L 203.881515 313.709531 
L 203.881515 258.165922 
L 170.632995 258.165922 
z
" clip-path="url(#p70d12b2a08)" style="fill: #55a868; opacity: 0.85"/>
   </g>
   <g id="patch_13">
    <path d="M 355.346994 313.709531 
L 388.595514 313.709531 
L 388.595514 293.318974 
L 355.346994 293.318974 
z
" clip-path="url(#p70d12b2a08)" style="fill: #55a868; opacity: 0.85"/>
   </g>
   <g id="patch_14">
    <path d="M 540.060993 313.709531 
L 573.309513 313.709531 
L 573.309513 304.591552 
L 540.060993 304.591552 
z
" clip-path="url(#p70d12b2a08)" style="fill: #55a868; opacity: 0.85"/>
   </g>
   <g id="patch_15">
    <path d="M 203.881515 313.709531 
L 237.130035 313.709531 
L 237.130035 306.791319 
L 203.881515 306.791319 
z
" clip-path="url(#p70d12b2a08)" style="fill: #c44e52; opacity: 0.85"/>
   </g>
   <g id="patch_16">
    <path d="M 388.595514 313.709531 
L 421.844034 313.709531 
L 421.844034 309.541612 
L 388.595514 309.541612 
z
" clip-path="url(#p70d12b2a08)" style="fill: #c44e52; opacity: 0.85"/>
   </g>
   <g id="patch_17">
    <path d="M 573.309513 313.709531 
L 606.558033 313.709531 
L 606.558033 307.33444 
L 573.309513 307.33444 
z
" clip-path="url(#p70d12b2a08)" style="fill: #c44e52; opacity: 0.85"/>
   </g>
   <g id="matplotlib.axis_1">
    <g id="xtick_1">
     <g id="line2d_1">
      <defs>
       <path id="md255e1ffff" d="M 0 0 
L 0 3.5 
" style="stroke: #000000; stroke-width: 0.8"/>
      </defs>
      <g>
       <use xlink:href="#md255e1ffff" x="154.008736" y="313.709531" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_1">
      <!-- Append -->
      <g transform="translate(134.820454 329.308945) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-24" d="M 2188 4044 
L 1331 1722 
L 3047 1722 
L 2188 4044 
z
M 1831 4666 
L 2547 4666 
L 4325 0 
L 3669 0 
L 3244 1197 
L 1141 1197 
L 716 0 
L 50 0 
L 1831 4666 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-53" d="M 1159 525 
L 1159 -1331 
L 581 -1331 
L 581 3500 
L 1159 3500 
L 1159 2969 
Q 1341 3281 1617 3432 
Q 1894 3584 2278 3584 
Q 2916 3584 3314 3078 
Q 3713 2572 3713 1747 
Q 3713 922 3314 415 
Q 2916 -91 2278 -91 
Q 1894 -91 1617 61 
Q 1341 213 1159 525 
z
M 3116 1747 
Q 3116 2381 2855 2742 
Q 2594 3103 2138 3103 
Q 1681 3103 1420 2742 
Q 1159 2381 1159 1747 
Q 1159 1113 1420 752 
Q 1681 391 2138 391 
Q 2594 391 2855 752 
Q 3116 1113 3116 1747 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-48" d="M 3597 1894 
L 3597 1613 
L 953 1613 
Q 991 1019 1311 708 
Q 1631 397 2203 397 
Q 2534 397 2845 478 
Q 3156 559 3463 722 
L 3463 178 
Q 3153 47 2828 -22 
Q 2503 -91 2169 -91 
Q 1331 -91 842 396 
Q 353 884 353 1716 
Q 353 2575 817 3079 
Q 1281 3584 2069 3584 
Q 2775 3584 3186 3129 
Q 3597 2675 3597 1894 
z
M 3022 2063 
Q 3016 2534 2758 2815 
Q 2500 3097 2075 3097 
Q 1594 3097 1305 2825 
Q 1016 2553 972 2059 
L 3022 2063 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-51" d="M 3513 2113 
L 3513 0 
L 2938 0 
L 2938 2094 
Q 2938 2591 2744 2837 
Q 2550 3084 2163 3084 
Q 1697 3084 1428 2787 
Q 1159 2491 1159 1978 
L 1159 0 
L 581 0 
L 581 3500 
L 1159 3500 
L 1159 2956 
Q 1366 3272 1645 3428 
Q 1925 3584 2291 3584 
Q 2894 3584 3203 3211 
Q 3513 2838 3513 2113 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-47" d="M 2906 2969 
L 2906 4863 
L 3481 4863 
L 3481 0 
L 2906 0 
L 2906 525 
Q 2725 213 2448 61 
Q 2172 -91 1784 -91 
Q 1150 -91 751 415 
Q 353 922 353 1747 
Q 353 2572 751 3078 
Q 1150 3584 1784 3584 
Q 2172 3584 2448 3432 
Q 2725 3281 2906 2969 
z
M 947 1747 
Q 947 1113 1208 752 
Q 1469 391 1925 391 
Q 2381 391 2643 752 
Q 2906 1113 2906 1747 
Q 2906 2381 2643 2742 
Q 2381 3103 1925 3103 
Q 1469 3103 1208 2742 
Q 947 2381 947 1747 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-24"/>
       <use xlink:href="#DejaVuSans-53" transform="translate(68.40625 0)"/>
       <use xlink:href="#DejaVuSans-53" transform="translate(131.890625 0)"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(195.375 0)"/>
       <use xlink:href="#DejaVuSans-51" transform="translate(256.90625 0)"/>
       <use xlink:href="#DejaVuSans-47" transform="translate(320.28125 0)"/>
      </g>
      <!-- new sample -->
      <g transform="translate(123.906392 341.31168) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-5a" d="M 269 3500 
L 844 3500 
L 1563 769 
L 2278 3500 
L 2956 3500 
L 3675 769 
L 4391 3500 
L 4966 3500 
L 4050 0 
L 3372 0 
L 2619 2869 
L 1863 0 
L 1184 0 
L 269 3500 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-3" transform="scale(0.015625)"/>
        <path id="DejaVuSans-56" d="M 2834 3397 
L 2834 2853 
Q 2591 2978 2328 3040 
Q 2066 3103 1784 3103 
Q 1356 3103 1142 2972 
Q 928 2841 928 2578 
Q 928 2378 1081 2264 
Q 1234 2150 1697 2047 
L 1894 2003 
Q 2506 1872 2764 1633 
Q 3022 1394 3022 966 
Q 3022 478 2636 193 
Q 2250 -91 1575 -91 
Q 1294 -91 989 -36 
Q 684 19 347 128 
L 347 722 
Q 666 556 975 473 
Q 1284 391 1588 391 
Q 1994 391 2212 530 
Q 2431 669 2431 922 
Q 2431 1156 2273 1281 
Q 2116 1406 1581 1522 
L 1381 1569 
Q 847 1681 609 1914 
Q 372 2147 372 2553 
Q 372 3047 722 3315 
Q 1072 3584 1716 3584 
Q 2034 3584 2315 3537 
Q 2597 3491 2834 3397 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-44" d="M 2194 1759 
Q 1497 1759 1228 1600 
Q 959 1441 959 1056 
Q 959 750 1161 570 
Q 1363 391 1709 391 
Q 2188 391 2477 730 
Q 2766 1069 2766 1631 
L 2766 1759 
L 2194 1759 
z
M 3341 1997 
L 3341 0 
L 2766 0 
L 2766 531 
Q 2569 213 2275 61 
Q 1981 -91 1556 -91 
Q 1019 -91 701 211 
Q 384 513 384 1019 
Q 384 1609 779 1909 
Q 1175 2209 1959 2209 
L 2766 2209 
L 2766 2266 
Q 2766 2663 2505 2880 
Q 2244 3097 1772 3097 
Q 1472 3097 1187 3025 
Q 903 2953 641 2809 
L 641 3341 
Q 956 3463 1253 3523 
Q 1550 3584 1831 3584 
Q 2591 3584 2966 3190 
Q 3341 2797 3341 1997 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-50" d="M 3328 2828 
Q 3544 3216 3844 3400 
Q 4144 3584 4550 3584 
Q 5097 3584 5394 3201 
Q 5691 2819 5691 2113 
L 5691 0 
L 5113 0 
L 5113 2094 
Q 5113 2597 4934 2840 
Q 4756 3084 4391 3084 
Q 3944 3084 3684 2787 
Q 3425 2491 3425 1978 
L 3425 0 
L 2847 0 
L 2847 2094 
Q 2847 2600 2669 2842 
Q 2491 3084 2119 3084 
Q 1678 3084 1418 2786 
Q 1159 2488 1159 1978 
L 1159 0 
L 581 0 
L 581 3500 
L 1159 3500 
L 1159 2956 
Q 1356 3278 1631 3431 
Q 1906 3584 2284 3584 
Q 2666 3584 2933 3390 
Q 3200 3197 3328 2828 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-4f" d="M 603 4863 
L 1178 4863 
L 1178 0 
L 603 0 
L 603 4863 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-51"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(63.375 0)"/>
       <use xlink:href="#DejaVuSans-5a" transform="translate(124.90625 0)"/>
       <use xlink:href="#DejaVuSans-3" transform="translate(206.6875 0)"/>
       <use xlink:href="#DejaVuSans-56" transform="translate(238.46875 0)"/>
       <use xlink:href="#DejaVuSans-44" transform="translate(290.5625 0)"/>
       <use xlink:href="#DejaVuSans-50" transform="translate(351.84375 0)"/>
       <use xlink:href="#DejaVuSans-53" transform="translate(449.25 0)"/>
       <use xlink:href="#DejaVuSans-4f" transform="translate(512.734375 0)"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(540.515625 0)"/>
      </g>
     </g>
    </g>
    <g id="xtick_2">
     <g id="line2d_2">
      <g>
       <use xlink:href="#md255e1ffff" x="338.722734" y="313.709531" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_2">
      <!-- Schema -->
      <g transform="translate(318.619609 329.308945) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-36" d="M 3425 4513 
L 3425 3897 
Q 3066 4069 2747 4153 
Q 2428 4238 2131 4238 
Q 1616 4238 1336 4038 
Q 1056 3838 1056 3469 
Q 1056 3159 1242 3001 
Q 1428 2844 1947 2747 
L 2328 2669 
Q 3034 2534 3370 2195 
Q 3706 1856 3706 1288 
Q 3706 609 3251 259 
Q 2797 -91 1919 -91 
Q 1588 -91 1214 -16 
Q 841 59 441 206 
L 441 856 
Q 825 641 1194 531 
Q 1563 422 1919 422 
Q 2459 422 2753 634 
Q 3047 847 3047 1241 
Q 3047 1584 2836 1778 
Q 2625 1972 2144 2069 
L 1759 2144 
Q 1053 2284 737 2584 
Q 422 2884 422 3419 
Q 422 4038 858 4394 
Q 1294 4750 2059 4750 
Q 2388 4750 2728 4690 
Q 3069 4631 3425 4513 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-46" d="M 3122 3366 
L 3122 2828 
Q 2878 2963 2633 3030 
Q 2388 3097 2138 3097 
Q 1578 3097 1268 2742 
Q 959 2388 959 1747 
Q 959 1106 1268 751 
Q 1578 397 2138 397 
Q 2388 397 2633 464 
Q 2878 531 3122 666 
L 3122 134 
Q 2881 22 2623 -34 
Q 2366 -91 2075 -91 
Q 1284 -91 818 406 
Q 353 903 353 1747 
Q 353 2603 823 3093 
Q 1294 3584 2113 3584 
Q 2378 3584 2631 3529 
Q 2884 3475 3122 3366 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-4b" d="M 3513 2113 
L 3513 0 
L 2938 0 
L 2938 2094 
Q 2938 2591 2744 2837 
Q 2550 3084 2163 3084 
Q 1697 3084 1428 2787 
Q 1159 2491 1159 1978 
L 1159 0 
L 581 0 
L 581 4863 
L 1159 4863 
L 1159 2956 
Q 1366 3272 1645 3428 
Q 1925 3584 2291 3584 
Q 2894 3584 3203 3211 
Q 3513 2838 3513 2113 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-36"/>
       <use xlink:href="#DejaVuSans-46" transform="translate(63.484375 0)"/>
       <use xlink:href="#DejaVuSans-4b" transform="translate(118.46875 0)"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(181.84375 0)"/>
       <use xlink:href="#DejaVuSans-50" transform="translate(243.375 0)"/>
       <use xlink:href="#DejaVuSans-44" transform="translate(340.78125 0)"/>
      </g>
      <!-- change -->
      <g transform="translate(320.321172 341.31168) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-4a" d="M 2906 1791 
Q 2906 2416 2648 2759 
Q 2391 3103 1925 3103 
Q 1463 3103 1205 2759 
Q 947 2416 947 1791 
Q 947 1169 1205 825 
Q 1463 481 1925 481 
Q 2391 481 2648 825 
Q 2906 1169 2906 1791 
z
M 3481 434 
Q 3481 -459 3084 -895 
Q 2688 -1331 1869 -1331 
Q 1566 -1331 1297 -1286 
Q 1028 -1241 775 -1147 
L 775 -588 
Q 1028 -725 1275 -790 
Q 1522 -856 1778 -856 
Q 2344 -856 2625 -561 
Q 2906 -266 2906 331 
L 2906 616 
Q 2728 306 2450 153 
Q 2172 0 1784 0 
Q 1141 0 747 490 
Q 353 981 353 1791 
Q 353 2603 747 3093 
Q 1141 3584 1784 3584 
Q 2172 3584 2450 3431 
Q 2728 3278 2906 2969 
L 2906 3500 
L 3481 3500 
L 3481 434 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-46"/>
       <use xlink:href="#DejaVuSans-4b" transform="translate(54.984375 0)"/>
       <use xlink:href="#DejaVuSans-44" transform="translate(118.359375 0)"/>
       <use xlink:href="#DejaVuSans-51" transform="translate(179.640625 0)"/>
       <use xlink:href="#DejaVuSans-4a" transform="translate(243.015625 0)"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(306.5 0)"/>
      </g>
     </g>
    </g>
    <g id="xtick_3">
     <g id="line2d_3">
      <g>
       <use xlink:href="#md255e1ffff" x="523.436733" y="313.709531" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_3">
      <!-- Time travel -->
      <g transform="translate(495.107046 328.307969) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-37" d="M -19 4666 
L 3928 4666 
L 3928 4134 
L 2272 4134 
L 2272 0 
L 1638 0 
L 1638 4134 
L -19 4134 
L -19 4666 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-4c" d="M 603 3500 
L 1178 3500 
L 1178 0 
L 603 0 
L 603 3500 
z
M 603 4863 
L 1178 4863 
L 1178 4134 
L 603 4134 
L 603 4863 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-57" d="M 1172 4494 
L 1172 3500 
L 2356 3500 
L 2356 3053 
L 1172 3053 
L 1172 1153 
Q 1172 725 1289 603 
Q 1406 481 1766 481 
L 2356 481 
L 2356 0 
L 1766 0 
Q 1100 0 847 248 
Q 594 497 594 1153 
L 594 3053 
L 172 3053 
L 172 3500 
L 594 3500 
L 594 4494 
L 1172 4494 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-55" d="M 2631 2963 
Q 2534 3019 2420 3045 
Q 2306 3072 2169 3072 
Q 1681 3072 1420 2755 
Q 1159 2438 1159 1844 
L 1159 0 
L 581 0 
L 581 3500 
L 1159 3500 
L 1159 2956 
Q 1341 3275 1631 3429 
Q 1922 3584 2338 3584 
Q 2397 3584 2469 3576 
Q 2541 3569 2628 3553 
L 2631 2963 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-59" d="M 191 3500 
L 800 3500 
L 1894 563 
L 2988 3500 
L 3597 3500 
L 2284 0 
L 1503 0 
L 191 3500 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-37"/>
       <use xlink:href="#DejaVuSans-4c" transform="translate(58 0)"/>
       <use xlink:href="#DejaVuSans-50" transform="translate(85.78125 0)"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(183.1875 0)"/>
       <use xlink:href="#DejaVuSans-3" transform="translate(244.71875 0)"/>
       <use xlink:href="#DejaVuSans-57" transform="translate(276.5 0)"/>
       <use xlink:href="#DejaVuSans-55" transform="translate(315.703125 0)"/>
       <use xlink:href="#DejaVuSans-44" transform="translate(356.8125 0)"/>
       <use xlink:href="#DejaVuSans-59" transform="translate(418.09375 0)"/>
       <use xlink:href="#DejaVuSans-48" transform="translate(477.28125 0)"/>
       <use xlink:href="#DejaVuSans-4f" transform="translate(538.8125 0)"/>
      </g>
     </g>
    </g>
   </g>
   <g id="matplotlib.axis_2">
    <g id="ytick_1">
     <g id="line2d_4">
      <defs>
       <path id="m7ab9843f37" d="M 0 0 
L -3.5 0 
" style="stroke: #000000; stroke-width: 0.8"/>
      </defs>
      <g>
       <use xlink:href="#m7ab9843f37" x="44.103906" y="313.709531" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_4">
      <!-- 0.0 -->
      <g transform="translate(21.200781 317.508359) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-13" d="M 2034 4250 
Q 1547 4250 1301 3770 
Q 1056 3291 1056 2328 
Q 1056 1369 1301 889 
Q 1547 409 2034 409 
Q 2525 409 2770 889 
Q 3016 1369 3016 2328 
Q 3016 3291 2770 3770 
Q 2525 4250 2034 4250 
z
M 2034 4750 
Q 2819 4750 3233 4129 
Q 3647 3509 3647 2328 
Q 3647 1150 3233 529 
Q 2819 -91 2034 -91 
Q 1250 -91 836 529 
Q 422 1150 422 2328 
Q 422 3509 836 4129 
Q 1250 4750 2034 4750 
z
" transform="scale(0.015625)"/>
        <path id="DejaVuSans-11" d="M 684 794 
L 1344 794 
L 1344 0 
L 684 0 
L 684 794 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-13"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-13" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_2">
     <g id="line2d_5">
      <g>
       <use xlink:href="#m7ab9843f37" x="44.103906" y="281.206136" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_5">
      <!-- 0.5 -->
      <g transform="translate(21.200781 285.004964) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-18" d="M 691 4666 
L 3169 4666 
L 3169 4134 
L 1269 4134 
L 1269 2991 
Q 1406 3038 1543 3061 
Q 1681 3084 1819 3084 
Q 2600 3084 3056 2656 
Q 3513 2228 3513 1497 
Q 3513 744 3044 326 
Q 2575 -91 1722 -91 
Q 1428 -91 1123 -41 
Q 819 9 494 109 
L 494 744 
Q 775 591 1075 516 
Q 1375 441 1709 441 
Q 2250 441 2565 725 
Q 2881 1009 2881 1497 
Q 2881 1984 2565 2268 
Q 2250 2553 1709 2553 
Q 1456 2553 1204 2497 
Q 953 2441 691 2322 
L 691 4666 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-13"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-18" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_3">
     <g id="line2d_6">
      <g>
       <use xlink:href="#m7ab9843f37" x="44.103906" y="248.70274" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_6">
      <!-- 1.0 -->
      <g transform="translate(21.200781 252.501569) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-14" d="M 794 531 
L 1825 531 
L 1825 4091 
L 703 3866 
L 703 4441 
L 1819 4666 
L 2450 4666 
L 2450 531 
L 3481 531 
L 3481 0 
L 794 0 
L 794 531 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-14"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-13" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_4">
     <g id="line2d_7">
      <g>
       <use xlink:href="#m7ab9843f37" x="44.103906" y="216.199345" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_7">
      <!-- 1.5 -->
      <g transform="translate(21.200781 219.998173) scale(0.1 -0.1)">
       <use xlink:href="#DejaVuSans-14"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-18" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_5">
     <g id="line2d_8">
      <g>
       <use xlink:href="#m7ab9843f37" x="44.103906" y="183.69595" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_8">
      <!-- 2.0 -->
      <g transform="translate(21.200781 187.494778) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-15" d="M 1228 531 
L 3431 531 
L 3431 0 
L 469 0 
L 469 531 
Q 828 903 1448 1529 
Q 2069 2156 2228 2338 
Q 2531 2678 2651 2914 
Q 2772 3150 2772 3378 
Q 2772 3750 2511 3984 
Q 2250 4219 1831 4219 
Q 1534 4219 1204 4116 
Q 875 4013 500 3803 
L 500 4441 
Q 881 4594 1212 4672 
Q 1544 4750 1819 4750 
Q 2544 4750 2975 4387 
Q 3406 4025 3406 3419 
Q 3406 3131 3298 2873 
Q 3191 2616 2906 2266 
Q 2828 2175 2409 1742 
Q 1991 1309 1228 531 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-15"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-13" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_6">
     <g id="line2d_9">
      <g>
       <use xlink:href="#m7ab9843f37" x="44.103906" y="151.192554" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_9">
      <!-- 2.5 -->
      <g transform="translate(21.200781 154.991382) scale(0.1 -0.1)">
       <use xlink:href="#DejaVuSans-15"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-18" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_7">
     <g id="line2d_10">
      <g>
       <use xlink:href="#m7ab9843f37" x="44.103906" y="118.689159" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_10">
      <!-- 3.0 -->
      <g transform="translate(21.200781 122.487987) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-16" d="M 2597 2516 
Q 3050 2419 3304 2112 
Q 3559 1806 3559 1356 
Q 3559 666 3084 287 
Q 2609 -91 1734 -91 
Q 1441 -91 1130 -33 
Q 819 25 488 141 
L 488 750 
Q 750 597 1062 519 
Q 1375 441 1716 441 
Q 2309 441 2620 675 
Q 2931 909 2931 1356 
Q 2931 1769 2642 2001 
Q 2353 2234 1838 2234 
L 1294 2234 
L 1294 2753 
L 1863 2753 
Q 2328 2753 2575 2939 
Q 2822 3125 2822 3475 
Q 2822 3834 2567 4026 
Q 2313 4219 1838 4219 
Q 1578 4219 1281 4162 
Q 984 4106 628 3988 
L 628 4550 
Q 988 4650 1302 4700 
Q 1616 4750 1894 4750 
Q 2613 4750 3031 4423 
Q 3450 4097 3450 3541 
Q 3450 3153 3228 2886 
Q 3006 2619 2597 2516 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-16"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-13" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_8">
     <g id="line2d_11">
      <g>
       <use xlink:href="#m7ab9843f37" x="44.103906" y="86.185763" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_11">
      <!-- 3.5 -->
      <g transform="translate(21.200781 89.984591) scale(0.1 -0.1)">
       <use xlink:href="#DejaVuSans-16"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-18" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="ytick_9">
     <g id="line2d_12">
      <g>
       <use xlink:href="#m7ab9843f37" x="44.103906" y="53.682368" style="stroke: #000000; stroke-width: 0.8"/>
      </g>
     </g>
     <g id="text_12">
      <!-- 4.0 -->
      <g transform="translate(21.200781 57.481196) scale(0.1 -0.1)">
       <defs>
        <path id="DejaVuSans-17" d="M 2419 4116 
L 825 1625 
L 2419 1625 
L 2419 4116 
z
M 2253 4666 
L 3047 4666 
L 3047 1625 
L 3713 1625 
L 3713 1100 
L 3047 1100 
L 3047 0 
L 2419 0 
L 2419 1100 
L 313 1100 
L 313 1709 
L 2253 4666 
z
" transform="scale(0.015625)"/>
       </defs>
       <use xlink:href="#DejaVuSans-17"/>
       <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
       <use xlink:href="#DejaVuSans-13" transform="translate(95.40625 0)"/>
      </g>
     </g>
    </g>
    <g id="text_13">
     <!-- Time (seconds) -->
     <g transform="translate(14.798438 209.177891) rotate(-90) scale(0.1 -0.1)">
      <defs>
       <path id="DejaVuSans-b" d="M 1984 4856 
Q 1566 4138 1362 3434 
Q 1159 2731 1159 2009 
Q 1159 1288 1364 580 
Q 1569 -128 1984 -844 
L 1484 -844 
Q 1016 -109 783 600 
Q 550 1309 550 2009 
Q 550 2706 781 3412 
Q 1013 4119 1484 4856 
L 1984 4856 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-52" d="M 1959 3097 
Q 1497 3097 1228 2736 
Q 959 2375 959 1747 
Q 959 1119 1226 758 
Q 1494 397 1959 397 
Q 2419 397 2687 759 
Q 2956 1122 2956 1747 
Q 2956 2369 2687 2733 
Q 2419 3097 1959 3097 
z
M 1959 3584 
Q 2709 3584 3137 3096 
Q 3566 2609 3566 1747 
Q 3566 888 3137 398 
Q 2709 -91 1959 -91 
Q 1206 -91 779 398 
Q 353 888 353 1747 
Q 353 2609 779 3096 
Q 1206 3584 1959 3584 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-c" d="M 513 4856 
L 1013 4856 
Q 1481 4119 1714 3412 
Q 1947 2706 1947 2009 
Q 1947 1309 1714 600 
Q 1481 -109 1013 -844 
L 513 -844 
Q 928 -128 1133 580 
Q 1338 1288 1338 2009 
Q 1338 2731 1133 3434 
Q 928 4138 513 4856 
z
" transform="scale(0.015625)"/>
      </defs>
      <use xlink:href="#DejaVuSans-37"/>
      <use xlink:href="#DejaVuSans-4c" transform="translate(58 0)"/>
      <use xlink:href="#DejaVuSans-50" transform="translate(85.78125 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(183.1875 0)"/>
      <use xlink:href="#DejaVuSans-3" transform="translate(244.71875 0)"/>
      <use xlink:href="#DejaVuSans-b" transform="translate(276.5 0)"/>
      <use xlink:href="#DejaVuSans-56" transform="translate(315.515625 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(367.609375 0)"/>
      <use xlink:href="#DejaVuSans-46" transform="translate(429.140625 0)"/>
      <use xlink:href="#DejaVuSans-52" transform="translate(484.125 0)"/>
      <use xlink:href="#DejaVuSans-51" transform="translate(545.3125 0)"/>
      <use xlink:href="#DejaVuSans-47" transform="translate(608.6875 0)"/>
      <use xlink:href="#DejaVuSans-56" transform="translate(672.171875 0)"/>
      <use xlink:href="#DejaVuSans-c" transform="translate(724.265625 0)"/>
     </g>
    </g>
   </g>
   <g id="patch_18">
    <path d="M 44.103906 313.709531 
L 44.103906 28.318125 
" style="fill: none; stroke: #000000; stroke-width: 0.8; stroke-linejoin: miter; stroke-linecap: square"/>
   </g>
   <g id="patch_19">
    <path d="M 44.103906 313.709531 
L 633.341562 313.709531 
" style="fill: none; stroke: #000000; stroke-width: 0.8; stroke-linejoin: miter; stroke-linecap: square"/>
   </g>
   <g id="text_14">
    <!-- 4.18s -->
    <g transform="translate(81.997755 39.418957) rotate(-45) scale(0.07 -0.07)">
     <defs>
      <path id="DejaVuSans-1b" d="M 2034 2216 
Q 1584 2216 1326 1975 
Q 1069 1734 1069 1313 
Q 1069 891 1326 650 
Q 1584 409 2034 409 
Q 2484 409 2743 651 
Q 3003 894 3003 1313 
Q 3003 1734 2745 1975 
Q 2488 2216 2034 2216 
z
M 1403 2484 
Q 997 2584 770 2862 
Q 544 3141 544 3541 
Q 544 4100 942 4425 
Q 1341 4750 2034 4750 
Q 2731 4750 3128 4425 
Q 3525 4100 3525 3541 
Q 3525 3141 3298 2862 
Q 3072 2584 2669 2484 
Q 3125 2378 3379 2068 
Q 3634 1759 3634 1313 
Q 3634 634 3220 271 
Q 2806 -91 2034 -91 
Q 1263 -91 848 271 
Q 434 634 434 1313 
Q 434 1759 690 2068 
Q 947 2378 1403 2484 
z
M 1172 3481 
Q 1172 3119 1398 2916 
Q 1625 2713 2034 2713 
Q 2441 2713 2670 2916 
Q 2900 3119 2900 3481 
Q 2900 3844 2670 4047 
Q 2441 4250 2034 4250 
Q 1625 4250 1398 4047 
Q 1172 3844 1172 3481 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-17"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-14" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-1b" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_15">
    <!-- 3.63s -->
    <g transform="translate(266.711753 75.446275) rotate(-45) scale(0.07 -0.07)">
     <defs>
      <path id="DejaVuSans-19" d="M 2113 2584 
Q 1688 2584 1439 2293 
Q 1191 2003 1191 1497 
Q 1191 994 1439 701 
Q 1688 409 2113 409 
Q 2538 409 2786 701 
Q 3034 994 3034 1497 
Q 3034 2003 2786 2293 
Q 2538 2584 2113 2584 
z
M 3366 4563 
L 3366 3988 
Q 3128 4100 2886 4159 
Q 2644 4219 2406 4219 
Q 1781 4219 1451 3797 
Q 1122 3375 1075 2522 
Q 1259 2794 1537 2939 
Q 1816 3084 2150 3084 
Q 2853 3084 3261 2657 
Q 3669 2231 3669 1497 
Q 3669 778 3244 343 
Q 2819 -91 2113 -91 
Q 1303 -91 875 529 
Q 447 1150 447 2328 
Q 447 3434 972 4092 
Q 1497 4750 2381 4750 
Q 2619 4750 2861 4703 
Q 3103 4656 3366 4563 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-16"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-19" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-16" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_16">
    <!-- N/A -->
    <g style="fill: #aaaaaa" transform="translate(458.758053 312.409395) rotate(-90) scale(0.07 -0.07)">
     <defs>
      <path id="DejaVuSans-31" d="M 628 4666 
L 1478 4666 
L 3547 763 
L 3547 4666 
L 4159 4666 
L 4159 0 
L 3309 0 
L 1241 3903 
L 1241 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-12" d="M 1625 4666 
L 2156 4666 
L 531 -594 
L 0 -594 
L 1625 4666 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-31"/>
     <use xlink:href="#DejaVuSans-12" transform="translate(74.8125 0)"/>
     <use xlink:href="#DejaVuSans-24" transform="translate(108.5 0)"/>
    </g>
   </g>
   <g id="text_17">
    <!-- 4.11s -->
    <g transform="translate(115.246274 44.186799) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-17"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-14" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-14" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_18">
    <!-- 3.57s -->
    <g transform="translate(299.960273 78.889278) rotate(-45) scale(0.07 -0.07)">
     <defs>
      <path id="DejaVuSans-1a" d="M 525 4666 
L 3525 4666 
L 3525 4397 
L 1831 0 
L 1172 0 
L 2766 4134 
L 525 4134 
L 525 4666 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-16"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-18" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-1a" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_19">
    <!-- N/A -->
    <g style="fill: #aaaaaa" transform="translate(492.006573 312.409395) rotate(-90) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-31"/>
     <use xlink:href="#DejaVuSans-12" transform="translate(74.8125 0)"/>
     <use xlink:href="#DejaVuSans-24" transform="translate(108.5 0)"/>
    </g>
   </g>
   <g id="text_20">
    <!-- 0.24s -->
    <g transform="translate(148.494794 295.682586) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-15" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-17" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_21">
    <!-- 0.25s -->
    <g transform="translate(333.208793 295.209229) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-15" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-18" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_22">
    <!-- N/A -->
    <g style="fill: #aaaaaa" transform="translate(525.255093 312.409395) rotate(-90) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-31"/>
     <use xlink:href="#DejaVuSans-12" transform="translate(74.8125 0)"/>
     <use xlink:href="#DejaVuSans-24" transform="translate(108.5 0)"/>
    </g>
   </g>
   <g id="text_23">
    <!-- 0.85s -->
    <g transform="translate(181.743314 255.676687) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-1b" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-18" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_24">
    <!-- 0.31s -->
    <g transform="translate(366.457313 290.829738) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-16" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-14" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_25">
    <!-- 0.14s -->
    <g transform="translate(551.171312 302.102316) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-14" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-17" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_26">
    <!-- 0.11s -->
    <g transform="translate(214.991834 304.302083) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-14" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-14" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(222.65625 0)"/>
    </g>
   </g>
   <g id="text_27">
    <!-- 0.064s -->
    <g transform="translate(398.131194 307.052377) rotate(-45) scale(0.07 -0.07)">
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-13" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-19" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-17" transform="translate(222.65625 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(286.28125 0)"/>
    </g>
   </g>
   <g id="text_28">
    <!-- 0.098s -->
    <g transform="translate(582.845193 304.845205) rotate(-45) scale(0.07 -0.07)">
     <defs>
      <path id="DejaVuSans-1c" d="M 703 97 
L 703 672 
Q 941 559 1184 500 
Q 1428 441 1663 441 
Q 2288 441 2617 861 
Q 2947 1281 2994 2138 
Q 2813 1869 2534 1725 
Q 2256 1581 1919 1581 
Q 1219 1581 811 2004 
Q 403 2428 403 3163 
Q 403 3881 828 4315 
Q 1253 4750 1959 4750 
Q 2769 4750 3195 4129 
Q 3622 3509 3622 2328 
Q 3622 1225 3098 567 
Q 2575 -91 1691 -91 
Q 1453 -91 1209 -44 
Q 966 3 703 97 
z
M 1959 2075 
Q 2384 2075 2632 2365 
Q 2881 2656 2881 3163 
Q 2881 3666 2632 3958 
Q 2384 4250 1959 4250 
Q 1534 4250 1286 3958 
Q 1038 3666 1038 3163 
Q 1038 2656 1286 2365 
Q 1534 2075 1959 2075 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-13"/>
     <use xlink:href="#DejaVuSans-11" transform="translate(63.625 0)"/>
     <use xlink:href="#DejaVuSans-13" transform="translate(95.40625 0)"/>
     <use xlink:href="#DejaVuSans-1c" transform="translate(159.03125 0)"/>
     <use xlink:href="#DejaVuSans-1b" transform="translate(222.65625 0)"/>
     <use xlink:href="#DejaVuSans-56" transform="translate(286.28125 0)"/>
    </g>
   </g>
   <g id="text_29">
    <!-- Write-path times by engine — all on S3 -->
    <g transform="translate(206.553984 16.318125) scale(0.12 -0.12)">
     <defs>
      <path id="DejaVuSans-Bold-3a" d="M 191 4666 
L 1344 4666 
L 2150 1275 
L 2950 4666 
L 4109 4666 
L 4909 1275 
L 5716 4666 
L 6859 4666 
L 5759 0 
L 4372 0 
L 3525 3547 
L 2688 0 
L 1300 0 
L 191 4666 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-55" d="M 3138 2547 
Q 2991 2616 2845 2648 
Q 2700 2681 2553 2681 
Q 2122 2681 1889 2404 
Q 1656 2128 1656 1613 
L 1656 0 
L 538 0 
L 538 3500 
L 1656 3500 
L 1656 2925 
Q 1872 3269 2151 3426 
Q 2431 3584 2822 3584 
Q 2878 3584 2943 3579 
Q 3009 3575 3134 3559 
L 3138 2547 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-4c" d="M 538 3500 
L 1656 3500 
L 1656 0 
L 538 0 
L 538 3500 
z
M 538 4863 
L 1656 4863 
L 1656 3950 
L 538 3950 
L 538 4863 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-57" d="M 1759 4494 
L 1759 3500 
L 2913 3500 
L 2913 2700 
L 1759 2700 
L 1759 1216 
Q 1759 972 1856 886 
Q 1953 800 2241 800 
L 2816 800 
L 2816 0 
L 1856 0 
Q 1194 0 917 276 
Q 641 553 641 1216 
L 641 2700 
L 84 2700 
L 84 3500 
L 641 3500 
L 641 4494 
L 1759 4494 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-48" d="M 4031 1759 
L 4031 1441 
L 1416 1441 
Q 1456 1047 1700 850 
Q 1944 653 2381 653 
Q 2734 653 3104 758 
Q 3475 863 3866 1075 
L 3866 213 
Q 3469 63 3072 -14 
Q 2675 -91 2278 -91 
Q 1328 -91 801 392 
Q 275 875 275 1747 
Q 275 2603 792 3093 
Q 1309 3584 2216 3584 
Q 3041 3584 3536 3087 
Q 4031 2591 4031 1759 
z
M 2881 2131 
Q 2881 2450 2695 2645 
Q 2509 2841 2209 2841 
Q 1884 2841 1681 2658 
Q 1478 2475 1428 2131 
L 2881 2131 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-10" d="M 347 2297 
L 2309 2297 
L 2309 1388 
L 347 1388 
L 347 2297 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-53" d="M 1656 506 
L 1656 -1331 
L 538 -1331 
L 538 3500 
L 1656 3500 
L 1656 2988 
Q 1888 3294 2169 3439 
Q 2450 3584 2816 3584 
Q 3463 3584 3878 3070 
Q 4294 2556 4294 1747 
Q 4294 938 3878 423 
Q 3463 -91 2816 -91 
Q 2450 -91 2169 54 
Q 1888 200 1656 506 
z
M 2400 2772 
Q 2041 2772 1848 2508 
Q 1656 2244 1656 1747 
Q 1656 1250 1848 986 
Q 2041 722 2400 722 
Q 2759 722 2948 984 
Q 3138 1247 3138 1747 
Q 3138 2247 2948 2509 
Q 2759 2772 2400 2772 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-44" d="M 2106 1575 
Q 1756 1575 1579 1456 
Q 1403 1338 1403 1106 
Q 1403 894 1545 773 
Q 1688 653 1941 653 
Q 2256 653 2472 879 
Q 2688 1106 2688 1447 
L 2688 1575 
L 2106 1575 
z
M 3816 1997 
L 3816 0 
L 2688 0 
L 2688 519 
Q 2463 200 2181 54 
Q 1900 -91 1497 -91 
Q 953 -91 614 226 
Q 275 544 275 1050 
Q 275 1666 698 1953 
Q 1122 2241 2028 2241 
L 2688 2241 
L 2688 2328 
Q 2688 2594 2478 2717 
Q 2269 2841 1825 2841 
Q 1466 2841 1156 2769 
Q 847 2697 581 2553 
L 581 3406 
Q 941 3494 1303 3539 
Q 1666 3584 2028 3584 
Q 2975 3584 3395 3211 
Q 3816 2838 3816 1997 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-4b" d="M 4056 2131 
L 4056 0 
L 2931 0 
L 2931 347 
L 2931 1625 
Q 2931 2084 2911 2256 
Q 2891 2428 2841 2509 
Q 2775 2619 2662 2680 
Q 2550 2741 2406 2741 
Q 2056 2741 1856 2470 
Q 1656 2200 1656 1722 
L 1656 0 
L 538 0 
L 538 4863 
L 1656 4863 
L 1656 2988 
Q 1909 3294 2193 3439 
Q 2478 3584 2822 3584 
Q 3428 3584 3742 3212 
Q 4056 2841 4056 2131 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-3" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-50" d="M 3781 2919 
Q 3994 3244 4286 3414 
Q 4578 3584 4928 3584 
Q 5531 3584 5847 3212 
Q 6163 2841 6163 2131 
L 6163 0 
L 5038 0 
L 5038 1825 
Q 5041 1866 5042 1909 
Q 5044 1953 5044 2034 
Q 5044 2406 4934 2573 
Q 4825 2741 4581 2741 
Q 4263 2741 4089 2478 
Q 3916 2216 3909 1719 
L 3909 0 
L 2784 0 
L 2784 1825 
Q 2784 2406 2684 2573 
Q 2584 2741 2328 2741 
Q 2006 2741 1831 2477 
Q 1656 2213 1656 1722 
L 1656 0 
L 531 0 
L 531 3500 
L 1656 3500 
L 1656 2988 
Q 1863 3284 2130 3434 
Q 2397 3584 2719 3584 
Q 3081 3584 3359 3409 
Q 3638 3234 3781 2919 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-56" d="M 3272 3391 
L 3272 2541 
Q 2913 2691 2578 2766 
Q 2244 2841 1947 2841 
Q 1628 2841 1473 2761 
Q 1319 2681 1319 2516 
Q 1319 2381 1436 2309 
Q 1553 2238 1856 2203 
L 2053 2175 
Q 2913 2066 3209 1816 
Q 3506 1566 3506 1031 
Q 3506 472 3093 190 
Q 2681 -91 1863 -91 
Q 1516 -91 1145 -36 
Q 775 19 384 128 
L 384 978 
Q 719 816 1070 734 
Q 1422 653 1784 653 
Q 2113 653 2278 743 
Q 2444 834 2444 1013 
Q 2444 1163 2330 1236 
Q 2216 1309 1875 1350 
L 1678 1375 
Q 931 1469 631 1722 
Q 331 1975 331 2491 
Q 331 3047 712 3315 
Q 1094 3584 1881 3584 
Q 2191 3584 2531 3537 
Q 2872 3491 3272 3391 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-45" d="M 2400 722 
Q 2759 722 2948 984 
Q 3138 1247 3138 1747 
Q 3138 2247 2948 2509 
Q 2759 2772 2400 2772 
Q 2041 2772 1848 2508 
Q 1656 2244 1656 1747 
Q 1656 1250 1848 986 
Q 2041 722 2400 722 
z
M 1656 2988 
Q 1888 3294 2169 3439 
Q 2450 3584 2816 3584 
Q 3463 3584 3878 3070 
Q 4294 2556 4294 1747 
Q 4294 938 3878 423 
Q 3463 -91 2816 -91 
Q 2450 -91 2169 54 
Q 1888 200 1656 506 
L 1656 0 
L 538 0 
L 538 4863 
L 1656 4863 
L 1656 2988 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-5c" d="M 78 3500 
L 1197 3500 
L 2138 1125 
L 2938 3500 
L 4056 3500 
L 2584 -331 
Q 2363 -916 2067 -1148 
Q 1772 -1381 1288 -1381 
L 641 -1381 
L 641 -647 
L 991 -647 
Q 1275 -647 1404 -556 
Q 1534 -466 1606 -231 
L 1638 -134 
L 78 3500 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-51" d="M 4056 2131 
L 4056 0 
L 2931 0 
L 2931 347 
L 2931 1631 
Q 2931 2084 2911 2256 
Q 2891 2428 2841 2509 
Q 2775 2619 2662 2680 
Q 2550 2741 2406 2741 
Q 2056 2741 1856 2470 
Q 1656 2200 1656 1722 
L 1656 0 
L 538 0 
L 538 3500 
L 1656 3500 
L 1656 2988 
Q 1909 3294 2193 3439 
Q 2478 3584 2822 3584 
Q 3428 3584 3742 3212 
Q 4056 2841 4056 2131 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-4a" d="M 2919 594 
Q 2688 288 2409 144 
Q 2131 0 1766 0 
Q 1125 0 706 504 
Q 288 1009 288 1791 
Q 288 2575 706 3076 
Q 1125 3578 1766 3578 
Q 2131 3578 2409 3434 
Q 2688 3291 2919 2981 
L 2919 3500 
L 4044 3500 
L 4044 353 
Q 4044 -491 3511 -936 
Q 2978 -1381 1966 -1381 
Q 1638 -1381 1331 -1331 
Q 1025 -1281 716 -1178 
L 716 -306 
Q 1009 -475 1290 -558 
Q 1572 -641 1856 -641 
Q 2406 -641 2662 -400 
Q 2919 -159 2919 353 
L 2919 594 
z
M 2181 2772 
Q 1834 2772 1640 2515 
Q 1447 2259 1447 1791 
Q 1447 1309 1634 1061 
Q 1822 813 2181 813 
Q 2531 813 2725 1069 
Q 2919 1325 2919 1791 
Q 2919 2259 2725 2515 
Q 2531 2772 2181 2772 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-af6" d="M 344 2156 
L 6056 2156 
L 6056 1350 
L 344 1350 
L 344 2156 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-4f" d="M 538 4863 
L 1656 4863 
L 1656 0 
L 538 0 
L 538 4863 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-52" d="M 2203 2784 
Q 1831 2784 1636 2517 
Q 1441 2250 1441 1747 
Q 1441 1244 1636 976 
Q 1831 709 2203 709 
Q 2569 709 2762 976 
Q 2956 1244 2956 1747 
Q 2956 2250 2762 2517 
Q 2569 2784 2203 2784 
z
M 2203 3584 
Q 3106 3584 3614 3096 
Q 4122 2609 4122 1747 
Q 4122 884 3614 396 
Q 3106 -91 2203 -91 
Q 1297 -91 786 396 
Q 275 884 275 1747 
Q 275 2609 786 3096 
Q 1297 3584 2203 3584 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-36" d="M 3834 4519 
L 3834 3531 
Q 3450 3703 3084 3790 
Q 2719 3878 2394 3878 
Q 1963 3878 1756 3759 
Q 1550 3641 1550 3391 
Q 1550 3203 1689 3098 
Q 1828 2994 2194 2919 
L 2706 2816 
Q 3484 2659 3812 2340 
Q 4141 2022 4141 1434 
Q 4141 663 3683 286 
Q 3225 -91 2284 -91 
Q 1841 -91 1394 -6 
Q 947 78 500 244 
L 500 1259 
Q 947 1022 1364 901 
Q 1781 781 2169 781 
Q 2563 781 2772 912 
Q 2981 1044 2981 1288 
Q 2981 1506 2839 1625 
Q 2697 1744 2272 1838 
L 1806 1941 
Q 1106 2091 782 2419 
Q 459 2747 459 3303 
Q 459 4000 909 4375 
Q 1359 4750 2203 4750 
Q 2588 4750 2994 4692 
Q 3400 4634 3834 4519 
z
" transform="scale(0.015625)"/>
      <path id="DejaVuSans-Bold-16" d="M 2981 2516 
Q 3453 2394 3698 2092 
Q 3944 1791 3944 1325 
Q 3944 631 3412 270 
Q 2881 -91 1863 -91 
Q 1503 -91 1142 -33 
Q 781 25 428 141 
L 428 1069 
Q 766 900 1098 814 
Q 1431 728 1753 728 
Q 2231 728 2486 893 
Q 2741 1059 2741 1369 
Q 2741 1688 2480 1852 
Q 2219 2016 1709 2016 
L 1228 2016 
L 1228 2791 
L 1734 2791 
Q 2188 2791 2409 2933 
Q 2631 3075 2631 3366 
Q 2631 3634 2415 3781 
Q 2200 3928 1806 3928 
Q 1516 3928 1219 3862 
Q 922 3797 628 3669 
L 628 4550 
Q 984 4650 1334 4700 
Q 1684 4750 2022 4750 
Q 2931 4750 3382 4451 
Q 3834 4153 3834 3553 
Q 3834 3144 3618 2883 
Q 3403 2622 2981 2516 
z
" transform="scale(0.015625)"/>
     </defs>
     <use xlink:href="#DejaVuSans-Bold-3a"/>
     <use xlink:href="#DejaVuSans-Bold-55" transform="translate(108.546875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4c" transform="translate(157.859375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-57" transform="translate(192.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(239.9375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-10" transform="translate(307.765625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-53" transform="translate(349.265625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-44" transform="translate(420.84375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-57" transform="translate(488.328125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4b" transform="translate(536.125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(607.3125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-57" transform="translate(642.125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4c" transform="translate(689.921875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-50" transform="translate(724.203125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(828.40625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-56" transform="translate(896.234375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(955.75 0)"/>
     <use xlink:href="#DejaVuSans-Bold-45" transform="translate(990.5625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-5c" transform="translate(1062.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(1127.328125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(1162.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-51" transform="translate(1229.96875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4a" transform="translate(1301.15625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4c" transform="translate(1372.734375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-51" transform="translate(1407.015625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-48" transform="translate(1478.203125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(1546.03125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-af6" transform="translate(1580.84375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(1680.84375 0)"/>
     <use xlink:href="#DejaVuSans-Bold-44" transform="translate(1715.65625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4f" transform="translate(1783.140625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-4f" transform="translate(1817.421875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(1851.703125 0)"/>
     <use xlink:href="#DejaVuSans-Bold-52" transform="translate(1886.515625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-51" transform="translate(1955.21875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-3" transform="translate(2026.40625 0)"/>
     <use xlink:href="#DejaVuSans-Bold-36" transform="translate(2061.21875 0)"/>
     <use xlink:href="#DejaVuSans-Bold-16" transform="translate(2133.234375 0)"/>
    </g>
   </g>
   <g id="legend_1">
    <g id="patch_20">
     <path d="M 528.867031 103.021641 
L 627.041562 103.021641 
Q 628.841562 103.021641 628.841562 101.221641 
L 628.841562 34.618125 
Q 628.841562 32.818125 627.041562 32.818125 
L 528.867031 32.818125 
Q 527.067031 32.818125 527.067031 34.618125 
L 527.067031 101.221641 
Q 527.067031 103.021641 528.867031 103.021641 
z
" style="fill: #ffffff; opacity: 0.9; stroke: #cccccc; stroke-linejoin: miter"/>
    </g>
    <g id="patch_21">
     <path d="M 530.667031 43.256719 
L 548.667031 43.256719 
L 548.667031 36.956719 
L 530.667031 36.956719 
z
" style="fill: #4c72b0; opacity: 0.85"/>
    </g>
    <g id="text_30">
     <!-- PyArrow -->
     <g transform="translate(555.867031 43.256719) scale(0.09 -0.09)">
      <defs>
       <path id="DejaVuSans-39" d="M 1831 0 
L 50 4666 
L 709 4666 
L 2188 738 
L 3669 4666 
L 4325 4666 
L 2547 0 
L 1831 0 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-33" d="M 1259 4147 
L 1259 2394 
L 2053 2394 
Q 2494 2394 2734 2622 
Q 2975 2850 2975 3272 
Q 2975 3691 2734 3919 
Q 2494 4147 2053 4147 
L 1259 4147 
z
M 628 4666 
L 2053 4666 
Q 2838 4666 3239 4311 
Q 3641 3956 3641 3272 
Q 3641 2581 3239 2228 
Q 2838 1875 2053 1875 
L 1259 1875 
L 1259 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-5c" d="M 2059 -325 
Q 1816 -950 1584 -1140 
Q 1353 -1331 966 -1331 
L 506 -1331 
L 506 -850 
L 844 -850 
Q 1081 -850 1212 -737 
Q 1344 -625 1503 -206 
L 1606 56 
L 191 3500 
L 800 3500 
L 1894 763 
L 2988 3500 
L 3597 3500 
L 2059 -325 
z
" transform="scale(0.015625)"/>
      </defs>
      <use xlink:href="#DejaVuSans-39"/>
      <use xlink:href="#DejaVuSans-44" transform="translate(60.640625 0)"/>
      <use xlink:href="#DejaVuSans-51" transform="translate(121.921875 0)"/>
      <use xlink:href="#DejaVuSans-4c" transform="translate(185.296875 0)"/>
      <use xlink:href="#DejaVuSans-4f" transform="translate(213.078125 0)"/>
      <use xlink:href="#DejaVuSans-4f" transform="translate(240.859375 0)"/>
      <use xlink:href="#DejaVuSans-44" transform="translate(268.640625 0)"/>
      <use xlink:href="#DejaVuSans-3" transform="translate(329.921875 0)"/>
      <use xlink:href="#DejaVuSans-33" transform="translate(361.703125 0)"/>
      <use xlink:href="#DejaVuSans-5c" transform="translate(422 0)"/>
      <use xlink:href="#DejaVuSans-24" transform="translate(481.1875 0)"/>
      <use xlink:href="#DejaVuSans-55" transform="translate(549.59375 0)"/>
      <use xlink:href="#DejaVuSans-55" transform="translate(588.953125 0)"/>
      <use xlink:href="#DejaVuSans-52" transform="translate(627.859375 0)"/>
      <use xlink:href="#DejaVuSans-5a" transform="translate(689.046875 0)"/>
     </g>
    </g>
    <g id="patch_22">
     <path d="M 530.667031 56.757422 
L 548.667031 56.757422 
L 548.667031 50.457422 
L 530.667031 50.457422 
z
" style="fill: #8b5cf6; opacity: 0.85"/>
    </g>
    <g id="text_31">
     <!-- Polars -->
     <g transform="translate(555.867031 56.757422) scale(0.09 -0.09)">
      <use xlink:href="#DejaVuSans-33"/>
      <use xlink:href="#DejaVuSans-52" transform="translate(56.734375 0)"/>
      <use xlink:href="#DejaVuSans-4f" transform="translate(117.921875 0)"/>
      <use xlink:href="#DejaVuSans-44" transform="translate(145.703125 0)"/>
      <use xlink:href="#DejaVuSans-55" transform="translate(206.984375 0)"/>
      <use xlink:href="#DejaVuSans-56" transform="translate(248.09375 0)"/>
     </g>
    </g>
    <g id="patch_23">
     <path d="M 530.667031 70.258125 
L 548.667031 70.258125 
L 548.667031 63.958125 
L 530.667031 63.958125 
z
" style="fill: #dd8452; opacity: 0.85"/>
    </g>
    <g id="text_32">
     <!-- DuckDB -->
     <g transform="translate(555.867031 70.258125) scale(0.09 -0.09)">
      <defs>
       <path id="DejaVuSans-27" d="M 1259 4147 
L 1259 519 
L 2022 519 
Q 2988 519 3436 956 
Q 3884 1394 3884 2338 
Q 3884 3275 3436 3711 
Q 2988 4147 2022 4147 
L 1259 4147 
z
M 628 4666 
L 1925 4666 
Q 3281 4666 3915 4102 
Q 4550 3538 4550 2338 
Q 4550 1131 3912 565 
Q 3275 0 1925 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-58" d="M 544 1381 
L 544 3500 
L 1119 3500 
L 1119 1403 
Q 1119 906 1312 657 
Q 1506 409 1894 409 
Q 2359 409 2629 706 
Q 2900 1003 2900 1516 
L 2900 3500 
L 3475 3500 
L 3475 0 
L 2900 0 
L 2900 538 
Q 2691 219 2414 64 
Q 2138 -91 1772 -91 
Q 1169 -91 856 284 
Q 544 659 544 1381 
z
M 1991 3584 
L 1991 3584 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-4e" d="M 581 4863 
L 1159 4863 
L 1159 1991 
L 2875 3500 
L 3609 3500 
L 1753 1863 
L 3688 0 
L 2938 0 
L 1159 1709 
L 1159 0 
L 581 0 
L 581 4863 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-25" d="M 1259 2228 
L 1259 519 
L 2272 519 
Q 2781 519 3026 730 
Q 3272 941 3272 1375 
Q 3272 1813 3026 2020 
Q 2781 2228 2272 2228 
L 1259 2228 
z
M 1259 4147 
L 1259 2741 
L 2194 2741 
Q 2656 2741 2882 2914 
Q 3109 3088 3109 3444 
Q 3109 3797 2882 3972 
Q 2656 4147 2194 4147 
L 1259 4147 
z
M 628 4666 
L 2241 4666 
Q 2963 4666 3353 4366 
Q 3744 4066 3744 3513 
Q 3744 3084 3544 2831 
Q 3344 2578 2956 2516 
Q 3422 2416 3680 2098 
Q 3938 1781 3938 1306 
Q 3938 681 3513 340 
Q 3088 0 2303 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
      </defs>
      <use xlink:href="#DejaVuSans-27"/>
      <use xlink:href="#DejaVuSans-58" transform="translate(77 0)"/>
      <use xlink:href="#DejaVuSans-46" transform="translate(140.375 0)"/>
      <use xlink:href="#DejaVuSans-4e" transform="translate(195.359375 0)"/>
      <use xlink:href="#DejaVuSans-27" transform="translate(253.265625 0)"/>
      <use xlink:href="#DejaVuSans-25" transform="translate(330.265625 0)"/>
     </g>
    </g>
    <g id="patch_24">
     <path d="M 530.667031 83.758828 
L 548.667031 83.758828 
L 548.667031 77.458828 
L 530.667031 77.458828 
z
" style="fill: #55a868; opacity: 0.85"/>
    </g>
    <g id="text_33">
     <!-- Iceberg -->
     <g transform="translate(555.867031 83.758828) scale(0.09 -0.09)">
      <defs>
       <path id="DejaVuSans-2c" d="M 628 4666 
L 1259 4666 
L 1259 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
       <path id="DejaVuSans-45" d="M 3116 1747 
Q 3116 2381 2855 2742 
Q 2594 3103 2138 3103 
Q 1681 3103 1420 2742 
Q 1159 2381 1159 1747 
Q 1159 1113 1420 752 
Q 1681 391 2138 391 
Q 2594 391 2855 752 
Q 3116 1113 3116 1747 
z
M 1159 2969 
Q 1341 3281 1617 3432 
Q 1894 3584 2278 3584 
Q 2916 3584 3314 3078 
Q 3713 2572 3713 1747 
Q 3713 922 3314 415 
Q 2916 -91 2278 -91 
Q 1894 -91 1617 61 
Q 1341 213 1159 525 
L 1159 0 
L 581 0 
L 581 4863 
L 1159 4863 
L 1159 2969 
z
" transform="scale(0.015625)"/>
      </defs>
      <use xlink:href="#DejaVuSans-2c"/>
      <use xlink:href="#DejaVuSans-46" transform="translate(29.5 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(84.484375 0)"/>
      <use xlink:href="#DejaVuSans-45" transform="translate(146.015625 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(209.5 0)"/>
      <use xlink:href="#DejaVuSans-55" transform="translate(271.03125 0)"/>
      <use xlink:href="#DejaVuSans-4a" transform="translate(310.390625 0)"/>
     </g>
    </g>
    <g id="patch_25">
     <path d="M 530.667031 97.259531 
L 548.667031 97.259531 
L 548.667031 90.959531 
L 530.667031 90.959531 
z
" style="fill: #c44e52; opacity: 0.85"/>
    </g>
    <g id="text_34">
     <!-- LanceDB -->
     <g transform="translate(555.867031 97.259531) scale(0.09 -0.09)">
      <defs>
       <path id="DejaVuSans-2f" d="M 628 4666 
L 1259 4666 
L 1259 531 
L 3531 531 
L 3531 0 
L 628 0 
L 628 4666 
z
" transform="scale(0.015625)"/>
      </defs>
      <use xlink:href="#DejaVuSans-2f"/>
      <use xlink:href="#DejaVuSans-44" transform="translate(55.71875 0)"/>
      <use xlink:href="#DejaVuSans-51" transform="translate(117 0)"/>
      <use xlink:href="#DejaVuSans-46" transform="translate(180.375 0)"/>
      <use xlink:href="#DejaVuSans-48" transform="translate(235.359375 0)"/>
      <use xlink:href="#DejaVuSans-27" transform="translate(296.890625 0)"/>
      <use xlink:href="#DejaVuSans-25" transform="translate(373.890625 0)"/>
     </g>
    </g>
   </g>
  </g>
 </g>
 <defs>
  <clipPath id="p70d12b2a08">
   <rect x="44.103906" y="28.318125" width="589.237656" height="285.391406"/>
  </clipPath>
 </defs>
</svg>

### Notes on write timing

**DuckDB append and schema change.** The 0.24s append and 0.25s schema change for DuckDB are not persisted operations. Both are in-session view redefinitions; no data is written to S3. These timings are not directly comparable to the persisted writes of the other four engines.

**LaminDB append and schema change scope.** The LaminDB append time (9.4s) includes an S3 upload, schema validation against the registered schema, stable UID assignment, lineage graph linking, and creation of a new collection version. The schema change time (3.5s) includes round-trips to a Postgres-backed schema registry that applies instance-wide. These operations have a wider scope than the equivalent operations in Iceberg (table-scoped) and LanceDB (table-scoped), which is reflected in the timing difference.

---

## Developer experience compared

| | PyArrow | Polars | DuckDB | Iceberg | LanceDB |
|---|---|---|---|---|---|
| **Setup** | 1 line, ~0s | 1 line, ~0s | 5 lines, ~1s | ~20 lines, ~8.7s | 3 lines, ~7.6s |
| **Data ingestion required** | No | No | No | No (wraps source Parquet) | Yes (copies to Lance format) |
| **Query API** | PyArrow / pandas | Polars / pandas | SQL | Iceberg expressions / pandas | PyArrow / pandas / SQL |
| **Store-mode query time** | ~1.1–1.4s | ~0.27–0.35s | ~0.77–0.87s | ~0.15–0.19s* | ~0.06–0.33s* |
| **Append** | S3 upload + schema validation + collection version | same as PyArrow | session-only view redefinition | atomic snapshot to S3 | versioned write to S3 |
| **Append time** | 9.4s | 9.5s | 0.24s† | 0.88s | 0.11s |
| **Schema change scope** | instance-wide registry | instance-wide registry | session only† | this table | this table |
| **Schema change time** | 3.5s | 3.6s | 0.25s† | 0.31s | 0.06s |
| **Time travel** | collection versions | collection versions | not supported | snapshot ID | version number |
| **ACID** | schema validation + collection versioning | same as PyArrow | none | full snapshot isolation | versioned appends |
| **Vector search** | no | no | no | no | yes |
| **Stays in LaminDB lineage** | yes | yes | yes | yes | no |

\* Post-ingest; excludes one-time setup cost of 8.7s (Iceberg) and 7.6s (LanceDB).
† Not persisted; session-scoped only.

---

## LaminDB as a data layer

The five engines above address the question of how to query data. LaminDB addresses a different question: how to manage data across the lifecycle of a project.

In this benchmark, LaminDB serves as the storage layer underneath all five query engines. The same collection is opened by each engine without any data movement or format conversion (with the exception of LanceDB, which copies the data out). LaminDB does not provide a query engine and does not compete with DuckDB, Iceberg, or LanceDB on query performance.

What LaminDB provides:

**Lineage.** Each pipeline notebook in this benchmark is a tracked transform. The timing results are saved as tracked artifacts. A final `plots.py` script reads those five artifacts as registered inputs and writes the comparison figures as registered outputs. The full provenance chain — from the original 1000 Genomes data transfer through to the figures in this report — is recorded in LaminHub:

<img src="data:image/png;base64,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" alt="LaminHub lineage graph: 1000genomes_parquet collection feeds five pipeline notebooks, each producing a benchmark_results parquet artifact, which plot_benchmark.py consumes to produce the comparison figures. DuckDB reads from the collection via S3 paths but does not register the collection as a lineage input — its parquet artifact is an output of the notebook run but the collection node has no arrow to it." style="max-width:100%;border-radius:6px;" />

Note: DuckDB is the one exception in this lineage graph. It reads the collection's Parquet files directly via S3 paths rather than through LaminDB's `collection.open()` API, so the collection node has no incoming arrow from `duckdb_pipeline.ipynb`. The benchmark result artifact (`benchmark_results/duckdb.parquet`) is still tracked as an output of that notebook run — DuckDB participates in lineage as a producer, but not as a registered consumer of the source collection.

**Schema validation.** A schema registered against a collection validates new artifacts at write time. In the governance demo included in the PyArrow and Polars pipelines, saving a DataFrame with an unrecognised column against a closed schema raises a `ValidationError` before the data reaches storage.

**Collection versioning.** Each append creates a new collection version. Prior versions remain addressable by UID, providing a form of time travel equivalent to Iceberg's snapshot history and LanceDB's version checkout — but at the collection level rather than the table level.

**Metadata-queryable collections.** Artifacts in LaminDB carry biological metadata (organism, tissue, disease, experimental factor). Collections can be filtered by these metadata fields before any data is opened, allowing engine-agnostic subsetting at the collection level.

These capabilities are available regardless of which query engine is used.

---

## Conclusion

The five approaches in this comparison cover the main strategies for querying Parquet-based genomic data from a LaminDB collection: lazy reads without ingestion (PyArrow, Polars, DuckDB), metadata-layer ingestion (Iceberg), and format-conversion ingestion (LanceDB).

The primary tradeoffs observed:

- **Setup cost vs. query cost.** Iceberg and LanceDB incur a one-time setup cost of 7–9s that is amortised across subsequent queries. PyArrow, Polars, and DuckDB have negligible setup cost but re-read S3 on each store-mode query.
- **Query conciseness.** DuckDB's SQL interface produces the most concise aggregation queries. PyArrow and Polars require more verbose pandas expressions for equivalent operations.
- **Write durability.** DuckDB appends and schema changes are session-scoped and not persisted. All other engines write to S3.
- **Write scope.** LaminDB write operations (append, schema change) have instance-wide scope and include provenance recording; Iceberg and LanceDB operations are table-scoped.
- **Lineage.** Only LaminDB and the engines reading from LaminDB in place (PyArrow, Polars, DuckDB) maintain provenance. LanceDB copies data out of LaminDB's lineage graph.
- **S3 parallelism.** Polars reads the six source shards concurrently; PyArrow's dataset API reads them more sequentially. On this dataset, the observed difference is ~4× in store mode. This is a single-run observation; further investigation is needed to characterise the effect across different shard counts and network conditions.

For teams selecting a query engine over a LaminDB collection, the relevant dimensions are: whether SQL is preferred over expression APIs, whether upfront ingestion cost is acceptable, whether write operations need to be durable and their scope, and whether provenance tracking is required.

---

## Author contributions

Raaghav Pillai performed the benchmarking work and wrote the pipelines. The original LaminDB ingestion pipeline this work builds on was developed by Sunny Sun. Alex Wolf and Sergei Rybakov supervised the project.

## Code & data availability

The five pipeline notebooks, the shared benchmarking utilities, and the plotting script are tracked in the `laminlabs/lakehouse-benchmarks` instance.

- [PyArrow pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/D10UPamv70IP0001)
- [Polars pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/2Wdo02w0MDgH0000)
- [DuckDB pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/tQaG9uhSD7BO0000)
- [Iceberg pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/wnVO8cu0qtOP0001)
- [LanceDB pipeline](https://lamin.ai/laminlabs/lakehouse-benchmarks/transform/WtZF9OX9v3uM0001)

The dataset is the 1000 Genomes Project CNV calls (DRAGEN, hg38), collection UID `K6X8Ejk3fjgAZT6h0000`.

## How to cite

```
Pillai R, Rybakov S & Wolf A (2026). Five ways to query a LaminDB collection:
a developer-experience comparison of PyArrow, Polars, DuckDB, Iceberg, and LanceDB.
Lamin Blog.
```
