# ✧ Daily Data Engineering Facts

Every morning this repo picks a fresh **article or interview question** on **PySpark & Spark internals, Delta Lake, Azure Data Factory, Microsoft Fabric** and Databricks from **Medium, Hashnode and dev.to**, plus a quick fact.
Updated automatically by GitHub Actions at 06:00 IST.

📚 **Every past pick is kept forever in the [Archive](ARCHIVE.md)**, one file per day under `archive/YYYY/MM/`.

## Today's pick

<!-- FACT:START -->
### ✧ Read of the day

**[Spark’s Catalyst Optimizer vs Tungsten Execution Engine: The Brain and the Brawn Behind Apache…](https://medium.com/h7w/sparks-catalyst-optimizer-vs-tungsten-execution-engine-the-brain-and-the-brawn-behind-apache-d40725f31559)** by Sriw World of Coding · *Medium*

> If you’ve ever wondered why Apache Spark is so blazing fast — and where exactly that magic happens — this article is for you. Continue reading on T3CH »

**Quick fact (Microsoft Fabric):** V-Order is a Fabric write-time optimisation for Parquet (special sorting, encoding and compression). Files stay standard Parquet but load faster in Power BI and SQL engines.

<sub>updated 2026-11-26</sub>
<!-- FACT:END -->

## As a card

<img src="./cards/2026-11-26-f4903e.svg" alt="Today's data engineering pick" width="100%"/>

Embed it anywhere (e.g. your profile README):

```md
<img src="https://raw.githubusercontent.com/alam0604/daily-data-engineering-facts/main/fact.svg" width="100%"/>
```

## How it works

Two GitHub Actions run every morning:

1. **Daily fact** (06:00 IST) runs `daily_pick.py`. It reads Medium tag feeds, the dev.to API and the Hashnode API, keeps only relevant posts (no course ads or job posts), and picks one. Odd days favour interview questions, even days favour articles. It updates this README, `fact.svg` and `today.json`.
2. **Archive fact** runs right after it and calls `archive_fact.py`. It saves the pick permanently:
   - `archive/YYYY/MM/YYYY-MM-DD.md`, one file per day
   - `archive/index.json`, every pick ever made
   - `ARCHIVE.md`, the list of all days, newest first

Other details:

- `history.json` remembers every pick so nothing repeats.
- If all sources are down, it falls back to the built-in fact bank in `update_fact.py`.
- No API keys and no cost. Change topics by editing the tag lists at the top of `daily_pick.py`.

All articles belong to their authors; this repo only links to them.

Run it now: **Actions → Daily fact → Run workflow**.
