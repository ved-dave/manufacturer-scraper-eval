# caleffi blind re-label — labeller's judgement calls

Written by the blind session (input: evidence text only). Comparison: `python gold/caleffi.blind.compare.py gold/caleffi.json DIR` (DIR = one <family_id>.json per family; caleffi.blind.json holds the same six).

# Blind labelling — 6 Caleffi families (en-us): main judgement calls

Sources: packet texts only. Every scored value has a verbatim quote, script-checked against the cited packet file (0 misses).
Precedent: harness/gold/*.ambiguities.md (non-Caleffi) only.

## Doc typing
- Multi-series technical brochures (5024: 01090_NA covers 7 series over 5 pp; 03194 water-treatment, 44 pp; na162: 03511_NA Presscon selector) are typed **catalog**. They rank below the page and are not cross-check partners, so the page values show as `page_only` with the catalog values in `alt_values`. Where only the catalog gives a value, it is `pdf_only`.
- Single-family sheets with tech data of 4 pages or fewer are typed **spec_sheet**: 3048 01403 and 03667 sell sheet, 5350 01085, 172 01155. 3048 03506 is typed **submittal**.
- Revit content guide NA11011 and the Idronics 7/16 journals are typed **other_doc**. The per-SKU "(pdf).pdf" drawing for 5024 is also **other_doc**, not CAD.
- 5024's 38459_NA is the instruction sheet for 5026/5027 and never mentions 5024. It is kept as iom_manual but not used as a spec source.

## Variants
- **172**: 22 SKUs (3–13 outlets, each with an "IN" inverted row). The IN codes are their own rows in the part-number table, so they are variants, not suffix options.
- **na162**: includes NA16265L (from the page heading/breadcrumb) plus the 3 part-number rows. The size for NA16265L comes from the catalog line.
- **5350-body**: only 535951A. The sheet codes 535051A/56A/59A/66A belong to the separate 5350 AutoFill page.
- **na39753**: the "Compatible with" series belong to other families. They are not variants.
- **3048**: 17 SKUs across 5 connection pages.

## Conflicts and other spec calls
- **3048 pressure**: spec sheet 01403 and submittal say 160 psi (11 bar); the page and the 03667 sell sheet say 175 psi. Marked conflict, displaying 160 psi.
- **3048 certifications**: only ASSE 1024 and CSA 64.5 count, because the sheet says "certified" for those two. NSF/ANSI/CAN 61/372 are worded "complies", so they go under standards only. IPC/IRC/UPC are plumbing codes and are not counted as standards.
- **3048 IOM**: it says "CSA B64.6"; this is noted but not used.
- **3048 applications**: "hydronic or irrigation" appears only as a back-syphon example, so it is not mapped.
- **5350-body**: the body-only page (1" G male) conflicts with the family sheet (3/4"–1" NPT/sweat/press union) on size_range and end_connections. The sheet value is displayed (SPEC 6a). "Commercial applications" in the page title gives the applications value `commercial`.
- **172 temperature**: temperature_range is the primary inlet max of 195°F. The 80–130°F control range is treated as an additional spec (mixing-valve precedent).
- **172 material**: material_body is brass (the mixing valve and manifold bodies). The cast-iron pump body is treated as a component.
- **na162 material**: material_body is copper, taken from the product name "Long copper press tail piece".
- **na162 ratings**: pressure (200 psi), temperature (0–250°F) and NSF/ANSI 372 come from range-wide catalog statements and are `pdf_only`. ASTM-B88 describes the pipe, not the product.
- **5024 standards**: "ISO 228-1A" is recorded as written in the connection text. The thread is recorded as `threaded`.

## Applications, CAD and images
- **Applications**: wording like "hydronic", "heating systems" or "radiant" that doesn't use a listed term is not mapped.
- **CAD**: only 5024 has CAD links (dwg/dxf/igs/stp). 172 shows "3D models bim" but the packet has no link, so cad is empty.
- **Images**: renditions with phash distance 0 were deduplicated, keeping the product/cover original. 160 px thumbnails were dropped.
- **5024/172 image pairs**: the cover-jpg/png-webp pairs are more than 12 phash apart, so both images are kept as separate views.
