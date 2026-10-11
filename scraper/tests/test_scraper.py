"""Offline tests (synthetic HTML modelled on real site markup; no network).
Run from scraper/:  .venv/bin/python -m unittest discover tests
"""
import unittest

from mfr_scraper import assets as A
from mfr_scraper import hosts as H
from mfr_scraper import discover as D
from mfr_scraper import page as P
from mfr_scraper import specs as S
from mfr_scraper.pipeline import base_name, group_families, merge_field, pdf_about_family, series_code_of
from mfr_scraper.robots import Robots

# Sitefinity-style div pairs inside a body whose class contains "header" (a real false-positive trap).
DIV_PAIRS = '''<html lang="en"><body class="header-body"><header><nav><a href="/x">Size</a></nav></header>
<h1>Series 35/36</h1>
<div class="specifications"><div class="item"><div class="title">Size Range</div><div class="data">NPS 22 to 120 / DN 550 to 3000</div></div>
<div class="item"><div class="title">Temperature Range</div><div class="data">-20°F to 400°F (-29°C to 204°C)</div></div>
<div class="item"><div class="title">Stem Materials</div><div class="data">416 Stainless Steel</div></div>
<div class="item"><div class="title">Maximum Allowable Operating Pressure</div><div class="data">Series 35: 75 psi (5 bar)<br> Series 36: 150 psi (10 bar)</div></div>
<div class="item"><div class="title">Certifications</div><div class="data">ABS, ATEX, NSF 61/372, PED</div></div></div>
<a href="/docs/specifications/datasheets/en_sds_s35.pdf">Download</a><a href="/docs/terms.pdf">Terms</a>
<footer><a href="/docs/terms.pdf">Terms</a></footer><button>Request a Quote</button></body></html>'''

# WordPress-style label + div, image wrapped in a link to the full-size original.
LABEL_PAIRS = '''<html lang="en-GB"><body><div class="breadcrumb"><a href="/">Home</a> / <a href="/c/">Ball Valves</a> / <span>D171ATH</span></div>
<h1>D171ATH 1/2" to 2"</h1>
<a class="product__image-main" href="/app/uploads/2023/06/D171ATH-BF-scaled.jpg"><img src="/app/uploads/2023/06/D171ATH-BF-1024x722.jpg" alt="D171ATH"></a>
<div class="product__specification"><label>Size</label><div>1/2" to 2"</div></div>
<div class="product__specification"><label>Pressure rating</label><div>PN25</div></div>
<div class="product__specification"><label>End Connections</label><div>Taper threaded to BS EN 10226-2 (ISO 7-1)</div></div>
<div class="product__specification"><label>Material</label><div>DZR Brass</div></div>
<h3>Ball Valve Pipe Ending and Crane FS Ball</h3><p>Embodied Carbon Request</p></body></html>'''

SCHEMA_ORG = '''<html lang="en-US"><head><script type="application/ld+json">{"@context":"https://schema.org","@graph":[
{"@type":"Product","name":"PEX Adapter 1/2\\"","sku":"643WG2","offers":{"@type":"Offer","price":"12.50","priceCurrency":"USD"},
 "image":"https://www.example.com/img/643WG2.jpg"},
{"@type":"BreadcrumbList","itemListElement":[{"position":1,"name":"Home"},{"position":2,"name":"Fittings"},{"position":3,"name":"PEX Adapter 1/2\\""}]}]}
</script></head><body><table><tr><th>End Connection</th><td>F1960 PEX x NPT</td></tr><tr><th>Body</th><td>Lead-free brass</td></tr></table></body></html>'''


class TestRobots(unittest.TestCase):
    def test_merged_groups_and_wildcards(self):
        r = Robots('User-agent: *\nDisallow: /wp/wp-admin/\nAllow: /wp/wp-admin/admin-ajax.php\n\n'
                   'User-agent: *\nDisallow: *.pdf\n\nUser-agent: *\nDisallow:\nSitemap: https://x.com/s.xml', 'mfr-scraper')
        self.assertFalse(r.allowed('https://x.com/app/uploads/2023/09/sheet.pdf'))
        self.assertTrue(r.allowed('https://x.com/product/ball-valves/d171/'))
        self.assertTrue(r.allowed('https://x.com/wp/wp-admin/admin-ajax.php'))
        self.assertFalse(r.allowed('https://x.com/wp/wp-admin/options.php'))
        self.assertEqual(r.sitemaps, ['https://x.com/s.xml'])

    def test_specific_agent_and_dollar_anchor(self):
        r = Robots('User-agent: *\nDisallow: /\n\nUser-agent: mfr-scraper\nDisallow: /*?productId=\nDisallow: /private$', 'mfr-scraper')
        self.assertTrue(r.allowed('https://x.com/products/a'))
        self.assertFalse(r.allowed('https://x.com/p?productId=3'))
        self.assertFalse(r.allowed('https://x.com/private'))
        self.assertTrue(r.allowed('https://x.com/private/page'))


class TestPageExtraction(unittest.TestCase):
    def fields(self, html):
        return {p.field: p.value for p in P.label_value_pairs(P.soup_of(html))}

    def test_div_pairs_not_treated_as_chrome(self):
        f = self.fields(DIV_PAIRS)
        self.assertEqual(f['size_range'], 'NPS 22 to 120 / DN 550 to 3000')
        self.assertEqual(f['_other'], '416 Stainless Steel')        # stem is not body material
        self.assertNotIn('material_body', f)
        self.assertEqual(S.parse_field('pressure_rating', f['pressure_rating'])[:2], (150.0, 'psi'))
        self.assertEqual(set(S.parse_field('certifications', f['certifications'])[0]) >= {'NSF/ANSI 61', 'NSF/ANSI 372', 'PED'}, True)

    def test_label_pairs_and_long_heading_ignored(self):
        f = self.fields(LABEL_PAIRS)
        self.assertEqual(S.parse_field('pressure_rating', f['pressure_rating']), (25.0, 'bar', 'PN25'))
        self.assertEqual(S.parse_field('end_connections', f['end_connections'])[0], ['BSPT'])
        self.assertNotIn('material_trim', f)

    def test_table_and_schema_org(self):
        soup = P.soup_of(SCHEMA_ORG)
        f = self.fields(SCHEMA_ORG)
        self.assertEqual(S.parse_field('end_connections', f['end_connections'])[0], ['NPT', 'PEX expansion'])   # SPEC 6 vocabulary
        self.assertEqual(P.product_skus(soup), ['643WG2'])
        self.assertEqual(P.breadcrumbs(soup)[1], 'Fittings')
        price = P.price_signals(soup, P.visible_text(soup))
        self.assertEqual((price['availability'], price['amount'], price['currency']), ('price_shown', 12.5, 'USD'))

    def test_price_wording(self):
        for text, status in [('Sign in for Pricing', 'login_required'), ('Request a Quote', 'request_quote'),
                             ('Our valves are great', 'not_published')]:
            soup = P.soup_of(f'<p>{text}</p>')
            self.assertEqual(P.price_signals(soup, text)['availability'], status)

    def test_image_link_to_original(self):
        cands = P.image_candidates(P.soup_of(LABEL_PAIRS), 'https://www.cranefs.com/product/x/')
        urls = [c[0] for c in cands]
        self.assertIn('https://www.cranefs.com/app/uploads/2023/06/D171ATH-BF-scaled.jpg', urls)
        best = max(cands, key=lambda c: A.rank_candidate(c[0], c[1]))
        self.assertTrue(best[0].endswith('-scaled.jpg'))


class TestSpecParsing(unittest.TestCase):
    def test_values(self):
        cases = [
            ('temperature_range', '0F -123F (-18D - 50C)', {'min': 0.0, 'max': 123.0}),
            ('temperature_range', '-22°F to +150°F', {'min': -22.0, 'max': 150.0}),
            ('size_range', '1/4" to 10" (6.35mm to 254mm)', {'min': '1/4', 'max': '10'}),
            ('size_range', 'NPS 0 100 200 300 400 500 600 700 800 900', None),
            ('pressure_rating', '600 WOG', 600.0),
            ('material_seat', 'O-Ring Materials', None),
            ('applications', 'Factor', None),
            ('material_body', 'One piece full flanged style. All bodies are drilled to ASME 125/150.', None),
            ('material_trim', 'Nylon 11 Coated Ductile Iron, Aluminum Bronze, Stainless Steel, Duplex Stainless Steel, Monel', 'list'),
        ]
        for field, raw, expected in cases:
            got = S.parse_field(field, raw)
            if expected is None:
                self.assertIsNone(got, raw)
            elif expected == 'list':
                self.assertIsNotNone(got, raw)
            else:
                self.assertEqual(got[0], expected, raw)

    def test_pdf_line_pairs(self):
        text = 'Temperature          -22°F to +150°F\nMedia                                  Factor\nBody Material:   Ductile Iron'
        got = {f: v for _, v, f, _ in S.pairs_from_text(text)}
        self.assertEqual(got['temperature_range'], '-22°F to +150°F')
        self.assertEqual(got['material_body'], 'Ductile Iron')


class TestDocsAndImages(unittest.TestCase):
    def test_doc_classification(self):
        cases = [
            ('https://b.com/docs/specifications/datasheets/en_sds_spvc211.pdf', 'Download', 'spec_sheet'),
            ('https://b.com/docs/x/br_en_datasheet_ac.pdf', 'Download', 'spec_sheet'),
            ('https://b.com/manuals/iom-manuals/en-iom-trunnion.pdf', 'Download', 'iom_manual'),
            ('https://x.com/chem/msds-cement.pdf', '', 'other_doc'),
            ('https://cdn.x.com/SpecSheets/550F3111%20-%20SPEC%20SHEET.PDF', '', 'spec_sheet'),
            ('https://x.com/docs/2026-price-list.pdf', '', 'price_list'),
            ('https://x.com/docs/submittal-643.pdf', '', 'submittal'),
            ('https://x.com/docs/limited-warranty.pdf', '', 'warranty'),
        ]
        for url, text, expected in cases:
            self.assertEqual(A.classify_doc(url, text), expected, url)

    def test_language(self):
        en = 'The valve is rated for the pressure and temperature of this system and is suitable for use with water. ' * 5
        fr = 'La vanne est conçue pour la pression et la température de ce système et pour une utilisation avec eau. ' * 4
        self.assertEqual(A.detect_lang(en)[0], 'en')
        self.assertEqual(A.detect_lang(en + fr)[0], 'en+fr')
        self.assertEqual(A.detect_lang(fr * 2)[0], 'fr')

    def test_cad(self):
        self.assertEqual(A.cad_from_url('https://x.com/a/607-2S.RFA'), {'cad_type': 'bim', 'formats': ['rfa']})
        self.assertEqual(A.cad_from_url('https://x.com/a/112003%20%28stp%29.stp')['formats'], ['step'])
        self.assertIsNone(A.cad_from_url('https://x.com/a/sheet.pdf'))

    def test_original_candidates(self):
        self.assertIn('https://x.com/up/D171-BF.jpg', A.original_candidates('https://x.com/up/D171-BF-300x212.jpg'))
        self.assertIn('https://d.com/sites/default/files/p/x.jpg',
                      A.original_candidates('https://d.com/sites/default/files/styles/thumbnail/public/p/x.jpg.webp?itok=a'))


class TestDiscoveryAndFamilies(unittest.TestCase):
    def test_templates(self):
        urls = [f'https://c.com/product/{cat}/{p}/' for cat in ('ball-valves', 'gate-valves', 'strainers') for p in 'abcdefg']
        urls += ['https://c.com/category/ball-valves/', 'https://c.com/resources?page=2', 'https://c.com/news/x']
        cands = D.candidate_pages(urls, ['c.com'])
        self.assertNotIn('https://c.com/resources?page=2', cands)
        self.assertNotIn('https://c.com/news/x', cands)
        t = D.build_templates(cands)
        self.assertIn('/product/*/*', t)
        self.assertTrue(D.match_template('https://c.com/product/x/y/', '/product/*/*'))

    def test_family_grouping_by_size_only(self):
        class R:
            def __init__(self, url, name, crumbs):
                self.url, self.name, self.crumbs = url, name, crumbs
        recs = [R('https://s.com/Products/640WP02', 'F1960 Poly Plug 1/2"', ['Home', 'Fittings', 'x']),
                R('https://s.com/Products/640WP03', 'F1960 Poly Plug 3/4"', ['Home', 'Fittings', 'y']),
                R('https://b.com/series-35', 'Series 35/36', []),
                R('https://b.com/series-30', 'Series 30/31', [])]
        groups = group_families(recs)
        self.assertEqual(sorted(len(g) for g in groups), [1, 1, 2])
        self.assertEqual(base_name('F1960 Poly Plug 1/2"'), 'f1960 poly plug')
        self.assertEqual(series_code_of('Series 35/36', 'https://b.com/series-35'), '35/36')


class TestMerge(unittest.TestCase):
    def cand(self, kind, value, unit=None):
        return {'kind': kind, 'value': value, 'unit': unit, 'conditions': None, 'raw': str(value),
                'source': {'url': f'https://x.com/{kind}', 'type': 'page' if kind == 'page' else 'pdf', 'quote': str(value)}}

    def test_spec_sheet_wins_conflict(self):
        m = merge_field('pressure_rating', [self.cand('page', 400.0, 'psi'), self.cand('sheet', 600.0, 'psi')])
        self.assertEqual((m['value'], m['display_source'], m['cross_check']), (600.0, 'pdf', 'conflict'))
        self.assertEqual(m['alt_values'][0]['value'], 400.0)

    def test_agree_across_units(self):
        m = merge_field('pressure_rating', [self.cand('page', 600.0, 'psi'), self.cand('sheet', 41.37, 'bar')])
        self.assertEqual(m['cross_check'], 'agree')
        self.assertEqual(len(m['sources']), 2)

    def test_page_beats_other_pdf_and_pdf_only_disagreement(self):
        m = merge_field('material_body', [self.cand('otherpdf', 'Bronze'), self.cand('page', 'Brass')])
        self.assertEqual((m['value'], m['display_source'], m['cross_check']), ('Brass', 'page', 'conflict'))
        m = merge_field('material_body', [self.cand('otherpdf', 'Bronze'), self.cand('sheet', 'Brass')])
        self.assertEqual((m['value'], m['cross_check']), ('Brass', 'pdf_only'))
        self.assertTrue(m.get('_pdf_disagreement'))
        self.assertNotIn('alt_values', m)


class TestDecisions(unittest.TestCase):
    """Behaviour decided on 2026-10-09: refines, PDF relevance, installation photos, robots override."""

    def cand(self, kind, value, unit=None):
        return TestMerge.cand(None, kind, value, unit)

    def test_refines(self):
        m = merge_field('material_body', [self.cand('page', 'Plastic'), self.cand('sheet', 'Polyphenylsulfone (PPSU)')])
        self.assertEqual((m['value'], m['cross_check']), ('Polyphenylsulfone (PPSU)', 'refines'))
        self.assertEqual(m['alt_values'][0]['value'], 'Plastic')
        m = merge_field('certifications', [self.cand('page', ['UL']), self.cand('sheet', ['UL', 'CSA', 'NSF/ANSI 61'])])
        self.assertEqual(m['cross_check'], 'refines')
        m = merge_field('certifications', [self.cand('page', ['UL', 'FM']), self.cand('sheet', ['UL'])])
        self.assertEqual(m['cross_check'], 'conflict')            # page lists something the sheet does not
        m = merge_field('material_body', [self.cand('page', 'Bronze'), self.cand('sheet', 'Brass')])
        self.assertEqual(m['cross_check'], 'conflict')

    def test_pdf_about_family(self):
        class R:
            url = 'https://b.com/valves/series-35-36'
        fam = {'series_code': '35/36', 'name': 'Series 35/36 Resilient Seated Butterfly Valve'}
        self.assertTrue(pdf_about_family('Bray Series 35/36 data sheet ...', fam, [R()]))
        self.assertTrue(pdf_about_family('Resilient seated valves datasheet', fam, [R()]))
        self.assertFalse(pdf_about_family('Series 70 electric actuator manual', fam, [R()]))

    def test_installation_photos(self):
        for name in ('821-200-rough-in.jpg', 'installation-photo.jpg', 'lifestyle_kitchen.jpg'):
            self.assertTrue(A.NON_PRODUCT_PHOTO.search(name), name)
        self.assertFalse(A.NON_PRODUCT_PHOTO.search('643WG2.jpg'))

    def test_pdf_tables_in_evidence_text(self):
        import io
        try:
            from reportlab.pdfgen import canvas  # optional; skip if unavailable
        except ImportError:
            self.skipTest('reportlab not installed')
        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        c.drawString(72, 720, 'Series 99 Data Sheet')
        c.save()
        text, pages, title, rev, rows = A.pdf_text(buf.getvalue())
        self.assertIn('Series 99', text)


class TestHostsAndVocab(unittest.TestCase):
    def test_registrable_domain(self):
        self.assertEqual(H.registrable_domain('www.bray.com'), 'bray.com')
        self.assertEqual(H.registrable_domain('shop.example.co.uk'), 'example.co.uk')
        self.assertEqual(H.page_hosts('https://www.siouxchief.com/'), ['siouxchief.com'])

    def test_detect_asset_hosts(self):
        class R:
            def __init__(self, docs, imgs):
                self.doc_links = [(u, '') for u in docs]
                self.image_cands = [(u, None, '', 'img') for u in imgs]
        pages = [R(['https://cdn.siouxchief.com/SpecSheets/a.PDF'], ['https://cdn.siouxchief.com/ProductImages/a.JPG',
                                                                     'https://www.facebook.com/tr.gif']) for _ in range(8)]
        pages += [R([], ['https://distributor.example.com/x.jpg'])]
        hosts, _ = H.detect_asset_hosts(pages, ['siouxchief.com'])
        self.assertEqual(hosts, [])                                  # cdn.siouxchief.com is already a page host
        pages = [R(['https://aalberts.compano.com/Data/x.pdf'], ['https://fonts.googleapis.com/a.png']) for _ in range(5)]
        hosts, _ = H.detect_asset_hosts(pages + [R([], ['https://other.com/a.jpg'])], ['aalberts-ips.us'])
        self.assertEqual(hosts, ['aalberts.compano.com'])

    def test_vocabularies(self):
        self.assertEqual(S.parse_connections('Sweat x FIP'), ['NPT', 'solder'])
        self.assertEqual(S.parse_connections('F1807 crimp ring x NPT'), ['NPT', 'PEX crimp'])
        self.assertEqual(S.parse_connections('Full Lug, Wafer'), ['wafer', 'lug'])
        terms, unmapped = S.map_vocab('Water, Wastewater, Power Generation, Pulp & Paper', S.APPLICATION_WORDS)
        self.assertEqual(terms, ['wastewater', 'power generation', 'pulp and paper'])
        self.assertIn('Water', unmapped)                              # plain "water" is not assumed potable



class TestVariantsFromHeadingList(unittest.TestCase):
    """Round 8: identifiers listed in the product heading are the family's orderable figures."""
    def test_heading_lists(self):
        from mfr_scraper.variants import from_name
        self.assertEqual(from_name('F646L / F641L / F656L 50mm to 200mm'), ['F646L', 'F641L', 'F656L'])
        self.assertEqual(from_name('FM638 / FM639'), ['FM638', 'FM639'])
        self.assertEqual(from_name('D2003 / D2004 3/8" to 1"'), ['D2003', 'D2004'])

    def test_series_and_singles_rejected(self):
        from mfr_scraper.variants import from_name
        for n in ('Series 5000/6000', 'Series 20/21', 'KM 20/21', 'D171 1/4" to 2 1/2"', 'D220W-D220CW', '3/8 / 1/2 valve', ''):
            self.assertEqual(from_name(n), [], n)



class TestTemperatureUnitInLabel(unittest.TestCase):
    """Round 9: pressure/temperature rows carry the unit only in the label ('TEMPERATURE (°C) -10 to 120')."""
    def test_rows(self):
        from mfr_scraper.specs import temperature_from_unit_label as T
        self.assertEqual(T('TEMPERATURE (°C) -10 to 100 110 120')[:2], ({'min': -10.0, 'max': 120.0}, 'C'))
        self.assertEqual(T('TEMPERATURE (°C) -10 to 120 -10 to 82')[:2], ({'min': -10.0, 'max': 120.0}, 'C'))
        self.assertEqual(T('5" CL125 MAX TEMPERATURE (°C) -10 to 90 -10 to 130')[:2], ({'min': -10.0, 'max': 90.0}, 'C'))
        self.assertEqual(T('MAX TEMPERATURE (°F) 250')[:2], ({'min': None, 'max': 250.0}, 'F'))
        self.assertEqual(T('TEMPERATURE (°C) -10 to 130 500 13804 0.525')[:2], ({'min': -10.0, 'max': 130.0}, 'C'))
        self.assertEqual(T('TEMPERATURE (°C) -10 to 100 110 120 186')[:2], ({'min': -10.0, 'max': 186.0}, 'C'))

    def test_rejects(self):
        from mfr_scraper.specs import temperature_from_unit_label as T
        for line in ('Pressure/Temperature Ratings', 'TEMPERATURE (°C)', 'Suitable for a wide temperature range -10°C to 130°C',
                     'Temperature sensor (C) wiring'):
            self.assertIsNone(T(line), line)



class TestApplicationsFromSheetProse(unittest.TestCase):
    """Round 10: applications stated in spec-sheet prose ("WRAS Approved for use with potable water")."""
    def test_prose(self):
        from mfr_scraper.specs import applications_from_text as A
        self.assertEqual(A('Features\n• WRAS Approved for use with potable water up to 85°C\nMaterials'),
                         (['potable water'], '• WRAS Approved for use with potable water up to 85°C'))
        self.assertEqual(A('Suitable for steam and condensate applications')[0], ['steam', 'condensate'])

    def test_no_use_stated(self):
        from mfr_scraper.specs import applications_from_text as A
        self.assertIsNone(A('Body: steam-tested ductile iron\nOffers zone, terminal bypass and end of line applications'))


if __name__ == '__main__':
    unittest.main()


class TestGenerality(unittest.TestCase):
    """AUTONOMOUS_RUN rule 4: no site-specific code in the scraper package."""
    SITE_STRINGS = ['bray', 'crane', 'cranefs', 'sioux', 'apollo', 'aalberts', 'compano', 'caleffi', 'cimberio',
                    'milwaukee', 'dixon']

    def test_no_site_names_in_scraper_code(self):
        import pathlib
        import re
        pkg = pathlib.Path(A.__file__).resolve().parent
        hits = []
        for f in sorted(pkg.glob('*.py')):
            for n, line in enumerate(f.read_text().splitlines(), 1):
                for s in self.SITE_STRINGS:
                    if re.search(re.escape(s), line, re.I):
                        hits.append(f'{f.name}:{n}: {s}: {line.strip()[:100]}')
        self.assertEqual(hits, [], 'site-specific strings in scraper code:\n' + '\n'.join(hits))


class TestCrashIsolation(unittest.TestCase):
    def test_guarded_flags_and_continues(self):
        from mfr_scraper.pipeline import SiteRun
        import collections
        r = object.__new__(SiteRun)
        r.flags, r.flag_examples, r.log = collections.Counter(), {}, lambda *a: None
        self.assertIsNone(r.guarded('page_crashed', 'https://x.test/p', lambda: 1 / 0))
        self.assertEqual(r.guarded('page_crashed', 'https://x.test/q', lambda a: a + 1, 1), 2)
        self.assertEqual(r.flags['page_crashed'], 1)
        self.assertIn('https://x.test/p: ZeroDivisionError', r.flag_examples['page_crashed'])


class TestVariants(unittest.TestCase):
    def test_row_and_line_layouts(self):
        from mfr_scraper import variants as V
        self.assertEqual([s for s, _, _ in V.from_lines('2\n1 SRH Model # SRH1 SRH2 SRH3\nHandle Length (in) 10.47 13.38')],
                         ['SRH1', 'SRH2', 'SRH3'])
        self.assertEqual([s for s, _, _ in V.from_rows([['Part No.', 'A-100', 'A-200']])], ['A-100', 'A-200'])

    def test_column_layout_with_size(self):
        from mfr_scraper import variants as V
        rows = [['Part Number', 'Size', 'Weight'], ['643WG2', '1/2"', '0.3 lb'], ['643WG3', '3/4"', '0.4 lb']]
        self.assertEqual([(s, z) for s, z, _ in V.from_rows(rows)], [('643WG2', '1/2"'), ('643WG3', '3/4"')])

    def test_parts_lists_and_dimension_tables_are_not_variants(self):
        from mfr_scraper import variants as V
        self.assertEqual(V.from_rows([['Item', 'Description', 'Material', 'Qty'], ['1', 'Base Plate', 'CF8M', '1'],
                                      ['2', 'Handle Body', 'CF8M', '1']]), [])
        self.assertEqual(V.from_rows([['Size', 'A', 'B'], ['2"', '4.5', '3.1'], ['3"', '5.5', '3.6']]), [])
        self.assertEqual(V.from_lines('Model shown: 30 series\nModels 2 3'), [])
        self.assertEqual(V.from_lines('Item No. 1 2 3'), [])


class TestPdfCap(unittest.TestCase):
    """Round 3: families with one datasheet per model (10+ primary PDFs) lost sheets to a cap of 10."""
    def test_cap_keeps_multi_datasheet_families(self):
        from mfr_scraper.settings import MAX_PDFS_PER_FAMILY
        self.assertGreaterEqual(MAX_PDFS_PER_FAMILY, 25)


class TestVariantHeadingLists(unittest.TestCase):
    """Round 4: a 'Models' spec label with the identifiers on the next line, comma-separated."""
    def test_heading_then_list(self):
        from mfr_scraper import variants as V
        got = V.from_lines('Size Range\n2" - 24"\nModels\n201, 203, 205, 210\nMaterials')
        self.assertEqual([s for s, _, _ in got], ['201', '203', '205', '210'])

    def test_same_line_commas(self):
        from mfr_scraper import variants as V
        self.assertEqual([s for s, _, _ in V.from_lines('Models: A-10, A-20, A-30')], ['A-10', 'A-20', 'A-30'])

    def test_heading_then_prose_rejected(self):
        from mfr_scraper import variants as V
        self.assertEqual(V.from_lines('Models\nSeries 70 and Series 71 actuators'), [])
        self.assertEqual(V.from_lines('Models\n2, 4'), [])


class TestVariantPlaceholders(unittest.TestCase):
    """Round 4: URL slugs are not identifiers; accessory pages listing another family's models get no variants."""
    def test_accessory_subset_moved(self):
        from mfr_scraper.pipeline import accessory_families
        pr = [{'availability': 'request_quote'}]
        valve = {'canonical_url': 'v', 'variants': [{'sku': s, 'prices': pr} for s in ('201', '205', '211', '212')]}
        acc = {'canonical_url': 'a', 'variants': [{'sku': s, 'prices': pr} for s in ('205', '211')]}
        other = {'canonical_url': 'o', 'variants': [{'sku': 'X-1', 'prices': pr}]}
        changed = accessory_families([valve, acc, other])
        self.assertEqual(changed, [acc])
        self.assertEqual(acc['variants'], [])
        self.assertEqual(acc['family_prices'], pr)
        self.assertEqual(len(valve['variants']), 4)
        self.assertEqual(len(other['variants']), 1)

    def test_slug_is_not_identifier(self):
        from mfr_scraper import variants as V
        self.assertFalse(V._is_id('SINGLE-DOOR-CHECK-VALVE'))
        self.assertFalse(V._is_id('SERIES-752-752HP-KNIFE-GATE-VALVE'))
        self.assertTrue(V._is_id('FM638'))


class TestFamilyPriceAlwaysFilled(unittest.TestCase):
    """Round 5: SPEC 7 family_prices availability is always filled, including not_published."""
    def test_not_published_main_page(self):
        from types import SimpleNamespace as NS
        from mfr_scraper.pipeline import family_price_page
        a, b = NS(price={'availability': 'not_published'}), NS(price={'availability': 'not_published'})
        self.assertIs(family_price_page([a, b]), a)
        c = NS(price={'availability': 'request_quote'})
        self.assertIs(family_price_page([a, c]), c)


class TestTemperatureRangeUnitOnce(unittest.TestCase):
    """Round 6: '-10 - 120°C' parsed as max -120 because only the upper bound carries the unit."""
    def test_ranges(self):
        from mfr_scraper.specs import parse_temperature as T
        self.assertEqual(T('-10 - 120°C'), ({'min': -10.0, 'max': 120.0}, 'C'))
        self.assertEqual(T('-10 to 120°C'), ({'min': -10.0, 'max': 120.0}, 'C'))
        self.assertEqual(T('10 - 120°C'), ({'min': 10.0, 'max': 120.0}, 'C'))
        self.assertEqual(T('-20°F to 400°F'), ({'min': -20.0, 'max': 400.0}, 'F'))
        self.assertEqual(T('5°C to 95°C'), ({'min': 5.0, 'max': 95.0}, 'C'))
        self.assertEqual(T('Maximum temperature 120°C'), ({'min': None, 'max': 120.0}, 'C'))


class TestSizeColumnTables(unittest.TestCase):
    """Round 7: sizes_available from the SIZE column of dimension tables (merged PDF rows included)."""
    def test_size_column(self):
        from mfr_scraper.specs import sizes_from_tables
        rows = [(1, ['PART', 'MATERIAL']), (1, ['SIZE (mm)', 'WEI (k', 'A (mm)']), (1, ['50', '2', '109']),
                (1, ['65 80', '3 3', '131.5 134']), (1, ['100', '4', '163']), (1, ['TECHNICAL HELPLINE', 'x'])]
        sizes, unit, pg, quote = sizes_from_tables(rows)
        self.assertEqual(sizes, ['50', '65', '80', '100'])
        self.assertEqual((unit, pg, quote), ('mm', 1, '50 | 2 | 109'))

    def test_inch_and_rejects(self):
        from mfr_scraper.specs import sizes_from_tables
        self.assertEqual(sizes_from_tables([(1, ['SIZE (inch)', 'A']), (1, ['1/2', '3']), (1, ['1-1/4', '4'])])[:2],
                         (['1/2', '1-1/4'], 'in'))
        self.assertIsNone(sizes_from_tables([(1, ['Size', 'A']), (1, ['Small', '3'])]))
        self.assertIsNone(sizes_from_tables([(1, ['Size range', 'DN15 to DN50'])]))


class TestParsedPdfCache(unittest.TestCase):
    """Shared PDFs were re-parsed for every family that linked them (~28% of the Sioux Chief run)."""
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def parse(self, body, pages=8):
        self.calls.append(body)
        return body.decode(), [body.decode()], 'T', None, [(1, ['DN', body.decode()])]

    def cache(self, cap=10_000):
        from pathlib import Path
        from mfr_scraper.pdfcache import ParsedPdfCache
        return ParsedPdfCache(root=Path(self.tmp.name), mem_cap=cap, parse=self.parse)

    def test_parsed_once_per_content_and_reused_across_runs(self):
        c = self.cache()
        first = c.get('aa11', b'sheet')
        self.assertEqual(c.get('aa11', b'sheet'), first)
        self.assertEqual(self.cache().get('aa11', b'sheet'), first)   # a new run reads the disk entry
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(first, ('sheet', ['sheet'], 'T', None, [(1, ['DN', 'sheet'])]))

    def test_memory_stays_under_cap(self):
        c = self.cache(cap=100)
        for i in range(50):
            c.get(f'{i:04x}', b'x' * 20)
        self.assertLessEqual(c.mem_bytes, 100)
        self.assertGreater(c.stats['evicted'], 0)
        c.get('0000', b'x' * 20)   # evicted from memory, still on disk
        self.assertEqual(len(self.calls), 50)

    def test_unreadable_entry_is_parsed_again(self):
        c = self.cache()
        c.get('bb22', b'sheet')
        (c.dir / 'bb' / 'bb22.json').write_text('{broken')
        self.assertEqual(self.cache().get('bb22', b'sheet')[0], 'sheet')
        self.assertEqual(len(self.calls), 2)
