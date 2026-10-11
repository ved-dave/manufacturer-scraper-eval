# Apollo: ambiguity log

Labeller session 2026-10-11 (branch `gold/apollo-auto`, base `auto/integration`). Scope: Apollo-branded families
only on https://aalberts-ips.us/ (allowed hosts `aalberts-ips.us`, `aalberts.compano.com`).

## Result: site blocked, no answer key built

| Family specs come from | Families |
|---|---|
| Both page and spec sheet | 0 |
| Page only | 0 |
| PDF only | 0 |

No family could be labelled, so there are no conflicts and no blind re-label. `gold/apollo.json` is **not**
committed: a gold file needs a complete `family_index` (the validator errors on an empty one), and committing
an empty key would make `apollo` look like a scorable dev site. This follows the Dixon precedent in
AUTONOMOUS_RUN.md section 1 ("blocked ... no answer key, no workarounds").

### What was tried (all at <= 1 request/second, UA `mfr-scraper-eval-labeller/1.0 (+mailto:vedd1539@gmail.com)`)

| Time (UTC) | Client | URL(s) | Result |
|---|---|---|---|
| 02:31 | HTTP client (curl) | `/`, `/robots.txt`, `/sitemap.xml`, `/sitemap_index.xml`, `/product-sitemap.xml`, `/wp-json/`, `/apollo/`, `/wp-content/uploads/`, `www.aalberts-ips.us/` | HTTP 200 with a 1,705-byte LiteSpeed page titled "Bot Verification" ("Verifying that you are not a robot...", invisible reCAPTCHA that POSTs to `/.lsrecap/recaptcha`). Same page for every path, including robots.txt and the sitemap. Server header `LiteSpeed`. |
| 02:32 | Normal Chrome on the VM (its own UA, no changes) | `/` | Same "Bot Verification" page; reCAPTCHA escalated to a visible image challenge ("Select all images with a bus"). Not solved (no challenge solving, AUTONOMOUS_RUN rule 6). Tab closed. |
| 02:34 | curl | `aalberts.compano.com/`, `/robots.txt`, `/sitemap.xml` | `/` redirects to the Compano login (`start.compano.com/login?...clientId=Aalberts`); robots.txt and sitemap.xml are 404. It is a PIM/asset host; asset URLs can only be found from the main site's pages. No login attempted. |
| 02:44, 02:54, 03:04, 03:14 | curl, one request each | `/` | Still "Bot Verification". |
| 02:46 | Normal Chrome | `/` | Still "Bot Verification"; visible image challenge ("fire hydrants"). Not solved. |
| 03:15 | Normal Chrome | `/` | Still "Bot Verification"; visible image challenge ("bus"). Not solved. |

Evidence: `apollo.evidence/text/` holds the extracted text of both challenge pages (HTTP client
`4846bcf8...`, Chrome `5373e635...`); `manifest.csv` lists them. Raw HTML and the two challenge screenshots stay
in `apollo.evidence/files/` on the labeller VM (git-ignored).

Not done, on purpose: third-party caches or archives (web.archive.org, search-engine caches) are not allowed
hosts and using them to get past the wall would be a bot-protection workaround; distributor copies are out of
scope (SPEC 1).

## Checkpoint self-review (DEVIN_TASK steps 1-3, AUTONOMOUS_RUN section 2)

- (a) Family definition vs SPEC 3: fixed in advance (below) but not applied; no pages were readable.
- (b) family_index from 2 independent sources: **not possible**. Sitemap: 0 (sitemap.xml returns the challenge
  page). Crawl: 0 (home page returns the challenge page). Counts: sitemap only 0 / crawl only 0 / both 0.
- (c) 15-family sample: `apollo.sample.py` fixes the draw (random.Random(42) over the index sorted by URL,
  proportional to category, coverage swaps logged); with an empty `apollo.family_index_meta.json` it draws
  nothing. No coverage swaps.
- (d) Scope decisions: the brand rule below is written down; it could not be applied to any page.

## Brand rule (fixed before any page was seen; for whoever labels this site once it is reachable)

A family is in scope if it is Apollo-branded. Decide with the first test in this order that gives an answer,
and log every family where the tests disagree:
1. **Product name** on the family page (H1/title) contains "Apollo" (e.g. "Apollo 70 Series"), or another
   Aalberts brand name (Shurjoint, VSH, Elkhart, Lasco, Conbraco legacy names count as Apollo only if the page
   calls them Apollo) -> that brand.
2. **Brand logo** shown with the product (product image or brand badge on the page, not the site header).
3. **Breadcrumb** / product-navigation brand level (e.g. Products > Apollo > Ball Valves).
4. **Document folder or file name** of the family's spec sheet (e.g. a path segment or prefix naming the brand).
5. Still undecided -> out of scope, listed in this log as borderline.

Families sold under two brands (co-branded pages) are in scope if Apollo is one of them.

## Judgement calls

| Case | Decision | Proposed SPEC wording |
|---|---|---|
| Whole site behind a reCAPTCHA wall, for an HTTP client and a normal browser | Treated as "stays blocked" (SPEC 1a): recorded here and in HARNESS_ISSUES.md; no answer key; no challenge solving, no archives | SPEC 1a: "A site whose every page (incl. robots.txt and sitemap) returns a CAPTCHA page to a normal browser is blocked; it gets no answer key, and agents are scored only on reporting `site_profile.blocked: true`." |
| `gold/apollo.json` with an empty family_index | Not committed (validator requires a non-empty family_index in gold; an empty key would be scored as if real) | HARNESS: allow a gold stub with `site_profile.blocked: true` and no families, or keep blocked sites out of `gold/` (Dixon precedent). |
| Brand decision order | Name > logo > breadcrumb > document folder > out of scope | SPEC 1: "On multi-brand sites, scope is decided per family by product name, then brand logo, then breadcrumb, then document folder; undecided families are out of scope and logged." |

## SPEC changes made

None. The blocked-site wording above is a proposal only; SPEC 1a already covers the case ("if a site stays
blocked, it is reported as blocked").

## Blind re-label

Not applicable: no labelled families.
