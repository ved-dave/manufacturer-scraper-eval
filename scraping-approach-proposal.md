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
| 3a | Layer 3: AI model on uncertain items only, with quote verification and answer caching (self-healing Level 1) | Spec accuracy and conflict precision up ≥ 5 points; cost per site known | 1–2 sessions (later) |
| 3b | Self-healing Levels 2–3: promote repeated AI answers to data rules; agent PRs for code-level gaps (see "Self-healing loop") | Unsure items and AI cost per site fall run over run; no dev-key metric drops | 1–2 sessions (later) |
| 4 | Fair test on unseen sites (Milwaukee, Caleffi once they have keys) vs old agent and current scraper | Beats both on recall *and* structure | ½ session + labelling |

\*Rough estimates in Devin sessions, not measured.

## Self-healing loop (Phase 3, to be tested later)
**Idea:** the AI resolves the items the rules can't decide, and what it learns is turned back into deterministic
rules. Over time fewer items are unsure, AI cost falls, and the system stays repeatable and auditable.

### Three levels, safest first
| Level | What happens | Who/what applies it | Gate |
|---|---|---|---|
| **1. Resolve** | At run time, the AI answers an unsure item (e.g. "does this PDF belong to the 640 Series?") with a verbatim quote from the stored document. Answers are cached by content hash, so a question is never paid for twice. | Automatic | Quote must be found in the stored text; otherwise the item stays unsure. Cost budget per site. |
| **2. Learn data rules** | When the AI resolves many similar items the same way, the pattern becomes a **data rule** (not code): a label synonym ("Working Press." → `pressure_rating`), a section rule ("Literature" tab → product documents), or a per-site profile entry (e.g. PDFs under one folder are named after their family). | Automatic, gated | The rule must reproduce the AI's decisions on a held-back set of its unsure items (e.g. ≥ 95% agreement) **and** change no decision that was already confident. Global rules (shared dictionaries) must also pass a regression check on the dev answer keys. Per-site rules can be promoted without keys. |
| **3. Fix code** | Unsure items that no data rule can express (a new page layout, a new table format) are batched into a task for a coding agent, which writes the fix as a PR. | Agent PR, human review | Tests, harness validation and dev-key scores must pass; a person approves the merge. |

### Guardrails
- **Answer keys never teach.** The AI and the rule learner never see answer keys at run time; keys only measure.
- **No quote, no answer.** Every AI decision cites verified source text.
- **Versioned and reversible.** Every promoted rule records the AI decisions it came from and the run that promoted
  it; any rule can be traced and rolled back. Each run records which rule versions it used.
- **No silent overrides.** A new rule that would change a confident decision goes to review instead.
- **Held-out sites stay untouched**, so the final test still measures generalisation.
- **Bounded cost:** only items the rules marked unsure go to the AI, within a per-site budget.

### Prerequisite (in the current PoC)
Unsure items are written to `<site>.decisions.jsonl` with full context: the candidate, the family it might belong
to, evidence for and against (with snippets and sources), and why the rules couldn't decide. They're counted per
site and per kind. That's the AI's work queue and the basis for the cost estimate.

### Storage (with `DATA_MODEL.md`)
Two more tables: `ai_decisions` (question, answer, quote, source version, model, cost, cached key) and `rules` (kind,
scope = global or site, definition, source decisions, status = proposed / promoted / retired, version). `runs.stats`
records the rule versions used.

### How it's measured
Per run and per site: unsure items (count and share), AI calls and cost, rules proposed / promoted / retired, and the
usual harness scores. Success means the unsure share and AI cost trend down while scores hold or improve.

## Decisions for the team
1. ~~Layer 1 source~~: decided: the old agent (with the `OLD_AGENT_IMPROVEMENTS.md` fields when available).
2. **AI layer:** which model, and what cost per site is acceptable? Should promoted per-site rules (self-healing
   Level 2) apply automatically, or be queued for review at first?
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
