"""Offline self-tests for the harness. Run from harness/:  python -m unittest discover tests"""
import copy
import csv
import json
import os
import tempfile
import unittest

from mfr_harness import normalize as N
from mfr_harness.config import HARNESS_ROOT, load_json
from mfr_harness.legacy import load_legacy_csv
from mfr_harness.score import score_legacy, score_siterun
from mfr_harness.validate import validate

TEMPLATE = load_json(HARNESS_ROOT / 'gold' / '_TEMPLATE.json')


def gold_fixture(full_template=False):
    """Template turned into a valid answer key for site 'bray' (allowed host www.bray.com).

    By default only the fully labelled family (series-100) is kept; full_template=True also keeps
    the variant-less family that demonstrates family_prices (SPEC 7)."""
    g = json.loads(json.dumps(TEMPLATE).replace('https://www.example.com', 'https://www.bray.com')
                   .replace('https://example.partcommunity.com', 'https://bray.partcommunity.com'))
    g['site'] = 'bray'
    if not full_template:
        g['families'] = g['families'][:1]
        g['family_index'] = g['family_index'][:1]
        g['coverage']['families'] = 1
    return g


EVIDENCE_TEXT = {
    '1' * 64: 'SERIES 100 SPECIFICATION SHEET  Sizes: 1/2" - 2"  Size (NPS) 1/2, 3/4, 1, 1-1/4,\n1-1/2, 2 '
              'Body: Lead Free Brass (C27453)  Pressure Rating: 600 WOG  Temperature: -20°F to 400°F '
              'Certified to NSF/ANSI 61 and NSF/ANSI 372; CSA listed. Conforms to MSS SP-110',
    '3' * 64: 'Series 100 Ball Valve  Sizes 1/2" to 2"  Body Material: Brass  Connections: NPT, Solder '
              'Max Pressure: 400 WOG  Ideal for potable water and HVAC hydronic systems. '
              'Contact your local distributor for pricing',
    '4' * 64: '2026 List Price Book  Series 100  100-050 1/2" $42.18',
    '5' * 64: 'Series 200 Butterfly Valve  Sizes on request  Request a Quote',
}


class EvidenceDir:
    """Temporary evidence/text/<sha256>.txt tree for the fixture."""

    def __enter__(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.makedirs(os.path.join(self.tmp.name, 'text'))
        for sha, text in EVIDENCE_TEXT.items():
            with open(os.path.join(self.tmp.name, 'text', f'{sha}.txt'), 'w') as f:
                f.write(text)
        return self.tmp.name

    def __exit__(self, *exc):
        self.tmp.cleanup()


def rule_errors(run, is_gold=True, evidence=True):
    with EvidenceDir() as ev:
        rep = validate(run, 'bray', is_gold=is_gold, evidence_dir=ev if evidence else None)
    return [i for i in rep.items if i[0] == 'ERROR' and not i[1].startswith('schema')], rep


class TestNormalize(unittest.TestCase):
    def test_image_renditions_collapse(self):
        same = [
            ('https://dixonvalve.com/sites/default/files/styles/thumbnail/public/product-groups/x.jpg.webp?h=a0&itok=uE',
             'https://dixonvalve.com/sites/default/files/product-groups/x.jpg'),
            ('https://www.cranefs.com/app/uploads/2023/06/D172ATH-PF-300x212.jpg',
             'https://www.cranefs.com/app/uploads/2023/06/D172ATH-PF.jpg'),
            ('https://cdn11.bigcommerce.com/s-h/images/stencil/50x50/products/115/386/778NPT__81859.1672337619.png?c=1',
             'https://cdn11.bigcommerce.com/s-h/images/stencil/original/products/115/386/778NPT__81859.1672337619.png'),
            ('https://www.caleffi.com/sites/default/files/styles/file_cover/public/product/cover/846101.jpg.webp?itok=Q',
             'https://www.caleffi.com/sites/default/files/product/cover/846101.jpg'),
        ]
        for a, b in same:
            self.assertEqual(N.image_key(a), N.image_key(b), a)
        self.assertNotEqual(N.image_key('https://a.com/x/valve-1.jpg'), N.image_key('https://a.com/x/valve-2.jpg'))

    def test_match_key(self):
        self.assertEqual(N.match_key('https://www.Bray.com/Products/A/?utm_source=x'), N.match_key('http://bray.com/products/a'))
        self.assertNotEqual(N.match_key('https://web.cimberio.com/index.php/figura/1?subcategoria_id=1'),
                            N.match_key('https://web.cimberio.com/index.php/figura/1?subcategoria_id=2'))

    def test_locale(self):
        self.assertEqual(N.locale_of_url('https://www.bray.com/de/valves'), 'de')
        self.assertEqual(N.locale_of_url('https://www.caleffi.com/en-int/x'), 'en-int')
        self.assertEqual(N.locale_of_url('https://web.cimberio.com/index.php/figura/pdf/1660?_lang=it'), 'it')
        self.assertIsNone(N.locale_of_url('https://www.milwaukeevalve.com/product/ml929e/'))
        self.assertEqual(N.market_flag('en-int'), 'non_na')
        self.assertEqual(N.market_flag('en-us'), 'na')
        self.assertFalse(N.is_english('fr'))

    def test_spec_compare(self):
        sv = lambda v, u=None: {'value': v, 'unit': u}
        self.assertEqual(N.compare_spec('pressure_rating', sv(600, 'psi'), sv(41.37, 'bar')), 1.0)
        self.assertEqual(N.compare_spec('temperature_range', sv({'min': -20, 'max': 400}, 'F'), sv({'min': -28.9, 'max': 204.4}, 'C')), 1.0)
        self.assertEqual(N.compare_spec('size_range', sv({'min': '1/2', 'max': '2-1/2'}), sv({'min': '0.5', 'max': '2 1/2'})), 1.0)
        self.assertEqual(N.compare_spec('certifications', sv(['NSF 61', 'Lead Free']), sv(['NSF/ANSI 61', 'NSF/ANSI 372'])), 1.0)
        self.assertLess(N.compare_spec('end_connections', sv(['NPT', 'solder']), sv(['NPT'])), 1.0)


try:
    import jsonschema  # noqa: F401
    HAVE_JSONSCHEMA = True
except ImportError:
    HAVE_JSONSCHEMA = False


class TestValidate(unittest.TestCase):
    @unittest.skipUnless(HAVE_JSONSCHEMA, 'pip install jsonschema')
    def test_template_matches_schema(self):
        _, rep = rule_errors(gold_fixture())
        self.assertEqual([i for i in rep.items if i[1].startswith('schema')], [])

    def test_gold_fixture_has_no_rule_errors(self):
        errors, _ = rule_errors(gold_fixture())
        self.assertEqual(errors, [])

    def test_gold_requires_evidence(self):
        errors, _ = rule_errors(gold_fixture(), evidence=False)
        self.assertTrue(any(w == 'evidence' for _, w, _ in errors))

    def test_catches_violations(self):
        g = gold_fixture()
        fam = g['families'][0]
        fam['images'].append(dict(fam['images'][0], url='https://www.bray.com/images/series-100-300x225.jpg', width=300, height=225))
        fam['documents'][0]['lang'] = 'fr'
        fam['documents'].append(dict(fam['documents'][0], url='https://amresist.com/x.pdf', lang='en'))
        fam['specs']['material_body']['sources'] = []
        msgs = ' | '.join(m for _, _, m in rule_errors(g)[0])
        for expected in ('rendition duplicate', 'below 300px', 'not English-primary', 'host not in allowlist', 'missing source'):
            self.assertIn(expected, msgs)

    def test_cross_check_and_precedence(self):
        g = gold_fixture()
        specs = g['families'][0]['specs']
        pr = specs['pressure_rating']
        # show the web page value instead of the spec sheet value
        specs['pressure_rating'] = dict(pr, value=400, display_source='page',
                                        sources=pr['alt_values'][0]['sources'],
                                        alt_values=[dict(pr['alt_values'][0], value=600, sources=pr['sources'])])
        specs['size_range']['cross_check'] = 'pdf_only'                 # both cited, so must be agree/conflict
        specs['temperature_range']['cross_check'] = 'conflict'          # conflict without alt_values
        specs['end_connections']['sources'][0]['quote'] = 'Connections: NPT, Grooved'   # not in the page text
        msgs = ' | '.join(m for _, _, m in rule_errors(g)[0])
        for expected in ('must be the displayed value', 'page and PDF both cited', 'alt_values is empty',
                         'quote not found'):
            self.assertIn(expected, msgs)

    def test_refines(self):
        g = gold_fixture()
        errors, rep = rule_errors(g)
        self.assertEqual(errors, [])
        self.assertFalse(any('refines' in m for s, _, m in rep.items if s == 'WARN'))
        mb = g['families'][0]['specs']['material_body']
        mb['cross_check'] = 'conflict'                               # a refinement mislabelled as conflict
        _, rep = rule_errors(g)
        self.assertTrue(any('should be refines' in m for s, _, m in rep.items if s == 'WARN'))
        mb['cross_check'] = 'refines'
        del mb['alt_values']
        self.assertTrue(any('alt_values is empty' in m for _, _, m in rule_errors(g)[0]))

    def test_near_duplicate_images_warn_not_error(self):
        g = gold_fixture()
        fam = g['families'][0]
        img = fam['images'][0]
        fam['images'].append(dict(img, url='https://www.bray.com/images/sibling-sku.jpg', phash='c3d1e0f0a0b0c0d1'))
        errors, rep = rule_errors(g)
        self.assertEqual(errors, [])
        self.assertTrue(any('possibly the same image' in m for s, _, m in rep.items if s == 'WARN'))
        fam['images'][-1]['phash'] = 'c3d1e0f0a0b0c0ff'          # distance 7: a different photo, no warning
        _, rep = rule_errors(g)
        self.assertFalse(any('possibly the same image' in m for _, _, m in rep.items))

    def test_gold_sample_has_no_coverage_warning(self):
        g = gold_fixture()
        g['coverage']['sitemap_families'] = 700
        _, rep = rule_errors(g)
        self.assertFalse(any(w == 'coverage' for _, w, _ in rep.items))

    def test_pdf_provenance(self):
        g = gold_fixture()
        fam = g['families'][0]
        fam['documents'][0]['found_on'] = 'https://www.bray.com/documents/library'   # not a family page
        fam['specs']['standards']['sources'][0]['url'] = 'https://www.bray.com/docs/other.pdf'
        msgs = ' | '.join(m for _, _, m in rule_errors(g)[0])
        self.assertIn("not linked from one of this family's pages", msgs)
        self.assertIn('not in the family documents', msgs)
        g = gold_fixture()
        g['families'][0]['series_code'] = '999'
        g['families'][0]['name'] = 'Series 999 Gate Valve'
        _, rep = rule_errors(g)          # linked from the family page: series-level sheet is fine
        self.assertFalse(any('does not mention series' in m for _, _, m in rep.items))


class TestFamilyPrices(unittest.TestCase):
    """SPEC 7: families without variants record their price status in family_prices."""

    def test_full_template_is_valid(self):
        errors, rep = rule_errors(gold_fixture(full_template=True))
        self.assertEqual(errors, [])
        self.assertEqual([i for i in rep.items if i[1].startswith('schema')], [])

    def test_family_prices_validated_like_variant_prices(self):
        g = gold_fixture(full_template=True)
        fp = g['families'][1]['family_prices'][0]
        fp['amount'] = 10.0                                   # amount without price_shown / currency
        fp['source']['quote'] = 'Call for a quote'            # not in the page text
        msgs = ' | '.join(m for _, _, m in rule_errors(g)[0])
        for expected in ('amount set but availability=request_quote', 'amount without currency', 'quote not found'):
            self.assertIn(expected, msgs)
        g = gold_fixture(full_template=True)
        g['families'][1]['family_prices'][0].update(availability='price_shown', amount=None)
        self.assertIn('availability=price_shown but amount is null', ' | '.join(m for _, _, m in rule_errors(g)[0]))

    def test_family_prices_not_allowed_with_variants(self):
        g = gold_fixture(full_template=True)
        g['families'][0]['family_prices'] = copy.deepcopy(g['families'][1]['family_prices'])
        g['families'][0]['family_prices'][0]['source'] = g['families'][0]['variants'][0]['prices'][0]['source']
        self.assertTrue(any('only for families without variants' in m for _, _, m in rule_errors(g)[0]))

    def test_family_price_availability_scored(self):
        g = gold_fixture(full_template=True)
        r = score_siterun(g, copy.deepcopy(g), 'bray')['labelled']['price']
        self.assertEqual(r['families_with_gold_family_price'], 1)
        self.assertEqual(r['variants_with_gold_price'], 2)
        self.assertEqual(r['availability_accuracy'], 1.0)
        p = copy.deepcopy(g)
        p['families'][1]['family_prices'][0]['availability'] = 'not_published'
        self.assertEqual(score_siterun(g, p, 'bray')['labelled']['price']['availability_accuracy'], 0.6667)
        del p['families'][1]['family_prices']                # missing family price counts as wrong
        self.assertEqual(score_siterun(g, p, 'bray')['labelled']['price']['availability_accuracy'], 0.6667)


class TestScore(unittest.TestCase):
    def test_perfect_prediction(self):
        g = gold_fixture()
        r = score_siterun(g, copy.deepcopy(g), 'bray')
        lab = r['labelled']
        self.assertEqual(r['family_index']['recall'], 1.0)
        self.assertEqual(lab['documents_primary']['recall'], 1.0)
        self.assertEqual(lab['documents_primary']['precision'], 1.0)
        self.assertEqual(lab['images']['recall'], 1.0)
        self.assertEqual(lab['image_best_version_rate'], 1.0)
        self.assertEqual(lab['specs_overall'], 1.0)
        self.assertEqual(lab['spec_completeness'], 1.0)
        self.assertEqual(lab['conflict_detection']['recall'], 1.0)
        self.assertEqual(lab['price']['amount_accuracy'], 1.0)

    def test_degraded_prediction(self):
        g = gold_fixture()
        p = copy.deepcopy(g)
        fam = p['families'][0]
        fam['canonical_url'] = fam['variants'][0]['page_url']           # found via a SKU page alias
        fam['documents'][0]['doc_type'] = 'brochure'                     # mislabelled spec sheet
        fam['documents'].append({'url': 'https://www.bray.com/docs/junk.pdf', 'doc_type': 'spec_sheet', 'lang': 'en'})
        fam['images'][0]['url'] = 'https://www.bray.com/images/series-100-300x225.jpg'  # low-res rendition
        fam['images'][0]['width'], fam['images'][0]['height'] = 300, 225
        fam['specs']['pressure_rating'] = dict(fam['specs']['pressure_rating'], value=400, cross_check='agree', alt_values=[])
        del fam['specs']['applications']
        fam['variants'][0]['prices'][0]['amount'] = 40.00
        r = score_siterun(g, p, 'bray')['labelled']
        self.assertEqual(r['labelled_families_found'], 1)
        self.assertEqual(r['documents_primary']['recall'], 1.0)      # found, though mislabelled
        self.assertEqual(r['documents_primary']['precision'], 0.6667)  # spec sheet + price list found, junk.pdf is a false positive
        self.assertEqual(r['doc_type_accuracy'], 0.6667)   # 1 of 3 matched docs mislabelled
        self.assertEqual(r['image_best_version_rate'], 0.0)
        self.assertEqual(r['specs_by_field']['pressure_rating'], 0.0)
        self.assertEqual(r['conflict_detection']['recall'], 0.0)
        self.assertEqual(r['spec_completeness'], 0.9)                 # 9 of 10 gold fields present
        self.assertLess(r['specs_by_gold_display_source']['page'], 1.0)
        self.assertEqual(r['price']['amount_accuracy'], 0.0)

    def test_legacy(self):
        g = gold_fixture()
        rows = [
            ('https://www.bray.com/products/series-100', 'site_page'),
            ('https://www.bray.com/de/products/series-100', 'site_page'),
            ('https://www.bray.com/about', 'site_page'),
            ('https://www.bray.com/docs/100-spec.pdf', 'pdf'),
            ('https://www.bray.com/docs/100-step.zip', 'archive'),
            ('https://www.bray.com/images/series-100-300x225.jpg', 'image'),
            ('https://www.bray.com/images/series-100-150x150.jpg', 'image'),
            ('https://amresist.com/product/x/', 'document'),
        ]
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, 'output.csv')
            with open(path, 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow(['url', 'url_type'])
                w.writerows(rows)
            r = score_legacy(g, load_legacy_csv(path), 'bray')
        self.assertEqual(r['family_index']['recall'], 1.0)
        self.assertEqual(r['labelled']['documents_primary_recall'], 0.5)   # spec sheet found, price list missing
        self.assertEqual(r['labelled']['cad_label_correct'], 0.0)   # zip labelled 'archive'
        self.assertEqual(r['labelled']['images']['rendition_only'], 1)
        self.assertEqual(r['noise']['non_english_rows'], 1)
        self.assertEqual(r['noise']['off_allowlist_rows'], 1)
        self.assertEqual(r['noise']['image_rendition_duplicates'], 1)


if __name__ == '__main__':
    unittest.main()


class TestRepoHygiene(unittest.TestCase):
    """A worktree's cache symlink was once committed; merging it replaced the real cache with a self-loop."""
    def test_no_tracked_cache_or_symlinks(self):
        import subprocess
        root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        try:
            out = subprocess.run(['git', 'ls-files', '-s'], cwd=root, capture_output=True, text=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            self.skipTest('git not available')
        self.assertEqual([l for l in out.splitlines() if l.startswith('120000 ')], [], 'symlinks are tracked')
        self.assertEqual([l for l in out.splitlines() if l.split('\t')[-1].startswith('scraper/cache')], [])
