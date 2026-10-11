# Approach B proof of concept: processing the old agent's link files

**Status: draft. The Sioux Chief rows are filled in when its runs finish (marked TBD).**

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
- **Phase 2 targets:** image and document recall ≥ 95% are not met on all dev sites. Sioux Chief: TBD.

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
| Families correct (precision) | 93 | 94 | 82 | – |
| Families predicted | 107 | 106 | 122 | – |
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

TBD

## 3. Families: predicted vs key

| Site | Key | B | Current scraper |
|---|---|---|---|
| Bray | 103 | 107 | 122 |
| Crane | 217 | 218 | 218 |
| Cimberio | 32 | 32 | 47 |
| Sioux Chief | 700 | TBD | TBD (previous run: ~5,600 extra) |

**Correct merges:**
- Cimberio: the old agent's 1,181 page URLs include 1,149 on `web.cimberio.com` (off-site). B keeps 32 product
  pages, 1:1 with the key. The current scraper makes 47 (duplicates from language and listing pages).
- Bray: listing and category pages are not made into families (page-role score); 107 vs the current scraper's 122.
- Sioux Chief: TBD.

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
| Sioux Chief | TBD | TBD | TBD | previous run 8:55 h, ~13,000 |
| Dixon | 9 (8 blocked) | 0:08 | – | – |
| Apollo | 9 (8 blocked) | 1:11 | – | – |

Note: the cold Crane run hung on one file the server sent a few bytes at a time (200/277 pages done). Every download
now gives up after 5 minutes (`DOWNLOAD_DEADLINE`, regression test added). The finished Crane run used that cache
(0 new requests, 3:43). On Bray, about 1,100 of B's 1,227 requests are asset downloads made only to learn type,
size and image dimensions.

## 5. Phase 2 targets

| Target | Result |
|---|---|
| Image recall ≥ 95% on dev sites | Not met: Bray 73, Crane 93, Cimberio 100, Sioux Chief TBD |
| Document recall ≥ 95% on dev sites | Not met: primary Bray 93, Crane 100, Cimberio 54 (inventory gap); Sioux Chief TBD |
| Precision drop ≤ 2 pts vs current scraper | Met on Bray, Crane, Cimberio (B is equal or higher on every precision metric) |
| Sioux Chief < 4 h | TBD |
| Better than current scraper overall | TBD (better on Cimberio, better grouping on Bray, mixed on Crane) |

## 6. Uncertain items (`decision: unsure` in `<site>.decisions.jsonl`)

Each record has the question, the candidate (URL, link text, section, type), the family (family_id, name,
series_code, identifiers), evidence for and against (short quotes with sources), why the rules couldn't decide,
the default action taken, and a cache key: the Phase 3 resolver's work queue.

| Kind | Bray | Crane | Cimberio | Default action |
|---|---|---|---|---|
| asset_to_family | 265 | 82 | 0 | keep |
| page_vs_pdf_conflict | 254 | 130 | 8 | keep both, flag conflict |
| doc_type | 70 | 19 | 0 | keep as spec_sheet |
| spec_value | 20 | 5 | 0 | keep first-ranked source |
| family_grouping | 0 | 26 | 10 | keep separate |
| page_role | 10 | 0 | 0 | drop |

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
| family_grouping | 0 on these keys (default "keep separate" is right: Crane/Cimberio family precision 100). The value is on sites with one page per part number. | Sioux Chief: TBD |
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
| Bray | 0 errors, 311 warnings | 2,779 → 2,205 (−21%) | 0 (1,075 snapshots) | families correct 93 → 94; image precision 86 → 83 |
| Crane | 0 errors, 3 warnings | 3,926 → 3,183 (−19%) | 0 (277 snapshots) | none |
| Cimberio | 0 errors, 2,189 warnings | 572 → 540 (−6%) | 0 (32 snapshots) | none |
| Sioux Chief | TBD | TBD | TBD | TBD |

Macro over the three sites: 74.60 → 74.63; no metric drops more than 2 points. All L1 SiteRuns validate with
0 errors.

- **Bray families +1:** `has_spec_table: false` and no product JSON-LD on `/resources` stop it from being a family.
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
