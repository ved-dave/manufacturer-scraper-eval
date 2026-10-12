# Results

Small, durable copies of the outputs behind the reports. The full run outputs (`harness/runs/`, ~28 GB) and the page
cache (`scraper/cache/`, ~22 GB) are not in git. They can be recreated from the code and the link lists.

- `scores/`: scorer output for every experiment, `<run>.<site>.json` (plus `.txt` summaries where present), scored
  against the unchanged answer keys in `harness/gold/`. Run names are explained in REPORT_APPROACH_B.md
  (e.g. `A` current scraper, `R4`/`RG2` item-table rule, `SP0` first site profile, `SP` site profile with the
  most-specific-page rule).
- `site-profiles/`: the four `<site>.profile.json` files from `python -m mfr_scraper profile`, plus
  `sioux-chief.mixed-families.csv`, the 32 profile families that mix answer-key families (measured after the run;
  the profile never reads the key).
- `team/`: the team packet, the one-page summary and the experiments comparison (PDF plus HTML source).
