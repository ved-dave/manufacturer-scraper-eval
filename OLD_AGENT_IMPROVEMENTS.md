# Old agent: free improvements to its output

**Purpose.** The existing link-collecting agent ("old agent") finds nearly every relevant link on a manufacturer's
site. It is the best recall source we have. But its output is a flat CSV (`url, url_type`), so everything it saw
while crawling (which page a link was on, what the link said, what the page was) is thrown away. Any later step
that needs that information has to crawl the site again.

This document lists information the agent **already has in hand** while crawling: it is visible in pages it has
already loaded, or in HTTP responses it has already received. Recording it costs almost nothing and makes the
agent the first stage of a pipeline: it collects and records, then a processing layer groups links into product
families, classifies documents and extracts specs (Approach B).

> **Rule for everything below: no new requests.** Only record what comes from pages and responses the agent already
> fetches. Don't download PDFs or images, or render JavaScript, just to fill a field.

---

## 1. Output format

Write **one JSON object per line** (JSONL), one file per site: `<site>.links.jsonl`. JSONL handles lists
(breadcrumbs, srcset) and missing values cleanly. A CSV export with the same column names is fine as well, but JSONL
is the reference format.

Two kinds of records, distinguished by `record`:

- `"page"`: one per HTML page the agent loaded.
- `"link"`: one per link (to a page, document, image or CAD file) found on a loaded page. The same target URL found
  on several pages produces several link records, one per `found_on` page. That repetition is the relationship data.

The JSON Schema is `harness/schema/link_record.schema.json` (to be added with the Approach B work). Field names below
are the contract.

---

## 2. Fields

### Priority 1: relationships (the biggest win)
| Field | Record | What it is | Why |
|---|---|---|---|
| `found_on` | link | URL of the page where this link appeared | Page → spec sheet / image / CAD relationships; enables family grouping without re-crawling |
| `link_text` | link | Visible anchor text; for images, the `alt` text | Best clue for document type ("Spec Sheet", "IOM") and which product a file belongs to |
| `section` | link | Text of the nearest preceding heading or the active tab/accordion label (e.g. "Downloads", "Specifications", "Related Products") | Separates this product's files from related-product links |
| `in_chrome` | link | `true` if the link sits inside `<header>`, `<footer>`, `<nav>` or an element whose class/id is a header/footer/menu/cookie banner | Lets processing drop site-wide links (terms, compliance PDFs) |
| `link_kind` | link | `a`, `img`, `source`, `iframe`, `link-rel`, `script-data` (where the URL came from) | `iframe` = embedded viewers (CAD); `img` vs `a` matters for images |

### Priority 2: HTTP facts (only for URLs the agent actually requested)
| Field | Record | Why |
|---|---|---|
| `status` | page/link | Dead links found immediately |
| `final_url` | page/link | Redirects, including redirects off the site (e.g. to a sister company) |
| `content_type` | page/link | True file type, e.g. a PDF served from a URL with no `.pdf` |
| `content_length` | page/link | Size without downloading |
| `last_modified`, `etag` | page/link | **Re-runs only re-check what changed**, which is essential at thousands of sites |

### Priority 3: page facts (the page is already loaded)
| Field | Record | Why |
|---|---|---|
| `page_title`, `h1` | page | Product / family name |
| `breadcrumb` | page | List of breadcrumb labels (from schema.org BreadcrumbList if present, else the breadcrumb element) | Category path, a strong family-grouping signal |
| `canonical_url` | page | `<link rel="canonical">` | Collapses duplicate URLs |
| `lang` | page | `<html lang>` | Language copies are tagged, not mixed in |
| `hreflang` | page | Map of `hreflang` → URL | Finds the English/US version of a page |
| `jsonld_product` | page | The schema.org `Product` object(s) as found (sku, name, brand, mpn, gtin, offers) | Structured SKU/name/price when the site provides it |
| `has_spec_table` | page | `true` if the page has a table / `dl` / label-value block with 2+ rows | Product page vs category page |
| `n_links_same_section` | page | Count of links to other pages under the same path prefix | High = listing/category page |
| `meta_description` | page | `<meta name="description">` | Cheap product summary |
| `html_snapshot` | page | Path or object-store key of the page HTML exactly as the agent received it | The processing layer can read pages (specs, downloads) **without fetching them again**. This is essential for sites that are hard to fetch. Storage cost only. |

### Priority 4: image details already in the HTML
| Field | Record | Why |
|---|---|---|
| `alt` | link (img) | Same as `link_text` for images |
| `width`, `height` | link (img) | From attributes, if present |
| `srcset` | link (img) | List of `{url, descriptor}`; pick the largest version without downloading every size |
| `wrapping_link` | link (img) | URL of an `<a>` around the image (often the full-size original) |

### Priority 5: crawl details
| Field | Record | Why |
|---|---|---|
| `site` | all | Site identifier (e.g. the registrable domain) |
| `discovered_via` | page | `sitemap`, `menu`, `link`, `seed` |
| `depth` | page | Clicks from the homepage |
| `sitemap_lastmod` | page | From the sitemap, if listed there |
| `crawled_at` | all | ISO 8601 timestamp |
| `agent_version` | all | For comparing runs |

### Labels and hygiene (no new data, just consistency)
- `url_type` uses one fixed label set: `page`, `pdf`, `image`, `cad`, `bim`, `archive`, `spreadsheet`, `video`,
  `other`. Set it from `content_type` when known, else from the extension. (Today the same kind of file gets different labels on different
  sites; e.g. CAD viewers were labelled "document".)
- `url` is **normalised**: scheme and host lowercase, no `#fragment`, tracking parameters removed (`utm_*`, `gclid`,
  `fbclid`), consistent percent-encoding. Keep the raw form in `url_raw` if it differs.
- **Tag, don't drop or merge.** Language copies, resized image renditions, footer links and off-site links are
  recorded with their tags (`lang`, `in_chrome`, `final_url`), not silently removed or mixed in. The processing
  layer decides what to keep.

---

## 3. Example records

```json
{"record":"page","site":"siouxchief.com","url":"https://www.siouxchief.com/Products/640WP02","status":200,
 "final_url":"https://www.siouxchief.com/Products/640WP02","content_type":"text/html","lang":"en",
 "page_title":"640WP02 - F1960 Poly Plug | Sioux Chief","h1":"F1960 Poly Plug",
 "breadcrumb":["Products","Fittings & Accessories","PEX Fittings","Plugs"],
 "canonical_url":"https://www.siouxchief.com/Products/640WP02","hreflang":{},
 "jsonld_product":null,"has_spec_table":true,"n_links_same_section":4,
 "discovered_via":"sitemap","depth":3,"sitemap_lastmod":"2026-05-02","last_modified":null,"etag":"\"a1b2\"",
 "crawled_at":"2026-10-11T14:02:11Z","agent_version":"2.0"}

{"record":"link","site":"siouxchief.com","url":"https://cdn.siouxchief.com/prodscmwebsite/SpecSheets/640%20SERIES%20-%20F1960%20POLY%20PLUG%20-%20SPEC%20SHEET.PDF",
 "url_type":"pdf","found_on":"https://www.siouxchief.com/Products/640WP02","link_text":"Spec Sheet",
 "section":"Downloads","in_chrome":false,"link_kind":"a","status":null,"content_type":null,
 "crawled_at":"2026-10-11T14:02:11Z","agent_version":"2.0"}

{"record":"link","site":"siouxchief.com","url":"https://cdn.siouxchief.com/prodscmwebsite/ProductImages/640WP02.JPG",
 "url_type":"image","found_on":"https://www.siouxchief.com/Products/640WP02","link_text":"640WP02","alt":"640WP02",
 "section":null,"in_chrome":false,"link_kind":"img","width":null,"height":null,"srcset":[],
 "wrapping_link":null,"crawled_at":"2026-10-11T14:02:11Z","agent_version":"2.0"}
```

---

## 4. Not free (don't add to the old agent)
- Downloading PDFs/images to inspect, hash or measure them.
- Rendering JavaScript in a browser.
- Extracting spec values from page text, classifying documents, grouping families. These are the processing layer's job.

---

## 5. Rollout order
1. **`found_on`, `link_text`, `section`, `in_chrome`, `link_kind`**: makes family grouping and document typing
   possible without re-crawling.
2. **`status`, `final_url`, `content_type`, `content_length`**: correct, live links with true types.
3. **`breadcrumb`, `canonical_url`, `lang`, `hreflang`, `page_title`/`h1`, `jsonld_product`, `has_spec_table`,
   `html_snapshot`**: clean grouping, no duplicates or language copies, and page content without re-fetching.
4. **`last_modified`, `etag`, `sitemap_lastmod`**: cheap incremental re-runs.
5. Image details and crawl details.

## 6. Acceptance checks
- Every `link` record has `found_on` that matches a `page` record's `url` in the same file.
- `url_type` only uses the fixed label set; `url` is normalised.
- Run time and request count are unchanged (within ±5%) compared with the current agent on the same site.
- The output validates against `harness/schema/link_record.schema.json`.
- The processing layer (Approach B) can read the file with no site-specific code.
