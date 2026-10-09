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
