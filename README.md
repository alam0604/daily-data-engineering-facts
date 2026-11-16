# ✧ Daily Data Engineering Facts

Every morning this repo picks a fresh **article or interview question** on **PySpark & Spark internals, Delta Lake, Azure Data Factory, Microsoft Fabric** and Databricks from **Medium, Hashnode and dev.to**, plus a quick fact.
Updated automatically by GitHub Actions at 06:00 IST.

## Today's pick

<!-- FACT:START -->
### ✧ Read of the day

**[Microsoft Azure Data Engineering | Course In Chennai](https://medium.com/@naveenkvisualpath/microsoft-azure-data-engineering-course-in-chennai-48b7889c8aa7)** by naveenk visualpath · *Medium*

> How to Build a Metadata-Driven Framework in Azure Data Factory? Continue reading on Medium »

**Quick fact (Azure Data Factory):** Triggers: Schedule (wall-clock), Tumbling window (fixed, non-overlapping intervals with backfill, retry and dependencies), Storage event (blob created/deleted), and Custom event.

<sub>updated 2026-11-16</sub>
<!-- FACT:END -->

## As a card

<img src="./fact.svg" alt="Today's data engineering pick" width="600"/>

Embed it anywhere (e.g. your profile README):

```md
<img src="https://raw.githubusercontent.com/alam0604/daily-data-engineering-facts/main/fact.svg" width="600"/>
```

## How it works

- `daily_pick.py` reads Medium tag feeds, the dev.to API and the Hashnode API, keeps only relevant posts, and picks one. Odd days favour interview questions, even days favour articles.
- `history.json` remembers every pick so nothing repeats.
- If all sources are down, it falls back to the built-in fact bank in `update_fact.py`.
- No API keys and no cost. Change topics by editing the tag lists at the top of `daily_pick.py`.

All articles belong to their authors; this repo only links to them.

Run it now: **Actions → Daily fact → Run workflow**.
