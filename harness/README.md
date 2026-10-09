# Manufacturer scraper evaluation harness

Scores scraping agents against a hand-labelled answer key, using the rules in `../SPEC.md`.
Pure Python standard library (`jsonschema` is optional but recommended). It never fetches URLs.

```
harness/
  DEVIN_TASK.md              brief for building the answer keys
  config/sites.json          per-site input URL, split, allowed hosts; global CAD-viewer hosts
  schema/siterun.schema.json output format for agents AND answer keys
  gold/_TEMPLATE.json        worked example of one fully labelled family
  gold/<site>.json           answer keys (to be built)
  runs/                      agent outputs (SiteRun JSON)
  reports/                   score reports
  mfr_harness/
    normalize.py   URL keys, image-rendition collapsing, locale detection, spec value comparison
    validate.py    schema + spec v1 rule checks (non-English, off-allowlist, dup images, citations, ...)
    score.py       gold vs prediction metrics (new agent JSON, or legacy CSV)
    legacy.py      reader + noise profile for the existing agent's output.csv
  tests/           offline self-tests (synthetic data)
```

## Commands
```bash
python -m unittest discover tests
python -m mfr_harness.validate gold/bray.json --site bray --gold
python -m mfr_harness.validate runs/bray.json --site bray --evidence runs/bray.evidence
python -m mfr_harness.score --site bray --gold gold/bray.json --pred runs/bray.json --out reports/bray.new.json
python -m mfr_harness.score --site bray --gold gold/bray.json --legacy ../train/bray/output.csv --out reports/bray.legacy.json
```

## What gets measured
| Metric | New agent | Legacy CSV |
|---|---|---|
| Family recall (vs complete family_index) | yes | yes (via site_page rows) |
| Family precision / duplicate families | yes | proxy: share of site_page rows that are families |
| Spec-sheet / submittal / price-list recall and precision | yes | recall only |
| Secondary document recall and precision | yes | recall only |
| doc_type / cad_type accuracy | yes | label agreement (legacy labels mapped to v1 kinds) |
| CAD recall and precision | yes | recall only |
| Image recall, best-version rate, duplicate pairs | yes | recall, best-version vs rendition-only |
| Variant recall and precision | yes | not scorable |
| Spec completeness (fields found from any source) | yes | not scorable |
| Spec field accuracy (per field, and split by page vs spec-sheet gold source) | yes | not scorable |
| Conflict detection recall/precision; cross-check rate; citation rate | yes | not scorable |
| Price availability and amount accuracy | yes | not scorable |
| Rule violations (non-English, off-allowlist, duplicates) | via validate | noise profile |

Asset, spec and price metrics are computed only inside the labelled families. Family metrics use the
complete `family_index`.

## Matching rules (in `normalize.py`)
- **Pages and documents**: case-insensitive URL with scheme, `www.`, trailing slash and tracking params
  removed. Documents also match on sha256.
- **Images**: rendition patterns collapsed (Drupal `/styles/*/public/`, `x.jpg.webp`, WordPress `-WxH`
  and `-scaled`, Shopify `_WxH`, BigCommerce `stencil/WxH`), or a phash Hamming distance of 6 or less.
  "Best version" means the exact URL from the answer key, or one at least as large.
- **Spec rules (validator)**: the displayed value follows precedence (spec sheet > page > other PDF);
  `cross_check` must match the cited source types; conflicts need `alt_values`; every quote must appear in
  `<evidence>/text/<sha256>.txt`; a PDF cited for specs must be in the family's documents, be linked from a
  family page, and (warning) mention the series code or name.
- **Specs (scorer)**: compared against the gold *displayed* value, per field type. Sets use F1; sizes are parsed from fractions such as `1-1/2`; pressure is
  converted to psi (±2%); temperature is converted to °F (±1.5°); certifications are mapped to standard
  names (e.g. `NSF 61` → `NSF/ANSI 61`, `lead free` → `NSF/ANSI 372`).
