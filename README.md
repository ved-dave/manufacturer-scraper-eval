# Manufacturer product-index scraping: evaluation experiment

**Question:** can we reliably build a product index (product families, variants, spec sheets, CAD, images, specs and
price status) from manufacturers' websites, and how do we **prove** it's accurate?

**Context:** builders in the US and Canada choosing manufacturers of electrical, plumbing and mechanical building
materials. Thousands of manufacturer sites eventually; this repo is the evaluation on **8 plumbing/valve
manufacturers**.

The experiment has three parts:
1. **Definition of "correct":** a written spec (`SPEC.md`) and a validation and scoring harness (`harness/`).
2. **Answer keys:** hand-verified, evidence-backed labels for a sample of product families per site, each checked by a
   blind re-label (two independent labellers).
3. **Systems compared on the same keys:**
   - the **old agent**: an existing link collector whose output is the CSVs in `train/ dev/ test/ challenge/`;
   - the **new scraper**: crawls and extracts end to end (`scraper/`, `mfr_scraper run`);
   - **Approach B**: the old agent's links in, plus a processing layer that groups, decides and extracts
     (`mfr_scraper process`).

---

## Status (Oct 2026)

| Piece | State |
|---|---|
| Spec | `SPEC.md`, refined through several labelling rounds (variants, vocabularies, `refines` vs `conflict`, document types, images) |
| Answer keys | **6 sites** with full keys: Bray, Crane, Sioux Chief, Cimberio, Milwaukee, Caleffi (15 labelled families each, plus a complete family index). Apollo has partial notes only (blocked). Blind re-label agreement on family spec fields **before fixes**: Bray 87%, Cimberio 81%, Crane 78%, Sioux Chief 76%, but **Milwaukee 50% and Caleffi 40%** (83% / 89% after fixes). The spec is still ambiguous on new layouts. |
| Blocked sites | **Dixon** (Cloudflare) and **Apollo** (reCAPTCHA) block automated requests: no full answer key. The old agent's data for them is accepted as input. |
| New scraper (v0.1 → round 10) | Works on familiar layouts. **Failed the first held-out test** (`REPORT.md`): it filtered out valid files and treated part-number pages as separate families. |
| Approach B PoC | Built and scored (`REPORT_APPROACH_B.md`). Grouping beats the current scraper on Bray and Cimberio. Phase 2 targets **not met**. A site-profile step largely fixes Sioux Chief's family count (603 vs 700 in the key, vs 6,324 for the current scraper) but lowers document precision, so it's opt-in. |
| AI resolver (Phase 3) | Prototype run on part of Sioux Chief: 323 of 497 grouping questions, stopped at the owner's decision. "Different" answers agreed with the key 83% of the time, "same" answers 58%. |
| Held-out test | Milwaukee and Caleffi have answer keys and **haven't been used yet**: they're the next clean test. |
| Database / services | Designed (`DATA_MODEL.md`), not built. |

### Headline numbers
- **Old agent:** finds almost every answer-key link (~98–100% on most sites, 54% of Cimberio's main documents). But its
  output is a flat, noisy list: no families, specs, variants or prices. On Bray, 90% of its page rows aren't products.
- **New scraper, first held-out test** (Sioux Chief, Cimberio): main documents found 46% / 25%, images 14% / 0%, specs
  15% / 35%. Most misses (83%) were files it had seen and then filtered out.
- **Approach B** (details per site in `REPORT_APPROACH_B.md` §2):
  - family precision on Bray 93% (current scraper 82%) and Cimberio 100% (66%);
  - documents and images are limited by keep/drop rules, not by the old agent's list;
  - with only `url,url_type` CSVs it re-fetches pages, so it's no cheaper than the current scraper.

---

## Documents: read in this order
| File | What it is |
|---|---|
| `scraping-approach-proposal.md` | **The current plan:** "collect wide, sort smart", phases, the self-healing loop, team decisions |
| `SPEC.md` | What counts as correct: scope, language, families/variants, inclusion, document types, spec fields and vocabularies, page-vs-PDF cross-check (`agree` / `refines` / `conflict`), provenance, evidence, price |
| `REPORT_APPROACH_B.md` | Approach B PoC results, family grouping, the AI resolver run, site profiles, recommendations |
| `REPORT.md` | First autonomous run: 10 scraper rounds, the held-out test, gap analysis |
| `OLD_AGENT_IMPROVEMENTS.md` | Free fields the old agent should add (`found_on`, `html_snapshot`, ...), as JSONL page/link records |
| `DATA_MODEL.md` | Post-PoC database design (link collector, processor and health-checker services) |
| `AUTONOMY_LOG.md` | Every decision and round made by the autonomous Devin runs |
| `AUTONOMOUS_RUN.md`, `APPROACH_B_RUN.md`, `prompt.md` | Instructions given to the Devin runs (history) |
| `results/` | Small copies of score files, site profiles and the team packet (`results/README.md`) |

---

## Repository layout
```
train/ dev/ test/ challenge/<site>/   input.txt (homepage) + output.csv (old agent's links: url,url_type)
SPEC.md                               definition of correct
harness/                              evaluation (pure Python; never fetches)
  config/sites.json                   sites, splits, allowed hosts, CAD-viewer hosts
  schema/                             siterun.schema.json (output format), link_record.schema.json (old-agent JSONL)
  gold/                               answer keys <site>.json, ambiguity logs, blind re-labels, evidence text
  mfr_harness/                        validate.py, score.py, validate_links.py, normalize.py, legacy.py
  tests/
scraper/                              the new scraper and the Approach B processing layer
  mfr_scraper/                        fetch, robots, discover, hosts, page, specs, assets, pipeline, pdfcache
  mfr_scraper/process/                Approach B: readers (L0 CSV / L1 JSONL), grouping, profile, resolver
  tests/
results/                              durable score files, site profiles, team packet
```
Not in git (re-creatable): `harness/runs/` (~28 GB of run outputs), `scraper/cache/` (~22 GB page cache), evidence
`files/` (original PDFs and HTML), and `*-evidence-files.zip`.

---

## How to run
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r scraper/requirements.txt -r harness/requirements.txt imagehash Pillow pdfplumber
(cd harness && python -m unittest discover tests)
(cd scraper && python -m unittest discover tests)
```

**New scraper** (crawls the site itself, given only a homepage):
```bash
cd scraper
python -m mfr_scraper run --site bray                                   # evaluation site -> ../harness/runs/bray.json
python -m mfr_scraper run --site acme --input-url https://www.acme.com/ # any manufacturer
```

**Approach B** (old agent's links in):
```bash
cd scraper
python -m mfr_scraper process --site bray --links ../train/bray/output.csv            # L0: url,url_type CSV
python -m mfr_scraper process --site bray --links <site>.links.jsonl --level L1       # L1: enriched records
python -m mfr_scraper profile --site sioux-chief --links ../test/sioux-chief/output.csv --offline --out <dir>
python -m mfr_scraper process --site sioux-chief --links ../test/sioux-chief/output.csv --offline \
    --profile <dir>/sioux-chief.profile.json --out <dir>                              # opt-in site profile
python -m mfr_scraper resolve ...    # Phase 3 AI resolver on "unsure" items (backends: api, claude-code)
```
`process` also writes `<site>.decisions.jsonl`: every keep / drop / unsure decision with its reason.

**Validate and score** (from `harness/`):
```bash
python -m mfr_harness.validate gold/bray.json --site bray --gold                      # an answer key
python -m mfr_harness.validate runs/bray.json --site bray --evidence runs/bray.evidence   # a system's output
python -m mfr_harness.score --site bray --gold gold/bray.json --pred runs/bray.json       # new scraper / Approach B
python -m mfr_harness.score --site bray --gold gold/bray.json --legacy ../train/bray/output.csv   # old agent
python -m mfr_harness.validate_links <file>                                           # an L0 CSV or L1 JSONL link file
```

---

## How the evaluation stays honest
- **Evidence for every value.** Each spec value and price cites its source with a verbatim quote. The validator checks
  the quote against the saved page or PDF text.
- **Answer keys are blind-checked.** A second labeller who never sees the first key re-labels 6 families; agreement is
  reported before and after fixes. Low agreement means the spec is unclear, so the spec gets fixed, not the label.
- **Labelling and engineering are kept apart.** Answer keys are built by sessions that never see the scraper code or its
  output, and the code never edits answer keys.
- **Held-out sites.** Systems are tuned only on development sites, and tested once on sites they were never tuned on.
  Sioux Chief and Cimberio were the first held-out test, so they're now used for development. **Milwaukee and Caleffi**
  are the current held-out test.
  - Their `split` labels in `harness/config/sites.json` predate this: Sioux Chief still says `test`, Cimberio
    `challenge`. Running on any `test`/`challenge` site needs `--allow-holdout`.
- **No score-chasing:** the harness can't be loosened, tests can't be deleted, and the scraper can't contain
  site-specific code (a test enforces this).

## Crawling rules (`SPEC.md` 1a)
- `robots.txt` is not obeyed (team decision); each run counts the URLs it overrode.
- Max 1 request per second per host, with an honest User-Agent and no logins or form submissions.
- Sites that block automated requests are recorded as blocked. The old agent's data for them is valid input.

---

## Next steps (`scraping-approach-proposal.md`)
1. **Tighten the spec where Milwaukee and Caleffi labellers disagreed** (see their `*.ambiguities.md` and
   `harness/gold/HARNESS_ISSUES.md`). Before-fix agreement of 40–50% means scores on those sites would partly measure
   spec ambiguity, not scraper quality.
2. **Upgrade the old agent** with the `OLD_AGENT_IMPROVEMENTS.md` fields, in this order:
   - `html_snapshot`, `status`, `final_url` and `content_type` (needed for blocked sites; no re-fetching);
   - `found_on`, `section`, `in_chrome` and `link_text`;
   - image sizes plus a content hash;
   - `etag` / `last_modified`.
3. **Fix the processing rules that drop listed items** (`REPORT_APPROACH_B.md` §10). Decide whether the site profile
   becomes the default, after splitting card families that mix product lines.
4. **Run the held-out test on Milwaukee and Caleffi:** old agent vs current scraper vs Approach B, once.
5. **Phase 3, the self-healing loop:** the AI resolves unsure items with verified quotes (start with page-vs-PDF
   conflicts), then repeated answers are promoted to data rules.
6. **Build the services and database** from `DATA_MODEL.md` once the processing layer meets its targets. Then extend to
   electrical and mechanical manufacturers (per-category spec fields).
