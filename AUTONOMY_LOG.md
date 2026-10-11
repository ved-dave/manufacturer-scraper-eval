# Autonomy log

Append-only. One entry per decision, round or problem. Times are UTC.

## 2026-10-11 02:30 · Phase 0 · Setup
- Cloned main @ e3d9577, created `auto/integration`. Read AUTONOMOUS_RUN.md, SPEC.md, harness/DEVIN_TASK.md, harness/README.md.
- **Role separation decision:** this (orchestrator) session does harness work and later the engineer role. All
  labelling (Phase 1) runs in separate child Devin sessions that are told never to open `scraper/` or any scraper
  output (Rule 1, preferred option). Blind re-labels run in further separate sessions with no access to the
  first-pass gold. This session does not open held-out gold files (sioux-chief, cimberio, milwaukee, caleffi); it only
  runs the validator on them (error counts) after harness changes, as Rule 3 requires, and merges their branches.
- `scraper/README.md` is read only after the labelling sessions have been launched, so no scraper knowledge can leak
  into the labelling prompts.
- No pre-commit hooks in the repo.

## 2026-10-11 02:45 · Phase 0 · Harness: `family_prices` (decided in AUTONOMOUS_RUN §1)
- Why: SPEC 7 put prices only on variants; families with no identifiers (13 of 15 Bray families, "Request a Quote")
  could not record a price status (HARNESS_ISSUES bray #1).
- Change: optional family field `family_prices` (array of `price`) in the schema; validator checks it like variant
  prices and errors if a family has both variants and `family_prices`; `score.py` scores its `availability` with the
  variant prices (`families_with_gold_family_price` added; `availability_accuracy` is over both); SPEC 7 sentence;
  `_TEMPLATE.json` gains a variant-less family `series-200` showing it.
- Tests: new `TestFamilyPrices` (4 tests). Existing tests unchanged in strength: `gold_fixture()` keeps only the first
  template family by default so their expected numbers still hold; the full template is checked by a new test.
- Result: 20/20 harness tests pass; bray and sioux-chief gold still validate with 0 errors.

## 2026-10-11 02:47 · Phase 0 · Config and repo hygiene
- `apollo` split `challenge` → `dev` (AUTONOMOUS_RUN §1).
- `.gitignore`: `*.evidence/files/` → `**/*.evidence/files/` (the old root-anchored pattern missed
  `harness/gold/*.evidence/files/`, HARNESS_ISSUES sioux-chief #1 / bray #5) and `*.zip` (Rule 9).

## 2026-10-11 02:30 · Phase 1 · Labelling sessions launched (labeller role, separate sessions)
Each child works from `auto/integration`, never opens `scraper/`/runs/reports, pushes its own branch; the
orchestrator merges. First-pass labellers stop after the first pass with the 6 blind families
(`random.Random(42).sample(sorted(15 family_ids), 6)`), then a separate blind session re-labels them, then the
first-pass session compares (before/after agreement) and fixes; < 80% before-fix spec agreement → `spec:` clarification.
| Task | Session | Branch |
|---|---|---|
| Crane key | https://outpostai.devinenterprise.com/sessions/7a66dd4390d44a7d84310c0bbeb111ec | gold/crane-auto |
| Apollo key (Apollo brand only) | https://outpostai.devinenterprise.com/sessions/1501569f7beb45ab935132c541c94241 | gold/apollo-auto |
| Cimberio key (held-out) | https://outpostai.devinenterprise.com/sessions/2298a5a862d04a138d305acd277cf4ad | gold/cimberio-auto |
| Sioux Chief vocabulary pass | https://outpostai.devinenterprise.com/sessions/da2097dccfab4f8dbdbb4c4837e93625 | gold/sioux-chief-vocab |
| Bray blind image/doc_type re-label (6 families from the earlier blind draw) | https://outpostai.devinenterprise.com/sessions/edea5461d1184f10aa77ca1c5893268f | blind/bray-imgdoc |
- Decision: SPEC clarifications made by concurrent labellers are applied to the other sites' gold files by one
  consistency session after all keys are in (avoids five sessions editing each other's gold).
- Decision: Sioux vocabulary pass is mechanical mapping (sources unchanged), so no blind re-label; logged as such.
- From here this session takes the engineer role and opens `scraper/` for the first time (labelling now runs only
  in the separate sessions above).

## 2026-10-11 02:32 · Phase 2 setup · Generality test + crash isolation (engineer role)
- Read `scraper/README.md` and the pipeline for the first time (all labelling runs in separate sessions).
- Added `TestGenerality` (rule 4): fails if any of bray, crane, cranefs, sioux, apollo, aalberts, compano, caleffi,
  cimberio, milwaukee, dixon appears (case-insensitive) in `scraper/mfr_scraper/*.py`. It failed on 9 lines —
  all docstrings/comments (CLI examples `--site bray`, host examples `www.bray.com`, `cdn.siouxchief.com`,
  `aalberts.compano.com`, a Bray sitemap statistic). No code logic was site-specific. Replaced with generic
  examples (`<site>`, `example.com`); test now passes. The test was not loosened to allow comments.
- Self-healing: added `SiteRun.guarded()`; a crash while fetching/parsing one page (`page_crashed`) or building
  one family (`family_crashed`) is flagged with the URL + exception and logged with a traceback, and the run continues.
  Unit test `TestCrashIsolation`. No metric effect expected (infrastructure, not a scored round).
- Round 1 (baseline) Bray run started in the background with the cold cache (1 req/s).

## 2026-10-11 02:37 · Phase 1 · Sioux Chief vocabulary pass merged
- Session da2097dc… pushed `gold/sioux-chief-vocab` (000e486 `spec:` + b744a12 gold). Merged into auto/integration (4f13cc3).
- Orchestrator (now in the engineer role) did **not** open `gold/sioux-chief.json`; it merged by git, read only the
  SPEC.md diff, and ran the gold validator (0 errors, 8 warnings — the known sibling-product near-duplicate image pairs)
  and harness tests (OK). The child's summary message listed the source-wording → term mapping table (vocabulary only).
- SPEC change: SPEC 6 "Mapping strictness" (no context-derived vocabulary terms; hub vs prose joining method;
  slash-separated alternatives record each; fields with no mappable wording are omitted, kept in `*_other`).
  Applies to all sites → consistency pass (Crane/Apollo/Cimberio labellers are told to pull SPEC from auto/integration
  before finalising; Bray is re-checked in the consistency pass together with SPEC 7 `family_prices`).
- No blind re-label (mechanical mapping, sources unchanged), as decided.

## 2026-10-11 02:40 · Phase 1 · Bray blind image/doc_type re-label done; comparison handed to a labeller
- Blind session edea5461… pushed `blind/bray-imgdoc` (6 families, documents + images only, never saw the Bray key).
- Because this orchestrator now holds the engineer role (has read `scraper/`), it does not edit gold. A separate
  labeller session (https://outpostai.devinenterprise.com/sessions/a490187bc4a1439f88014943e4a0f6ce, branch
  `gold/bray-imgdoc-consistency`) computes before/after agreement, fixes gold, clarifies SPEC 5 if < 85%, and applies the
  run's SPEC changes (SPEC 7 `family_prices`, SPEC 6 mapping strictness) to all Bray families.
- Decision: the Bray consistency pass is done before Phase 2 scores are compared across rounds; rounds scored on the
  old Bray key are re-scored on the new key so before/after numbers always use the same key.

## 2026-10-11 02:48 · Phase 1 · Cimberio first pass done; blind re-label launched
- Labeller 2298a5a8… pushed `gold/cimberio-auto` first pass (75b1ffd): validator 0 errors / 8 warnings (`refines`
  heuristic on material_body, logged in HARNESS_ISSUES); family index 32 families, all found by both sitemap and crawl;
  coverage CAD/BIM 3, multi-variant 15, prices shown 13; no swaps. Added `store-herjth7887.mybigcommerce.com`
  (Cimberio's own BigCommerce store, hosts the price-book PDF) to sites.json allowed_hosts.
- Blind sample (Random(42), 6): 778pvw, 30xlc, 1220nl, 778pvws, 747nl, 746. Blind session:
  https://outpostai.devinenterprise.com/sessions/58603f6a53e14b3f9e2fb0aa794dcf75 (branch `blind/cimberio`, never
  opens the cimberio key). Orchestrator did not open any cimberio gold file (held-out).

## 2026-10-11 02:52 · Phase 1 · Bray image/doc_type re-check + SPEC 6/7 consistency merged
- Labeller a490187b… pushed `gold/bray-imgdoc-consistency` (c3c6c20 `spec:`, 89e9113 `gold(bray):`); merged.
- Blind vs key, 6 families (script `harness/gold/bray.blind-imgdoc.compare.py`):
  | Row | Before fix | After fix |
  |---|---|---|
  | Documents | 44/44 (100%) | 44/44 (100%) |
  | doc_type | 32/44 (73%) | 44/44 (100%) |
  | Images | 13/17 (76%) | 15/17 (88%) |
  | image_type | 13/13 (100%) | 15/15 (100%) |
- doc_type and images were below 85% before fixes → SPEC clarified: SPEC 5 "Classify by content" (ordered rules:
  iom_manual incl. safety/SIL and protocol manuals; catalog incl. ordering-code guides and technical manuals > 4 pages;
  spec_sheet ≤ 4 pages with a technical-data block whatever it is called; brochure; other_doc; software/config files
  not recorded) and SPEC 4 "Image edge cases" (product markings/letter markers do not make an infographic; option
  collages count; labellers use only image URLs the page links). Applied to all 15 Bray families (11 more document
  entries changed outside the 6). Series 5000/6000 brochure → spec_sheet, so its sheet values now take precedence.
- SPEC 7: 12 variant-less Bray families now carry `family_prices` (request_quote). SPEC 6 strictness applied.
- Gold validator: 0 errors, 0 warnings; harness tests OK.
- Consequence for Phase 2: Bray round-1 baseline is scored on this updated key.

## 2026-10-11 02:57 · Phase 1 · Cimberio blind re-label done
- Blind session 58603f6a… pushed `blind/cimberio` (c08c7db; validator 0 errors / 0 warnings). Per family spec
  fields / docs / CAD / images / variants: 778pvw 9/2/0/0/3, 30xlc 11/1/0/1/3, 1220nl 8/2/0/2/9, 778pvws 9/2/0/3/3,
  747nl 8/1/1/2/6, 746 10/1/1/1/3. First-pass labeller told to run stage 2 and apply the new SPEC 4/5/6 paragraphs.
