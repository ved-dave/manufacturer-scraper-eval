# Cimberio blind relabel (second labeller): ambiguity log

Source share over 55 scored spec fields in 6 families: page-only 1 (1%), PDF-only 2 (3%), both 52 (94%: agree 38, refines 6, conflict 8).

Format: case | decision | SPEC rule

## Conflicts
- 778pvw/778pvws pressure_rating: Specifications sheet + TDS-778 Technical Data say 360 PSI, page says 360 PSI, but TDS-778 p5 legend block (next to CV/CM/CS/MT ball-valve torque legend) says 'Working Pressure: 250 PSI' | value 360 psi (both spec sheets' Technical Characteristics), cross_check conflict, 250 psi from the TDS legend block in alt_values | SPEC 6a: conflicts never resolved silently; numbers never refine
- 778pvw/778pvws temperature_range: sheets + page say 15-200 F; TDS-778 p5 legend block says 'Working Limit for Fluids: -4° F - 248° F' | value 15-200 F, conflict, -4..248 F in alt_values | SPEC 6a
- 30xlc material_body: TDS + page prose 'DZR "CR" corrosion-resistant brass'; page Materials list 'Body: Hot Forged Brass ASTM C37700' | value DZR CR brass (spec sheet), conflict (different alloys), C37700 in alt_values | SPEC 6a ('Brass' vs 'Bronze' style contradiction)
- 30xlc material_seals: TDS 'EPDM-ASTM D 2002 M2 o-rings' vs page 'EPDM - ASTM D 2000 M2' (twice) | value from sheet (D 2002 M2), conflict, page value in alt_values; likely a typo in one source but not resolved | SPEC 6a
- 747nl standards: sheet lists MSS SP-110, PS 117-2004, EN ISO 9001, ISO 5208; page lists EN ISO 9001, ISO 5208 and ANSI B1.20.1 (thread standard) which the sheet lacks | sheet list displayed, conflict, page list in alt_values | SPEC 6a ('the page lists an item the sheet does not')
- 746 size_range: TDS-746 'Sizes: ½" - 2"' vs page part-number table 1/2"-1" | value 1/2-2 (sheet), conflict, page 1/2-1 in alt_values | SPEC 6a: a different range is a conflict

## Judgement calls
- 746 sizes_available: sheet FNPT dimensions table lists 1/2..2 (6 sizes), page lists 3 part-number sizes | sheet list displayed, refines (sheet list contains every page item and more), page list in alt_values | SPEC 6a refines definition for lists
- 746 end_connections: sheet 'FNPT (ANSI B1.20.1), CC (SWT), Press' covers all 746 versions; this NPT page says 'FNPT x FNPT' | sheet value NPT, solder, press displayed, refines, page [NPT] alt; 'CC (SWT)' wording also kept in end_connections_other | SPEC 6a precedence + SPEC 6 controlled vocab (SWT = sweat -> solder)
- 746 PDF text layer: fraction glyphs are custom-encoded (\x10=½, \x13=¾, \x11=¼) and degree is '¡' | quotes copied verbatim from the extracted text (with those characters), clean wording in raw_text | SPEC 6c: quote must appear in the evidence text
- 746 revision_date: sheet code 'TDS-746 á 09-24', file name TechDataSheet-746_10-24.pdf | revision_date 2024-09 from document content | brief: revision_date from the document
- CimPress / CimPRESS connections | mapped to 'press' (brand name of Cimberio's press-fit end; sheets say 'press x press connections') | SPEC 6 controlled vocabulary: press
- 778 family grouping: TDS-778_v5 and Cim 778 SpecificationsV2 are series sheets listing 14 models (778, 778P, 778PV ... 778PVWS) | each US product page is its own family; variants are only the part numbers of that page's model (778PVW-04/06/07; 778PVWS-04/06/07), the other models' part numbers belong to other families | SPEC 3 variants = identifiers listed for this family; SPEC 6b series sheet linked from the page
- 778 material_body: Specifications 'DZR Brass ANSI C27453 or EN 12165 CW511L body'; TDS 'EN 12165-CW511L "NL" Brass'; page 'corrosion-resistant brass' | value from the two spec sheets, refines (DZR = corrosion-resistant brass, more specific), page wording in alt_values | SPEC 6a refines ('Brass' -> 'No-Lead Brass')
- 778 'Technical data applies to Cim 778 ... ONLY (without any options)' | TDS values still used for 778PVW/778PVWS since the Specifications sheet and the page state the same 360 PSI / 15-200 F for these models | SPEC 6a precedence
- 778 standards: TDS 'Threads: NPT - ANSI B1.20.1' and 'Test Pressures: According to ISO 5208' sit in base-778 (NPT) and copied-legend blocks | not recorded as standards for the press-connection PVW/PVWS; ISO 5208 note kept in additional_specs.test_pressures | most useful to a builder; avoid citing blocks that describe other models
- Annex G statement 'Based on NSF/ANSI 61-2008 Annex G in compliance with Section 116875 of the California Health & Safety Code' | not a certification claim; kept in additional_specs.lead_free_compliance. certifications only where a source says 'NSF/ANSI 61 Certified' (778PVW, 778PVWS) | never infer a value
- 30xlc pressure_rating: page has no working pressure (only 'opens at .36 PSI' and test pressures per ISO 5208) | pdf_only 290 psi; opening pressure kept in additional_specs | SPEC 6a pdf_only
- 30xlc material_trim: page 'Disc: EPDM'; stem 'Hot Forged Brass ASTM C37700' (Materials list) vs 'Hostaform thermoplastic free rotating stem' (prose + TDS) | material_trim = disc EPDM (page_only, TDS states no disc material); stem and spring materials kept in additional_specs | SPEC 6 trim = disc/ball; avoid scoring a self-contradicting stem value
- 1220nl standards: page 'Conforms to MSS-SP-110'; TDS 'MSS-SP-110, PS117-2004, and EN ISO 9001' + 'ISO 5208' | sheet list displayed, refines, page list alt | SPEC 6a refines (sheet list contains page list and more)
- 1220nl temperature: both sources state '-4° F to 248° F' and also '250° F temperature rating' | temperature_range -4..248 F (agree); 250° F rating kept in additional_specs.temperature_rating | SPEC 6 temperature range from the explicit range statement
- 1220nl / 747nl applications: 'plumbing and heating applications', 'heating (LPHW) and cooling applications' | no controlled term named (heating != 'hydronic heating', cooling != 'chilled water'), field omitted, wording in applications_other | SPEC 6 mapping strictness
- 30xlc applications: 'domestic and commercial plumbing, sanitary systems, autoclaves, pumps, and compressed air systems' | commercial, compressed air; rest in applications_other ('domestic plumbing' is not 'domestic hot water' or 'residential') | SPEC 6 mapping strictness
- 778 applications: 'domestic hot water recirculation systems' | domestic hot water; 'sanitary circuits' in applications_other | SPEC 6
- 746 applications: 'Ideal for HVAC systems, plumbing installations, sanitary systems, and applications with non-corrosive liquids' | HVAC; rest in applications_other | SPEC 6
- Standards vs certifications: MSS SP-110, PS 117-2004, EN ISO 9001/ISO 9001, ISO 5208, EN 12266-1, ANSI B1.20.1 | all recorded as standards (conformance/manufacture statements), none as certifications | SPEC 6 certifications/standards
- 1220nl Instructions PDF: Italian-parent QA1210 rev. 11 17/06/2019 manual for 'CIM 1220CRNL', in English, hosted on cimberiovalve.us and linked as 'Instructions' from the 1220NL page | included as iom_manual, lang en, revision 2019-06-17; not a spec source | SPEC 2 language from content; SPEC 4 PDFs included
- 747nl TDS page 2 header '747NL Full Port Ball Valve' | template copy error; sheet still used (title and page 1 say 747NL Balancing Valve) | SPEC 6b provenance holds (linked + names series)
- Doc types: TechDataSheet-*.pdf = spec_sheet; 'Cim 778 SpecificationsV2.pdf' (guide specification 'The valve shall be...' + model selection with job/approval block) = spec_sheet | both primary | SPEC 5
- Prices: no amount on any product page (BigCommerce price block renders only '(You save )', purchasable false, no add-to-cart, no option selectors); site header offers 'Request a Quote' | every variant availability request_quote, amount null, quote 'Request a Quote' (site header); no form submitted. The brief said the site shows prices; none observed for these 6 families | SPEC 7 availability always filled
- Variant selectors / tabs: rendered pages checked in a normal browser (Playwright over CDP): 0 option selectors, no tabs/accordions; all content in Additional Information + Product Description | nothing to step through | SPEC 6a
- Images: galleries mix product photos with flow/pressure-drop and pressure/temperature charts | charts excluded (not product photos or dimensional drawings); largest rendition = BigCommerce /images/stencil/original/ URL | SPEC 4 images
- 778pvw image: only product photo is 795x207 at the original rendition | excluded (< 300 px shortest side); family has 0 images | SPEC 4 min 300 px
- 778pvws images: gallery includes two photos of the bare threaded 778 valve body (with binder points) besides the full PVWS assembly | kept as distinct product views (product_photo) since they are on this family's page | SPEC 4 every distinct product view
- BIM: 747NL and 746 pages link 'REVIT' -> DA02770000BIM.rfa / DA03940000BIM.rfa (OLE Revit families, Revit 2017 'Cim747' / Revit 2016 'Cim 746') | cad_type bim, formats [rfa], gated false | SPEC 5 CAD taxonomy
- 747nl 'How to Install' YouTube embed and 778 'Video' embed | not documents/CAD/images; not recorded | SPEC 4
- Blind relabel scope: family_index lists only the 6 assigned families; sample_seed set to 42 only to satisfy the schema (families were assigned, not sampled) | as instructed by the task | task brief
- store-herjth7887.mybigcommerce.com: named as Cimberio asset host in the brief but not referenced by any of the 6 pages | no sites.json change needed (cimberiovalve.us + cdn11.bigcommerce.com already allowed) | task brief

## SPEC changes made
- None.
