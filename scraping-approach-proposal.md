# Proposal: two-layer "collect wide, sort smart" scraper

*Current plan. Drafted 11 Oct 2026, updated 11 Oct 2026 to match the team's decisions. Phase 2 is in progress (Approach B PoC).*

## The problem in one line
The old agent **collects too much and doesn't sort it**. The new scraper **sorts well but filters too strictly**.
Combine their strengths: collect everything relevant, then decide item by item on evidence.

## Update after the final test
- **Sioux Chief (held-out):**
  - The new scraper found 91.6% of families, 46.4% of main docs, 13.5% of images and 3.4% of variants. The old
    agent was at 100% on everything that can be scored.
  - Cause: Sioux Chief has one page per part number, and the scraper read each page as a family (6,270 vs 700).
  - So grouping part-number pages into families is a required Layer 2 step, run as a whole-site pass.
- **Phase 0 gap analysis (done):** of 80 key items the new scraper missed on Bray, Crane and Cimberio, 66 (83%) were
  on pages it crawled and then filtered out. Only 9 were never seen by our crawl. Details in `REPORT.md` §4.
- **Layer 1 source (decided):** the old agent is the link collector. `OLD_AGENT_IMPROVEMENTS.md` lists the free
  fields it should add (`found_on` first). Until those exist, Layer 2 works from its current CSVs (`url, url_type`)
  and fetches pages itself when it needs them.
- **Blocked sites (decided):** the old agent's data for sites that block automated access (e.g. Apollo, Dixon) is
  valid input and is processed like any other site.
- **Storage:** the Postgres link-table and processor design is in `DATA_MODEL.md`.

## Architecture

```
            manufacturer site (polite: ~1 req/s per host, honest user agent)
                                   │
   ┌───────────────────────────────▼────────────────────────────────┐
   │ LAYER 1 - COLLECT (the "vacuum")                               │
   │  sitemap + crawl → every page, PDF, image, CAD link            │
   │  on ANY host (CDN/storage domains included)                    │
   │  each row: url · type · found_on page · link position          │
   │            (main content / nav / footer) · link text           │
   │  source: the old agent (current CSVs now; enriched fields      │
   │          per OLD_AGENT_IMPROVEMENTS.md when added)             │
   └───────────────────────────────┬────────────────────────────────┘
                                   │ candidate list (big, noisy)
   ┌───────────────────────────────▼────────────────────────────────┐
   │ LAYER 2 - CHEAP RULES (deterministic, current scraper code)    │
   │  group pages into product families                             │
   │  drop obvious junk: logos/icons, duplicate image sizes,        │
   │     non-English, nav/footer links                              │
   │  keep obvious matches: PDF names the product's part numbers    │
   │  extract easy fields: tables, part numbers, sizes, temps       │
   │  every item gets: decision · confidence · reason               │
   └──────────────┬──────────────────────────────────┬──────────────┘
          confident│                       uncertain │
                   │       ┌─────────────────────────▼──────────────┐
                   │       │ LAYER 3 - AI MODEL (only uncertain     │
                   │       │ items)                                 │
                   │       │  "does this file belong to product X?" │
                   │       │  free-text specs → fields              │
                   │       │  page vs PDF conflicts                 │
                   │       │  MUST quote exact source text; the     │
                   │       │  quote is checked against the doc      │
                   │       └─────────────────────────┬──────────────┘
                   ▼                                 ▼
   ┌────────────────────────────────────────────────────────────────┐
   │ OUTPUT: one record per product family (current schema)         │
   │  specs · variants · prices · docs · images · CAD + sources     │
   │  REJECTED LIST: every dropped item + reason (audit / debugging)│
   └───────────────────────────────┬────────────────────────────────┘
                                   ▼
   ┌────────────────────────────────────────────────────────────────┐
   │ MEASURE: existing harness vs answer keys                       │
   │  recall + precision per field · cost · run time                │
   │  legacy pile = extra "did we miss anything?" check             │
   └────────────────────────────────────────────────────────────────┘
```

## Why this design
- **Recall problem:** Layer 1 stops dropping things because of *where* they're stored.
  That gap cost Cimberio all its images and most of its documents.
- **Noise problem:** Layer 2 removes the junk that makes up most of the legacy pile
  (on Bray, 90% of its page rows aren't products).
- **Hard cases:** Layer 3 handles judgement calls, and only for the uncertain items,
  which keeps cost low and most of the output repeatable.
- **Debuggable:** every miss shows up in the rejected list with its reason.
- **Measurable:** the answer keys and harness already exist, so each layer's effect is a number.

## What we have vs what's new
| Piece | Status |
|---|---|
| Crawl, family grouping, table/PDF extraction, output schema, harness, 4 answer keys | **Exists** (this run) |
| Follow assets on any host + record found_on / link position | **In progress** (Approach B PoC); old-agent fields specified in `OLD_AGENT_IMPROVEMENTS.md` |
| Group part-number pages into families by evidence | **In progress** (Approach B PoC) |
| Confidence + reason per item, rejected list | **In progress** (Approach B PoC: `<site>.decisions.jsonl`) |
| Parse each PDF once (speed) | **Exists** (parsed-PDF cache; Bray 13 → 7 min, identical output) |
| Filter images before download (speed) | New, small |
| AI layer for uncertain items, quote verification, cost tracking | New, medium |
| Old agent as Layer 1 | **Decided**; field upgrades need access to its code |
| Held-out answer keys (Milwaukee, Caleffi) | **In progress** (separate labelling session) |
| More answer keys from new manufacturers | Later (scope is the 8 repo sites for now) |
| Postgres tables and separate services | Designed in `DATA_MODEL.md`; built after the PoC |

## Phased plan (each phase scored on the same keys before the next)
| Phase | Work | Success check | Rough effort* |
|---|---|---|---|
| 0 (done) | Gap analysis: key items the legacy agent found that we missed, per site (read-only) | Know what share of misses is "filtered" vs "never seen" | < ½ session |
| 1 | Wider dev set from the repo's sites: Sioux Chief and Cimberio move to dev (their final test is spent); Milwaukee and Caleffi get new held-out keys | Keys validate; blind re-label agreement ≥ 80% | **In progress** |
| 2 | Layers 1+2 (Approach B PoC): process the old agent's links; evidence-based grouping and keep/drop; rejected list; speed fixes; reader ready for the enriched fields | Image and doc recall ≥ 95% on dev (Bray, Crane, Sioux Chief, Cimberio); precision drop ≤ 2 points; a ~6,000-product site in < 4 h; beats the current scraper | **In progress** |
| 3 | Layer 3: AI model on uncertain items only, with quote verification | Spec accuracy and conflict precision up ≥ 5 points; cost per site known | 1–2 sessions |
| 4 | Fair test on unseen sites (Milwaukee, Caleffi once they have keys) vs old agent and current scraper | Beats both on recall *and* structure | ½ session + labelling |

\*Rough estimates in Devin sessions, not measured.

## Decisions for the team
1. ~~Layer 1 source~~: decided: the old agent (with the `OLD_AGENT_IMPROVEMENTS.md` fields when available).
2. **AI layer:** which model, and what cost per site is acceptable?
   Hosted model vs local model (local is cheaper and private, but weaker).
3. **Repeatability:** is some run-to-run variation acceptable for the uncertain items
   (mitigations: fixed model version, temperature 0, cached answers)?
4. **Speed target:** how fast must a large catalogue (~6,000 products) finish?
5. **Which sites next:** after the PoC, which new manufacturers (electrical, plumbing, mechanical) get answer keys.

## Risks
- Wider collection means more candidates for the sorter. If Layer 2 rules are weak, precision drops.
  Mitigation: phase 2's precision gate.
- AI answers can be confidently wrong. Mitigation: mandatory verbatim quote, checked against the source document.
- Sites that block automated access (Apollo, Dixon) have no answer keys, so their output is processed from the old
  agent's data but can't be scored; pages and files our components can't fetch are marked, not guessed.
- Results on only two dev sites misled us once already. That's why the dev set now has four sites of different
  layouts, and a separate held-out test (Milwaukee, Caleffi) comes last.
