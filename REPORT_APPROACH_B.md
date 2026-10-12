# Approach B proof of concept: processing the old agent's link files

**Status: draft. The Sioux Chief L1 (simulated) numbers are filled in when that run finishes (marked pending).**

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
- **L1 (simulated from our cache) changes speed, not scores:** 6–21% fewer downloads, all page fetches replaced by
  snapshots, scores within 1 point. The larger L1 benefits (blocked sites, items on pages we never fetched) can't be
  simulated from our cache; they are estimates below.
- **Sioux Chief, the large part-number site, is worse than the current scraper.** B finds 54% of the key's families
  (current scraper 93%), with 3,749 families against 700 in the key (current scraper 6,324). The old agent's list
  contains 100% of them. The cause is one rule: Sioux product pages link to more than 15 related product pages, so
  the "listing page" rule drops them. 360 of the 700 key families lost every page that way. Grouping itself is mostly
  right where it acts (84 of 89 multi-page families are correct) but too cautious: 769 "same family?" pairs are left
  for the resolver.
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
| Families found | 54 | pending | 93 | 100 |
| Duplicate families (scorer) | 3,625 | pending | 5,679 | – |
| Families predicted | 3,749 | pending | 6,324 | – |
| Labelled families found (of 15) | 11 | pending | 14 | – |
| Primary docs recall | 43 | pending | 46 | 100 |
| Primary docs precision | 100 | pending | 100 | – |
| Secondary docs recall | 33 | pending | 90 | 100 |
| CAD recall | 71 | pending | 14 | 100 |
| CAD precision | 100 | pending | 100 | – |
| Image recall | 22 | pending | 14 | 100 |
| Image precision | 46 | pending | 79 | – |
| Best image version rate | 67 | pending | 93 | 100 |
| Variant recall | 6 | pending | 3 | – |
| Variant precision | 100 | pending | 100 | – |
| Spec accuracy | 17 | pending | 15 | – |
| Spec completeness | 34 | pending | 29 | – |
| Citation rate | 100 | pending | 100 | – |
| Conflict detection | 0 of 8 (none flagged) | pending | 0 of 8 (none flagged) | – |
| Price availability | 6 | pending | 3 | – |

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
| Sioux Chief | TBD | TBD | TBD | TBD |

Macro over the three sites: 74.60 → 74.60; no metric drops more than 2 points. All L1 SiteRuns validate with
0 errors.

- **Regression found on Sioux Chief and fixed (`f4ca6bb`):** the first L1 run lost 718 key pages (families found
  54 → 43). The simulator set `has_spec_table` only for 3+ label/value rows (the documented definition is 2+), and
  the processor treated `false` as "no spec values at all", removing even a single recognised spec value. Pages fell
  under the product threshold and were dropped as listings. Now `false` only removes the spec-table signal, and the
  simulator uses 2+ rows. The Bray "families correct 93 → 94" from the first L1 run came from the same mechanism and
  is gone after the fix. All L1 numbers here are after the fix.
- **Bray image precision −3:** with width/height in L1 the image isn't downloaded, so the perceptual-hash duplicate
  check doesn't run, and 3 "-copy"/mobile renditions are kept as extra images. An L1 producer should emit a content
  hash, or the processor should still hash images it would keep.
- **Why scores barely move:** the simulated L1 contains what the processor already rebuilds by fetching the page.
  It removes work (snapshots replace every page fetch; dead links and image sizes need no download), not mistakes.

**Not measurable here (estimates):**
- **Blocked sites.** Dixon and Apollo: 0 families today because every page request is blocked. The old agent
  reached those pages, so its snapshots would be the only input that can produce families there.
- **Cold-run time.** Page fetching was 1,053 s of Bray's 1,544 s cold run (68%); snapshots remove it, so ~17 min of
  26. Sioux Chief: TBD.
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
   through: Bray image precision −3). (d) `etag`/`last_modified`/`content_length` for cheap re-runs. Page facts
   (`breadcrumb`, `jsonld_product`, `has_spec_table`) are useful but we already rebuild them from the snapshot.
2. **Fix discovery gaps in the agent separately.** Cimberio's price list and half its main documents were never
   listed; no L1 field fixes that.
3. **Fix the processing rules that lose listed items** (no new data needed): non-product URL words as whole path
   segments; spec tables outweighing listing cues (+3 Bray families, up to 360 Sioux Chief families: the biggest single fix); combo-photo naming (Bray images); multi-product
   documents without false spec conflicts (round 3, Crane secondary docs 55 vs 71).
4. **Phase 3 resolver: start with `page_vs_pdf_conflict`** (largest queue, about +2–3 macro points), then
   `family_grouping` on part-number sites (Sioux Chief: 769 pairs). The decisions log already has the fields the resolver needs.
