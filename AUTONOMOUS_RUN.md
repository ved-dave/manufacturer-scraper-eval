# Autonomous run: build answer keys, improve the scraper, run the final test

Owner is away. You (Devin) run the whole process without check-ins, using the rules below to make
decisions yourself. **Re-read this file at the start of every phase and whenever you are unsure.**
Everything you decide goes in `AUTONOMY_LOG.md` (append-only), so the owner can audit it afterwards.

Goal: a single, **site-agnostic** scraper (`scraper/`) that, given only a manufacturer's homepage URL,
produces an accurate product index per `SPEC.md`, measured honestly against hand-verified answer keys.

---

## 0. Non-negotiable rules
Breaking any of these invalidates the work. If a rule blocks progress, log it and move on to other work.

**Evaluation integrity**
1. **Two roles, kept apart.** *Labeller* work (answer keys in `harness/gold/`) and *engineer* work
   (`scraper/`) must not influence each other.
   - Labelling for a site is done in a session that has **not opened `scraper/` or any scraper output**.
     Use a separate Devin session per answer key if you can start one; otherwise do all labelling phases
     **before** opening `scraper/` for the first time in this session.
   - The engineer never edits `harness/gold/*.json` and never changes a gold value to match scraper output.
2. **Held-out sites.** `sioux-chief`, `milwaukee` (test split) and `caleffi`, `cimberio` (challenge split) are
   held out. (`apollo` becomes a dev site; see section 1.) While improving the scraper you must not run it on them (`--allow-holdout`
   is forbidden until Phase 4), and must not open their gold files or score reports. They are run **once**,
   in Phase 4. No scraper changes are allowed after the Phase 4 run.
3. **Harness changes** (`harness/mfr_harness/`, `schema/`, `tests/`) only to fix a real bug or to implement
   something SPEC.md requires. Each needs a test, its own commit message starting `harness:`, and a log
   entry explaining why. **Never** loosen a check, delete or weaken a test, or change scoring to raise a score.
   After any harness change, every gold file must still validate with 0 errors.
4. **Generality.** No site-specific code in `scraper/mfr_scraper/`: no site names, domains, URL paths or
   CSS selectors for particular sites. Add a unit test that fails if any of these strings appear in
   `scraper/mfr_scraper/*.py`: `bray, crane, cranefs, sioux, apollo, aalberts, compano, caleffi, cimberio,
   milwaukee, dixon`. Every fix must be justified as "this helps an unknown manufacturer because …".

**Crawling**
5. robots.txt is **not** obeyed (SPEC 1a). Max 1 request/second per host, the honest User-Agent already in
   `scraper/mfr_scraper/settings.py`, no logins, no form submissions.
6. **Never work around bot protection** (Cloudflare challenges, 403/429 walls, CAPTCHAs): no stealth browsers,
   challenge solving, proxy rotation or UA spoofing. Blocked sites are reported as blocked (Dixon is one).
7. Use the fetch cache. Use `--refresh` only when you have reason to think a page changed, at most once per
   site per day.

**Repository**
8. **Do not push to `main`.** Create branch `auto/integration` from the latest `main` and do all work on it
   or on short-lived branches merged into it. Open one PR `auto/integration` → `main` at the end (Phase 5)
   for the owner to review. Keep it rebased on `main`.
9. Never commit binaries: no `*.evidence/files/`, `*.zip` archives, or caches. Commit evidence `text/` and `manifest.csv` only.
10. No new paid services or API keys. **No LLM calls inside the scraper** in this run: it stays deterministic.
    If you conclude that an LLM fallback is needed, write the design and expected gain in the log as a
    recommendation for the owner instead.

---

## 1. Decisions already made (apply them; don't re-ask)
- Spec: SPEC.md is authoritative (crawling 1a, language 2, inclusion 4 incl. images, variants 3, fields,
  vocabularies and family/variant rules 6, cross-check `refines`/`conflict` 6a, provenance 6b, evidence 6c, price 7).
- **Apollo** becomes a **dev** site (change `split` in `harness/config/sites.json` to `dev`). Scope: **Apollo-branded
  families only**. Other Aalberts brands on the same site (Shurjoint, VSH, Elkhart, Lasco, etc.) are out of
  scope. Log how brand is decided (name, logo, breadcrumb or document folder).
- **Cimberio** scope: the US site `cimberiovalve.us` plus its own asset hosts. The Italian parent site
  `web.cimberio.com` is out of scope unless a US product page links one of its files directly as that
  product's asset (and then the language rules still apply).
- **Family-level price status (schema gap)**: SPEC 7 assumes prices sit on variants, but many families have no
  variants (e.g. "Request a Quote" with no identifiers). Implement this as a harness change (Rule 3):
  - an optional family field `family_prices` (array of the existing `price` object), used **only** when the
    family has no variants;
  - add it to the schema; validate it like variant prices;
  - score its `availability` in `score.py` alongside variant prices;
  - add a SPEC 7 sentence, a template example and tests.
- Dixon: blocked by Cloudflare; no answer key, no workarounds. Keep it listed and verify the scraper reports it as blocked.

When SPEC.md is genuinely silent or ambiguous, choose the option that is (a) most useful to a builder
choosing products and (b) easiest for two independent labellers to apply the same way. Write it into SPEC.md
in a commit starting `spec:`, log it, and apply it to **all** existing gold files.

---

## 2. Phase 1: answer keys (labeller role)
Follow `harness/DEVIN_TASK.md` for each site, with these changes for autonomy:
- **No checkpoint wait.** At the checkpoint, self-review against this list, log the review, and continue:
  family definition matches SPEC 3; the index is built from 2 sources with counts; sample drawn with seed 42
  and the coverage swaps logged; scope decisions applied.
- **Blind re-label of 6 families** by a separate session (or skipped and logged as a gap if impossible).
  Report agreement **before** and after fixes.
- If **before-fix** agreement on family spec fields is below 80%, find which SPEC rule caused the disagreements,
  clarify SPEC.md (Rule in section 1), re-label, and re-measure. Do this at most twice per site; then log and move on.

Order (skip any that already exists and validates on `main` or an open PR, and review it instead):
1. **Crane** (`crane`, dev). If a `gold/crane` branch or PR already exists from an earlier session, finish it.
2. **Apollo** (`apollo`, dev, Apollo brand only).
3. **Cimberio** (`cimberio`, challenge; it has prices). Built by a labeller that never sees the scraper.
4. **Sioux Chief vocabulary pass**: map `end_connections` and `applications` in `gold/sioux-chief.json` to the
   SPEC 6 vocabularies (unmapped wording to `additional_specs`), keeping sources unchanged.
5. **Bray image and document-type re-check**: a blind image-only and doc_type-only re-label of the same 6 Bray
   families under the current SPEC 4 and 5 rules. If before-fix agreement is below 85%, clarify the rules
   (SPEC 5 doc types: decide where technical manuals, safety manuals and software documents go) and re-label.

Each answer key: validate `--gold` with 0 errors, then merge into `auto/integration`.

---

## 3. Phase 2: scraper improvement loop (engineer role)
**Dev sites**: `bray`, `crane`, `apollo` (when their keys exist). Never the held-out sites.

Each round:
1. Run the scraper on every dev site with a key: `python -m mfr_scraper run --site <s>` (full site).
2. Validate the output: `python -m mfr_harness.validate runs/<s>.json --site <s> --evidence runs/<s>.evidence`.
   **0 errors required.**
3. Score: `python -m mfr_harness.score --site <s> --gold gold/<s>.json --pred runs/<s>.json --out reports/<s>.rN.json`.
4. Pick the **largest gap by expected impact** across sites (see the backlog below), write a hypothesis in the log
   (what fails, why, the general fix, and the expected metric change), implement it, and add unit tests.
5. Re-run and re-score **all** dev sites. **Keep the change only if**:
   - the macro average of the key metrics (below) improves by ≥ 1 point, **and**
   - no dev site drops by more than 2 points on any key metric, **and**
   - all tests pass, validation shows 0 errors, and the generality test passes.

   Otherwise revert it (or rework it, at most twice) and log why.
6. Commit with a message stating the metric change.

**Key metrics** (macro-average over dev sites): family recall, family precision, primary document recall and
precision, image recall, spec accuracy (`specs_overall`), spec completeness, variant recall, price availability
accuracy, conflict-detection precision.

**Targets** (stop the loop early if all are met on every dev site): family recall and precision ≥ 95%;
primary document recall ≥ 85% at precision ≥ 95%; image recall ≥ 85%; spec accuracy ≥ 80%; completeness ≥ 85%;
variant recall ≥ 70% where variants exist; price availability ≥ 90%; conflict precision ≥ 50%.

**Stop** the loop when targets are met, or after **3 consecutive rounds** gain under 1 point, or after **12 rounds**.

**Self-healing**
- If a run crashes, find the root cause, add a regression test, fix it, and re-run. A crash on one page must
  never kill a site run: catch it, flag it with the URL, and continue.
- If a site's output suddenly drops by more than 10% on any metric versus the previous round, treat it as a regression
  (likely a code bug or a site change). Diff the outputs, find the cause, and fix or revert before continuing.
- If a site starts returning 403/429 or challenge pages, stop crawling it for the day, log it, and continue
  with other sites (Rule 6).
- Never "fix" a score by changing the harness or gold (Rules 1 and 3).

**Backlog** (from the round 1 analysis on Bray; re-prioritise using your own scores):
1. **Variants and price status**: read orderable items with identifiers from model/part-number tables on pages and
   spec sheets (SPEC 3); attach the page's price status to them. Use `family_prices` when there are no variants.
2. **Family precision**: industry and landing pages (e.g. "<industry> products") pass the product test. Product pages
   have their own spec data and downloads; landing pages mostly link to other product pages.
3. **Materials, standards and certifications** (46–64% on Bray): wrong line chosen, or multi-series PDF tables mixed in.
   Check the misses individually; prefer table rows labelled for this family.
4. **False conflicts** (conflict precision ~11%): compare like with like (e.g. a page listing several materials against
   a sheet listing one should usually be `refines` or `agree` under SPEC 6a, not `conflict`).
5. **`sizes_available`** (0%): read size columns of dimension tables.
6. **Primary document recall** (64% on Bray): find where the missed spec sheets are linked (tabs, JS data, document
   libraries) and handle that generally.
7. Any family the scraper still misses (e.g. Bray's Series 70-HAZ): find out why.

---

## 4. Phase 4: final test (once)
Only after Phase 2 has stopped and its last commit is tagged `pre-final-test`:
1. Run the scraper with `--allow-holdout` on `sioux-chief` and `cimberio` (and on any other held-out site that has
   a merged answer key). Validate the output. Score it.
2. Score the **old agent** on the same keys: `python -m mfr_harness.score --site <s> --gold gold/<s>.json --legacy <split>/<s>/output.csv`.
3. **No scraper changes after this point.** If the final test reveals a bug, describe it in the report; don't fix it.

---

## 5. Phase 5: report and hand-off
1. Write `REPORT.md`:
   - a summary in plain language for a non-engineer
   - a table: dev scores per round; final test scores (new scraper vs old agent) per site and metric
   - what improved and why; what is still weak; known risks
   - blind re-label agreement for each answer key
   - every SPEC.md change made in this run
   - recommendations (including whether an LLM fallback is worth it, and where)
2. Open the PR `auto/integration` → `main` with the report as its description. **Do not merge it.**
3. `AUTONOMY_LOG.md`: one entry per decision or round: timestamp, phase, what was done, why, metric before/after,
   kept/reverted.

---

## 6. Command reference
```bash
# setup (repo root)
python3 -m venv .venv && . .venv/bin/activate
pip install -r scraper/requirements.txt -r harness/requirements.txt imagehash Pillow pdfplumber
(cd harness && python -m unittest discover tests)
(cd scraper && python -m unittest discover tests)

# scraper (from scraper/)
python -m mfr_scraper discover --site bray
python -m mfr_scraper run --site bray                 # writes ../harness/runs/bray.json (+ .csv, .evidence/)
python -m mfr_scraper run --site bray --limit 10 --out runs-dev   # quick check

# harness (from harness/)
python -m mfr_harness.validate gold/bray.json --site bray --gold
python -m mfr_harness.validate runs/bray.json --site bray --evidence runs/bray.evidence
python -m mfr_harness.score --site bray --gold gold/bray.json --pred runs/bray.json --out reports/bray.r1.json
```
Current baseline (round 1, Bray): family recall 97%, family precision 82%, spec accuracy 65%, completeness 84%,
primary document recall 64% (precision 100%), image recall 82%, variants 0%, price availability 0%.
