# Autonomous run report: manufacturer-scraper-eval

## Summary in plain language

**Bottom line:** on the two dev sites the scraper improved a lot, but on the held-out sites it did badly.
On the held-out sites, the old agent found more of the right links on every metric we can compare. What it can't do is
organise them: no grouping by product, no specs, part numbers or prices. The answer keys, the harness changes and the
gap analysis below are the reusable result. The scraper code is a good second layer for sorting and extraction, but
it is not ready to stand on its own.

- **What was built.** Answer keys exist for 4 manufacturers: Bray, Crane, Cimberio and Sioux Chief. Two labellers
  working independently agreed on 82-100% of fields. Apollo and Dixon are blocked by bot protection, so only Bray and
  Crane could be used for development.
- **Dev sites.** Over 10 measured rounds, the scraper went from finding no part numbers to finding 87% of them.
  Price status went from 0% to 89% correct, specs from 54% to 64% correct, and main documents from 81% to 96% found.
  It has no site-specific code.
- **First held-out site (Cimberio).** Products: 97% found. Everything else failed. Its images and most datasheets are
  stored on BigCommerce CDN/store domains, which the scraper refuses to follow. It also throws away shared datasheets
  as site navigation.
- **Second held-out site (Sioux Chief).** This site has one web page per part number. The scraper treated each page
  as a separate product: 6,270 "products" where the key has 700. That one mistake pulled down documents (46%),
  images (14%), part numbers (3%) and specs (15%). It is also why the run took about 9 hours.
- **Old agent.** It found 98-100% of the key's links on every site except Cimberio documents (54%). Its output is a
  flat list of URLs with no product grouping, and it carries a lot of noise. On Bray, 90% of its page rows aren't
  products.
- **Gap analysis.** Most of what the scraper misses (66 of 80 items, 83%) was on pages its own crawl visited; its
  filters dropped it. Only 9 key items were found by the old agent and never seen by our crawl.
- **What to do next** (§9):
  - group part-number pages into products;
  - follow links to asset hosts;
  - decide by evidence (does this file name this product?) instead of location;
  - parse each PDF once;
  - get answer keys for 2-3 more varied sites before tuning again.

## 1. What was done

| Phase | Result |
|---|---|
| 1. Answer keys | Crane (new, 15 families), Cimberio US (new, held out), Sioux Chief vocabulary pass, Bray blind image/doc-type re-check, SPEC consistency pass on every key. **Apollo blocked**: every URL, robots.txt and sitemap included, returns a LiteSpeed reCAPTCHA page, so it has no key. Dixon is blocked too (Cloudflare, as already documented). |
| 2. Scraper rounds | 10 rounds on the two usable dev sites (Bray, Crane). Round 1 is the baseline; rounds 2-10 each passed the keep rule and were kept. No site-specific code (`TestGenerality` passes). |
| 3. Consistency | SPEC decisions made during the run were applied to all gold keys (separate labeller sessions). |
| 4. Final test | Run once at tag `pre-final-test` on the held-out sites that have keys: Sioux Chief and Cimberio. Milwaukee and Caleffi have no answer key in the repo, so they could not be scored and were not run. |
| 5. Hand-off | This report, `AUTONOMY_LOG.md`, and this PR (not merged). |

## 2. Dev scores per round

Rounds: R1 baseline · R2 variants from model/part-number tables + `family_prices` · R3 PDF cap per family 10 → 30 ·
R4 identifier lists under a "Models" heading; URL tails must look like identifiers; accessory pages don't take other
families' models · R5 every variant-less family reports a price status · R6 temperature ranges with the unit only on
the upper bound · R7 sizes from the SIZE / DN column of dimension tables · R8 variants from identifier lists that open
the product heading ("F646L / F641L / F656L") · R9 temperature rows with the unit in the row label ("TEMPERATURE (°C)
-10 to 100") · R10 applications from spec-sheet prose that states a use ("WRAS approved for use with potable water").
Bray R4 is the reworked R4 (the first R4 attempt regressed price availability and was reworked, see the log).

**Bray**

| Metric | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9 |
|---|---|---|---|---|---|---|---|---|---|
| Family recall | 97.1 | 97.1 | 97.1 | 97.1 | 97.1 | 97.1 | 97.1 | 97.1 | 97.1 |
| Family precision | 82.0 | 82.0 | 82.0 | 82.0 | 82.0 | 82.0 | 82.0 | 82.0 | 82.0 |
| Primary doc recall | 61.0 | 61.0 | 92.7 | 92.7 | 92.7 | 92.7 | 92.7 | 92.7 | 92.7 |
| Primary doc precision | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| Image recall | 80.5 | 80.5 | 80.5 | 80.5 | 80.5 | 80.5 | 80.5 | 80.5 | 80.5 |
| Spec accuracy | 65.6 | 65.6 | 66.3 | 66.3 | 66.3 | 67.1 | 67.1 | 67.1 | 67.1 |
| Spec completeness | 84.4 | 84.4 | 85.2 | 85.2 | 85.2 | 85.2 | 85.2 | 85.2 | 85.2 |
| Variant recall | 0.0 | 27.3 | 27.3 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| Price availability | 0.0 | 62.5 | 62.5 | 95.8 | 95.8 | 95.8 | 95.8 | 95.8 | 95.8 |
| Conflict precision | 10.7 | 10.7 | 12.9 | 12.9 | 12.9 | 12.9 | 12.9 | 12.9 | 12.9 |

**Crane**

| Metric | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9 |
|---|---|---|---|---|---|---|---|---|---|
| Family recall | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| Family precision | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| Primary doc recall | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| Primary doc precision | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| Image recall | 78.0 | 78.0 | 78.0 | 78.0 | 78.0 | 78.0 | 78.0 | 78.0 | 78.0 |
| Spec accuracy | 42.2 | 42.2 | 42.2 | 42.2 | 42.2 | 44.4 | 56.2 | 56.2 | 59.6 |
| Spec completeness | 64.2 | 64.2 | 64.2 | 64.2 | 64.2 | 64.2 | 76.5 | 76.5 | 79.6 |
| Variant recall | 0.0 | 22.2 | 22.2 | 22.2 | 22.2 | 22.2 | 22.2 | 74.1 | 74.1 |
| Price availability | 0.0 | 16.2 | 16.2 | 16.2 | 43.2 | 43.2 | 43.2 | 81.1 | 81.1 |
| Conflict precision | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 20.0 | 20.0 | 33.3 |

R10: Bray spec accuracy 66.6, completeness 85.9, conflict precision 12.5 (other metrics as R9); Crane spec accuracy
61.5, completeness 82.7 (other metrics as R9).

Macro (Bray + Crane), R1 → R10: primary doc recall 80.5 → 96.4 · spec accuracy 53.9 → 64.1 · completeness 74.3 →
84.3 · variant recall 0 → 87.1 · price availability 0 → 88.5 · conflict precision 5.4 → 22.9 · family recall /
precision and image recall unchanged (98.6 / 91.0 / 79.3).

## 3. Final test: new scraper vs old agent (held-out sites, run once at `pre-final-test`)

Old-agent rows are scored from its CSV, which has only `url` and `url_type`. Specs, variants, prices and any
family-linked precision can't be scored for it ("n/s").

| Metric | Sioux Chief: new | Sioux Chief: old | Cimberio: new | Cimberio: old |
|---|---|---|---|---|
| Family recall | 91.6 | 100 | 96.9 | 100 |
| Family precision | 100 (but 5,634 duplicate families, see below) | n/s | 66.0 | n/s |
| Primary doc recall | 46.4 | 100 | 25.0 | 53.6 |
| Primary doc precision | 100 | n/s | 100 | n/s |
| Secondary doc recall | 90.0 | 100 | — | 100 |
| Doc type / label accuracy | 75.0 | 100 | — | 100 |
| CAD recall | 14.3 | 100 | — | 0 |
| Image recall | 13.5 (precision 78.9) | 100 | 0 | 100 (best version 0) |
| Spec accuracy | 15.4 | n/s | 34.5 | n/s |
| Spec completeness | 29.0 | n/s | 42.9 | n/s |
| Variant recall | 3.4 | n/s | 0 | n/s |
| Price availability | 3.4 | n/s | 0 | n/s |
| Conflict detection | 0 of 8 found, 0 false | n/s | 0 | n/s |
| Rows output | 6,270 families | 15,017 URLs | — | — |

Validation: both predictions 0 errors, 0 warnings (Sioux Chief checked with evidence quotes). 0 crashes.
Sioux Chief: ~8 h 55 min, about 13,000 requests (6,546 pages, 635 PDFs, 5,681 images). Cimberio: 82 requests, ~2 min.

For reference, the old agent on the dev keys: Bray family 100, primary docs 100, CAD 100, images 97.6; Crane family 98.6,
primary docs 100, CAD 66.7, images 100. Its CSVs are 2,211 rows (Bray) and 1,944 rows (Crane). On Bray only 10% of its
site-page rows are families; on Crane, 78%. CAD labels were wrong on both.

## 4. Bugs found by the final test (described, not fixed: AUTONOMOUS_RUN §4)

1. **One page per part number is read as one family per page (Sioux Chief).** For example, `640WP02`, `640WP03` and
   `640WP04` are separate pages of one family. Result: 6,270 predicted families against 700 in the index (5,634
   duplicates).
   - Each "family" has no variants, so variant and price recall are ~3%.
   - A family's documents, images and specs are spread over sibling pages.
   - The same shared PDFs are parsed again for every page, which is the main reason for the ~9 h run.

   Neither dev site has this layout.
2. **Asset hosts are not followed (Cimberio).** All 17 key images (`cdn11.bigcommerce.com`) and 13 key documents
   (`store-…mybigcommerce.com`) were skipped as off-allowlist.
3. **Shared datasheets are dropped as site chrome** even when their text names the family (Cimberio
   `TechDataSheet-*`). Variants and prices that only appear in those sheets are lost with them.
4. **Image filter is too strict.** Image recall is ~79% on dev sites against the old agent's 98-100%. Sioux Chief
   logged 18,811 images skipped as installation/lifestyle photos.
5. **Speed.** Fetching is fully sequential, and the server's response time stacks on top of the 1 req/s gap. Parsed
   PDFs are not memoised per run (`process_pdf` re-parses cached bodies). Images are downloaded just to measure them.
   A 60-second py-spy sample of the Sioux Chief run: waiting on the server ~34%, rate-limiter sleep ~29%, PDF parsing
   ~28%, image hashing ~4%.

**Gap analysis.** For each key document, image and CAD file, I asked: did the old agent have it, did our crawl see it,
and why was it missed. Matching is by host + path, which under-counts old-agent image renditions.

| Site | Key items | New scraper found | Missed: seen in crawl, filtered | Missed: fetched then dropped | Missed: never seen |
|---|---|---|---|---|---|
| Bray | 164 | 153 | 6 | 3 | 2 |
| Crane | 136 | 113 | 21 | 2 | 0 |
| Cimberio | 56 | 10 | 39 | 0 | 7 |
| **Total** | 356 | 276 | **66 (83% of misses)** | 5 | 9 |

The old agent found 9 key items that our crawl never saw (2 Bray images, 7 Cimberio documents). Everything else
the scraper missed, its own crawl had already seen. (Sioux Chief not included in this table.)

## 5. Blind re-label agreement (6 families per key, `random.Random(42)`)

| Key | Before fixes | After SPEC clarification | Notes |
|---|---|---|---|
| Crane | spec fields 50/64 (78%); documents 20/29; images 1/33 | spec fields 60/63 (95%); documents 29/29; images 17/17; doc_type 100%; variants 10/10; cross_check 92% | Disagreement was `standards` scope and unlinked image URLs; both became SPEC rules. |
| Cimberio | spec fields 47/58 (81%) | 47/57 (82%); documents 9/14; variants 27/27; images 9/9; CAD 2/2; cross_check 80% | Blind labeller missed a public price-list PDF; `material_body` differs by wording only. |
| Bray (images + doc types only) | documents 44/44; doc_type 32/44 (73%); images 13/17 (76%) | doc_type 44/44 (100%); images 15/17 (88%) | Led to SPEC 5 "classify by content" and SPEC 4 image edge cases. |
| Sioux Chief | not re-labelled | — | Vocabulary pass was a mechanical mapping with sources unchanged. |
| Apollo | — | — | Blocked by bot protection; no key. |

## 6. SPEC.md changes made in this run

1. SPEC 7 `family_prices`: a family with no variants reports its price status at family level (schema, validator, scorer and tests updated). `availability` is always filled, `not_published` included.
2. SPEC 6 controlled-vocabulary mapping strictness: no terms inferred from context; "Water" alone is not potable water; hub vs prose joining methods; fields with no mappable wording go to `*_other`.
3. SPEC 4 image edge cases: product markings / short cutaway markers don't make an infographic; option collages count; only image URLs the page links, at the fullest linked rendition.
4. SPEC 5 classify documents by content, not filename/label (ordered rules; software/config files not recorded; English must be primary and ≥ 50% of a multilingual document).
5. SPEC 3 option codes (`.AT`, `.PF`, bare-shaft figures, suffixes) are not variants.
6. SPEC 6 parallel BSP / G / ISO 228 / BS 2779 threads → `threaded`; taper wording → `BSPT`.
7. SPEC 6 PN / class designations → pressure in bar when they rate the product.
8. SPEC 6 `standards` include thread/flange standards the product is made, tested, drilled or flanged to; "formerly" or other products' standards excluded.
9. SPEC 6 standards keep the source spelling; spelling-only differences are the same standard in `cross_check`.
10. SPEC 6 a PN that only qualifies a flange connection is not the pressure rating when a working pressure is stated.
11. SPEC 3 / 7 models on an accessory page that are variants of another family go to `additional_specs.models`; the accessory's price status goes to `family_prices`. Several applicable PNs in one source → the highest.

## 7. What improved and why
- **Variants and prices** (R2, R4, R5, R8): variants come from model/part-number tables, model headings and
  identifier lists. Every family without variants now reports its price status (`family_prices`).
- **Primary documents** (R3): raising the per-family PDF cap from 10 to 30 stopped Bray's spec sheets being cut off.
- **Specs** (R6, R7, R9, R10): temperature ranges with the unit given once or in the row label; sizes from SIZE/DN/NPS
  columns; applications from sheet prose.
- **Robustness:** crash isolation per family (0 crashes in every run), the generality test (no site names in the
  scraper), and the repo-hygiene test (no tracked symlinks or caches).

## 8. What is still weak and known risks
- **Family grouping.** It assumes one page per family. It fails on sites with one page per part number (Sioux Chief)
  and is 82% precise on Bray.
- **Asset discovery.** It is filtered by host and by "site chrome" heuristics, which loses CDN-hosted and shared files.
- **Image recall.** About 79% on dev, 0-14% held out.
- **Conflict detection.** 13-33% precision on dev, 0 on held-out sites.
- **Applications from prose (R10).** This can add false terms. Seen on dev: "vacuum" from "vacuum to high-pressure
  applications", and "fire protection" from fittings brochures.
- **Only two dev sites.** The 10 rounds were tuned against Bray and Crane, and both keep their assets on their own
  domain with one page per family. The dev gains therefore overstate how well the scraper generalises.
- **Speed.** About 9 h for a ~6,000-product catalogue. Roughly 2.5× the minimum the 1 req/s rule allows.
- **Missing keys.** Milwaukee and Caleffi have none, so they remain an unused clean test set. Apollo and Dixon are
  blocked by bot protection.

## 9. Recommendations
1. **Group part-number pages into families.** Use evidence the pages share: the same breadcrumb or category, the same
   PDFs, a common name stem, or a "related sizes" block. Then each page becomes a variant with its own price.
   This is the largest single fix on the evidence of Sioux Chief.
2. **Collect wide, decide by evidence.**
   - Follow every asset a product page links to, on any host. Keep the polite limits and no bot-protection workaround.
   - Keep a shared file when its text names the family or its identifiers.
   - Give each item a keep/drop/unsure decision with a reason, and write the rejected items out for audit.

   The gap analysis says this recovers up to ~89% of current misses without any new discovery source.
3. **Speed.** Memoise parsed PDFs and image measurements by content hash. Filter images from the HTML before
   downloading them. Fetch different hosts concurrently, each still at ≤ 1 req/s.
4. **More dev keys first.** Add 2-3 more unblocked manufacturers, including one with CDN-hosted assets and one with
   per-part-number pages, before the next tuning rounds.
5. **The old agent stays useful.** It is a fast, high-recall link source and a recall checklist. It is not usable as
   the input to a sorting layer until its CSV records the page each URL was found on (`found_on`).
6. **LLM fallback: worth it, narrowly.**
   - **Where:**
     - which family an uncertain asset belongs to;
     - free-prose spec fields (applications, standards wording);
     - page-vs-PDF conflict adjudication.
   - **How:** only for items the deterministic rules mark as unsure. The answer must quote verbatim text, and the
     quote is checked against the stored document.
   - **Expected gain:** the weakest fields (conflict precision 13-33%, spec accuracy ~64%, asset assignment on
     unusual sites).
   - **Measure:** on the same keys before adopting it.
   - **Not for:** family grouping or discovery, which deterministic rules can fix (items 1 and 2).

The owner has also started discussing a link table in Postgres, where the old agent writes links and a worker service
categorises, extracts and health-checks them. Items 1-3 and 6 map onto that design. It is not decided and not built
in this run.

## 10. Change made after the final test (owner request)
The owner asked for the repeated-PDF-parsing fix (§4 bug 5, §9 item 3) to be added to this PR. It was made **after**
the final test, so every held-out score above belongs to tag `pre-final-test`, not to this commit.

- `scraper/mfr_scraper/pdfcache.py`: `ParsedPdfCache.get(sha256, body)` wraps `assets.pdf_text`. Each PDF is parsed
  once, keyed by content hash. Only the extracted result is cached (text, page texts, title, revision date, table
  rows), never the PDF body or pdfplumber objects. Results live on disk in `scraper/cache/parsed-pdf/v<PARSER_VERSION>-p<pages>/`
  (gitignored), so re-runs skip parsing. A byte-capped in-memory LRU serves repeats within a run
  (`PDF_PARSE_MEM_BYTES`, 64 MB). Unreadable entries are parsed again, and failed writes are ignored.
- The run now prints the cache stats and peak memory at the end.
- Tests: `TestParsedPdfCache` covers parse-once and reuse across runs, the memory cap with eviction, and corrupt
  entries.
- End-to-end check: full Bray run with the fetch cache warm, before vs after.

| Bray run | Wall time | Peak RSS | PDFs parsed | Output |
|---|---|---|---|---|
| Before (tag code) | 13 min 08 s | 1,087 MB | 566 parses | — |
| After, cold parse cache | 7 min 10 s | 1,106 MB | 317 parsed, 249 repeats served from memory | identical |
| After, warm parse cache | 1 min 40 s | 285 MB | 0 parsed (317 from disk, 249 from memory) | identical |

"Identical" means `bray.json` is byte-identical once timestamps are masked, and all 439 evidence text files have the
same hashes. The parsed cache for Bray takes 18 MB on disk. Peak memory comes from pdfplumber while it parses, not
from the cache: with nothing left to parse, the warm run peaks at 285 MB.
