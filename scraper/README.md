# mfr-scraper (v0.1)

Site-agnostic manufacturer product scraper. Given a manufacturer's homepage, it finds product
families and extracts spec sheets, CAD, the best image versions, specs (cross-checked page vs PDF),
and price status. Output is a SiteRun JSON in the harness format (`../harness/schema/`), so it is
scored against the answer keys with no conversion.

v0 is fully deterministic: no LLM. Every spec value carries a verbatim quote and a snapshot of
its source, and the harness checks that each quote appears in that snapshot.

## Usage
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m mfr_scraper discover --site bray              # product templates + URL count
.venv/bin/python -m mfr_scraper run --site bray --limit 5 --out runs-dev   # quick dev sample
.venv/bin/python -m mfr_scraper run --site bray                   # full site -> ../harness/runs/bray.json
.venv/bin/python -m mfr_scraper run --site acme --input-url https://www.acme.com/   # ANY manufacturer: URL only
.venv/bin/python -m unittest discover tests                       # offline tests

# validate / score with the harness
cd ../harness
python -m mfr_harness.validate runs/bray.json --site bray --evidence runs/bray.evidence
python -m mfr_harness.score --site bray --gold gold/bray.json --pred runs/bray.json
```
Sites in the **test** and **challenge** splits are refused unless `--allow-holdout` is passed.
Only pass it for final evaluation, never while tuning the scraper.

## Pipeline
| Stage | Module | What it does |
|---|---|---|
| Fetch | `fetch.py`, `robots.py` | robots.txt parsed per RFC 9309 for sitemaps and Crawl-delay; **Disallow is not obeyed (SPEC 1a)**, and each overridden URL is counted in `run_stats.robots_overridden`. 1 req/s per host (or Crawl-delay); retries; size caps; disk cache = raw store. Blocks and errors are not cached. |
| Hosts | `hosts.py` | Only the homepage URL is needed. Page hosts = its registrable domain (+ subdomains). Asset hosts = other hosts serving files on ≥25% of product pages, minus third-party services. The configured list is only an override (`--use-config-hosts`) and, for evaluation sites, the reference. Product pages that redirect off-site are dropped. |
| Discover | `discover.py` | Sitemaps (recursive, gz) **plus** a bounded menu crawl from the homepage (depth 3, 150 pages); sitemaps are often incomplete. URLs grouped into **templates** by path shape. A few pages per template are scored for product signals (schema.org Product, spec label/value pairs, spec downloads, breadcrumbs; listing pages penalised). |
| Page extraction | `page.py`, `specs.py` | Generic label/value extractor (tables, `dl`, div pairs, `label` + div), skipping header/footer/nav. Labels mapped to schema fields by synonym; values parsed (sizes + `size_unit`, psi/bar/PN, °F/°C, certifications, standards). `end_connections` and `applications` are mapped to the SPEC 6 controlled vocabularies; unmapped wording goes to `additional_specs`. schema.org Product/Offer for SKU and price; wording for `login_required` / `request_quote`. |
| Documents & CAD | `assets.py` | PDFs downloaded, `%PDF` verified, sha256, text + table rows via **pdfplumber** (MIT), language by stopwords (`en+fr` when English leads), doc_type from URL/link text/title, then first-page text. CAD by extension; zips opened and their CAD formats listed; viewer hosts become `cad_viewer`. |
| Images | `assets.py`, `pipeline.py` | Candidates from `img`, `srcset`, links around images, and schema.org. Grouped by rendition key; the largest/original version is fetched (resized URLs get original-URL guesses); <300 px dropped; perceptual-hash duplicates collapsed. |
| Site chrome | `pipeline.py` | Documents/images on more than 20% of sampled pages (footer PDFs, logos) are excluded; images shared by 3+ families are treated as non-specific. |
| Spec merge | `pipeline.py` | Per field: spec sheet/submittal PDF > page > other PDF. Only PDFs that name the family (series code or distinctive name words) supply values. Page vs PDF compared with the harness's comparators → `agree` / `refines` (sheet is a more specific form) / `conflict` (contradiction; sheet value shown, page value in `alt_values`) / `pdf_only` / `page_only`. |
| Families | `pipeline.py` | Pages that differ only by size tokens under the same parent category are grouped as variants of one family; otherwise one page = one family. |
| Output | `pipeline.py` | `<out>/<site>.json` (SiteRun), `<site>.csv` (url, url_type, family_id), `<site>.evidence/` (files, text, manifest). |

## Known limits of v0 (what the answer keys should tell us about)
- **No browser mode yet.** Sites that return 403 to plain HTTP (e.g. Dixon) are reported as blocked.
  Next step: a Playwright fetch mode at the same slow rate, with no bot-protection workarounds.
- **No LLM fallback.** Pages without label/value structure, specs only in prose, and image-only spec
  tables are missed. The LLM goes behind an interface once scores show where the rules fall short.
- **Variants** come only from schema.org SKUs or from grouping SKU-level pages; series pages with a
  size table do not yet produce variants, so price status on those families is reported only as a flag.
- **PDF tables:** 2–3 column rows and `Label  value` lines are used; per-size multi-column tables are not yet mapped to variants.
- **Conflict noise:** on Bray (78 families) the run reports 206 conflict, 15 refines and 27 agree fields. Many conflicts are pages listing several materials or options where the sheet lists one. The Bray answer key will show which are real.
- **No incremental mode yet** (lastmod / ETag / hash diffing, comparison with the previous run).
  The cache already prevents re-downloading during development.
