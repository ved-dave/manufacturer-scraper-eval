# Approach B proof of concept: processing the old agent's link files


## Summary in plain language

We took the old agent's list of links for each site and ran a new processing step over it. The step sorts the
links into product families, picks documents, CAD, images, specs and variants, and records why it kept or dropped
each item. It writes the same SiteRun JSON as the current scraper and is scored against the same answer keys. No
LLM calls; every rule is deterministic.

- **Grouping works.** Cimberio families correct: 100% (current scraper 66%). Bray: 93% vs 82%, with 107 families
  predicted against 103 in the key (current scraper: 122). Crane ties at 100%.
- **Documents and images are limited by our keep/drop rules, not by the old agent's list.** On Bray and Crane the old
  agent's list already contains 100% of the answer-key documents and 98–100% of the images. Every miss on those sites
  is an item our rules dropped. Cimberio is the exception: its list is missing about half the main documents and the
  price list.
- **Not cheaper on bare CSVs.** With only `url,url_type`, the processor re-downloads every page and most files. It
  made about as many requests as the current scraper on Bray, and more on Cimberio.
- **Blocked sites give nothing.** Dixon and Apollo block our page requests, so both produce 0 families (runs complete
  and validate with 0 errors).
- **L1 (simulated from our cache) changes speed, not scores:** 6–20% fewer fetches (Sioux Chief 19%), all page
  fetches replaced by snapshots, Sioux Chief offline processing 49 → 36 min. Scores are unchanged except image
  precision (Bray −3, Sioux Chief −13), because images with known sizes skip the duplicate check. The larger L1 benefits (blocked sites, items on pages we never fetched) can't be
  simulated from our cache; they are estimates below.
- **Sioux Chief, the large part-number site, is worse than the current scraper.** B finds 54% of the key's families
  (current scraper 93%), with 3,749 families against 700 in the key (current scraper 6,324). The old agent's list
  contains 100% of them. The cause is one rule: Sioux product pages link to more than 15 related product pages, so
  the "listing page" rule drops them. 360 of the 700 key families lost every page that way. Grouping itself is mostly
  right where it acts (84 of 89 multi-page families are correct) but too cautious: 769 "same family?" pairs are left
  for the resolver.
- **Option A (post-round, section 11):** routing "listing" pages that have product URLs and spec evidence to the
  unsure queue instead of dropping them raises Sioux Chief families found from 54 to 88 (current scraper 93) and
  secondary docs from 33 to 87, with Bray, Crane and Cimberio unchanged. 5,725 families against 700 remain:
  grouping is now the main gap.
- **Phase 2 targets: not met.** Image and document recall ≥ 95% fail on Bray, Cimberio and Sioux Chief; Sioux Chief
  took 4 h 09 min (target < 4 h); Sioux Chief image precision is 33 points below the current scraper.

## 1. What was built

- `harness/schema/link_record.schema.json` and `python -m mfr_harness.validate_links <file>` (L0 CSV or L1 JSONL).
- `scraper/mfr_scraper/process/`: `readers.py` (L0 and L1 into one `LinkSet`), `run.py` (`ProcessRun`),
  `grouping.py`, `context.py`, `simulate_l1.py` (the L1 measurement harness, §7).
- `python -m mfr_scraper process --site <s> --links <file>` writes `<s>.json` (SiteRun), `<s>.csv`,
  `<s>.decisions.jsonl` (every keep / drop / unsure with its reason) and `<s>.evidence/`.
- L1 fields used when present: `html_snapshot` (no page fetch); `found_on`/`link_text`/`section`/`in_chrome`/
  `link_kind` (grouping and document typing); `status`/`final_url`/`content_type` (dead links skipped without a
  download); `breadcrumb`, `canonical_url`, `lang`, `hreflang`, `jsonld_product`, `has_spec_table` (page role,
  grouping, language copies); image `width`/`height`/`srcset`/`alt` (largest version and 300 px rule without a
  download). Absent fields: the page is fetched once.
- Blocked requests are recorded on the item. After 8 blocked responses in a row the host is not asked again and the
  remaining items are recorded as blocked.
- Hand-written L1 fixture: `scraper/tests/fixtures/l1_sample.jsonl`. Process tests: `scraper/tests/test_process.py`.

## 2. Results per site and metric

B = this processing layer (final code). "Current scraper" = `mfr_scraper run`. "Old agent (inventory)" =
`score.py --legacy`: whether the item is anywhere in the agent's list. It has no family linkage, so precision,
specs, variants and prices can't be scored for it. All numbers are % against the answer key.

### bray

| Metric | B (L0 CSV) | B (L1, simulated) | Current scraper | Old agent (inventory) |
|---|---|---|---|---|
| Families found | 97 | 97 | 97 | 100 |
| Families correct (precision) | 93 | 93 | 82 | – |
| Families predicted | 107 | 107 | 122 | – |
| Primary docs recall | 93 | 93 | 93 | 100 |
| Primary docs precision | 100 | 100 | 100 | – |
| Secondary docs recall | 95 | 95 | 95 | 100 |
| CAD recall | 100 | 100 | 100 | 100 |
| CAD precision | 100 | 100 | 100 | – |
| Image recall | 73 | 73 | 80 | 98 |
| Image precision | 86 | 83 | 85 | – |
| Variant recall | 100 | 100 | 100 | – |
| Variant precision | 100 | 100 | 100 | – |
| Spec accuracy | 67 | 67 | 67 | – |
| Spec completeness | 86 | 86 | 86 | – |
| Citation rate | 100 | 100 | 100 | – |
| Conflict precision | 12 | 12 | 12 | – |
| Price availability | 96 | 96 | 96 | – |

### crane

| Metric | B (L0 CSV) | B (L1, simulated) | Current scraper | Old agent (inventory) |
|---|---|---|---|---|
| Families found | 100 | 100 | 100 | 99 |
| Families correct (precision) | 100 | 100 | 100 | – |
| Families predicted | 218 | 218 | 218 | – |
| Primary docs recall | 100 | 100 | 100 | 100 |
| Primary docs precision | 100 | 100 | 100 | – |
| Secondary docs recall | 55 | 55 | 71 | 100 |
| CAD recall | 100 | 100 | 100 | 67 |
| CAD precision | 100 | 100 | 100 | – |
| Image recall | 93 | 93 | 78 | 100 |
| Image precision | 100 | 100 | 100 | – |
| Variant recall | 74 | 74 | 74 | – |
| Variant precision | 74 | 74 | 74 | – |
| Spec accuracy | 61 | 61 | 61 | – |
| Spec completeness | 83 | 83 | 83 | – |
| Citation rate | 100 | 100 | 100 | – |
| Conflict precision | 50 | 50 | 33 | – |
| Price availability | 81 | 81 | 81 | – |

### cimberio

| Metric | B (L0 CSV) | B (L1, simulated) | Current scraper | Old agent (inventory) |
|---|---|---|---|---|
| Families found | 100 | 100 | 97 | 100 |
| Families correct (precision) | 100 | 100 | 66 | – |
| Families predicted | 32 | 32 | 47 | – |
| Primary docs recall | 54 | 54 | 25 | 54 |
| Primary docs precision | 100 | 100 | 100 | – |
| Secondary docs recall | 100 | 100 | 12 | 100 |
| CAD recall | 100 | 100 | 67 | 0 |
| CAD precision | 100 | 100 | 100 | – |
| Image recall | 100 | 100 | 0 | 100 |
| Image precision | 50 | 50 | – | – |
| Variant recall | 0 | 0 | 0 | – |
| Variant precision | – | – | – | – |
| Spec accuracy | 53 | 53 | 35 | – |
| Spec completeness | 72 | 72 | 43 | – |
| Citation rate | 100 | 100 | 100 | – |
| Conflict precision | 0 | 0 | 0 | – |
| Price availability | 0 | 0 | 0 | – |

### sioux-chief

| Metric | B (L0 CSV) | B (L1, simulated) | Current scraper | Old agent (inventory) |
|---|---|---|---|---|
| Families found | 54 | 54 | 93 | 100 |
| Duplicate families (scorer) | 3,625 | 3,625 | 5,679 | – |
| Families predicted | 3,749 | 3,749 | 6,324 | – |
| Labelled families found (of 15) | 11 | 11 | 14 | – |
| Primary docs recall | 43 | 43 | 46 | 100 |
| Primary docs precision | 100 | 100 | 100 | – |
| Secondary docs recall | 33 | 33 | 90 | 100 |
| CAD recall | 71 | 71 | 14 | 100 |
| CAD precision | 100 | 100 | 100 | – |
| Image recall | 22 | 21 | 14 | 100 |
| Image precision | 46 | 33 | 79 | – |
| Best image version rate | 67 | 52 | 93 | 100 |
| Variant recall | 6 | 6 | 3 | – |
| Variant precision | 100 | 100 | 100 | – |
| Spec accuracy | 17 | 17 | 15 | – |
| Spec completeness | 34 | 34 | 29 | – |
| Citation rate | 100 | 100 | 100 | – |
| Conflict detection | 0 of 8 (none flagged) | 0 of 8 (none flagged) | 0 of 8 (none flagged) | – |
| Price availability | 6 | 6 | 3 | – |

Family precision is 100 for both systems but not informative here: the scorer also matches a family by series code,
and Sioux Chief's 700 key entries cover nearly every series. "Duplicate families" is the useful measure. B's family
recall by page is 340 of 700; the cold run's 59% included 75 series-code-only matches, the final code 38.
The 4 labelled families B misses (865-12ECD, 230-2906101, 304-06, 886-ER) were all dropped as listing pages.

## 3. Families: predicted vs key

| Site | Key | B | Current scraper |
|---|---|---|---|
| Bray | 103 | 107 | 122 |
| Crane | 217 | 218 | 218 |
| Cimberio | 32 | 32 | 47 |
| Sioux Chief | 700 | 3,749 (3,625 duplicates) | 6,324 (5,679 duplicates) |

**Correct merges:**
- Cimberio: the old agent's 1,181 page URLs include 1,149 on `web.cimberio.com` (off-site). B keeps 32 product
  pages, 1:1 with the key. The current scraper makes 47 (duplicates from language and listing pages).
- Bray: listing and category pages are not made into families (page-role score); 107 vs the current scraper's 122.
- Sioux Chief: 84 of the 89 families built from several pages stay inside one key family, e.g. 118M204 + 118M206,
  119Q208 + 119Q210 (shared spec sheet + breadcrumb + identifier stem).

**Wrong merges (Sioux Chief, not fixed):** 5 of 89 multi-page families span 2–3 key families: 250-11 + 250-11A +
250-11P + 250-12A; 637PX20 + 637PX25; 833-22F + 833-23F + 833-225F + 833-235F + 833-625F; 854-23I + 854-24I + 854-63I +
854-64I; 862-227I + 862-627I. All were merged by a spec sheet shared across the series.

**Wrong merges found and fixed:**
- Crane: DA931 + DA941, DM900 + DM921 + DM931, FM469 + FM492 (6 families) were merged by "same breadcrumb leaf + same
  model code" because "931" was read as a size suffix of "DA". Fixed: only codes with a digit before the trailing
  letters lose a trailing number (640WP02 → 640WP; DA931 stays DA931). Crane: 208 → 218 families. The family
  precision metric didn't catch this (the key's canonical page was still a family); the decisions log did.
- Cimberio: 778V vs 778VS were merged by a series-wide spec sheet (round 1 fix).

## 4. Requests and wall time (cold runs, empty cache)

| Site | B requests | B wall | Current requests | Current wall |
|---|---|---|---|---|
| Bray | 1,227 | 25:44 | 1,110 | 21:45 |
| Crane | 828 before a stall (see note) | stalled at 37 min | 1,505 | 29:28 |
| Cimberio | 404 | 6:12 | 82 | 1:26 |
| Sioux Chief | 20,639 | 4:09:15 | 14,408 | 4:21:23 |
| Dixon | 9 (8 blocked) | 0:08 | – | – |
| Apollo | 9 (8 blocked) | 1:11 | – | – |

Note: the cold Crane run hung on one file the server sent a few bytes at a time (200/277 pages done). Every download
now gives up after 5 minutes (`DOWNLOAD_DEADLINE`, regression test added). The finished Crane run used that cache
(0 new requests, 3:43). Sioux Chief B: page reads 2 h 07 min, waiting for file downloads
(one host, one file at a time, 1 s politeness delay) ~1 h 40 min, families ~20 min. The final-code re-run from
cache took 49 min with 0 requests. On Bray, about 1,100 of B's 1,227 requests are asset downloads made only to learn type,
size and image dimensions.

## 5. Phase 2 targets

| Target | Result |
|---|---|
| Image recall ≥ 95% on dev sites | Not met: Bray 73, Crane 93, Cimberio 100, Sioux Chief 22 |
| Document recall ≥ 95% on dev sites | Not met: primary Bray 93, Crane 100, Cimberio 54 (inventory gap), Sioux Chief 43 |
| Precision drop ≤ 2 pts vs current scraper | Met on Bray, Crane, Cimberio; not met on Sioux Chief (image precision 46 vs 79) |
| Sioux Chief < 4 h | Not met: 4 h 09 min cold (current scraper 4 h 21 min) |
| Better than current scraper overall | Not met: better on Cimberio, better grouping on Bray, mixed on Crane, worse on Sioux Chief (families found 54 vs 93) |

## 6. Uncertain items (`decision: unsure` in `<site>.decisions.jsonl`)

Each record has the question, the candidate (URL, link text, section, type), the family (family_id, name,
series_code, identifiers), evidence for and against (short quotes with sources), why the rules couldn't decide,
the default action taken, and a cache key: the Phase 3 resolver's work queue.

| Kind | Bray | Crane | Cimberio | Sioux Chief | Default action |
|---|---|---|---|---|---|
| asset_to_family | 265 | 82 | 0 | 386 | keep |
| page_vs_pdf_conflict | 254 | 130 | 8 | 663 | keep both, flag conflict |
| doc_type | 70 | 19 | 0 | 566 | keep as spec_sheet |
| spec_value | 20 | 5 | 0 | 7 | keep first-ranked source |
| family_grouping | 0 | 26 | 10 | 769 | keep separate |
| page_role | 10 | 0 | 0 | 0 | drop |

### Five examples per kind

**page_role**

- bray: Is this a product page? `https://www.bray.com/`. Why undecided: product signals are borderline. Default: drop.

**asset_to_family**

- bray: Does this image belong to Supplier Code of Conduct? `lerik.Sitefinity.Frontend/assets/dist/img/dummy.jpg?package=Bootstrap4` (section: Compliance Validation Information). Why undecided: a shared file in product content; the rules cannot tell which families it covers. Default: keep.
- bray: Does this document belong to 2-Cx? `com/docs/default-source/brochures/product-brochures/en_ovw_cxline_.pdf` (section: Product Brochure). Why undecided: a shared file in product content; the rules cannot tell which families it covers. Default: keep.
- bray: Does this document belong to 3-Cx? `com/docs/default-source/brochures/product-brochures/en_ovw_cxline_.pdf` (section: Product Brochure). Why undecided: a shared file in product content; the rules cannot tell which families it covers. Default: keep.
- bray: Does this document belong to 4-Cx? `com/docs/default-source/brochures/product-brochures/en_ovw_cxline_.pdf` (section: Product Brochure). Why undecided: a shared file in product content; the rules cannot tell which families it covers. Default: keep.
- bray: Does this document belong to KM 20/21? `com/docs/default-source/brochures/product-brochures/en_ovw_cxline_.pdf` (section: Product Brochure). Why undecided: a shared file in product content; the rules cannot tell which families it covers. Default: keep.

**page_vs_pdf_conflict**

- bray: Page and PDF disagree on material_body for 2-Cx: which is right? `https://www.bray.com/cx-line/2-cx-ptfe-lined-butterfly-valve` (section: material_body). Why undecided: page and PDF values contradict (SPEC 6a conflict); both are kept and flagged. Default: keep both (conflict).
- bray: Page and PDF disagree on standards for 2-Cx: which is right? `bray.com/docs/default-source/specifications/datasheets/en_sds_2-cx.pdf` (section: standards). Why undecided: page and PDF values contradict (SPEC 6a conflict); both are kept and flagged. Default: keep both (conflict).
- bray: Page and PDF disagree on material_body for 3-Cx: which is right? `https://www.bray.com/cx-line/3-cx-resilient-seated-butterfly-valve` (section: material_body). Why undecided: page and PDF values contradict (SPEC 6a conflict); both are kept and flagged. Default: keep both (conflict).
- bray: Page and PDF disagree on end_connections for 3-Cx: which is right? `bray.com/docs/default-source/specifications/datasheets/en_sds_3-cx.pdf` (section: end_connections). Why undecided: page and PDF values contradict (SPEC 6a conflict); both are kept and flagged. Default: keep both (conflict).
- bray: Page and PDF disagree on size_range for 4-Cx: which is right? `https://www.bray.com/cx-line/4-cx-double-offset-butterfly-valve` (section: size_range). Why undecided: page and PDF values contradict (SPEC 6a conflict); both are kept and flagged. Default: keep both (conflict).

**doc_type**

- bray: Is this document a spec_sheet or a brochure? `bray.com/docs/default-source/specifications/datasheets/en_sds_3-cx.pdf` (section: Sales Data Sheet). Why undecided: URL/link/title say one type, the first page reads as another. Default: keep as spec_sheet.
- bray: Is this document a spec_sheet or a iom_manual? `y.com/docs/default-source/specifications/datasheets/en_sds_km20-21.pdf` (section: Sales Data Sheet). Why undecided: URL/link/title say one type, the first page reads as another. Default: keep as spec_sheet.
- bray: Is this document a spec_sheet or a warranty? `fault-source/specifications/datasheets/sds_s70_servonxt_ethernetip.pdf` (section: Sales Data Sheet). Why undecided: URL/link/title say one type, the first page reads as another. Default: keep as spec_sheet.
- bray: Is this document a spec_sheet or a certificate? `ray.com/docs/default-source/specifications/datasheets/en_sds_ac_70.pdf` (section: Sales Data Sheet). Why undecided: URL/link/title say one type, the first page reads as another. Default: keep as spec_sheet.
- bray: Is this document a brochure or a spec_sheet? `-source/brochures/product-brochures/b_1055_en_mccannalok_metal_2pg.pdf` (section: Product Brochure). Why undecided: URL/link/title say one type, the first page reads as another. Default: keep as brochure.

**spec_value**

- bray: Which certifications value is right for 3-Cx? `bray.com/docs/default-source/specifications/datasheets/en_sds_3-cx.pdf` (section: certifications). Why undecided: PDFs disagree; the spec-sheet value is shown by precedence. Default: keep displayed value.
- bray: Which certifications value is right for 4-Cx? `bray.com/docs/default-source/specifications/datasheets/en_sds_4-cx.pdf` (section: certifications). Why undecided: PDFs disagree; the spec-sheet value is shown by precedence. Default: keep displayed value.
- bray: Which end_connections value is right for KM 20/21? `y.com/docs/default-source/specifications/datasheets/en_sds_km20-21.pdf` (section: end_connections). Why undecided: PDFs disagree; the spec-sheet value is shown by precedence. Default: keep displayed value.
- bray: Which certifications value is right for Tri Lok®-Cx? `/docs/default-source/specifications/datasheets/en_eu_sds_trilok-cx.pdf` (section: certifications). Why undecided: PDFs disagree; the spec-sheet value is shown by precedence. Default: keep displayed value.
- bray: Which applications value is right for Series 70? `default-source/specifications/datasheets/sds-1078-el-ctrls-haz-loc.pdf` (section: applications). Why undecided: PDFs disagree; the spec-sheet value is shown by precedence. Default: keep displayed value.

**family_grouping**

- cimberio: Is https://cimberiovalve.us/1220nln part of the same family as https://cimberiovalve.us/1220nl? `https://cimberiovalve.us/1220nln` (section: no lead). Why undecided: stem and breadcrumb match but nothing else links the pages. Default: keep separate.
- cimberio: Is https://cimberiovalve.us/778p part of the same family as https://cimberiovalve.us/778-threaded? `https://cimberiovalve.us/778p` (section: no lead). Why undecided: stem and breadcrumb match but nothing else links the pages. Default: keep separate.
- cimberio: Is https://cimberiovalve.us/778vs part of the same family as https://cimberiovalve.us/778V? `https://cimberiovalve.us/778vs` (section: ball valves). Why undecided: stem and breadcrumb match but nothing else links the pages. Default: keep separate.
- cimberio: Is https://cimberiovalve.us/778pvs part of the same family as https://cimberiovalve.us/778pv? `https://cimberiovalve.us/778pvs` (section: cimpress valves). Why undecided: stem and breadcrumb match but nothing else links the pages. Default: keep separate.
- cimberio: Is https://cimberiovalve.us/778pvw part of the same family as https://cimberiovalve.us/778pv? `https://cimberiovalve.us/778pvw` (section: cimpress valves). Why undecided: stem and breadcrumb match but nothing else links the pages. Default: keep separate.

### Estimated score value if each kind were resolved correctly

Estimates, not measurements. "Macro" = the 10-metric keep-rule average over Bray, Crane and Cimberio (now 74.6).

| Kind | What resolving it changes | Estimate |
|---|---|---|
| page_vs_pdf_conflict | Conflict precision is 12 (Bray) and 50 (Crane): most flagged conflicts are formatting differences ("-10 to 100" vs "10 - 120°C" from a multi-column table). Dismissing false ones and picking the right value. | +2 to +3 macro; +1 to +3 spec accuracy |
| asset_to_family | On labelled families, the default (keep) is already right for 48 of 55 Bray items and 4 of 4 Crane items. 7 Bray items are kept but the key drops them. The other 283 are on unlabelled families. | ≤ +1 to +2 Bray doc/image precision |
| doc_type | Document label correctness (not a keep-rule metric). | 0 to +1 |
| spec_value | 25 values; spec accuracy covers ~13 fields × 15 labelled families per site. | ~+1 spec accuracy |
| family_grouping | 0 on these keys (default "keep separate" is right: Crane/Cimberio family precision 100). The value is on sites with one page per part number. | Sioux Chief: 769 pairs (e.g. 117-12 vs 117-03, 117Q22 vs 117-03). Merging the right ones cuts duplicates, but family recall is capped by the listing-rule drops (§9), so first fix that rule. Roughly +0 to +5 Sioux family recall; large duplicate reduction |
| page_role | 10 Bray pages (company, policy, materials pages); default drop is right for all 10. Bray's 3 missed families are not in this queue (see §8). | 0 |

## 7. L1: measured (simulated from our cache) and estimated

**How it was measured.** The old agent doesn't emit L1 yet. `python -m mfr_scraper.process.simulate_l1` builds an L1
file per site from the old agent's CSV plus the pages and files our runs already downloaded: an `html_snapshot` and
page facts for every cached page, link context (`found_on`, `link_text`, `section`, `in_chrome`) from those
snapshots, file facts (`status`, `final_url`, `content_type`, `content_length`, `etag`, `last_modified`) and image
`width`/`height`. Only URLs in the agent's list are included, so it adds no discovery. Assets in the list that no
cached page links to get `found_on: null` (validator warning, not error). Both inputs were processed offline with
the same code.

| Site | L1 file validation | Fetch attempts L0 → L1 | Page fetches L1 | Macro-relevant score changes |
|---|---|---|---|---|
| Bray | 0 errors, 311 warnings | 2,779 → 2,221 (−20%) | 0 (1,075 snapshots) | image precision 86 → 83 |
| Crane | 0 errors, 3 warnings | 3,900 → 3,183 (−18%) | 0 (277 snapshots) | none |
| Cimberio | 0 errors, 2,189 warnings | 572 → 540 (−6%) | 0 (32 snapshots) | none |
| Sioux Chief | 0 errors, 1,218 warnings | 58,732 → 47,459 (−19%) | 0 (6,851 snapshots) | image precision 46 → 33, best version 67 → 52, image recall 22 → 21; all other metrics unchanged |

Macro over Bray, Crane and Cimberio: 74.60 → 74.60; Sioux Chief: 42.26 → 42.16. No key metric drops more than 2
points (image precision is not a key metric). All L1 SiteRuns validate with
0 errors.

- **Regression found on Sioux Chief and fixed (`f4ca6bb`):** the first L1 run lost 718 key pages (families found
  54 → 43). The simulator set `has_spec_table` only for 3+ label/value rows (the documented definition is 2+), and
  the processor treated `false` as "no spec values at all", removing even a single recognised spec value. Pages fell
  under the product threshold and were dropped as listings. Now `false` only removes the spec-table signal, and the
  simulator uses 2+ rows. The Bray "families correct 93 → 94" from the first L1 run came from the same mechanism and
  is gone after the fix. All L1 numbers here are after the fix.
- **Image precision (Bray 86 → 83, Sioux Chief 46 → 33):** with width/height in L1 the image isn't downloaded, so the perceptual-hash duplicate
  check doesn't run, and 3 "-copy"/mobile renditions are kept as extra images. An L1 producer should emit a content
  hash, or the processor should still hash images it would keep.
- **Why scores barely move:** the simulated L1 contains what the processor already rebuilds by fetching the page.
  It removes work (snapshots replace every page fetch; dead links and image sizes need no download), not mistakes.

**Not measurable here (estimates):**
- **Blocked sites.** Dixon and Apollo: 0 families today because every page request is blocked. The old agent
  reached those pages, so its snapshots would be the only input that can produce families there.
- **Cold-run time.** Page fetching was 1,053 s of Bray's 1,544 s cold run (68%); snapshots remove it, so ~17 min of
  26. Sioux Chief: page reading was 2 h 07 min of the 4 h 09 min cold run, so ~2 h with snapshots, under the 4 h
  target (estimate). Offline processing from the same cache: 49:08 (CSV) → 36:28 (L1).
- **Re-runs.** `etag`/`last_modified`/`content_length` allow skipping unchanged files; not exercised (no second crawl).
- **Discovery.** Items the old agent never listed (Cimberio's price list, half its main documents) are not fixed by
  L1 fields; that needs better discovery in the agent.

## 8. Dixon and Apollo (no answer keys)

Both runs complete and validate with 0 errors. Dixon: Cloudflare 403 on every page request; Apollo: a "Bot
Verification" page. After 8 blocked responses the host is not asked again; every remaining item is recorded as
blocked in the decisions log. 0 families: with only `url,url_type` there is nothing to read specs or groupings from.

## 9. Families dropped as listing pages (Bray, Sioux Chief)

All three product pages are in the old agent's list; our page-role rules dropped them without flagging them as unsure.
- `series-70-hazardous-location`: dropped as "non-product section by URL". `NON_PRODUCT_WORDS` (shared with the
  current scraper's discovery code) matches `location` as any hyphen-separated word, not only as a path section.
- `air-release-ezi-vac`, `series-pva`: dropped as listing pages (listing score −4 outweighed 3 spec pairs and spec
  downloads).
Sioux Chief: 2,921 pages were dropped as "listing page", including every page of 360 of the 700 key families
(e.g. `Products/865-12ECD`, signals: download, breadcrumb, commerce words, listing −4). The rule fires when a page
links to more than 15 pages at the same or deeper level of its section; Sioux product pages link to that many related
products. 2,340 of the 2,921 had a spec table or spec download.
Not fixed: all 4 improvement rounds were used. Both are general rule fixes (match non-product words only as whole
path segments; let spec tables + spec downloads outweigh listing cues), worth about +3 Bray family recall and up to +46 points of Sioux Chief family recall by page (340 → up to 700 of 700).

## 10. Recommendations

1. **Change the old agent to emit L1, in this order.** (a) `html_snapshot` plus `status`/`final_url`/`content_type`:
   the only way to get anything from sites that block us (Dixon, Apollo), and it removes all page fetching (68% of
   Bray's cold run). (b) `found_on`/`section`/`in_chrome`/`link_text`: exact link context even when a page can't be
   re-fetched. (c) image `width`/`height`/`srcset` plus a content hash (without the hash, duplicate renditions slip
   through: Bray image precision −3, Sioux Chief −13). (d) `etag`/`last_modified`/`content_length` for cheap re-runs. Page facts
   (`breadcrumb`, `jsonld_product`, `has_spec_table`) are useful but we already rebuild them from the snapshot.
2. **Fix discovery gaps in the agent separately.** Cimberio's price list and half its main documents were never
   listed; no L1 field fixes that.
3. **Fix the processing rules that lose listed items** (no new data needed): non-product URL words as whole path
   segments; spec tables outweighing listing cues (tried as option A, section 11: Sioux Chief families found 54 → 88); combo-photo naming (Bray images); multi-product
   documents without false spec conflicts (round 3, Crane secondary docs 55 vs 71).
4. **Phase 3 resolver: start with `page_vs_pdf_conflict`** (largest queue, about +2–3 macro points), then
   `family_grouping` on part-number sites (Sioux Chief: 769 pairs). The decisions log already has the fields the resolver needs.

## 11. Option A: listing-page rule fix (post-round experiment, outside the 4-round rule)

Run after the PR's main results, at the user's request. The numbers in sections 1–10 are unchanged; this section
reports the fix separately. Re-processed from cache (no new fetching).

**Rule** (`listing_with_product_evidence` in `process/run.py`): a page with the listing cue (more than 15
same-section links) is kept and queued as `page_role` unsure (default action `keep`) when all of these hold:
- its URL names it a product page (`url_word`: `/product(s)/`, `/p/`, `/item/`, `/model/`, `/series/`);
- it has strong product evidence (`spec_pairs`, `spec_download` or `jsonld_product`);
- it passes the product threshold without the listing penalty.

Otherwise it is still dropped. The `url_word` condition was added after checking the decision logs: without it, the
rule would also keep 24 Crane `/category/...` pages and 24 Bray `/solutions/...`/category pages that have spec-like
facet tables. None of those 48 pages are in the answer keys. That first version was stopped before scoring.

**Sioux Chief** (% of answer key):

| Metric | B (final) | B + option A | Current scraper |
|---|---|---|---|
| Families found | 54 | **88** | 93 |
| Families predicted (key: 700) | 3,749 | 5,725 | 6,324 |
| Labelled families found (of 15) | 11 | 14 | 14 |
| Primary docs recall | 43 | 43 | 46 |
| Secondary docs recall | 33 | **87** | 90 |
| CAD recall | 71 | 71 | 14 |
| Image recall | 22 | 27 | 14 |
| Image precision | 46 | 50 | 79 |
| Best image version rate | 67 | 60 | 93 |
| Variant recall | 6 | 4 | 3 |
| Spec accuracy / completeness | 17 / 34 | 18 / 35 | 15 / 29 |
| Price availability | 6 | 4 | 3 |
| Offline processing time | 49 min | 57 min | – |

- **Keep rule:** macro 42.26 → 46.63 (+4.37); no key metric drops more than 2 points; 0 validation errors.
- **Reproduced:** a second offline run with the final code gave identical scores and an identical SiteRun, apart from
  `retrieved_at` timestamps.
- **Pages rescued:** 2,052 product pages, covering 318 of the 360 key families that had lost every page to the
  listing rule. 869 listing drops remain, all without strong product evidence.
- **Variants and price:** 10 → 8 of 179 key variants, all in one key family (`643WG2`). In B (final), its WG2 pages
  formed a family with canonical `643WG2`. Rescued sibling pages now pull those SKUs into the `...WG7` families, so no
  predicted family matches the key's `643WG2` canonical. That is a grouping and canonical-choice effect, not lost data.
- **Bray, Crane, Cimberio:** identical scores. No page there meets all three conditions. Bray's two listing-dropped
  key families (`/check-valves/air-release-ezi-vac`, `/pinch-valves/series-pva`) are not rescued, because their URLs
  have no product word.
- **Unsure queue (Sioux Chief):**
  - `page_role` +2,052 (default keep).
  - `family_grouping` 769 → 1,648: more product pages means more "same family?" pairs.
  - Multi-page families 88 → 100.

**What it shows:**
- Recall now nearly matches the current scraper (88 vs 93), with documents, CAD, images and specs equal or better.
- The duplicate problem remains: 5,725 families against 700. Each part-number page is still its own family unless
  the evidence ties it to another.
- The next lever is family grouping (the resolver on `family_grouping`, or a stronger deterministic series rule),
  not page discovery or page roles.

## 12. Family grouping rule R4 and resolver (post-round experiment, outside the 4-round rule)

**Duplicate metric.** `family_index` now reports `duplicate_families` and `dedup_rate` (1.0 = one predicted family per
key family). Each predicted family is assigned to its single best-matching key family, and repeats are counted. The
keep-rule script reports `dedup`. Before R4: Bray and Cimberio 1.00, Crane 0.995, Sioux Chief 0.107 (current scraper
0.103). So duplicates are the Sioux Chief gap for both systems.

**R4 (deterministic).** Two single-product pages are merged only when:
- each page lists the other's part number in its own item table;
- both pages have the same breadcrumb leaf;
- both identifiers have the same stem.

Every merge records its evidence. On the 1,648 Sioux Chief `family_grouping` questions from Option A, this clue was
right 542 times and wrong 2 times (both 615-series pairs). It covered 70% of the pairs the key calls the same family.
Every page grouped into a family is also recorded as one of that family's variants, which keeps provenance complete.
The first R4 run gave 10 `found_on` validation errors, and this fixed them.

**Sioux Chief** (% of the key unless noted; offline from cache):

| | Option A | R4 | Current scraper |
|---|---|---|---|
| Families produced (key: 700) | 5,725 | 4,574 | 6,324 |
| Duplicates score | 0.107 | 0.137 | 0.103 |
| Families found | 88.3 | 90.1 | 92.9 |
| Multi-page families | 100 | 687 | – |
| Variants found / correct (of 179) | 4.5 / 100 | 19.0 / 89.5 | 3 |
| Price availability | 4 | 19 | 3 |
| Images found / correct | 27 / 50 | 40 / 61 | 14 / 79 |
| Main docs found / correct | 42.9 / 100 | 39.3 / 91.7 | 46 |
| Other docs correct | 100 | 96.3 | – |
| CAD | 71 | 57 | 14 |
| Spec completeness | 34.6 | 31.8 | 29 |
| `family_grouping` unsure | 1,648 | 497 | – |
| Validation errors | 0 | 0 | 0 |
| Offline processing time | 55:38 | 51:32 | – |

- **Keep rule: fails.** The macro score rises 68.41 → 69.18 across the 4 sites. Sioux Chief main docs (found and correct) and
  spec completeness each drop more than 2 points.
- **Drop causes:**
  - Key family `643WG2` spans the 643–647 WG series, and we still split it. With R4, its best match moved from a
    `645WGC2` piece to a `643WG2` piece, which carries fewer files: main docs 3 → 2, and it also explains the CAD
    and spec-completeness change. No file is lost; the other pieces still carry the files.
  - Key family `304-06` (Deburring Tool) was not matched before. It now matches a non-key `304-1` cutting-tool family
    on series only, which adds 2 false docs and 4 false variants. The `304-1` group itself (304-1, -08, -12, -12B) is
    a legitimate R4 merge of pages outside the key.
- **Bray, Crane, Cimberio:** identical scores. R4 never fires there.

**Resolver (Phase 3, level 1): built, not run.** `python -m mfr_scraper resolve --decisions <file>` answers
`family_grouping` unsure records from the cached page text only.
- An answer is kept only if both quoted passages appear in the stored pages. Everything else stays unsure.
- Answers are cached by question key and prompt version, and each record stores the model, cost and cached flag.
- The run stops at `--budget-usd`.
- `process --resolutions <file>` merges only verified "same" answers.
- It never reads the answer keys.

No model credential was available in this session, so it has not run. Estimate: about 3.4k input tokens per question,
about $0.012 with Sonnet, so about $6 for the 497 remaining Sioux Chief questions.

**What it shows:** item tables are a precise grouping clue. Variants rise 4 → 19 and duplicates fall by 1,151
families. Duplicates are still at 0.137, though, and what's left (for example 643WG vs 644WG) needs judgement, so it's
the resolver's job. The scorer also still credits only one piece of a split family, so canonical choice alone can
move document and spec scores by several points.

## 13. Resolver run on Sioux Chief (stopped at 323 of 497 questions)

The run used `resolve --backend claude-code --model sonnet`: Claude Code in print mode, signed in with the owner's Claude
subscription, with no tools and no project context. The run hit the subscription's usage limit at 323 questions and
was then stopped at the owner's decision (see "Why the run was stopped" below). The machine was signed out of the
Claude account afterwards.

**Answers:** 256 verified "different", 59 verified "same", 4 unparseable and 4 with quotes not found in the pages
(those 8 stay unsure). At API prices this is about $0.027 per question, measured on the first 3; Claude Code adds
prompt overhead. The cost to the owner is $0 beyond the subscription.

**Agreement with the answer key** (measured after the run, never used by the resolver):

| Resolver said | Answers | Key agrees |
|---|---|---|
| same | 59 | 34 (58%) |
| different | 256 | 213 (83%) |

The main error is a replacement-parts page judged the same family as the product it serves (for example 118-01 "parts for 118
Series sillcock" with 118-C208). The quotes are real, so the quote check cannot catch this.

**Applying the 59 verified "same" links** (offline re-run, R4 → R4 + resolver):

| | R4 | R4 + resolver |
|---|---|---|
| Families produced (key: 700) | 4,574 | 4,515 |
| Duplicates score | 0.1367 | 0.1385 |
| Families found | 90.1 | 90.3 |
| Multi-page families | 687 | 657 |
| Variants found / correct | 19.0 / 89.5 | 20.1 / 90.0 |
| Images found / correct | 39.6 / 61.1 | 40.5 / 61.6 |
| Price availability | 19.0 | 20.1 |
| Validation errors | 0 | 0 |
| Offline processing time | 51:32 | 53:16 |

- **Keep rule:** passes (Sioux Chief macro 46.05 → 46.39, no key-metric drop above 2 points).
- **What it shows:**
  - The gain is small, because most answers are "different".
  - The scorecard does not count the roughly 25 wrong merges against us.
  - At 58% precision on "same", this prompt is not good enough for automatic merging. Next: a stricter prompt that
    excludes parts and accessory pages (`fg-2`). It would have to be labelled as tuned on Sioux Chief and checked on
    another site before promotion.

**Why the run was stopped (owner's decision, not resumed):**
- Each "same family?" answer can merge at most two families into one. Even a perfect resolver on all 497 questions
  could take Sioux Chief from 4,574 families to about 4,077 at best, against 700 in the key.
- By the key, only about 1 in 4 of these pairs is truly the same family (77 of the 315 answered). So a perfect resolver
  would remove about 120 families (estimate).
- **Most duplicate families never become a question.** The unsure queue only holds pairs that already share a
  part-number stem and category. The resolver cannot fix duplicates it is never asked about.
- The answer key treats replacement-parts and accessory lines as their own families (`gold_meta` and
  `sioux-chief.ambiguities.md`: "Accessories sold under their own catalog name are their own family"). That is the
  main reason the "same" answers disagree with the key.

**Conclusion:** the resolver is not the main lever for Sioux Chief grouping. The next lever is a better grouping clue
that covers pairs the rules never ask about. A candidate (not tested) is the site's own category cards: the key's
families were built from them (family = category + catalog name on the card). They are site data, not the key. Check
first whether the old agent's link list contains those category pages.
