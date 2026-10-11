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
