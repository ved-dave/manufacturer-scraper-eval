"""Approach B processing layer: L0/L1 readers, link-file validation, grouping, decisions (no network)."""
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'harness'))

from PIL import Image  # noqa: E402

from mfr_scraper.fetch import Response  # noqa: E402
from mfr_scraper.process import grouping as G  # noqa: E402
from mfr_scraper.process.fetching import is_blocked  # noqa: E402
from mfr_scraper.process.readers import read_l0, read_l1, read_links  # noqa: E402
from mfr_scraper.process.run import ProcessRun  # noqa: E402
from mfr_harness.validate_links import validate_file  # noqa: E402

FIX = Path(__file__).parent / 'fixtures'
L1 = FIX / 'l1_sample.jsonl'
BASE = 'https://www.example-valves.com/products'
CDN = 'https://cdn.example-valves.com'

PAGE_03 = b'''<html lang="en"><head><title>AB100-03</title>
<script type="application/ld+json">{"@type":"Product","name":"Widget Ball Valve 3/4\\"","sku":"AB100-03"}</script></head>
<body><main><h1>Widget Ball Valve 3/4"</h1><table><tr><th>Size</th><td>3/4"</td></tr>
<tr><th>Pressure Rating</th><td>600 psi WOG</td></tr></table>
<h2>Downloads</h2><a href="https://cdn.example-valves.com/docs/AB100-series-spec-sheet.pdf">Spec Sheet</a>
<h2>Other Sizes</h2><a href="https://www.example-valves.com/products/AB100-02">AB100-02</a></main></body></html>'''


def png(w, h, color=(200, 30, 30)):
    b = io.BytesIO()
    im = Image.new('RGB', (w, h), color)
    for x in range(0, w, 40):
        for y in range(0, h, 40):
            im.putpixel((x, y), (0, 0, 0))
    im.save(b, 'PNG')
    return b.getvalue()


class FakeFetcher:
    """Answers from a dict; the spec sheet is blocked (403) to exercise the blocked-item path."""
    def __init__(self):
        self.calls = []
        self.stats = {'requests': 0, 'cache_hits': 0, 'robots_overridden': 0, 'errors': 0}
        self.blocked_hosts, self.purpose_stats, self.blocked = {}, {}, []
        self.answers = {
            f'{BASE}/AB100-03': (200, 'text/html', PAGE_03),
            f'{CDN}/docs/AB100-series-spec-sheet.pdf': (403, 'text/html', b'Forbidden'),
            f'{CDN}/img/AB100-02-1200.jpg': (200, 'image/png', png(1200, 1200)),
            f'{CDN}/img/AB100-02.jpg': (200, 'image/png', png(400, 400)),
        }

    def get(self, url, kind='html', purpose=None):
        self.calls.append(url)
        self.stats['requests'] += 1
        st, ct, body = self.answers.get(url, (404, 'text/html', b''))
        return Response(url, url, st, {'content-type': ct}, body)

    def response_blocked(self, r):
        return is_blocked(r)


def run_fixture(**kw):
    out = tempfile.mkdtemp()
    f = FakeFetcher()
    pr = ProcessRun('example-valves', L1, out_dir=out, input_url='https://www.example-valves.com/',
                    allowed_hosts=['www.example-valves.com', 'cdn.example-valves.com'], fetcher=f, log=lambda *a: None, prefetch=False, **kw)
    return pr, pr.run(), f


class TestReaders(unittest.TestCase):
    def test_l1_reader(self):
        ls = read_links(L1)
        self.assertEqual(ls.level, 'L1')
        self.assertEqual(len(ls.pages), 3)
        p = ls.pages[f'{BASE}/AB100-02']
        self.assertEqual(p.breadcrumb[-1], 'Ball Valves')
        self.assertTrue(p.html_snapshot.endswith('ab100-02.html') and Path(p.html_snapshot).exists())
        img = next(l for l in ls.links if l.url.endswith('AB100-02.jpg'))
        self.assertEqual((img.width, img.height, img.srcset[0]['width']), (400, 400, 1200))
        self.assertEqual(len(ls.links_on()[f'{BASE}/AB100-02']), 7)

    def test_l0_reader_skips_malformed_rows(self):
        with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False) as f:
            f.write('url,url_type\nhttps://x.com/a,site_page\nhttps://x.com/a.pdf,pdf\n%20975,broken\nhttps://x.com/i.jpg,image\n')
        ls = read_l0(f.name)
        self.assertEqual((ls.level, len(ls.pages), len(ls.links)), ('L0', 1, 2))
        self.assertTrue(all(l.found_on is None for l in ls.links))

    def test_link_file_validation(self):
        errors, warnings, counts = validate_file(L1)
        self.assertEqual(errors, [])
        self.assertEqual(counts, {'pages': 3, 'links': 8})
        bad = Path(tempfile.mkdtemp()) / 'bad.jsonl'
        bad.write_text(L1.read_text() + json.dumps({'record': 'link', 'site': 's', 'url': 'https://a/b.pdf', 'url_type': 'pdf',
                                                    'found_on': 'https://a/not-a-page'}) + '\n'
                       + json.dumps({'record': 'link', 'site': 's', 'url': 'https://a/c', 'url_type': 'webpage', 'found_on': f'{BASE}/AB100-02'}) + '\n')
        errors, _, _ = validate_file(bad)
        self.assertTrue(any('found_on has no page record' in e for e in errors))
        self.assertTrue(any('schema' in e for e in errors))


class TestProcessL1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pr, cls.out, cls.fetcher = run_fixture()
        cls.dec = cls.pr.decisions

    def test_snapshot_used_and_missing_page_fetched_once(self):
        self.assertNotIn(f'{BASE}/AB100-02', self.fetcher.calls)
        self.assertEqual(self.fetcher.calls.count(f'{BASE}/AB100-03'), 1)
        self.assertEqual(self.pr.page_sources, {'snapshot': 2, 'fetched': 1})

    def test_sku_pages_grouped_into_one_family_with_variants(self):
        fams = self.out['families']
        self.assertEqual(len(fams), 1)
        f = fams[0]
        self.assertEqual(sorted(v['sku'] for v in f['variants']), ['AB100-02', 'AB100-03'])
        self.assertEqual(f['series_code'], 'AB100')
        ev = self.out['site_profile']['grouping']['merges'][0]['evidence']
        self.assertTrue(any(e.startswith('R1') for e in ev) and any(e.startswith('R3') for e in ev))

    def test_listing_page_from_l1_facts(self):
        d = next(d for d in self.dec if d['kind'] == 'page_role' and d['url'] == f'{BASE}/')
        self.assertEqual((d['decision'], d['reason']), ('drop', 'listing page'))

    def test_blocked_spec_sheet_recorded_and_kept_from_link_evidence(self):
        docs = self.out['families'][0]['documents']
        self.assertEqual([(d['doc_type'], d['http_status'], d['mime_verified']) for d in docs], [('spec_sheet', 403, False)])
        self.assertTrue(any(d.get('blocked') for d in self.dec if d['url'] == f'{CDN}/docs/AB100-series-spec-sheet.pdf'))
        self.assertEqual(self.fetcher.calls.count(f'{CDN}/docs/AB100-series-spec-sheet.pdf'), 1)

    def test_asset_decisions(self):
        by = {d['url']: d for d in self.dec if d['kind'] in ('asset', 'asset_to_family')}
        self.assertEqual(by[f'{CDN}/fr/docs/AB100-fiche.pdf']['decision'], 'drop')
        self.assertEqual(by['https://www.example-valves.com/static/logo.png']['decision'], 'drop')
        self.assertEqual(by[f'{CDN}/docs/full-line-catalog.pdf']['reason'],
                         'in page chrome (header/footer/nav) and does not name the family')
        self.assertIn('below 300 px per L1', by[f'{CDN}/img/AB100-02-thumb.jpg']['reason'])
        self.assertNotIn(f'{CDN}/img/AB100-02-thumb.jpg', self.fetcher.calls)

    def test_image_picks_largest_srcset_version(self):
        ims = self.out['families'][0]['images']
        self.assertEqual([(i['url'], i['width']) for i in ims], [(f'{CDN}/img/AB100-02-1200.jpg', 1200)])
        self.assertNotIn(f'{CDN}/img/AB100-02.jpg', self.fetcher.calls)

    def test_unsure_item_has_resolver_context(self):
        u = next(d for d in self.dec if d['decision'] == 'unsure' and d['url'] == f'{CDN}/docs/ZX900-brochure.pdf')
        self.assertEqual(u['unsure_kind'], 'asset_to_family')
        for k in ('question', 'candidate', 'family', 'evidence_for', 'evidence_against', 'why_undecided', 'default_action', 'cache_key'):
            self.assertIn(k, u)
        self.assertEqual(u['candidate']['section'], 'Related Products')
        self.assertEqual(u['family']['series_code'], 'AB100')
        self.assertIn('AB100-02', u['family']['identifiers'])

    def test_every_decision_has_reason(self):
        self.assertTrue(all(d['decision'] in ('keep', 'drop', 'unsure') and d['reason'] for d in self.dec))


class TestCodeMatching(unittest.TestCase):
    def test_codes_match_whole_tokens_only(self):
        self.assertFalse(ProcessRun._code_in('778v', 'cimberio-778vws-valve.png'))   # cimberio round 1 regression
        self.assertTrue(ProcessRun._code_in('778v', '778v_new.png'))
        self.assertTrue(ProcessRun._code_in('ab10002', 'ab100-02-spec.pdf'))
        self.assertFalse(ProcessRun._code_in('113', 'p2113.jpg'))


class TestImageRules(unittest.TestCase):
    def test_charts_are_not_product_views(self):   # cimberio round 3
        from mfr_scraper.process.run import CHART_IMAGE, DIMENSION_WORDS
        for n in ('778Temperature_Pressure_Diagram.jpg', '747PRSNL_Pressure_Chart.JPG', 'flow-curve.png'):
            self.assertTrue(CHART_IMAGE.search(n), n)
        self.assertFalse(CHART_IMAGE.search('1220NL_side.jpg'))
        self.assertTrue(DIMENSION_WORDS.search('dimension diagram'))


class TestDocRules(unittest.TestCase):
    def test_recommended_specs_is_not_a_related_section(self):   # bray round 4
        from mfr_scraper.process.run import RELATED_SECTION
        self.assertFalse(RELATED_SECTION.search('Recommended Specs'))
        self.assertTrue(RELATED_SECTION.search('Recommended Products'))
        self.assertTrue(RELATED_SECTION.search('Related Products'))


class TestGrouping(unittest.TestCase):
    def rec(self, url, name, crumbs, docs=(), tables=()):
        from mfr_scraper.pipeline import PageRec
        return PageRec(url=url, name=name, crumbs=list(crumbs), lang='en', alternates={}, pairs=[], doc_links=list(docs),
                       image_cands=[], iframes=[], price={}, skus=[], sha='', tables=list(tables), text='', retrieved_at='')

    def test_catalog_on_many_pages_does_not_merge_and_names_must_match(self):
        crumbs = ['Products', 'Plugs']
        cat = ('https://c.example/catalog-spec-sheet.pdf', 'Spec Sheet')
        recs = [self.rec('https://x.example/p/640WP02', 'Poly Plug 1/2"', crumbs, [cat]),
                self.rec('https://x.example/p/640WP03', 'Poly Plug 3/4"', crumbs, [cat]),
                self.rec('https://x.example/p/117-03', 'Vacuum Breaker', ['Products', 'Valves']),
                self.rec('https://x.example/p/117-12', 'Sillcock', ['Products', 'Valves'])]
        groups, ev, unsure = G.group_pages(recs)
        self.assertEqual(sorted(len(g) for g in groups), [1, 1, 2])
        self.assertEqual(len(unsure), 1)   # 117-03 vs 117-12: same leaf + stem, different names

    def test_series_sheet_does_not_merge_different_models(self):
        sheet = ('https://x.example/TechDataSheet-778.pdf', 'Tech Data Sheet')   # cimberio round 2 regression
        recs = [self.rec('https://x.example/778V', 'Balancing Valve 778V', ['Valves', 'Balancing'], [sheet]),
                self.rec('https://x.example/778VS', 'Balancing Valve with Strainer 778VS', ['Valves', 'Balancing'], [sheet])]
        groups, _, _ = G.group_pages(recs)
        self.assertEqual(len(groups), 2)
        self.assertEqual([G.core_of(x) for x in ('AB100-02', '640WP02', '778VS', '113-32', '1220NL')],
                         ['AB100', '640WP', '778VS', '113', '1220NL'])

    def test_whole_family_pages_stay_separate(self):
        table = [['Model', 'Size'], ['S30-02', '2"'], ['S30-03', '3"']]
        a = self.rec('https://x.example/p/S30', 'Series 30', ['Valves'], tables=table)
        self.assertFalse(G.page_info(a)['single'])

    def test_pages_listing_each_other_in_item_tables_merge(self):   # sioux-chief 113-32 / 113-33
        crumbs = ['Products', 'Valves', 'Sillcocks/Hydrants']
        items = [['Item No', 'Description'], ['113-32', '1/2" MIP'], ['113-33', '3/4" MIP']]
        a = self.rec('https://x.example/Products/113-32', '113-32', crumbs, tables=items)
        b = self.rec('https://x.example/Products/113-33', '113-33', crumbs, tables=items)
        c = self.rec('https://x.example/Products/113-40', '113-40', crumbs, tables=[['Item No', 'Description'], ['113-40', 'x'], ['113-32', 'y']])
        d = self.rec('https://x.example/Products/113-41', '113-41', ['Products', 'Drains'], tables=[['113-41', 'x'], ['113-32', 'y']])
        groups, ev, unsure = G.group_pages([a, b, c, d])
        self.assertEqual(sorted(len(g) for g in groups), [1, 1, 2])     # c is listed by nobody, d is in another category
        merged = next(i for i, g in enumerate(groups) if len(g) == 2)
        self.assertEqual({r.url for r in groups[merged]}, {a.url, b.url})
        self.assertTrue(ev[merged][0].startswith('R4 '))

    def test_grouped_pages_keep_their_variants(self):   # sioux-chief: spec PDF found_on a grouped page lost its variant
        from mfr_scraper.pipeline import accessory_families
        pr = [{'availability': 'request_quote'}]
        table = {'canonical_url': 't', 'variants': [{'sku': s, 'page_url': 't', 'prices': pr} for s in ('861-2PX', '861-2PXR', '861-3P')]}
        grouped = {'canonical_url': 'g', 'variants': [{'sku': '861-2PX', 'page_url': 'g', 'prices': pr},
                                                      {'sku': '861-2PXR', 'page_url': 'g-r', 'prices': pr}]}
        self.assertEqual(accessory_families([table, grouped], keep_grouped_pages=True), [])
        self.assertEqual([v['page_url'] for v in grouped['variants']], ['g', 'g-r'])
        self.assertEqual(accessory_families([table, grouped]), [grouped])


    def test_every_grouped_page_becomes_a_variant(self):   # sioux-chief 871-4 + 871-16: spec PDF found_on 871-16
        from mfr_scraper.process.run import grouped_variants
        a = self.rec('https://x.example/Products/871-4', '871-4', ['Cleanouts'])
        b = self.rec('https://x.example/Products/871-16', '871-16', ['Cleanouts'])
        fam = {'variants': [], 'family_prices': [{'availability': 'not_published'}]}
        grouped_variants(fam, [a, b], lambda r: {'availability': 'not_published'})
        self.assertEqual([(v['sku'], v['page_url']) for v in fam['variants']], [('871-4', a.url), ('871-16', b.url)])
        self.assertNotIn('family_prices', fam)

class TestResolver(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        self.dir = Path(tempfile.mkdtemp())
        dec = {'decision': 'unsure', 'unsure_kind': 'family_grouping', 'cache_key': 'k1', 'question': 'same?',
               'candidate': {'url': 'https://x.example/a'}, 'family': {'canonical_url': 'https://x.example/b'}}
        (self.dir / 'd.jsonl').write_text(json.dumps(dec) + '\n' + json.dumps({**dec, 'cache_key': 'k1'}) + '\n')
        self.texts = {'https://x.example/a': 'Brass Boiler Drain\n1/2" MIP', 'https://x.example/b': 'Brass Boiler Drain\n3/4" MIP'}

    def run_resolver(self, reply, budget=1.0):
        from unittest import mock
        from mfr_scraper.process import resolve as R
        calls = []

        def ask(prompt):
            calls.append(prompt)
            return reply, 1000, 100
        with mock.patch.object(R, 'page_text', lambda f, u: self.texts.get(u)), mock.patch.object(R, 'HostQueueFetcher'):
            out, stats = R.resolve('x', self.dir / 'd.jsonl', self.dir / 'r.jsonl', ask, 'm', self.dir / 'c.json',
                                   budget, 3.0, 15.0, log=lambda *a: None)
        return out, stats, calls

    def test_verified_answer_is_cached_and_applied(self):
        from mfr_scraper.process.resolve import same_family_links
        reply = '{"answer": "same", "quote_a": "brass boiler  drain", "quote_b": "Brass Boiler Drain", "reason": "sizes"}'
        out, stats, calls = self.run_resolver(reply)
        self.assertEqual((len(out), len(calls), stats['verified']), (1, 1, 1))     # duplicate question asked once
        self.assertEqual(same_family_links(self.dir / 'r.jsonl')[0][:2], ('https://x.example/a', 'https://x.example/b'))
        _, stats, calls = self.run_resolver(reply)
        self.assertEqual((len(calls), stats['cached']), (0, 1))                    # never paid for twice

    def test_unverifiable_quote_stays_unsure(self):
        out, stats, _ = self.run_resolver('{"answer": "same", "quote_a": "Bronze Gate Valve", "quote_b": "Brass Boiler Drain"}')
        self.assertEqual((out[0]['answer'], out[0]['verified'], stats['quote_failed']), ('unsure', False, 1))

    def test_budget_stops_new_questions(self):
        out, stats, calls = self.run_resolver('{"answer": "different"}', budget=0.0)
        self.assertEqual((len(calls), stats['budget_stop'], out[0]['answer']), (0, 1, 'unsure'))


class TestDownloadDeadline(unittest.TestCase):
    def test_trickling_download_is_abandoned(self):   # crane cold run hung on one stalled response
        import tempfile
        from pathlib import Path
        from unittest import mock
        from mfr_scraper import fetch as F
        from mfr_scraper.robots import Robots

        class Slow:
            url, status_code, headers = 'https://x.example/a.pdf', 200, {'Content-Type': 'application/pdf'}
            def iter_content(self, n):
                while True:
                    yield b'x'
            def close(self):
                pass

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(F, 'CACHE_DIR', Path(tmp)), \
                mock.patch.object(F, 'DOWNLOAD_DEADLINE', 0):
            f = F.Fetcher('deadline-test', log=lambda *a: None)
            f._robots['https://x.example'] = Robots('', F.AGENT_NAME)
            f._wait = lambda *a: None
            f.session = mock.Mock(request=mock.Mock(return_value=Slow()))
            r = f.get('https://x.example/a.pdf', kind='pdf')
        self.assertFalse(r.ok)
        self.assertIn('download exceeded', r.error)
        self.assertEqual(f.session.request.call_count, 1)


class L1SpecTableTest(unittest.TestCase):
    def test_false_keeps_single_spec_value(self):
        from mfr_scraper.process.run import apply_spec_table
        s = {'spec_pair': 1, 'breadcrumb': 1}
        apply_spec_table(s, False)
        self.assertEqual(s, {'spec_pair': 1, 'breadcrumb': 1})
        s = {'spec_pairs': 3}
        apply_spec_table(s, False)
        self.assertEqual(s, {})
        s = {'spec_pair': 1}
        apply_spec_table(s, True)
        self.assertEqual(s, {'spec_pairs': 3})

    def test_simulated_has_spec_table_is_two_rows(self):
        from mfr_scraper import page as P
        from mfr_scraper.process.simulate_l1 import page_facts
        html = ('<html><body><table><tr><th>Body material</th><td>Brass</td></tr>'
                '<tr><th>Max pressure</th><td>200 psi</td></tr></table></body></html>')
        self.assertTrue(page_facts(P.soup_of(html), 'https://x.example/p')['has_spec_table'])



class ListingWithProductEvidenceTest(unittest.TestCase):
    def test_listing_cue_with_spec_evidence_is_kept(self):
        from mfr_scraper.process.run import listing_with_product_evidence as f
        self.assertTrue(f({'spec_pairs': 3, 'breadcrumb': 1, 'url_word': 1, 'listing_like': -4}, 4.0))
        self.assertTrue(f({'spec_download': 2, 'breadcrumb': 1, 'url_word': 1, 'listing_like': -4}, 4.0))

    def test_category_page_with_facet_table_still_dropped(self):
        from mfr_scraper.process.run import listing_with_product_evidence as f
        self.assertFalse(f({'spec_pairs': 3, 'breadcrumb': 1, 'download': 1, 'listing_like': -4}, 4.0))

    def test_plain_listing_still_dropped(self):
        from mfr_scraper.process.run import listing_with_product_evidence as f
        self.assertFalse(f({'download': 1, 'breadcrumb': 1, 'url_word': 1, 'commerce_words': 1, 'listing_like': -4}, 4.0))
        self.assertFalse(f({'spec_download': 2, 'listing_like': -4}, 4.0))
        self.assertFalse(f({'spec_pairs': 3, 'breadcrumb': 1}, 4.0))

if __name__ == '__main__':
    unittest.main()
