# Bray: ambiguity log

Labelled 2026-10-10 against SPEC on main (80104b4 or later): variant = orderable item with its own identifier (SPEC 3), material lists at family level, controlled `end_connections` / `applications` vocabularies, size units NPS/DN/CTS/IPS/in/mm.

## Spec source breakdown (15 families)

| Family specs come from | Families |
|---|---|
| Both page and spec sheet | 15 |
| Page only | 0 |
| PDF only | 0 |

Per family-level spec value (129 values; no variant overrides):

| agree | refines | conflict | page_only | pdf_only |
|---|---|---|---|---|
| 68 | 10 | 19 | 14 | 18 |

## Scope and family index

1. **Family = one English Bray product page** (Specifications + Downloads tabs), keyed by Bray's series name. Combined series ("Series 20/21", "Series 22/23", "Series 5000/6000") are one family because Bray publishes one page and one spec sheet for them.
2. **103 families: 79 in both sources, 24 crawl only, 0 sitemap only.** The crawl-only pages (e.g. Series 76, 98C, 98EH/98H, PVA, the five Cx Line pages, 3W/3L) are live product pages missing from `sitemap.xml`.
3. **Excluded:** 3 sitemap URLs returning 404 (Series 39 resilient, 770, 950); 5 PFA-lined URLs that redirect to amresist.com (sister company, outside allowed_hosts); category/filter pages; "closer look"/"discover" marketing pages; the drawings/BIM resource library (no files in page source); locale duplicates (recorded as `alternates`).
4. **Categories** come from the Products menu. The pinch valve sits under Knife Gate Valves there and was kept in that category; Cx Line is under Integrated Solutions.

## Sample and coverage

5. **"≥ 3 families with more than one variant": met, 3 families.** Under SPEC 3 (identifiers listed on the page or in the spec sheet): Single Door (8 models, page), Series SA16 (3 models, page) and SRH Series (SRH1-3, sales data sheet model table). SA16 was swapped in for PEZ SA-4AX at the checkpoint.
6. **SRH Series variants come from the sheet only.** The page lists no identifiers; the sales data sheet model table lists "SRH Model # SRH1 SRH2 SRH3" (handle lengths 10.47 / 13.38 / 19.125 in). Ved's 2026-10-10 follow-up: the SPEC 3 rule wins over the earlier Single Door/SA16-only list, so these are variants (request_quote, no overrides). Identifiers found on the other 14 families were re-checked against the rule and NOT made variants:
   - **5A, 5B, 5B Resin bracket tables ("VSM / Actuator Std. Part No.", e.g. 5B0000-22600534):** these are mounting-bracket kits, a separate accessory product, not versions of the switch box.
   - **"Part Numbering System" charts** (5A, 5B, 5B Resin, Tri Lok, Tri Lok-Cx, 746HP, 942 manuals; 5000/6000 selection guide): code templates such as "5A000X-126X X XXX / E X", not a list of orderable items.
   - **Example part numbers on the per-model Single Door / SA16 sheets** (e.g. "V0215SMZ (For 2”, Class 150, ... Series 210)"): one illustration of the code per sheet; the models themselves are already variants.
   - **70-HAZ "S70-130/180":** sizes named in an IP-rating exclusion, not a listed set of orderable items.
7. **CAD coverage swap across categories.** All five CAD families (STEP zips) are Control Accessories, so Series F15/F30 (Ball Valves) was replaced by Series 5B to reach 3 CAD families (approved).
8. **Not CAD:** Series 70 zip (PLC software installer), 5B/5B Resin DeviceNet zip (`.eds`, `.ico`) and Profibus zip (`.gsd`). Listed in `labelling_notes`, not in `cad`.

## Variants and prices

9. **Price: every family shows only "Request a Quote".** Recorded as `request_quote` in every family's `labelling_notes` and as a `request_quote` price on each Single Door and SA16 variant (schema has no family-level price).
10. **SA16 models: page says "205, 211, 212"; the SA16 sheet says "Compatibility Bray 205, 210, or 211 Series".** Page models used as variants (the page is the identifier source); discrepancy kept in `additional_specs.compatibility`.
11. **Single Door has 14 per-model data sheets** (205/210/211/212-312 by seat type) and no sheet for 201, 203, 260. The Series 210 seat-ring hard-seat sheet is used as the family spec sheet; seat materials and body style stay page values because they are split across sheets. Each data sheet carries `variant_skus` for its model(s).
12. **Example part numbers are not variants:** Single Door sheet "part number: V0215SMZ (For 2”, Class 150, ...)" is a configured example; Series 5B technical manual bracket kit numbers are accessories. Series 5000/6000 part-number selection guide is a configurator code, not a list.

## Field mapping calls

13. **Component → field:** disc/gate → `material_trim`; knife-gate liner (746HP polyurethane) → `material_seat`; packing / O-rings / seal rings → `material_seals`; seat energizer, stem, spacer kept in `additional_specs`.
14. **Non-numeric temperatures** (Single Door "Cryogenic to High Temperature (Pending Model Selected)", SA16 "Pending Materials Selected") are in `additional_specs`, not `temperature_range`.
15. **Pressure depends on gate material and size (746HP).** The highest rating (232 psi, Duplex 2205 & 17-4PH gate, NPS 2-24) is the value with `conditions`; the full table is in `additional_specs.pressure_rating_by_gate`.
16. **Applications mapping:** "Power" → `power generation`; "Water & Wastewater" → `wastewater`; "Steam Distribution" → `steam`; "Upstream Oil and Gas"/"oil & gas" → `oil and gas`; "Chemical Processing" → `chemical`; "Pulp and Paper Liquor" → `pulp and paper`. "Water" alone, "Geothermal Steam", "Refining", "Shipbuilding", "LNG", "Cryogenic Services", "Solids Handling" etc. kept verbatim in `applications_other` (no potable wording; geothermal steam is a sector, not the steam service).
17. **Body styles:** "Gate" (Tri Lok) is the long double-flanged pattern → `flanged`; "RTJ" and 746HP "Solid Flange / Double Flange" body figures → `end_connections_other`.
18. **Images (SPEC 4 Images row, revised 2026-10-10):** every distinct product view (photos, 3D renders, cutaways) is a `product_photo`; no dimensional drawings appear on the Bray pages. Dropped: smaller renditions (filename stem / URL key / phash ≤ 2; largest kept), and crops/zooms of a kept view: 746HP `heroshot-05--copy` (zoom of the two-valve `--copy-2`) and the 5A 600x600 homehero (zoom of the 640x406 version). Excluded: the 5A/5B indicator-option chart (8 tiles with labels, an options infographic) and the Series 942 "closer look" in-pipe scene (in-use scene, SPEC 4). The lettered/numbered callouts on the cutaways are small, so the cutaways count as product views, not infographics. 39 images across the 15 families.
19. **Document types:** Sales Data Sheet, Recommended Specs and Weights & Dimensions = `spec_sheet`. The switch boxes (5A, 5B, 5B Resin) have none of these, so their product Technical (Sales) Manual is the spec sheet (changed after the blind re-label). Other Technical Sales Manuals = `catalog`; SIL Safety Manuals and the 5B/5C CommPro protocol manual = `other_doc`; Reference/Selection guides, bulletins, bolting guides = `other_doc`. The 1B "HIPPS-Compliant Fast-Acting Valve Solutions" PDF stays `spec_sheet` per Bray's "Sales Data Sheet" label even though it covers Tri Lok and 1B together (blind: `brochure`); it carries no cited value.

## Conflicts (19)

Displayed value is the spec sheet's, except Series 5000/6000 and Series 1B, where the PDF is a brochure / selection guide (not a spec sheet), so the page value is displayed (SPEC 6a precedence).

| Family | Field | Page | PDF |
|---|---|---|---|
| Series 5000/6000 | standards | ASME B16.34, MSS SP-72, API 598, ASME B1.20.1, ASME B16.11 | adds ISO 5211; lacks ASME B16.34, API 598 |
| Series 1B | pressure_rating | ASME CL150, 300, 600, 900, 1500 | ASME Class 150, 300, 600, 900 (brochure) |
| Series 1B | material_seals | Graphite (body seals) | Graphite, NBR, Viton (brochure BOM) |
| Series 1B | standards | API 6D, ASME B16.34, API 598, ASME B16.10, ISO 15848-2 | API 6D, ASME B16.34, PED, ASME B16.5, ASME B16.25, NACE MR0175 (brochure) |
| Series 20/21 | certifications | adds ATEX, NSF 372, PE(S)R | CE/PED, NSF/ANSI 61, SIL, ABS, BV, DNV (2012 Recommended Specs) |
| Tri Lok | end_connections | adds Wafer | Lug, Double Flanged, Buttweld |
| Tri Lok | certifications | adds PE(S)R, TR CU | EAC instead of TR CU |
| Tri Lok | standards | adds ISO 7005, "EN 1092" | adds ISO 5211, MSS SP-101, EN 1092-1 |
| Series 22/23 | certifications | adds ATEX, PE(S)R | CE/PED, SIL, ABS, BV, DNV |
| Single Door | material_body | adds Titanium | WCB, CLB, A395, CF8M |
| Single Door | pressure_rating | adds API 594 classes 150-2500 | ASME 125/150/300, DIN PN10-40 |
| Single Door | certifications | adds API 6FD, FM, ULC | CE/PED, CRN, NSF-61 |
| Single Door | standards | adds API 594 | ASME B16.34, API 598 |
| Tri Lok-Cx | size_range | DN 80 to 600 | DN 80 to 400 |
| Tri Lok-Cx | temperature_range | -60°C to 400°C | -60°C to 450°C |
| Tri Lok-Cx | pressure_rating | 40 bar | PN 10, PN 25, PN 40 (number vs class list; numbers never refine) |
| Series 746HP | material_trim | adds Titanium gate | sheet gate list |
| Series 746HP | applications | adds Wastewater | Mining, Power, Chemical |
| Series 942 | temperature_range | seat/packing "Up to 482°F (250°C)" | -40°F to 392°F |

## Refines (10)

SRH material_body (page "heavy duty stainless steel" → sheet "CF8M"); Series 5B material_body (page "aluminum base and cover" → manual "Die cast aluminum"); Tri Lok material_body and material_trim (sheet adds alloys); Single Door material_trim ("SS316 as standard" → "Stainless Steel (ASTM A351 CF8M)"); Tri Lok-Cx certifications (+API 607), standards (+EN 558; EN 12266 → EN 12266-1 & 2), applications; Series 942 certifications (+CRN) and standards (+ASME B16.5). The validator's heuristic warns on three of these (SRH material_body, Single Door material_trim, Tri Lok-Cx standards); both kept as refines by hand review.

## Blind re-label (6 families, separate session, never saw gold)

Random(42) draw of 6 from the 15: Series 5A, Series 70-HAZ, SRH Series, Series 5B Resin, Series 5B, Series 1B. "Before fixes" = raw blind vs my first-pass gold (commit 51148a1); "after fixes" = current gold.

| Row | Before fixes | After fixes |
|---|---|---|
| Variants (family SKU sets) | 5/6 (83%) | 6/6 (100%) |
| Documents (found + doc_type) | 33/44 (75%) | 43/44 (97%) |
| CAD (zip + formats) | 3/3 (100%) | 3/3 (100%) |
| Images (matched either way) | 9/17 (52%) | 7/16 (43%) |
| Family spec fields (value) | 28/32 (87%) | 29/32 (90%) |
| Variant overrides | 6/6 (100%) | 6/6 (100%) |
| cross_check values (fields in both) | 24/30 (80%) | 28/30 (93%) |

Images across the three rule states: first pass 9/17; after the blind fixes under the old rule (cutaways excluded) 8/13; under the revised SPEC 4 rule 7/16. The blind pass ran under the old rule, so the cutaways now kept (5A, 5B Resin) count as gold-only. Two more mismatches are the same render at a different crop (5A homehero: gold keeps the full 640x406, blind the 600x600 zoom; 1B banner: gold keeps the 4278x1416 full banner, blind the 2000x1302 crop), and phash doesn't match crops. Counting those two as matches gives 9/14. The rest are gold-only distinct photos (5B Resin bare box, 70-HAZ second angle, SRH second handle view), each checked visually.

Gold fixed where the blind pass was right:
- SRH material_body: page "stainless steel" missed → `refines`.
- 5A material_body: page "die-cast aluminum" missed → `agree`.
- 5B material_body: page "aluminum" → `refines`.
- 1B material_seals: page Graphite missed; was NBR/Viton only → `conflict`.
- Switch-box Technical (Sales) Manuals → `spec_sheet`; Safety Manuals and CommPro → `other_doc`.
- Duplicate crops collapsed.
- SRH variants SRH1-3 (after Ved's SPEC 3 ruling).

Kept gold (blind differs):
- **70-HAZ certifications `agree`:** the Recommended Specs PDF says "Hazardous location enclosure shall be UL certified to:"; blind recorded page_only.
- **1B material_trim `agree`:** the brochure BOM lists all four ball materials incl. "ASTM A182 Gr. F316 w/ENP"; blind recorded a conflict.
- **1B pressure_rating / size_unit:** blind left class-only pressure and size_unit out; gold records "ASME CL150 ... 1500" (conflict with brochure 150-900) and `in` from the page's inch sizes.
- **1B standards:** blind also listed ISO 15848-1 under standards; gold has it only in certifications, where the page puts it.
- **1B HIPPS PDF doc_type:** see #19.
