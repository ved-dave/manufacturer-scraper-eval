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

## 2026-10-11 03:00 · Phase 1 · Labelling sessions launched (labeller role, separate sessions)
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

## 2026-10-11 03:10 · Phase 2 setup · Generality test + crash isolation (engineer role)
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
