# ✧ Daily Data Engineering Facts

A new fact every day on **PySpark & Spark internals, Delta Lake, Azure Data Factory, Microsoft Fabric** and SQL, plus the interview questions that come up again and again.
Updated automatically by GitHub Actions at 06:00 IST.

## Today's fact

<!-- FACT:START -->
### ✧ Azure Data Factory

> Triggers: Schedule (wall-clock), Tumbling window (fixed, non-overlapping intervals with backfill, retry and dependencies), Storage event (blob created/deleted), and Custom event.

<sub>Fact #48 of 68 · updated 2026-11-16</sub>
<!-- FACT:END -->

## As a card

<img src="./fact.svg" alt="Today's data engineering fact" width="600"/>

Embed it anywhere (e.g. your profile README):

```md
<img src="https://raw.githubusercontent.com/alam0604/daily-data-engineering-facts/main/fact.svg" width="600"/>
```

## How it works

- `update_fact.py` holds the fact bank and picks one by date, so it's a new fact each day.
- `.github/workflows/daily-fact.yml` runs it every morning and commits the updated `README.md` and `fact.svg`.
- No API keys and no cost. To add facts, append to `FACTS` in `update_fact.py`.

Run it now: **Actions → Daily fact → Run workflow**.
