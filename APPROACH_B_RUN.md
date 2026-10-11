# Approach B run: old-agent links in, product index out

Owner is away. You (Devin) run this unattended. **Re-read this file at the start of every phase.** All rules in
`AUTONOMOUS_RUN.md` section 0 (evaluation integrity, crawling, repository) still apply unless this file overrides
them.

**Override of `AUTONOMOUS_RUN.md` rule 6 (blocked sites).** The old agent's output for sites that block automated
access (e.g. Dixon, Apollo) is **valid input** and is used like any other site's. Our own components make ordinary
requests at the polite rate. When a request is blocked (403/429/challenge page), record the status on that item,
don't retry it, and continue with the data the old agent supplied. Log every decision and every round in `AUTONOMY_LOG.md` under a new heading "Approach B".

## Why
The first autonomous run (PR #4, `REPORT.md`) showed:
- the old agent finds ~98–100% of the right links;
- the new scraper finds and structures well on familiar layouts but drops most of what it misses with its own filters
  (83% of misses were on pages it had crawled);
- it treats one-page-per-part-number sites as one family per page.

**Approach B:** the old agent is the discovery stage; a **processing layer** turns its links into the SPEC product
index (families, variants, documents, CAD, images, specs, cross-checks, prices). The old agent will soon emit extra
"free" fields (`OLD_AGENT_IMPROVEMENTS.md`). The processing layer must use them when present and work without them.

**Question to answer:** with the same answer keys, does Approach B beat (a) the current scraper and (b) the old agent,
on development sites **and** on held-out sites it was never tuned on? And how many requests does it cost?

---

## 0. Setup and evaluation split
1. Branch `approachb/integration` from the latest `main`. Do not push to `main`. Open one PR at the end; don't merge it.
2. **New evaluation split** (Sioux Chief and Cimberio were exposed by the first final test, so they can't be held out
   again). Update `harness/config/sites.json` and log it:

   | Role | Sites |
   |---|---|
   | **dev** (tune here) | `bray`, `crane`, `sioux-chief`, `cimberio` |
   | **held-out** (final test once) | `milwaukee`, `caleffi` |
   | **old-agent-only** (no key; processed from old-agent data, not scored) | `apollo`, `dixon` |

   Use `split: "dev"` for dev and `split: "test"` for held-out sites, so the existing `--allow-holdout` guard covers them.
3. Old-agent inputs already in the repo: `train/bray/output.csv`, `train/crane/output.csv`,
   `test/sioux-chief/output.csv`, `challenge/cimberio/output.csv`, `test/milwaukee/output.csv`,
   `challenge/caleffi/output.csv`, `dev/dixon/output.csv`, `challenge/apollo/output.csv`. These are **inputs**, not answer keys; any phase may read them.

---

## Phase 1: held-out answer keys (labeller role)
Build answer keys for **Milwaukee** and **Caleffi**, following `harness/DEVIN_TASK.md` and the labeller rules in
`AUTONOMOUS_RUN.md` (no checkpoint wait; self-review and log; blind re-label of 6 families with before/after agreement;
clarify SPEC and re-label if before-fix spec agreement < 80%, at most twice).
- **Independence:** the labeller must not open `scraper/`, any processing-layer code, or any run output. Use separate
  Devin sessions for labelling if you can. Otherwise finish Phase 1 completely **before** opening any engineering code.
- Caleffi is multilingual: apply SPEC 2 (prefer en-US/en-CA, then en, then international English with `non_na`).
- If a held-out site can't be loaded for labelling, log it and drop it from the held-out set (an answer key needs the
  live pages).
- Merge each validated key (0 errors) into `approachb/integration`.

## Phase 2: the link-record format and the emulator (engineer role)
1. Add `harness/schema/link_record.schema.json` implementing `OLD_AGENT_IMPROVEMENTS.md` exactly: `page` and `link`
   records, field names, `url_type` label set, normalised `url`. Add a validator command for link files and tests.
2. **Readers for two input levels:**
   - **L0, legacy:** the current `output.csv` (`url, url_type` only).
   - **L1, enriched:** `<site>.links.jsonl` per the schema.
3. **Emulator** (`scraper/mfr_scraper/emulate_agent.py` or similar): produces L1 records **as the improved old agent
   would**. Rules that keep it honest:
   - It fetches **only** the HTML pages the old agent's CSV lists as pages (plus the homepage), i.e. the pages the old
     agent itself visited. It must not discover new pages.
   - It records only the "free" fields: link and page facts visible in those pages and their HTTP responses.
   - It **never** downloads PDFs, images or CAD files.
   - Its request count must stay within the old agent's page count +1. Log the counts.
4. Produce L1 files for all dev and held-out sites. Save them under `harness/runs/linkrecords/` (git-ignored like other runs)
   and record their counts in the log.

## Phase 3: the processing layer (engineer role)
A new module (e.g. `scraper/mfr_scraper/process/`), entry point
`python -m mfr_scraper process --site <s> --links <file> [--level L0|L1]`, writing a SiteRun JSON scored by the existing harness.
**Reuse** the existing extraction code (spec parsing, vocabularies, PDF parsing and caching, cross-check merge, evidence,
output) rather than duplicating it.

Steps, each **site-agnostic**:
1. **Ingest and tag.** Normalise URLs; tag language copies (`lang`/`hreflang`/URL locale), chrome links, off-site
   redirects, renditions. **Tag, don't drop yet.**
2. **Edges.** L1: page → asset edges come from `found_on`. L0: fetch each product-candidate page once to build edges,
   and **count these requests separately** (the cost of not having `found_on`).
3. **Page roles.** Classify pages as product / listing / other using evidence: `has_spec_table`, `jsonld_product`,
   breadcrumb depth, `n_links_same_section`, product-specific downloads. L0 derives these by fetching.
4. **Family grouping.** This is the key new capability. Merge product pages into one family when they share evidence:
   - the same spec sheet or submittal (strong): a PDF linked from a small set of pages that also share a breadcrumb
     parent or title stem. A catalog linked from many unrelated pages must **not** merge families;
   - the same breadcrumb leaf plus a common identifier stem (e.g. `640WP02`, `640WP03`);
   - "other sizes", "related sizes" or variant-selector blocks linking the pages to each other.

   Each grouped page becomes a **variant** (identifier, size, page URL, price status). A page that is already a whole
   family stays one family (Bray, Crane). Record the evidence behind each merge in the output (e.g. in
   `site_profile`) so that grouping errors can be audited.
5. **Asset decisions by evidence, not location.** For each candidate asset on a family's pages:
   - follow it on **any host** (polite rate; a blocked request is recorded, not retried);
   - keep a shared file if its text or link names the family or its identifiers;
   - drop chrome only when it is genuinely site-wide **and** doesn't name the family.

   Every asset gets `keep` / `drop` / `unsure` with a reason. Write rejected and unsure items to
   `<site>.decisions.jsonl` for auditing.
6. **Documents** typed by SPEC 5 (content first), using `link_text` and `section` from L1 as strong hints.
7. **Images:** use `srcset`, `wrapping_link` and `width`/`height` from L1 to pick the largest version before downloading;
   download only the chosen version (for dimensions and phash). SPEC 4 rules.
8. **Specs, cross-check, prices** via the existing code: page values from fetched product pages (L0) or pages the
   emulator saved (L1; store page HTML snapshots for evidence), PDF values from spec sheets, SPEC 6/6a/7.

## Phase 4: improvement loop on dev sites
Same loop and keep rule as `AUTONOMOUS_RUN.md` Phase 2, over the 4 dev sites, with 3 systems scored side by side each round:

| System | Command |
|---|---|
| A (current scraper) | `python -m mfr_scraper run --site <s>` |
| B-L0 (legacy CSV in) | `python -m mfr_scraper process --site <s> --links <split>/<s>/output.csv --level L0` |
| B-L1 (enriched in) | `python -m mfr_scraper process --site <s> --links runs/linkrecords/<s>.links.jsonl --level L1` |

- Tune **B** (the processing layer). Don't spend rounds on A; it's the baseline.
- Keep rule: the B-L1 macro average over the 4 dev sites improves by ≥ 1 point, no dev site drops more than 2 points on any
  key metric, tests pass, and validation shows 0 errors. Stop at targets (as in `AUTONOMOUS_RUN.md`), after 3 rounds under
  1 point, or after 12 rounds.
- Also record **requests per site** and wall time for each system. Approach B's case rests partly on cost.
- Also fix these two notes from the PR #4 review:
  - derive the parsed-PDF cache version automatically from the extraction code (e.g. a hash of `assets.pdf_text`'s
    source and its settings) instead of a hand-bumped `PARSER_VERSION`;
  - make peak-memory reporting correct on macOS (`ru_maxrss` is bytes there, KiB on Linux).

**Old-agent-only sites (Apollo, Dixon).** Each round, also run B-L0 on their CSVs and check that it completes,
validates with 0 errors, and degrades gracefully where pages or files can't be fetched: families from URL and identifier
evidence, document types from file names and link text, and every blocked item marked. They aren't scored (no key).
Report what B can and can't produce from old-agent data alone, which shows the value of `html_snapshot` and the other
fields in `OLD_AGENT_IMPROVEMENTS.md` for such sites.

## Phase 5: final test (once)
Tag `approachb-pre-final`. Then, on the held-out sites with keys (Milwaukee, Caleffi), run all three systems plus
the old agent (`score.py --legacy`), validate, score and record requests. **No processing-layer changes after this.**
Bugs found are described, not fixed.

## Phase 6: report
`REPORT_APPROACH_B.md`, plain-language summary first:
- the dev and held-out comparison tables: A vs B-L0 vs B-L1 vs old agent, per site and metric, plus requests and time;
- grouping quality: predicted vs key family counts per site, with examples of correct and wrong merges;
- what L1's fields bought over L0 (accuracy and requests), field by field where measurable. This tells the owner which
  `OLD_AGENT_IMPROVEMENTS.md` fields matter most;
- old-agent-only sites (Apollo, Dixon): what was produced from the old agent's data alone, what couldn't be, and why;
- answer-key agreement for Milwaukee and Caleffi;
- SPEC changes made, known weaknesses, and recommendations, including whether to adopt Approach B and where an LLM
  fallback would help (measured, if you tested it; no paid services without approval).

Open the PR `approachb/integration` → `main` with the report as its description. Don't merge it.
