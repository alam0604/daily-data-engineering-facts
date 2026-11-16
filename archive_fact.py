"""Archives every daily pick permanently, in dated folders.

Run by .github/workflows/archive-fact.yml right after the "Daily fact" workflow.

- archive/index.json            every pick ever made (never trimmed, never overwritten)
- archive/YYYY/MM/YYYY-MM-DD.md  one file per day with that day's pick(s) and quick fact
- ARCHIVE.md                     table of contents, newest first, linking to each day

Sources: today.json (full details of today's pick) and history.json (backfills any
older pick that is not archived yet). Safe to run many times: entries are de-duplicated.
"""
import json
import os
from collections import defaultdict

from daily_pick import SPAM

INDEX = "archive/index.json"


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def key(e):
    return e.get("url") or f'{e["date"]}|{e.get("fact", "")}'


def render_day(date, entries):
    lines = [f"# ✧ {date}", ""]
    for e in entries:
        lines.append(f"## {e.get('kind', 'Pick')}")
        lines.append("")
        if e.get("url"):
            by = f" by {e['author']}" if e.get("author") else ""
            src = f" · *{e['source']}*" if e.get("source") else ""
            lines.append(f"**[{e.get('title', e['url'])}]({e['url']})**{by}{src}")
            lines.append("")
            if e.get("brief"):
                lines.append(f"> {e['brief']}")
                lines.append("")
        if e.get("fact"):
            lines.append(f"**Quick fact ({e.get('fact_topic', 'Data Engineering')}):** {e['fact']}")
            lines.append("")
    lines.append("[← All days](../../../ARCHIVE.md)")
    return "\n".join(lines) + "\n"


def main():
    index = load(INDEX, [])
    known = {key(e): e for e in index}
    added = 0

    candidates = []
    today = load("today.json", None)
    if today:
        candidates.append(today)
    candidates += load("history.json", [])

    for c in candidates:
        if SPAM.search(c.get("title", "")):
            continue
        k = key(c)
        if k in known:
            # fill in details we didn't have before (e.g. backfilled from history.json)
            for f, v in c.items():
                known[k].setdefault(f, v)
            continue
        entry = dict(c)
        entry.setdefault("kind", "Read of the day")
        index.append(entry)
        known[k] = entry
        added += 1

    index.sort(key=lambda e: e["date"])
    os.makedirs("archive", exist_ok=True)
    with open(INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=1, ensure_ascii=False)

    by_day = defaultdict(list)
    for e in index:
        by_day[e["date"]].append(e)

    for date, entries in by_day.items():
        y, m, _ = date.split("-")
        path = f"archive/{y}/{m}/{date}.md"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(render_day(date, entries))

    toc = ["# ✧ Archive", "", f"Every daily pick so far: **{len(index)}** across **{len(by_day)}** days.", ""]
    month = None
    for date in sorted(by_day, reverse=True):
        y, m, _ = date.split("-")
        if (y, m) != month:
            month = (y, m)
            toc += ["", f"## {y}-{m}", ""]
        titles = "; ".join(e.get("title") or e.get("fact_topic", "Fact") for e in by_day[date])
        toc.append(f"- [{date}](archive/{y}/{m}/{date}.md): {titles}")
    with open("ARCHIVE.md", "w", encoding="utf-8") as f:
        f.write("\n".join(toc) + "\n")

    print(f"archived {added} new pick(s); total {len(index)} across {len(by_day)} day(s)")


if __name__ == "__main__":
    main()
