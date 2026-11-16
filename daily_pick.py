"""Daily pick: pulls a fresh, technical data-engineering article or interview question
from Medium, Hashnode and dev.to, and writes it to README.md and fact.svg.

- Sources: Medium tag RSS feeds, dev.to public API, Hashnode public GraphQL API.
- Focus: Databricks, PySpark / Spark (questions, interview questions, architecture),
  Azure Data Factory, Microsoft Fabric and optimisation. Posts are ranked by how
  technical they are; opinion, career and news posts are skipped.
- Odd days prefer interview-question posts; even days prefer everything else.
- history.json remembers what was already shown, so nothing repeats (never trimmed).
- today.json holds today's full pick; archive_fact.py (second workflow) files it under archive/.
- If every source fails, it falls back to the built-in fact bank in update_fact.py.
"""
import datetime
import html
import json
import random
import re
import textwrap
import time
import urllib.request
import xml.etree.ElementTree as ET

from update_fact import FACTS, MARK_END, MARK_START, todays_fact

UA = {"User-Agent": "Mozilla/5.0 (daily-data-engineering-facts; +https://github.com/alam0604/daily-data-engineering-facts)"}

MEDIUM_TAGS = ["pyspark", "apache-spark", "spark-optimization", "databricks", "delta-lake",
               "azure-data-factory", "microsoft-fabric", "data-engineering-interview"]
DEVTO_TAGS = ["pyspark", "apachespark", "spark", "databricks", "dataengineering", "microsoftfabric", "azuredatafactory"]
HASHNODE_TAGS = ["pyspark", "apache-spark", "databricks", "data-engineering", "azure-data-factory", "microsoft-fabric"]

# Must mention at least one core topic...
RELEVANT = re.compile(
    r"databricks|pyspark|spark|data ?factory|\badf\b|ms ?fabric|microsoft fabric|"
    r"fabric (lakehouse|warehouse|pipeline|notebook|capacity)|onelake|delta lake|\bdelta\b|lakehouse|"
    r"unity catalog|synapse", re.I)
# ...and is ranked higher the more technical it is.
TECH = re.compile(
    r"optimi[sz]|performance|tuning|faster|slow|cost|partition|shuffle|skew|salting|broadcast|join|\baqe\b|adaptive|"
    r"cache|persist|memory|executor|driver|\bdag\b|catalyst|tungsten|internals|architecture|under the hood|deep dive|"
    r"z-?order|liquid clustering|vacuum|optimize|merge|\bcdc\b|\bscd\b|incremental|watermark|streaming|"
    r"pipeline|copy activity|trigger|integration runtime|dataflow|notebook|medallion|v-?order|direct lake|"
    r"interview|question|explained|how to|best practices|pattern|debug|troubleshoot|\budf\b|window function", re.I)
# Skip opinion / career / news-style posts.
OFFTOPIC = re.compile(
    r"\bcareer|journey|roadmap|my experience|story of|announc|webinar|\bevent\b|conference|meetup|newsletter|"
    r"weekly|digest|resume|layoff|are we really|future of|why i (left|quit)", re.I)
SPAM = re.compile(
    r"course|training|institute|certification|classes|coaching|tutorial in|online demo|free demo|"
    r"enrol|placement|hiring|\bjobs?\b|salary|\bin (chennai|hyderabad|bangalore|bengaluru|pune|ameerpet|noida)", re.I)
QUESTION = re.compile(r"interview|question|\bq&a\b|asked", re.I)
HISTORY_FILE = "history.json"
TODAY_FILE = "today.json"


def get(url, data=None, headers=None, timeout=20):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def clean(text, limit=200):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + "…"
    return text


def from_medium():
    out = []
    for tag in MEDIUM_TAGS:
        try:
            root = ET.fromstring(get(f"https://medium.com/feed/tag/{tag}"))
        except Exception as e:
            print(f"medium/{tag}: {e}")
            continue
        for item in root.iter("item"):
            ns_creator = "{http://purl.org/dc/elements/1.1/}creator"
            ns_content = "{http://purl.org/rss/1.0/modules/content/}encoded"
            out.append({
                "source": "Medium",
                "title": (item.findtext("title") or "").strip(),
                "url": (item.findtext("link") or "").split("?")[0],
                "author": item.findtext(ns_creator) or "",
                "brief": clean(item.findtext("description") or item.findtext(ns_content)),
            })
    return out


def from_devto():
    out = []
    for tag in DEVTO_TAGS:
        try:
            posts = json.loads(get(f"https://dev.to/api/articles?tag={tag}&top=60&per_page=30"))
        except Exception as e:
            print(f"devto/{tag}: {e}")
            continue
        finally:
            time.sleep(1.5)
        for p in posts:
            out.append({
                "source": "dev.to",
                "title": p.get("title", ""),
                "url": p.get("url", ""),
                "author": (p.get("user") or {}).get("name", ""),
                "brief": clean(p.get("description")),
            })
    return out


def from_hashnode():
    out = []
    hdr = {"Content-Type": "application/json", "Accept": "application/json",
           "User-Agent": "daily-data-engineering-facts/1.0"}
    for tag in HASHNODE_TAGS:
        raw = b""
        try:
            body = json.dumps({"query": TAG_POSTS, "variables": {"slug": tag}}).encode()
            raw = get("https://gql.hashnode.com/", data=body, headers=hdr)
            res = json.loads(raw)
            if res.get("errors"):
                print(f"hashnode/{tag}: {res['errors'][0].get('message')}")
            edges = (((res.get("data") or {}).get("tag") or {}).get("posts") or {}).get("edges", [])
        except Exception as e:
            print(f"hashnode/{tag}: {e} | response starts: {raw[:150]!r}")
            continue
        for e in edges:
            n = e["node"]
            out.append({
                "source": "Hashnode",
                "title": n.get("title", ""),
                "url": n.get("url", ""),
                "author": (n.get("author") or {}).get("name", ""),
                "brief": clean(n.get("brief")),
            })
    return out


TAG_POSTS = """query($slug: String!) { tag(slug: $slug) { posts(first: 20, filter: {sortBy: popular}) {
  edges { node { title url brief author { name } } } } } }"""


def load_history():
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def score(p):
    """How technical a post looks: distinct technical terms, title counts double."""
    in_title = {m.lower() for m in TECH.findall(p["title"])}
    in_text = {m.lower() for m in TECH.findall(p["title"] + " " + p["brief"])}
    return 2 * len(in_title) + len(in_text)


def pick(posts, history, today):
    seen = {h["url"] for h in history}
    uniq = {}
    for p in posts:
        text = p["title"] + " " + p["brief"]
        if (p["url"] and p["title"] and p["url"] not in seen and RELEVANT.search(text)
                and not SPAM.search(p["title"]) and not OFFTOPIC.search(p["title"]) and score(p) >= 2):
            uniq.setdefault(p["url"], p)
    pool = sorted(uniq.values(), key=score, reverse=True)
    if not pool:
        return None
    want_question = today.toordinal() % 2 == 1
    preferred = [p for p in pool if bool(QUESTION.search(p["title"])) == want_question] or pool
    rng = random.Random(today.toordinal())
    return rng.choice(preferred[:5])  # one of the 5 most technical


def render_svg(label, title, sub, today, fact_topic=None, fact=None):
    font = "Segoe UI, Helvetica, Arial, sans-serif"
    t_lines = textwrap.wrap(title, width=52)[:3]
    f_lines = textwrap.wrap(fact, width=72)[:6] if fact else []
    y = 78
    parts = []
    for l in t_lines:
        parts.append(f'<text x="32" y="{y}" font-family="{font}" font-size="19" font-weight="600" fill="#f1f5f9">{html.escape(l)}</text>')
        y += 26
    if sub:
        parts.append(f'<text x="32" y="{y}" font-family="{font}" font-size="12" fill="#94a3b8">{html.escape(sub)}</text>')
        y += 22
    if f_lines:
        parts.append(f'<line x1="32" y1="{y}" x2="568" y2="{y}" stroke="#6366f1" stroke-opacity="0.35"/>')
        y += 26
        parts.append(f'<text x="32" y="{y}" font-family="{font}" font-size="12" fill="#a5b4fc" letter-spacing="1.5">QUICK FACT · {html.escape((fact_topic or "").upper())}</text>')
        y += 24
        for l in f_lines:
            parts.append(f'<text x="32" y="{y}" font-family="{font}" font-size="14" fill="#e2e8f0">{html.escape(l)}</text>')
            y += 20
    height = y + 30
    body = "\n  ".join(parts)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="{height}" viewBox="0 0 600 {height}">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#1e1b4b"/><stop offset="1" stop-color="#0f172a"/></linearGradient></defs>
  <rect width="600" height="{height}" rx="14" fill="url(#g)" stroke="#6366f1" stroke-opacity="0.5"/>
  <text x="32" y="40" font-family="{font}" font-size="13" fill="#a5b4fc" letter-spacing="1.5">✧ {html.escape(label.upper())}</text>
  {body}
  <text x="568" y="{height - 14}" text-anchor="end" font-family="{font}" font-size="10" fill="#64748b">{today.strftime('%d %b %Y')} · daily-data-engineering-facts</text>
</svg>
"""


def main():
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).date()
    posts = from_medium() + from_hashnode() + from_devto()
    counts = {s: sum(p["source"] == s for p in posts) for s in ("Medium", "Hashnode", "dev.to")}
    print("fetched:", counts)

    history = load_history()
    post = pick(posts, history, today)
    idx, (topic, fact) = todays_fact(today)

    if post:
        kind = "Interview question of the day" if QUESTION.search(post["title"]) else "Read of the day"
        by = f" by {post['author']}" if post["author"] else ""
        block = (
            f"{MARK_START}\n"
            f"### ✧ {kind}\n\n"
            f"**[{post['title']}]({post['url']})**{by} · *{post['source']}*\n\n"
            + (f"> {post['brief']}\n\n" if post["brief"] else "")
            + f"**Quick fact ({topic}):** {fact}\n\n"
            f"<sub>updated {today.isoformat()}</sub>\n"
            f"{MARK_END}"
        )
        svg = render_svg(f"{kind} · {post['source']}", post["title"],
                         f"by {post['author']}" if post["author"] else post["source"], today, topic, fact)
        history.append({"date": today.isoformat(), "url": post["url"], "title": post["title"],
                        "source": post["source"]})
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=1, ensure_ascii=False)
        record = {"date": today.isoformat(), "kind": kind, **post}
        print(f"picked (score {score(post)}): [{post['source']}] {post['title']} {post['url']}")
    else:
        print("no technical posts found, using built-in fact")
        block = (
            f"{MARK_START}\n### ✧ {topic}\n\n> {fact}\n\n"
            f"<sub>updated {today.isoformat()}</sub>\n{MARK_END}"
        )
        svg = render_svg(f"Daily data engineering fact · {topic}", fact, "", today)
        record = {"date": today.isoformat(), "kind": "Fact of the day"}

    record.update({"fact_topic": topic, "fact": fact})
    with open(TODAY_FILE, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=1, ensure_ascii=False)

    with open("fact.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    with open("README.md", encoding="utf-8") as f:
        readme = f.read()
    readme = re.sub(re.escape(MARK_START) + r".*?" + re.escape(MARK_END),
                    lambda _: block, readme, flags=re.S)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme)


if __name__ == "__main__":
    main()
