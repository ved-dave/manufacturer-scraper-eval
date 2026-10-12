# Harness / SPEC issues

## sioux-chief (gold labelling, SPEC v1.1 relabel)

Most issues from the first pass were adopted on `main` (robots override, `refines`, family-page provenance, multilingual `lang`, installation-photo exclusion, phash warning, `login_required` price coverage). Still open:

1. **`.gitignore` does not ignore `harness/gold/*.evidence/files/`.** The pattern `*.evidence/files/` contains a slash, so git anchors it to the repo root and it only matches `<x>.evidence/files/` at the top level. `git check-ignore harness/gold/sioux-chief.evidence/files/<sha>.pdf` returns nothing. Suggested fix: `**/*.evidence/files/` (or `harness/gold/*.evidence/files/`). For this branch I excluded the folder via `.git/info/exclude` only; `.gitignore` is unchanged.
2. **Family-level lists lose per-variant attribution.** SPEC 6 moves per-variant differences in list fields (`certifications`, `standards`, `applications`, `end_connections`) into one family list. For `certifications`/`standards` this reads as if every variant holds every listing (e.g. `643WG2`: NSF/ANSI 61 for the brass adapters and cUPC for the 645 PVC/CPVC transitions end up in one list). Suggest saying explicitly that a family list is the union over variants, or allowing overrides for certification/standard lists that apply to only some variants.
3. **Parallel-translation documents and the ≥ 50% English rule.** Sioux Chief instruction sheets often carry the full text in EN/FR/ES. English comes first but is about a third of the text, so SPEC 2 excludes them, even though they are the main installation document for the product (3 excluded in this sample). If they should count, the rule could be "English first and a complete English version".
4. **`refines` for terms that aren't strict narrowings.** "A.R.E." (acid-resistant enamel) on the page vs "enamel-coated cast iron" on the sheet: consistent, but neither contains the other, so SPEC 6a leaves it as `conflict`. A `consistent` / `complements` value, or guidance, would help scorers.
5. **(Resolved 2026-10-10: family-level comma list, no overrides; added to SPEC 6.)** **Per-variant differences in single-valued text fields.** SPEC 6 says to override only when the family level can't express the difference "as a range or list". The blind pass read that as allowing a list for `material_body` / `material_seals` (e.g. `["PVC","ABS"]`). Gold uses overrides, because those are `text` kinds in `SPEC_KINDS` and a list loses the variant mapping. The scorer will mark one of the two forms wrong. Please say which form is intended.
6. **(Resolved 2026-10-10: CTS and IPS are valid; added to SPEC 6.)** **`size_unit` for copper-tube sizes.** SPEC lists "NPS / DN / in". Sioux Chief sizes PEX/CPVC/copper products in CTS (copper tube size), so the blind pass used `CTS` and gold used `in`. Please say whether `CTS` is a valid value.


## bray (gold labelling, 2026-10-10)

1. **No family-level price.** Every Bray family is "Request a Quote" and only 2 of 15 list identifiers, so `request_quote` can only be recorded in `labelling_notes` for 13 families. A family-level `price_status` field would make this scoreable.
2. **`refines` heuristic misses three hand-checked refinements.** `srh-series` material_body ("stainless steel" → "CF8M"), `single-door` material_trim ("SS316 as standard (or Higher Grade)" → "Stainless Steel (ASTM A351 CF8M)") and `tri-lok-cx` standards ("EN 12266" → "EN 12266-1", "EN 12266-2") warn as "does not look like a narrower form". Standard part numbers (`X` → `X-1`) and cast/wrought grade equivalents could be treated as narrower forms.
3. **Per-model spec sheets.** Single Door has 14 data sheets, one per model and seat type. SPEC 6a assumes one spec sheet per family; it is unclear whether family-level cross-check should use one representative sheet (done here) or the union of all sheets.
4. **Sheet-only model lists vs the variant rule (resolved).** The SRH sheet lists "SRH1 SRH2 SRH3" with no page identifiers. Ved ruled that SPEC section 3 ("page or spec sheet") wins, so SRH has 3 variants. Open point for SPEC: say explicitly that accessory part numbers (e.g. bracket kits), part-numbering templates and single example part numbers are not variants.
5. **`.gitignore` still does not ignore `harness/gold/*.evidence/files/`** (see sioux-chief #1). Excluded via `.git/info/exclude` on this branch.
6. **No allowed_hosts change.** No cited image comes from `newbrayprod.azurewebsites.net`, so `config/sites.json` is unchanged.


## cimberio (gold labelling, 2026-10-11)

1. **allowed_hosts: added `store-herjth7887.mybigcommerce.com`.** The Resources page links the List Price Book (`/content/PL-Cimberio_V0016.2_LR.pdf`) on this host. It is Cimberio's own BigCommerce store host (same store hash `s-herjth7887` as the product CDN, and its home page redirects to cimberiovalve.us with the Cimberio title and canonical). Not a distributor. The same file (identical SHA-256) is also at `cimberiovalve.us/content/`, but the link on the site points to the store host, so gold cites that URL.
2. **PDF glyph mapping in two Cimberio sheets.** TDS-746 and TDS-3739 use a subset VAGRounded font with no Unicode map for fractions: PyMuPDF returns `\x10` for ½, `\x11` for ¼, `\x13` for ¾, and MacRoman mojibake (`¡` for °, `¥` for •). The committed evidence text for these two PDFs applies this mapping (checked against page renders). Otherwise a quote such as `Sizes: 2½" - 8"` cannot be matched. The validator could map C0 control characters, or SPEC could allow a documented glyph map in evidence text.
3. **`refines` heuristic warns on `material_body` for the 778 series** ("corrosion-resistant brass" on the page vs "DZR Brass ANSI C27453 or EN 12165 CW511L" on the sheet) and for 74PRSNL. Same issue as bray #2: alloy designations are narrower forms.
4. **Variant prices come from a price-list PDF, not the product page.** Product pages show only "Request a Quote". Exact Cim No. rows in the linked List Price Book give a public `list` price (`availability=price_shown`, source = PDF page quote). SPEC 7 does not say which wins when the product page says request-a-quote but a public list price book prices the same SKU. Gold uses the price book, because it is a published price with an exact identifier match.
5. **SPEC 5 page-count rule vs one-family technical data sheets.** TechDataSheet-778_v5 is titled "Technical Data Sheet" but is 8 pages and covers 14 models, so rule 2 makes it a `catalog`. That moves it below the product page in SPEC 6a precedence, and its values no longer take part in the cross-check.

6. **Consistency pass (2026-10-11).** Two SPEC 6 clarifications added (`spec:` commits): standards spelling-only differences, and flange-only PN designations vs a stated working pressure. No harness or allowed_hosts change. Note: this file contains a stray merge-base marker line `||||||| e34e4bf` after the crane blind re-label section (left as is).

## crane (gold labelling, 2026-10-11)

1. **`config/sites.json`: no `allowed_hosts` change; `cad_viewer_hosts` added.** Every Crane PDF, image and CAD zip is served from `www.cranefs.com/app/uploads/`, so `allowed_hosts` stays `["www.cranefs.com"]`. The "BIM - ... Revit" download links go to the third-party BIM library bimstore (`www.bimstore.co`, `www.bimstore.co.uk`), which needs an account to download. These are not Crane hosts, so they were added to the crane `cad_viewer_hosts` (hosted CAD/BIM library, like partcommunity) and recorded as `cad_viewer`, `gated: true`. Consider adding bimstore to `global_cad_viewer_hosts`: other UK manufacturers use it too.
2. **`market_flag` warning for a single-locale non-US site.** cranefs.com is a UK (en-GB) site with no locale prefix. Gold uses `non_na`; the validator warns "URL locale None suggests na" for all 15 families. A per-site default market (e.g. `market: non_na` in sites.json) would remove the false warning.
3. **Grouped sheets that cover sibling families.** Many Crane sheets cover 2-3 figures that each have their own page (D102B/D103B/D104B, F611/F626, D931/D933/D934). SPEC 3 says variants are identifiers "on the page or in the family's spec sheet", which would make D102B a variant of D103B. Gold excludes identifiers that have their own family page (written into SPEC 3 in this branch).
4. **Size lists for reducing fittings.** For reducing bushes (Fig. 140) the size is a pair ("1/2 x 1/8"). `size_range` min/max hold strings, so gold uses the larger end (1/2 .. 6) for `size_range` and keeps the full pairs in `sizes_available`. SPEC could state this.


## crane (blind re-label)
- config/sites.json: added `bimstore.co.uk` and `bimstore.co` to `global_cad_viewer_hosts` (Crane BIM/Revit links go to BIMstore; recorded as gated cad_viewer, never logged into).
- validate.py market_flag check uses only the URL locale, so an en-GB-only site with no locale prefix WARNs "suggests na" even though SPEC 1 says en-GB -> non_na.


## apollo (gold labelling, 2026-10-11)

1. **Site blocked.** Every URL on `aalberts-ips.us` (incl. robots.txt and sitemap.xml) returns a LiteSpeed reCAPTCHA "Bot Verification" page, to the labeller's HTTP client and to a normal Chrome browser (visible image challenge), over 45 minutes of single, spaced retries. No answer key built; details and evidence in `apollo.ambiguities.md`. Apollo should be handled like Dixon (scraper expected to report it as blocked) until the site is reachable.
2. **No gold form for a blocked site.** `validate --gold` errors when `family_index` is empty, so a blocked site cannot have a valid gold stub. `gold/apollo.json` was therefore not committed. Suggest either keeping blocked sites out of `gold/` (current Dixon practice) or accepting a stub with `site_profile.blocked: true` and no families, scored only on whether the agent reports the block.
3. **No allowed_hosts change.** Nothing beyond the blocked pages and the `aalberts.compano.com` login redirect was reachable, so `config/sites.json` is unchanged.

## caleffi (gold labelling, 2026-10-11)

1. **`config/sites.json`: no change.** Every Caleffi page, PDF, CAD file, image and the price workbook is served from `www.caleffi.com`. The generic BIM portal `bim.caleffi.com` is not product-specific and is not recorded, so no host was added.
2. **No spreadsheet source type.** The US price list is an xlsx ("June 1, 2026 List Price sheet.xlsx"). The schema's source `type` is `page|pdf`, so gold cites it as `pdf`, `page` 1, `section` "Sheet1", against a TSV text snapshot of the sheet. Proposed SPEC wording: "Spreadsheet price lists (xlsx/csv) are cited with `type: "sheet"`, `section` = worksheet name, `page` = null, and the snapshot is a tab-separated text dump of the worksheet." Until then, gold applies the `pdf` reading consistently.
3. **Sell sheets with a technical-data block.** Caleffi's 2-page "sell sheets" carry a CODE table and a MAX. WORKING PRESSURE / TEMPERATURE block. Proposed SPEC 5 wording: "A document of four pages or fewer about one family that has a technical-data block is a `spec_sheet` whatever its title; `brochure` only when it has no technical-data block." Gold applies this (03555, 03667, 03618 -> spec_sheet).
4. **One-bound temperature ratings.** Several sheets state only a maximum ("Max. working temperature: 240°F"). Gold records `temperature_range` `{max: N}` with no `min`. Proposed SPEC 6 wording: "When a source states only one bound, `temperature_range` holds only that bound."
5. **Series field spanning unrelated products.** Caleffi's "Series" field covers different products (574 = AutoFill and FlowShield). Gold groups by (series code, product name before the first comma). Proposed SPEC 3 wording: "A shared series code makes pages one family only when they also share the product name/type."
6. **`refines` warning for alloy designations.** The validator warns on 3048 `material_body` ("DZR low-lead brass CW724R-M" vs page "DZR low lead brass") because of the hyphen. Gold keeps `refines` (Bray precedent: sheet adds the alloy).
7. **Blind re-label: family-spec agreement before fixes was 43% (below 80%).** Most of the gap was gold omissions (size_unit; sizes or connections the page states), which are now fixed. Three rules were read differently:
   - *Cross-check against a catalog.* Proposed SPEC 6a wording: "`cross_check` compares the page with every PDF that states the field, catalogs included; precedence still decides `value` (a catalog never displaces the page)." Gold applies this (crane 140/257 precedent).
   - *Sheets covering more than the sampled code.* Proposed SPEC 6b wording: "A spec-sheet statement is a source for a code only when it describes that code; size/connection lines for sibling kits (e.g. complete valves with fittings) do not apply to a body-only code."
   - *Component lines.* Proposed SPEC 6 wording: "A material stated for one component of an assembly (e.g. 'mixing valve unit: body brass' in a mixing station) is not the product's `material_body`."
