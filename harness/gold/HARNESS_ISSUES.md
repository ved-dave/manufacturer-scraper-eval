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
4. **Sheet-only model lists vs the variant rule.** The SRH sheet lists "SRH1 SRH2 SRH3" with no page identifiers. DEVIN_TASK says identifiers "on the page or in the family's spec sheet"; the Bray decision limited variants to page models. Worth stating in SPEC 3.
5. **`.gitignore` still does not ignore `harness/gold/*.evidence/files/`** (see sioux-chief #1). Excluded via `.git/info/exclude` on this branch.
6. **No allowed_hosts change.** No cited image comes from `newbrayprod.azurewebsites.net`, so `config/sites.json` is unchanged.
