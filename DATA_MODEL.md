# Data model (for after the Approach B proof of concept)

**Status:** design only. The Approach B proof of concept (`APPROACH_B_RUN.md`) uses plain JSON/JSONL files. If it
works, this is the database the separate services move to. Nothing here needs building for the proof of concept.

## 1. Services and how they share data

```
[Link collector]   (the old agent, upgraded per OLD_AGENT_IMPROVEMENTS.md)
     │  runs periodically per site; writes what it saw
     ▼
 sites · links · page_links · link_versions
     │
     ▼
[Processor]        (Approach B processing layer)
     │  reads new/changed rows; groups families, decides assets, extracts specs, cross-checks
     ▼
 families · family_assets · variants · spec_values · spec_sources · prices
     ▲
[Health checker]   re-checks links (status, etag / last_modified); marks dead or changed links,
                   which triggers reprocessing of the affected families
```

The services never call each other; **the tables are the contract**. Each service records its runs in `runs`.

## 2. Tables

Postgres. `JSONB` holds data whose shape may still evolve, so SPEC changes don't require migrations.

### Collected data (link collector + health checker)
```
sites          id PK, homepage_url UNIQUE, status (ok / blocked / paused), crawl_schedule,
               last_crawled_at

links          id PK, site_id → sites, url UNIQUE (normalised), url_type, status, reason,
               etag, last_modified, first_seen, last_seen, gone_at, last_checked

page_links     page_link_id → links, target_link_id → links, link_text, section, in_chrome,
               link_kind, first_seen, last_seen
               PK (page_link_id, target_link_id)

link_versions  id PK, link_id → links, sha256, fetched_at, http_status, content_type,
               blob_path, text_blob_path, facts JSONB
               UNIQUE (link_id, sha256)

runs           id PK, stage (collect / process / check), service_version, site_id → sites,
               started_at, finished_at, stats JSONB
```

### Derived data (processor)
```
families       id PK, site_id → sites, stable_key, name, series_code, product_type, market_flag,
               canonical_link_id → links, spec_source_summary, run_id → runs
               UNIQUE (site_id, stable_key, run_id)

family_assets  family_id → families, link_id → links, role, decision (keep / drop / unsure),
               reason, variant_scope (NULL = whole family, else list of variant ids), run_id → runs
               PK (family_id, link_id, run_id)

variants       id PK, family_id → families, sku, size, page_link_id → links, run_id → runs

spec_values    id PK, family_id → families, variant_id → variants NULL (= family level),
               field, value JSONB, unit, conditions, display_source (page / pdf),
               cross_check (agree / refines / conflict / pdf_only / page_only),
               is_alt BOOL (true = page value kept beside a displayed sheet value), run_id → runs

spec_sources   spec_value_id → spec_values, link_version_id → link_versions, quote, page, section

prices         id PK, family_id → families NULL, variant_id → variants NULL
               (exactly one set; family only when the family has no variants),
               availability, amount, currency, price_type, unit_of_measure, pack_qty,
               min_order_qty, effective_date, price_list_id, notes,
               link_version_id → link_versions, quote, run_id → runs
```

## 3. Why it's shaped this way (lessons from the evaluation runs)

| Design choice | Reason |
|---|---|
| `page_links` edge table instead of a `found_on` column | One shared spec sheet can be linked from dozens of SKU pages. Those relationships are the main evidence for grouping families (the Sioux Chief failure: 6,270 predicted families vs 700). |
| `link_versions` with `sha256`, `blob_path`, `text_blob_path` | Every value can be traced to the exact copy it came from, and its `quote` checked against the stored text (the evidence rule enforced by the harness today). Unchanged files aren't stored twice. |
| `facts JSONB` on versions | Page facts (breadcrumb, lang, canonical, schema.org product, has_spec_table) and file facts (doc_type, lang, revision date, image width/height/phash) describe one specific version. |
| `spec_values` + `spec_sources` | A field can be stated by the page and the spec sheet (agree / refines / conflict). The displayed value, the page's alternative (`is_alt`) and every source quote must all be kept (SPEC 6a). |
| `variant_id NULL` on `spec_values` | Family-level values vs per-variant overrides (SPEC 6). |
| `prices` on family **or** variant | Families without variants still report their price status (SPEC 7 `family_prices`). |
| `family_assets.decision` + `reason` | The evidence-based keep/drop step (the other main gap-analysis fix) stays auditable, including what was rejected. |
| `run_id` on all derived rows, `stable_key` on families | Periodic reprocessing doesn't overwrite history: runs can be compared, a bad run rolled back, and family identity stays stable across runs. |
| `first_seen` / `last_seen` / `gone_at`, `etag` / `last_modified` | Collector and processor work incrementally: only new or changed links are reprocessed. This is essential at thousands of sites. |
| `sites.status` | Blocked or paused sites are visible, not silently empty. |

## 4. Key behaviours
- **Incremental processing:** the processor selects sites with links whose `last_seen` or newest `link_versions.fetched_at`
  is later than its last completed run for that site, and reprocesses only the affected families.
- **Re-runnable:** processing the same inputs twice produces the same rows (stable keys + content hashes); a run is
  written in full, then marked complete in `runs`.
- **Current view:** a view (or materialised view) per derived table selects rows from each site's latest completed
  process run. Apps read the views, not raw rows.
- **Health checks** update `links.status/last_checked/etag`; a changed `etag` or `sha256` creates a new `link_versions`
  row and queues the families that use that link.
- **Evaluation stays file-based:** an exporter writes a site's current view as SiteRun JSON, so the harness and answer
  keys keep working unchanged.

## 5. Mapping from the proof-of-concept files
| PoC file / field | Table |
|---|---|
| Link records (`OLD_AGENT_IMPROVEMENTS.md`), `record: "page"` | `links` (url, status…) + `link_versions` (facts, `html_snapshot` → `blob_path`) |
| Link records, `record: "link"` | `links` (target) + `page_links` (`found_on`, `link_text`, `section`, `in_chrome`, `link_kind`) |
| SiteRun `families[]` | `families` |
| `families[].documents / cad / images` | `family_assets` (+ `link_versions.facts` for doc_type, lang, sha256, width/height/phash) |
| `families[].variants[]` | `variants` |
| `families[].specs` and `variants[].spec_overrides` | `spec_values` (+ `alt_values` → rows with `is_alt`) and `spec_sources` |
| `variants[].prices`, `families[].family_prices` | `prices` |
| Evidence `files/` and `text/` | blob storage via `blob_path` / `text_blob_path` |

## 6. Migration path (after the proof of concept)
1. Create the tables; write a loader from the PoC's JSONL/SiteRun files (section 5) and load one site end to end.
2. Put the processor behind a small storage interface (read changed pages/links, write a run), with a file backend and a
   Postgres backend; keep scoring via the SiteRun exporter.
3. Upgrade the old agent to write `links`, `page_links` and `link_versions` directly.
4. Schedule the three services; add the incremental and health-check behaviours (section 4).
