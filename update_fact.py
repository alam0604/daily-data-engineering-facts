"""Picks today's data-engineering fact and writes it to README.md and fact.svg.

Runs daily via .github/workflows/daily-fact.yml. No API keys needed:
facts come from FACTS below and rotate by date, so every day is different
and the cycle repeats only after len(FACTS) days.
"""
import datetime
import html
import re
import textwrap

FACTS = [
    # ---------- Spark architecture & internals ----------
    ("Spark Architecture", "A Spark application has one driver and many executors. The driver builds the DAG, splits it into stages and tasks, and schedules tasks on executors; executors run tasks and cache data. Lose the driver and the whole app dies."),
    ("Spark Architecture", "A job becomes stages at every shuffle boundary (wide dependency). Inside a stage, narrow transformations are pipelined, and each stage runs one task per partition."),
    ("Spark Internals", "Transformations are lazy. Nothing runs until an action (count, collect, write, show) is called, which lets Catalyst optimise the whole plan before execution."),
    ("Spark Internals", "Catalyst optimises queries in four phases: analysis, logical optimisation, physical planning and code generation. Tungsten then runs whole-stage codegen, fusing operators into one JVM function."),
    ("Spark Internals", "Narrow transformations (map, filter, union) need no data movement. Wide ones (groupBy, join, distinct, repartition) trigger a shuffle, the most expensive operation in Spark."),
    ("Spark Internals", "spark.sql.shuffle.partitions defaults to 200. On small data that means 200 tiny tasks; on huge data it means giant ones. AQE can coalesce them automatically at runtime."),
    ("Spark Internals", "Adaptive Query Execution (on by default since Spark 3.2) re-optimises at runtime: it coalesces shuffle partitions, switches sort-merge joins to broadcast joins, and splits skewed partitions."),
    ("Spark Internals", "Executor memory is split into execution memory (shuffles, joins, sorts) and storage memory (cache). Under unified memory management they borrow from each other; execution can evict cached blocks."),
    ("Spark Internals", "spark.sql.autoBroadcastJoinThreshold defaults to 10 MB. Tables smaller than this are broadcast to every executor, so the join needs no shuffle on the big side."),
    ("Spark Internals", "Sort-merge join is Spark's default for two large tables: both sides are shuffled by key, sorted, then merged. Broadcast hash join skips the shuffle when one side is small."),
    ("Spark Internals", "Dynamic Partition Pruning (Spark 3.0+) pushes a filter from a dimension table into the scan of a partitioned fact table at runtime, so unneeded partitions are never read."),
    ("Spark Internals", "Speculative execution (spark.speculation) launches duplicate copies of slow tasks on other executors and keeps whichever finishes first. Useful for straggler nodes, not for data skew."),
    ("Spark Internals", "The DAG scheduler handles stages; the task scheduler sends tasks to executors. Data locality levels, best to worst: PROCESS_LOCAL, NODE_LOCAL, RACK_LOCAL, ANY."),
    ("Spark Internals", "Lineage is how Spark recovers lost partitions: it recomputes them from their parent RDDs. Very long lineage chains (iterative jobs) are cut with checkpoint()."),
    # ---------- PySpark performance ----------
    ("PySpark Performance", "repartition(n) does a full shuffle and can increase or decrease partitions. coalesce(n) only merges partitions without a full shuffle, so it is the cheap way to reduce them before a write."),
    ("PySpark Performance", "Python UDFs serialize every row between the JVM and the Python worker. Prefer built-in functions; if you need Python, pandas_udf uses Arrow to move data in vectorised batches."),
    ("PySpark Performance", "cache() on a DataFrame is persist(StorageLevel.MEMORY_AND_DISK). It is lazy too: the data is only cached when the first action runs. Call unpersist() when you are done."),
    ("PySpark Performance", "Data skew fix: salting. Add a random suffix to the hot key on the big side, explode the small side across the same suffixes, join, then aggregate back."),
    ("PySpark Performance", "collect() pulls the whole DataFrame to the driver and is a classic OOM. Use take(n), show(), or write the result out instead."),
    ("PySpark Performance", "Avoid count() just to check emptiness. df.isEmpty() (Spark 3.3+) or len(df.take(1)) == 0 stops after the first row."),
    ("PySpark Performance", "Read only what you need: select columns early so Parquet/Delta column pruning kicks in, and filter early so predicate pushdown skips row groups and files."),
    ("PySpark Performance", "Each withColumn() call adds a projection to the plan. Adding dozens in a loop bloats the plan and slows analysis; use a single select() or withColumns() (Spark 3.3+)."),
    ("PySpark Performance", "broadcast() is a hint: F.broadcast(small_df) forces a broadcast join even if the table is above autoBroadcastJoinThreshold. Keep it well within driver and executor memory."),
    ("PySpark Performance", "Small-files problem: thousands of tiny files mean thousands of tasks and slow listing. Fix it with coalesce before writing, Delta OPTIMIZE, or optimized writes / auto compaction."),
    ("PySpark Performance", "df.explain('formatted') shows the physical plan. Look for Exchange (shuffle), BroadcastHashJoin vs SortMergeJoin, and PushedFilters on the scan node."),
    # ---------- PySpark interview questions ----------
    ("Interview Q", "Q: What's the difference between groupByKey and reduceByKey? A: reduceByKey combines values on each partition before the shuffle (map-side combine), so far less data moves across the network."),
    ("Interview Q", "Q: Why can a job fail with 'Container killed by YARN for exceeding memory limits'? A: Off-heap usage (Python workers, overhead) exceeded spark.executor.memoryOverhead. Raise overhead or cut per-task data."),
    ("Interview Q", "Q: Difference between persist() and checkpoint()? A: persist keeps the lineage and can be lost with an executor; checkpoint writes to reliable storage and truncates the lineage."),
    ("Interview Q", "Q: How many tasks does a stage run? A: One per partition of the RDD/DataFrame at that stage. Number of tasks running at once = executors x cores per executor."),
    ("Interview Q", "Q: What does a window function need that groupBy doesn't? A: groupBy collapses rows; a window keeps every row and computes over a partition, e.g. row_number() over (partitionBy(id).orderBy(ts))."),
    ("Interview Q", "Q: How do you remove duplicates keeping the latest record? A: row_number() over a window partitioned by key and ordered by timestamp desc, then filter row_number == 1."),
    ("Interview Q", "Q: client vs cluster deploy mode? A: In client mode the driver runs where you submit (e.g. a laptop or edge node); in cluster mode it runs inside the cluster, which is what you want for production."),
    ("Interview Q", "Q: What is an accumulator? A: A write-only shared variable that executors add to and only the driver reads. Updates inside transformations can be double-counted if tasks are retried."),
    ("Interview Q", "Q: map vs flatMap? A: map returns exactly one output per input; flatMap returns zero or more and flattens them, e.g. splitting lines into words."),
    ("Interview Q", "Q: How do you handle late-arriving data in Structured Streaming? A: withWatermark('event_time', '10 minutes') lets Spark drop state older than the watermark while still accepting late rows within it."),
    # ---------- Delta Lake / Lakehouse ----------
    ("Delta Lake", "Every Delta write adds a JSON commit to _delta_log. Every 10 commits Spark writes a Parquet checkpoint, so readers don't replay the whole log."),
    ("Delta Lake", "Time travel: SELECT * FROM t VERSION AS OF 12 or TIMESTAMP AS OF '2026-01-01'. It only works while the old files survive VACUUM (default retention 7 days)."),
    ("Delta Lake", "MERGE INTO is how you do upserts and SCD Type 2 on Delta. Add the partition column to the ON condition so MERGE can prune files instead of scanning the whole table."),
    ("Delta Lake", "Z-ORDER BY co-locates related values in the same files, so data skipping using min/max stats can skip more files. Liquid clustering is the newer, incremental alternative."),
    ("Delta Lake", "Delta enforces schema on write: mismatched columns fail. Use .option('mergeSchema', 'true') to evolve the schema intentionally."),
    ("Delta Lake", "Change Data Feed (delta.enableChangeDataFeed = true) records row-level inserts, updates and deletes, so downstream tables can process only what changed."),
    ("Lakehouse", "Medallion architecture: Bronze = raw as ingested, Silver = cleaned, deduplicated and conformed, Gold = business-level aggregates ready for BI."),
    ("Lakehouse", "Delta uses optimistic concurrency: writers read a snapshot, write files, then try to commit. If another commit touched the same files, the commit fails with a conflict exception."),
    # ---------- Azure Data Factory ----------
    ("Azure Data Factory", "ADF's building blocks: pipelines (workflows) contain activities; activities use datasets (data shape) that point to linked services (connections). Integration runtimes provide the compute."),
    ("Azure Data Factory", "Three integration runtimes: Azure IR (cloud compute), Self-hosted IR (reach on-prem or private networks), and Azure-SSIS IR (lift-and-shift SSIS packages)."),
    ("Azure Data Factory", "Incremental load pattern: store a watermark (last modified time) in a control table, Lookup it, Copy rows newer than it, then update the watermark with a Stored Procedure activity."),
    ("Azure Data Factory", "ForEach runs in parallel by default (batchCount up to 50). Set isSequential = true when iterations must run in order or would hit the same target."),
    ("Azure Data Factory", "Triggers: Schedule (wall-clock), Tumbling window (fixed, non-overlapping intervals with backfill, retry and dependencies), Storage event (blob created/deleted), and Custom event."),
    ("Azure Data Factory", "Mapping Data Flows run on Spark clusters managed by ADF. They are visual and need no code, but each run pays for cluster start-up unless you set a TTL to keep it warm."),
    ("Azure Data Factory", "Parameterise linked services and datasets so one pipeline can load 100 tables from a metadata table, instead of building 100 pipelines."),
    ("Azure Data Factory", "Use Key Vault linked services for secrets and a managed identity for authentication, so no passwords live in pipeline JSON."),
    ("Azure Data Factory", "Activity dependency conditions: Succeeded, Failed, Completed and Skipped. Combine them to build try/catch-style error handling in a pipeline."),
    ("Azure Data Factory", "Interview Q: Lookup vs Get Metadata? A: Lookup returns rows from a dataset (max 5,000 rows or 4 MB); Get Metadata returns properties such as childItems, size, lastModified or exists."),
    # ---------- Microsoft Fabric ----------
    ("Microsoft Fabric", "OneLake is Fabric's single tenant-wide data lake ('OneDrive for data'). Every workspace and item stores its data there, in Delta Parquet by default."),
    ("Microsoft Fabric", "Shortcuts in OneLake point to data in ADLS Gen2, S3, GCS or other workspaces without copying it. Engines read it as if it were local."),
    ("Microsoft Fabric", "Lakehouse vs Warehouse in Fabric: Lakehouse is Spark-first (notebooks, files + tables, read-only SQL endpoint); Warehouse is T-SQL-first with full DML and multi-table transactions."),
    ("Microsoft Fabric", "Direct Lake mode lets Power BI semantic models read Delta tables in OneLake directly: near-Import speed without scheduled refresh copies."),
    ("Microsoft Fabric", "V-Order is a Fabric write-time optimisation for Parquet (special sorting, encoding and compression). Files stay standard Parquet but load faster in Power BI and SQL engines."),
    ("Microsoft Fabric", "Fabric capacities are measured in Capacity Units (F2 to F2048). All workloads, from Spark to Power BI, draw from the same capacity, and smoothing spreads bursts over time."),
    ("Microsoft Fabric", "Fabric Data Factory = Data pipelines (the ADF-style orchestrator) plus Dataflow Gen2 (Power Query-based transformations that can write to Lakehouse or Warehouse)."),
    ("Microsoft Fabric", "Mirroring replicates databases such as Azure SQL, Cosmos DB and Snowflake into OneLake as Delta tables, continuously and with near-real-time latency."),
    ("Microsoft Fabric", "Fabric Spark starter pools are pre-warmed, so notebook sessions start in seconds. Custom pools let you choose node size and autoscale, at the cost of a slower start."),
    ("Microsoft Fabric", "Real-Time Intelligence in Fabric: Eventstreams ingest events, Eventhouses (KQL databases) store and query them, and Activator triggers actions on patterns."),
    # ---------- SQL & general DE ----------
    ("SQL", "Logical query order: FROM -> JOIN -> WHERE -> GROUP BY -> HAVING -> SELECT -> DISTINCT -> ORDER BY -> LIMIT. That's why a SELECT alias can't be used in WHERE."),
    ("SQL", "RANK leaves gaps after ties (1,1,3), DENSE_RANK doesn't (1,1,2), and ROW_NUMBER always gives unique numbers (1,2,3)."),
    ("Data Modeling", "SCD Type 1 overwrites old values; Type 2 adds a new row with effective dates and an is_current flag, so history is kept; Type 3 keeps a 'previous value' column."),
    ("Data Engineering", "Idempotent pipelines produce the same result when re-run: use MERGE or overwrite by partition instead of blind appends, so retries and backfills never duplicate data."),
    ("File Formats", "Parquet is columnar with per-row-group min/max statistics, so engines can skip data. CSV has no schema or stats; Avro is row-based and good for streaming and schema evolution."),
]

START = datetime.date(2026, 1, 1)
MARK_START = "<!-- FACT:START -->"
MARK_END = "<!-- FACT:END -->"


def todays_fact(today):
    idx = (today - START).days % len(FACTS)
    return idx, FACTS[idx]


def render_svg(topic, text, today):
    lines = textwrap.wrap(text, width=62)
    line_h = 22
    height = 110 + line_h * len(lines)
    tspans = "".join(
        f'<tspan x="32" dy="{0 if i == 0 else line_h}">{html.escape(l)}</tspan>'
        for i, l in enumerate(lines)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="{height}" viewBox="0 0 600 {height}">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#1e1b4b"/><stop offset="1" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="600" height="{height}" rx="14" fill="url(#g)" stroke="#6366f1" stroke-opacity="0.5"/>
  <text x="32" y="40" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="13" fill="#a5b4fc" letter-spacing="1.5">✧ DAILY DATA ENGINEERING FACT · {html.escape(topic.upper())}</text>
  <text x="32" y="74" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="15" fill="#e2e8f0">{tspans}</text>
  <text x="32" y="{height - 22}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="11" fill="#64748b">{today.strftime('%d %b %Y')} · github.com/alam0604/daily-data-engineering-facts</text>
</svg>
"""


def main():
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30))).date()
    idx, (topic, text) = todays_fact(today)

    with open("fact.svg", "w", encoding="utf-8") as f:
        f.write(render_svg(topic, text, today))

    block = (
        f"{MARK_START}\n"
        f"### ✧ {topic}\n\n"
        f"> {text}\n\n"
        f"<sub>Fact #{idx + 1} of {len(FACTS)} · updated {today.isoformat()}</sub>\n"
        f"{MARK_END}"
    )
    with open("README.md", encoding="utf-8") as f:
        readme = f.read()
    readme = re.sub(
        re.escape(MARK_START) + r".*?" + re.escape(MARK_END),
        lambda _: block,
        readme,
        flags=re.S,
    )
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    print(f"Fact #{idx + 1}: [{topic}] {text}")


if __name__ == "__main__":
    main()
