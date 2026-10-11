# crane blind re-label — unclear cases

Spec source share (6 families): all 6 families `both` (page + PDF). 4 families have a spec sheet (datasheet displayed); 257 and 140 have only a multi-product catalog PDF (page displayed where both state a field).

## Conflicts
- d171aexs size_range | page `1/4" to 2"` vs datasheet table `1/2 ... 2` -> datasheet {1/2, 2} displayed, page in alt_values, cross_check conflict | SPEC 6a (numbers never refine)
- 257 / 140 standards | page `BS taper to BS21 and ISO7` vs catalog `Design standard BS EN 10242` / `Thread standard BS EN 10226-2 taper` -> page ["BS 21","ISO 7"] displayed (catalog is lower precedence), catalog list in alt_values, conflict | SPEC 6a precedence; lists that name different items are conflict

## Judgement calls
- market_flag | site is en-GB only (html lang="en-GB", no hreflang) -> non_na; validator WARNs "URL locale None suggests na" (6 warnings, accepted) | SPEC 1 table "Only international English (en-GB) -> non_na"
- prices | no price, cart, quote or price list anywhere; only a "Distributor" locator link -> availability not_published (family_prices for 5 families, per variant for d103b) | SPEC 7
- variants f621/f634/d171aexs/257/140 | sizes have no own identifiers on page or datasheet -> no variants, sizes in sizes_available | SPEC 3
- variants d103b | datasheet D103B table lists part numbers 0JG93620L/21M/22N/23P/24Q per size -> 5 variants; D102B table (0JG93607P..11K, single KVS column) is the 2-port sibling, excluded (3-port table identified by KVS DIRECT WAY / ANGLE WAY columns) | SPEC 3
- f634 Valve Selection | F635 (gearbox) / F635B (bare shaft) are separate products, not F634 variants | SPEC 3
- d171aexs `.AT` suffix / malleable `G` suffix | part-numbering templates, not variants | SPEC 3
- 257 / 140 malleable brochure | 24-page multi-product "Malleable Pipe Fittings Brochure & Datasheets" -> doc_type catalog (not spec_sheet) | SPEC 5
- 140 / 257 per-size "Fig. No. ... PDF" | single-page outline drawings with no dimensions and no extractable text -> other_doc, lang en (rendered text "CRANE FLUID SYSTEMS 1/2" x 1/4" Hexagon Bush Fig. 140") | SPEC 5 rule 5 (no technical-data block, so not spec_sheet)
- Stress Corrosion Cracking statement | technical bulletin -> other_doc, revision_date 2020-03-31 from "31/03/2020 issued by the Engineering Department" | SPEC 5
- revision_date of datasheets | "Vaild as of DDMMYY" read as day-month-year (081220 -> 2020-12-08, 130325 -> 2025-03-13, 240124 -> 2024-01-24; F634 21/11/25 -> 2025-11-21); IOMs show only "Rev A" -> null | SPEC 5
- certificates revision_date | WRAS = "Certificate issued" date; Kitemark = "Latest Issue"; UL = "Issue Date" | SPEC 5
- BIMstore links (f621, d171aexs) | third-party Revit library, needs account, not opened -> cad_viewer gated; bimstore.co.uk + bimstore.co added to global_cad_viewer_hosts | task brief
- CAD ZIP formats | listed from ZIP contents (dwg, iges, step, ipt; Creo .prt.1 -> prt); 140-0.75x0.50.zip has no .ipt and also carries unrelated legacy PDFs; 140-1.00x0.75.zip carries logo images — ignored | SPEC 5 CAD
- butterfly liner | EPDM liner of a resilient-seated butterfly valve recorded as material_seat; disc -> material_trim; O-ring -> material_seals | SPEC 6 materials
- f621 end_connections | "Semi-lugged" -> lug; page "To suit flange connections BS EN 1092-2 ..." describes mating flanges -> end_connections_other | SPEC 6 mapping strictness
- d103b end_connections | "BSP Female Parallel ISO-228" -> BSPT (literal "BSP" wording in the BSPT row), parallel noted in end_connections_other | SPEC 6 mapping strictness
- d171aexs US end connection | "ANSI B1.20.1:1983" names no listed NPT wording -> end_connections_other | SPEC 6 mapping strictness
- standards scope | product conformance standards plus thread/flange standards named in the end-connection spec | SPEC 6 (silent) — proposed: "standards = every standard the source says the product conforms to or is threaded/drilled to"
- 257 / 140 applications | catalog cover "IDEAL FOR" list is range-wide -> natural gas, compressed air, steam (from "Hot Water & Steam"), chilled water (from "Chilled/Heating Water"); 140 also fire protection (UL section lists 140); Sprinkler Systems, Heating Water, Hot Water, Fuel Transfer -> applications_other | SPEC 6 mapping strictness
- 140 sizes | reducing designations kept as "1/2 x 1/8" ... "6 x 4" (40 rows, catalog p.7); size_range uses the larger outlet 1/2 .. 6 | SPEC 6 (silent on reducing fittings)
- 257 size_unit | 257 catalog table header has no unit -> size_unit omitted (140 table header says "(inch)") | never infer
- 257 / 140 material_body | page "Malleable Iron - Black or Galvanised" -> value "Malleable Iron", finishes in additional_specs.finish | SPEC 6
- d103b material_body page source | page states it only in the title "3 Port Valve – Cast Iron" -> used as page source (agree) | SPEC 6a
- f634 images | photos on the F634 page are named F631_... -> kept as linked (live-site fact), product_photo | SPEC 4
- 257 "c" images | exploded component view of the union -> distinct product view, product_photo | SPEC 4
- d171aexs YouTube video | not a document/CAD/image -> not recorded | SPEC 5
