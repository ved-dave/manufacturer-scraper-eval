# Devin prompts: answer-key labelling

Paste these into Devin one at a time. Prompt 1 → checkpoint reply → (review) → Prompt 2.

---

## Prompt 1 (pilot: Sioux Chief)

```
Project folder on my machine: /Users/veddave/Desktop/url_csv_dataset

You're building a hand-verified answer key that we'll use to score web-scraping agents.
No scraper is being built in this task.

SETUP: work in your VM, not on my machine
1. Copy these from my project folder into your VM workspace:
   SPEC.md, harness/ (everything in it), and train/, dev/, test/, challenge/.
2. Do ALL crawling, downloading, labelling, tests, and validation inside your VM.
   Do not run anything on my machine and do not install anything on it.
3. In the VM, from harness/:
   python3 -m venv .venv && . .venv/bin/activate
   pip install -r requirements.txt imagehash Pillow pypdf
   python -m unittest discover tests      # must pass, including the schema test (no skips)

READ FIRST, fully, in this order (your VM copies):
1. SPEC.md (the rules: what counts, labels, precedence, provenance, evidence)
2. harness/DEVIN_TASK.md (your step-by-step task and acceptance criteria)
3. harness/schema/siterun.schema.json and harness/gold/_TEMPLATE.json (exact output format)

SCOPE: the site `sioux-chief` ONLY (https://www.siouxchief.com/).

CHECKPOINT: after DEVIN_TASK steps 1–3 (site profile, complete family_index from two
sources, and the 15-family sample), STOP and send me:
- the platform/locale findings and any proposed allowed_hosts changes
- family_index counts (sitemap only / crawl only / both) and how you grouped SKUs into families
- the 15 sampled families with their categories, and any coverage swaps
Wait for my approval before labelling.

HARD RULES
- Follow SPEC.md exactly. If the spec is unclear, make a reasonable call, log it in
  gold/sioux-chief.ambiguities.md, and continue. Don't guess silently.
- Do not modify harness/mfr_harness/, harness/schema/, or harness/tests/. Report harness bugs
  or spec gaps in harness/gold/HARNESS_ISSUES.md instead. You may propose allowed_hosts changes
  to config/sites.json, but list each change in HARNESS_ISSUES.md.
- Polite crawling: obey robots.txt, at most 1 request/sec per host, a descriptive User-Agent,
  no logins, no form submissions, no bot-protection workarounds. If you're blocked, record it and tell me.
- Never infer spec values. Every value needs a verbatim quote that appears in your saved evidence text.
- Check every spec field on BOTH the product page (all tabs and variant selectors) and the spec PDF.
  On a conflict, display the spec sheet value, keep the page value in alt_values, and flag it.
- Do not run harness/mfr_harness/score.py.

DONE (all checked inside the VM):
- `python -m unittest discover tests` passes with no skips
- `python -m mfr_harness.validate gold/sioux-chief.json --site sioux-chief --gold` reports 0 errors
- Every box in the DEVIN_TASK.md acceptance checklist is ticked, or the reason it can't be is explained

DELIVER BACK TO MY MACHINE
Copy ONLY these into /Users/veddave/Desktop/url_csv_dataset/harness/ on my machine,
and overwrite nothing else:
- gold/sioux-chief.json
- gold/sioux-chief.ambiguities.md
- gold/sioux-chief.sample.py
- gold/sioux-chief.evidence/ (files/, text/, manifest.csv)
- gold/HARNESS_ISSUES.md
- config/sites.json, only if you changed allowed_hosts

Then send me a summary with: the full validator output, the page-only / PDF-only / both
breakdown, the number of conflicts, the re-label agreement numbers, and the top 5 ambiguities.
```

---

## Checkpoint reply

If the family list and sample look right:

```
Approved. Proceed with steps 4–6 for the 15 sampled families.
```

Otherwise correct it first, e.g. "Family X is really two series, split it" or "Swap in a family that has a price list."

---

## Prompt 2 (Bray, after reviewing Sioux Chief)

Fold anything learned from the Sioux Chief review into `SPEC.md` first, then:

```
Same task and same rules as sioux-chief, now for the site `bray` (https://www.bray.com/).
First re-copy SPEC.md and harness/ from /Users/veddave/Desktop/url_csv_dataset into your VM;
they may have been updated after the Sioux Chief review.
Bray is multilingual: use only the US English pages (SPEC section 2), and record the other
language versions as alternates. Bray's CAD files are STEP files inside zip archives, so open
each zip and list the formats inside.
Same checkpoint after steps 1–3. Deliver gold/bray.* back to my machine the same way.
```

---

## Reviewing what Devin delivers

1. **Spot-check 2–3 families by hand** against the live site. This is the only check that catches labels that are wrong but still pass validation.
2. **`ambiguities.md`:** each judgement call is a candidate addition to `SPEC.md`.
3. **The conflicts list:** if there are many, verify one or two by hand.
4. **`HARNESS_ISSUES.md`:** fix the harness before running Prompt 2.
5. **Re-validate locally:** `cd harness && python3 -m mfr_harness.validate gold/sioux-chief.json --site sioux-chief --gold`

---

## Prompt 3: fix PR #1 (Sioux Chief) after the spec update (2026-10-09)

```
Follow-up on your Sioux Chief answer key (PR #1, branch gold/sioux-chief). The spec and harness changed
based on your HARNESS_ISSUES.md and ambiguity log. Thank you; most of your suggestions were adopted.

SETUP
Re-copy SPEC.md and harness/ (everything except harness/gold/) from
/Users/veddave/Desktop/url_csv_dataset into your VM, overwriting your copies. Then from harness/:
  python -m unittest discover tests        # must pass, 16 tests, none skipped
Read the changed parts of SPEC.md: 1a (crawling), 2 (multilingual lang), 4 (installation photos),
6 (family vs variant level, single size), 6a (`refines`), 6b (provenance).

WHAT CHANGED
- robots.txt is no longer obeyed (SPEC 1a). Rate limits, the honest User-Agent, and no logins/forms still apply.
- New cross_check value `refines`: the spec sheet is a more specific form of the page value
  (page "Plastic" → sheet "PPSU"; the sheet's list contains the page's list and more). It counts as
  agreement; display the sheet value and keep the page value in alt_values. Contradictions stay `conflict`.
- Variant spec_overrides ONLY when a scored field differs and can't be expressed at family level
  as a range or list. A single-size family has size_range min = max.
- Installation / application / lifestyle photos (e.g. "Rough-in/Finish Installation" tabs) are EXCLUDED.
- Image duplicates: only the same image at another size is an error. Photos of different sibling SKUs
  are distinct images; phash ≤ 2 is now only a warning.
- Provenance: a spec sheet linked from the family's own page is enough; a missing series code is no longer a warning.
- Multilingual documents: lang lists languages in order, e.g. `en+fr+es` (English first and ≥ 50%).
- login_required on every variant satisfies the price coverage requirement.

TASKS
1. Remove the binaries from the branch. harness/gold/sioux-chief.evidence/files/ must NOT be in the
   branch history (it is now git-ignored). Keep files/ in your VM; keep text/ and manifest.csv in git.
   Rebase the branch onto the latest origin/main (main now includes the updated SPEC, harness and a new
   scraper/ folder; take main's versions of everything outside harness/gold/). Rewrite the branch history so
   no commit contains files/ (e.g. squash the branch into a single commit), then force-push gold/sioux-chief. Confirm that `git ls-tree -r origin/gold/sioux-chief` lists no files/ paths.
2. Relabel the 15 families against the new rules:
   a. Every `conflict` where the sheet is a more specific form of the page value becomes `refines`.
      The validator warns "should be refines" for each candidate; check each one by hand.
   b. Remove variant spec_overrides that the new family-vs-variant rule doesn't require. Use min = max for single sizes.
   c. Remove installation/application/lifestyle photos. Restore any sibling-SKU photos that were
      dropped only because of the old phash ≤ 6 rule.
   d. robots.txt: if any sampled family links documents under /downloads/ (previously skipped),
      add them now with full document fields and evidence.
   e. Use the new multilingual lang format where it applies.
3. Blind re-label check, repeated with the new rules: a separate session, working only from the spec and
   the site (not your gold), labels the same 3 families as before PLUS 3 more drawn with Random(43)
   (6 total). Report agreement per row: variants, documents, CAD/BIM, images, family spec fields,
   variant overrides, and cross_check values. Fix the gold where the re-label was right, and say which.
4. Validate: `python -m mfr_harness.validate gold/sioux-chief.json --site sioux-chief --gold` → 0 errors,
   and no "should be refines" warnings left unexplained.

HARD RULES (unchanged)
Don't modify harness code, schema or tests; report problems in HARNESS_ISSUES.md. Never infer values.
Don't run score.py. Sioux Chief is the held-out test site: don't share gold contents outside the PR.

DELIVER
Force-push gold/sioux-chief and update the PR description with: the validator output; the before/after
counts of conflict, refines and agree; the new 6-family agreement table next to the old 3-family one;
the number of images removed and restored; any /downloads/ documents added; and the size of the PR
(confirm there are no binary files).
```
