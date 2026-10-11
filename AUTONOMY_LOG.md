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

## 2026-10-11 02:58 · Phase 1 · Crane first pass done; blind re-label launched
- Labeller 7a66dd43… pushed `gold/crane-auto` (408d7c1 `spec:`, e78609d gold): validator 0 errors / 15 warnings
  (market_flag `non_na` for a UK site whose URLs have no locale prefix). Family index: sitemap 217, crawl 216, both 216,
  sitemap-only 1 (`/product/uncategorized/commpac/`), crawl-only 0. Coverage swap D15 → FM638/FM639 (3 multi-variant
  families). Bimstore BIM links (account needed) → crane `cad_viewer_hosts`.
- Blind sample: f621, 257, 140, f634, d171aexs, d103b-cast-iron. Blind session
  https://outpostai.devinenterprise.com/sessions/cb0b968126bd4643bb5b75a4458f4f20 (branch `blind/crane`).

## 2026-10-11 02:58 · Phase 2 · Round 1 (baseline) — Bray only (Crane/Apollo keys not merged yet)
- Code: auto/integration before any scraper logic change. Full Bray run; validation 0 errors / 22 warnings.
- Scored on the updated Bray key (SPEC 4/5/6/7 consistency pass merged):
  family recall 97.1 · precision 82.0 · primary doc recall 61.0 / precision 100 · image recall 80.5 · spec accuracy 64.8 ·
  completeness 84.4 · variant recall 0 · price availability 0 · conflict precision 10.7.
- Matches the AUTONOMOUS_RUN baseline within 3 points (doc recall 64 → 61 and image 82 → 80.5 are due to the key's
  SPEC 4/5 re-check adding documents/images).
- Run flags: price_status_without_variant 119, pdf_cap_reached 32, site_chrome_document_skipped 248, 5 product pages
  redirect off-site.

## 2026-10-11 02:58 · Phase 2 · Round 2 hypothesis — variants from identifier tables + family_prices
- What fails: variants 0% and price availability 0%. The scraper only makes variants from schema.org SKUs or grouped
  SKU pages; Bray lists identifiers in spec-sheet rows ("SRH Model # SRH1 SRH2 SRH3") and has no variant field for the
  12 identifier-less "Request a Quote" families, whose status was only a flag.
- General fix (helps an unknown manufacturer because model/part-number tables and quote-only pages are the two most
  common ways manufacturers publish orderable items and price status): new `variants.py` reads (a) rows labelled with
  an identifier heading (Model #, Part No., Catalog No., SKU, Order code…) followed by ≥ 2 identifiers and (b) tables
  with an identifier column (with a size column → variant.size), from the family's pages, else its own spec sheets;
  bare "Item"/"Part" (parts lists) and dimension tables are rejected. Page price status is attached to each variant;
  families with no variants get `family_prices` (SPEC 7). Tests: TestVariants (3).
- Expected: price availability 0 → ~80+ (12 family_prices + SRH variants), variant recall 0 → ~20 (SRH 3 of 14).

## 2026-10-11 03:01 · Phase 1 · Cimberio key final (blind compared) — merged
- `gold/cimberio-auto` f77382c merged (47bf4cc). Gold validator 0 errors / 8 warnings (`refines` on material_body,
  HARNESS_ISSUES); harness tests OK. Orchestrator did not open the key (held-out): only the validator summary line,
  the non-gold diff (sites.json allowed host, HARNESS_ISSUES) and the labeller's report were looked at.
- Blind agreement, 6 families (BEFORE raw blind vs first pass 75b1ffd → AFTER vs final): family spec fields 47/58 (81%)
  → 47/57 (82%); documents found 9/14 → 9/14 (the blind labeller missed the public List Price Book on /resources/; kept
  because its part numbers match the variants); variants 27/27; images 9/9; CAD 2/2; cross_check 91% → 80% (SPEC 5
  made TechDataSheet-778_v5, 8 pages / 14 models, a catalog, so size fields became page_only); material_body 1/6
  (punctuation/word order only; gold copies sheet wording); standards 1/6 (Annex G statement).
- Spec-field agreement ≥ 80%, so no SPEC clarification round. Labeller's top ambiguity "price-list PDF price vs
  Request a Quote on the page" is recorded for REPORT.md.

## 2026-10-11 03:19 · Phase 1 · Apollo blocked — no answer key
- Labeller 1501569f… (02:31–03:15 UTC, ≤ 1 req/s): every URL on aalberts-ips.us incl. robots.txt and sitemap.xml returns
  a LiteSpeed reCAPTCHA "Bot Verification" page, for the descriptive-UA client and the VM's normal Chrome alike;
  aalberts.compano.com root redirects to a Compano login. No challenge solved, no archives/distributor copies (rule).
- Decision: no apollo.json (an empty key fails `validate --gold` and would make Apollo look scorable). Treated like
  Dixon. Branch `gold/apollo-auto` merged for the record (block evidence text, brand rule, sample script,
  HARNESS_ISSUES; conflict in HARNESS_ISSUES.md resolved by keeping both sections).
- Consequence: the dev sites with keys for Phase 2 are Bray and Crane.

## 2026-10-11 03:19 · Phase 1 · Crane key final (blind compared) — merged
- `gold/crane-auto` ad64c1f merged (26084e5); validator 0 errors / 15 warnings (UK `market_flag`); tests OK.
- Blind agreement (BEFORE blind vs e78609d → AFTER vs ad64c1f): family spec fields 50/64 (78%) → 60/63 (95%);
  documents found 20/29 → 29/29; images 1/33 → 17/17; doc_type 100%; variants 10/10; cross_check 82% → 92%.
- Below 80% before fixes; root cause `standards` (0/6: conformance-only vs incl. thread/flange standards) → SPEC
  clarified (48ccaa4), `standards` re-labelled in all 15 families, re-measured once (95%).
- SPEC changes: SPEC 3 option codes are not variants; parallel BSP threads (G, ISO 228, BS 2779) → `threaded`;
  standards scope; PN/class designations. Images were 1/33 because the first pass used unlinked originals — fixed by
  the SPEC 4 "use only image URLs the page links" rule. bimstore.co(.uk) added as CAD-viewer hosts (account-gated BIM).

## 2026-10-11 03:19 · Consistency pass launched (every gold file follows every SPEC change)
- Three labeller sessions — bray 9a49e8a2…, sioux-chief 6e24e99f…, cimberio c47e5409… — branches
  `gold/<site>-consistency`: apply SPEC 3 option codes, SPEC 4 image edge cases, SPEC 5 classify by content, SPEC 6
  strictness/threads/standards/PN, SPEC 7 family_prices, logging every change. Crane already follows all of them.

## 2026-10-11 03:19 · Phase 2 · Round 2 Bray result; Crane being added
- Bray r1 → r2: variant recall 0 → 21.4, price availability 0 → 53.8; every other key metric unchanged; validation
  0 errors; 0 crashes. Crane baseline (r1 code, separate worktree, shared cache) running, then r2 code on Crane,
  before the keep/revert decision (the rule needs every dev site with a key).

## 2026-10-11 03:20 · Phase 2 · Round 3 hypothesis — per-family PDF cap drops primary documents
- What fails: Bray primary-document recall 61% (25/41). Of 16 missed primary docs, 13 were never fetched; 11 belong to
  families whose pages link more than 10 PDFs (e.g. one datasheet per model on single-door check valves, 10 of ≥ 18
  fetched). `MAX_PDFS_PER_FAMILY = 10` stops after 10 even with primary-looking links sorted first; run flag
  `pdf_cap_reached` fired on 32 families. The same cap hides the datasheets that list variant identifiers.
- General fix: raise the cap to 30 (still bounded; it only costs crawl time at 1 req/s). Test: TestPdfCap.
- Bookkeeping: round 2 candidate committed on local branch `round/2` (a8db6a8, worktree ~/wt-r2) so Crane can be
  scored with exactly the round 2 code while the round 3 Bray run (r2 + cap) uses a different host in parallel.
  Rounds are still judged one at a time against the previous kept state.

## 2026-10-11 03:23 · Consistency pass · Cimberio merged
- `gold/cimberio-consistency` 5e26384 merged (d4557a7); validator 0 errors / 8 warnings (unchanged); tests OK.
  Changes: Standards scope 10 (spelling as the sources print it); SPEC 3, BSPT/threaded, PN/class, SPEC 4/5/6/7: 0.
- New `spec:` commits: 878f517 (standards keep each source's spelling; spacing/hyphen-only differences are the same
  standard when cross-checked), aecaeb9 (a PN describing only a flange connection is not the pressure rating when the
  source states a working pressure). Sent to the bray and sioux-chief consistency sessions; crane labeller asked to
  apply them on `gold/crane-consistency`.
- Problem: my earlier HARNESS_ISSUES.md conflict resolution (apollo merge) left diff3 base-marker lines
  `||||||| e34e4bf`; my sed removed only <<<<<<< / ======= / >>>>>>>. Removed them now; future conflict resolutions
  also strip `|||||||` lines.

## 2026-10-11 03:24 · Consistency pass · Crane merged
- `gold/crane-consistency` 6848b24 merged; validator 0 errors / 15 warnings (unchanged); tests OK. Standards spelling
  (878f517): 8 changes in 7 families (e.g. `ISO 228` → `ISO-228` as printed), no cross_check change; flange-only PN
  (aecaeb9): 0. The large crane.json line diff is re-serialisation; the parsed JSON differs only in the logged values.

## 2026-10-11 03:26 · Consistency pass · Bray merged; earlier rounds re-scored
- `gold/bray-consistency` e5eb473 merged; validator 0 errors / 0 warnings; tests OK. 13 changes: SPEC 3 (SA16
  accessory's 205/211/212 are single-door models → `additional_specs.models`, family_prices request_quote), standards
  scope 3, PN/class 3 (Tri Lok-Cx 40 bar, Tri Lok 150 bar, Single Door 40 bar), standards spelling 5.
- New `spec:` cb6232e (accessory pages listing another family's models; highest PN when several) → sent to the
  sioux-chief session and to the crane/cimberio labellers (`gold/<site>-consistency2`).
- Key changed, so every stored Bray run was re-scored on it (rule: compare rounds on the same key):
  r1 → r2: specs 65.6 → 65.6; variant recall 0 → 27.3; price availability 0 → 62.5; all other metrics unchanged.

## 2026-10-11 03:27 · Consistency pass · cb6232e on Crane and Cimberio
- `gold/crane-consistency2` (2d171f5) and `gold/cimberio-consistency2` (d356fd9) merged: cb6232e changes nothing
  in either key (log entries only). Validators unchanged (crane 0/15 warnings, cimberio 0/8). Sioux Chief pending.

## 2026-10-11 03:28 · Consistency pass · Sioux Chief merged — Phase 1 + consistency pass complete
- `gold/sioux-chief-consistency` 068fc93 merged (33c639c); validator 0 errors / 8 warnings (pre-existing sibling-SKU
  photo pairs); tests OK. Orchestrator did not open the key (held-out). 20 changes: SPEC 3 option suffix lists 2,
  SPEC 5 classify by content 10 (brochures with ordering tables → catalog), standards spelling 8; others 0; no `spec:`.
- State of keys: bray (dev/train, 15 labelled), crane (15), cimberio (held-out, 15 labelled of 32), sioux-chief
  (held-out); apollo and dixon blocked (no keys); milwaukee and caleffi have no keys in this repo (no labeller task for
  them in AUTONOMOUS_RUN Phase 1), so the Phase 4 final test covers sioux-chief and cimberio.
- Every gold file now follows every SPEC paragraph added in this run.

## 2026-10-11 03:37 · Phase 2 · Round 3 Bray result (Crane pending)
- Bray r2 → r3 (cap 10 → 30): primary doc recall 61.0 → 92.7 (precision 100), specs 65.6 → 66.3, completeness
  84.4 → 85.2, conflict precision 10.7 → 12.9; other metrics unchanged; validation 0 errors; 0 crashes;
  `pdf_cap_reached` no longer fires. doc_type accuracy 76 → 79.
- Still missing: single-door check-valve variants (8 gold identifiers) are not extracted even though its datasheets are
  now fetched → next variant hypothesis.

## 2026-10-11 03:38 · Phase 2 · Round 4 hypothesis (stacked on r3, pending r2/r3 decisions)
- Gap: Bray single-door check valve has 8 gold variants (201, 203, …, 312) but r3 extracts none. The page's spec block
  renders as a label line `Models` followed by a value line `201, 203, 205, 210, 211, 212, 260, 312`; r2's line
  pattern only matched label and identifiers on one whitespace-separated line.
- Change (general): `variants.from_lines` also accepts an identifier label line followed by a line of ≥2
  identifiers, and comma/semicolon separators on the same line. Prose or short numbers after the label are rejected
  by the existing identifier test. Tests: `TestVariantHeadingLists` (3). Snapshots: round/2 a8db6a8, round/3 6dc9739
  (worktrees ~/wt-r2, ~/wt-r3) so each round is scored on both dev sites separately.

## 2026-10-11 03:53 · Phase 2 · Round 1 baseline on Crane (pre-candidate code, worktree ~/wt-r1)
- Full-site run, 218 families, 0 crashes, validation 0 errors / 220 warnings.
- Crane r1: family R/P 100/100, primary docs R/P 100/100, images 78.0, specs 42.2, completeness 64.2, variants 0,
  price availability 0, conflict precision 0. Macro (bray+crane) r1: fam R 98.5, fam P 91.0, docs R 80.5,
  images 79.3, specs 53.9, completeness 74.3, variants 0, price 0, conflict 5.4.

## 2026-10-11 03:54 · Phase 2 · Round 4 first attempt regressed → reworked
- Bray r3 → r4 (heading-list pattern only): variant recall unchanged at 27.3, price availability 62.5 → 58.3. Root cause:
  (1) single-door never reached the table extractor because the v0 fallback made placeholder "variants" from its URL
  slug (`SINGLE-DOOR-CHECK-VALVE` ×2; also `SERIES-752-752HP-…`, `SERIES-39-…`); (2) the new pattern took
  `205, 211, 212` from the SA-16 accessory page, which lists models of the check valve (SPEC 3 accessory rule).
- Rework (general): a URL tail is only used as an identifier if it passes the identifier test (has a digit, ≤25
  chars), duplicates within a family are dropped; post-pass `accessory_families`: a family whose identifiers are a
  strict subset of another family's loses them and keeps its price status in `family_prices`. Tests:
  `TestVariantPlaceholders` (2). Re-running Bray as r4b.

## 2026-10-11 04:08 · Phase 2 · Round 2 decision: KEPT (merged round/2 → a0ecc22)
| metric | bray r1 | bray r2 | crane r1 | crane r2 | macro r1 | macro r2 |
|---|---|---|---|---|---|---|
| variant recall | 0 | 27.3 | 0 | 22.2 | 0 | 24.7 |
| price availability | 0 | 62.5 | 0 | 16.2 | 0 | 39.4 |
| all other key metrics | = | = | = | = | = | = |
- Macro gain ≫ 1 point, no metric dropped on either site, validation 0 errors (crane 220 warnings, bray 23),
  0 crashes, 36 tests OK incl. generality. Crane r2 variant precision 46% (D103B tables over-collect codes of the
  sibling cast-iron family) and crane variant-less families have no `family_prices` (gold: `not_published`) —
  logged as next gaps. Apollo: no key (blocked), so dev = bray + crane.
- Bray r4b (r3 + reworked r4): variant recall 27.3 → 100 (precision 100), price availability 62.5 → 95.8, others
  unchanged. Awaiting crane r3/r4b before deciding r3 and r4.

## 2026-10-11 04:09 · Problem · committed cache symlink wiped the scraper cache (self-healed)
- Root cause: worktrees got `scraper/cache` as a symlink to the main cache; `.gitignore` had `scraper/cache/`
  (trailing slash matches directories only), so `git add scraper` in ~/wt-r2 committed the symlink. Merging round/2
  replaced the main (ignored) cache directory with that symlink — a self-loop — so the HTTP cache was lost and
  crane r3 crashed on every page (crash isolation kept the run alive; run discarded).
- Results already harvested (bray r1–r4b, crane r1–r2) finished before the merge and are unaffected.
- Fix: symlink untracked, `.gitignore` → `scraper/cache`, real cache dir recreated; test
  `TestRepoHygiene` fails if any symlink or anything under scraper/cache is tracked. Later runs re-fetch at
  1 req/s (live pages may differ slightly from the earlier rounds' fetches; noted as a comparability risk).

## 2026-10-11 04:10 · Phase 2 · Round 5 hypothesis (stacked on r4: round/4 = d6df3f2 in ~/wt-r4)
- Gap: crane price availability 16.2: 10 of 15 gold families are variant-less with `family_prices`
  `not_published`, but the scraper only emitted `family_prices` when a status other than not_published was
  shown. SPEC 7 says availability is always filled.
- Change (general): every variant-less family gets `family_prices` from `family_price_page` (first page with a
  published status, else the main page → not_published); the accessory post-pass keeps a not_published status too.
  Test: `TestFamilyPriceAlwaysFilled`.

## 2026-10-11 04:20 · Phase 2 · Round 6 hypothesis (stacked on r5: round/5 = 5e37c4a in ~/wt-r5)
- Gap: crane temperature accuracy 15%. Pages state "-10 - 120°C" / "-10 to 120°C" with the unit only on the upper
  bound; `parse_temperature` only saw "- 120°C" and produced `{min: null, max: -120}` (wrong sign, lost min).
- Change (general): a range pattern "A (-|to) B °unit" with optional signs is parsed first (only if A ≤ B); else the
  old per-reading logic. Test: `TestTemperatureRangeUnitOnce` (6 cases incl. the unchanged formats).
- Queued next gaps (crane): `sizes_available` never filled from size columns of dimension tables (15/15 missing);
  PDF row "TEMPERATURE (°C) -10 to 120" not read; applications from "potable water"/"chilled water" prose.

## 2026-10-11 04:26 · Phase 2 · Round 7 hypothesis (stacked on r6: round/6 = 7d3f2d1 in ~/wt-r6)
- Gap: crane `sizes_available` 0% (15/15 missing), size_range/size_unit missing on 8 families: spec sheets give sizes
  only as the first column of a dimension table headed "SIZE (mm)" / "SIZE (inch)" / "SIZE (DN)"; pdfplumber merges
  some rows ("65 80").
- Change (general): `specs.sizes_from_tables` reads the first table on a sheet whose first header cell is a size
  heading, collecting each size token of the first column until a non-size row; unit from the heading. Emitted as a
  sheet candidate for sizes_available (and size_range/size_unit if absent). Tests: `TestSizeColumnTables` (2).

## 2026-10-11 04:39 · Phase 2 · Round 5 Bray result (cold cache)
- Bray r5 (r3+r4+r5, pages re-fetched after the cache incident): identical key metrics to r4b — so the re-fetch did
  not shift Bray scores, and r5 has no effect on Bray (its not_published family statuses are already scored via
  variants/family_prices). Validation 0 errors / 23 warnings, 0 crashes.
