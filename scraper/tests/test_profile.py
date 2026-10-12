"""Site profile: card detection, card families, profile-driven grouping (no network)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mfr_scraper import page as P  # noqa: E402
from mfr_scraper.pipeline import PageRec  # noqa: E402
from mfr_scraper.process import grouping as G  # noqa: E402
from mfr_scraper.process import profile as SP  # noqa: E402


def category_page(cards):
    body = ''.join(f'<div class="tile"><span class="fam">{name}</span><a href="/item/{i}">'
                   f'<img src="/i/{sku}.jpg" alt="{sku}"></a><p>Item Number: {sku}</p></div>' for i, (name, sku) in enumerate(cards))
    return P.soup_of(f'<html><body><header><a href="/">Home</a></header><div class="grid">{body}</div></body></html>')


def rec(url, name, crumbs, tables=()):
    return PageRec(url=url, name=name, crumbs=list(crumbs), lang='en', alternates={}, pairs=[], doc_links=[],
                   image_cands=[], iframes=[], price={}, skus=[], sha='', tables=list(tables), text='', retrieved_at='')


PAGE_A = [('Ball Valve', '113-32'), ('Ball Valve', '113-33'), ('Ball Valve', '113-34'), ('Sillcock', '117-12'), ('Sillcock', '117-13')]
PAGE_B = [('Vacuum Breaker', '117-03'), ('Vacuum Breaker', '117-04'), ('Floor Drain', '832-2'), ('Floor Drain', '832-3'), ('Ball Valve', '113-32')]


class TestSiteProfile(unittest.TestCase):
    def setUp(self):
        self.pages = [('https://x.example/cat/1', category_page(PAGE_A)), ('https://x.example/cat/2', category_page(PAGE_B))]

    def test_card_shape_is_learned_from_repeated_names(self):
        spec = SP.learn_card_spec(self.pages)
        self.assertEqual((spec['card_class'], spec['name_class']), ('tile', 'fam'))
        cards = SP.extract_cards(self.pages[0][1], self.pages[0][0], spec)
        self.assertEqual([(c['name'], c['ident']) for c in cards], PAGE_A)
        self.assertEqual(cards[0]['href'], 'https://x.example/item/0')

    def test_distinct_names_only_is_not_a_card_shape(self):   # a grid of family pages, one card each
        grid = [(f'Series {n}', f'S{n}-01') for n in range(10, 16)]
        self.assertIsNone(SP.learn_card_spec([('https://x.example/a', category_page(grid)), ('https://x.example/b', category_page(grid))]))

    def test_same_card_on_two_category_pages_is_one_family(self):
        spec = SP.learn_card_spec(self.pages)
        fams = SP.card_families([c for u, s in self.pages for c in SP.extract_cards(s, u, spec)])
        by_name = {f['name']: f['members'] for f in fams}
        self.assertEqual(len(fams), 4)
        self.assertEqual(by_name['Ball Valve'], ['113-32', '113-33', '113-34'])

    def test_part_number_goes_to_most_specific_category(self):   # a parent category repeats its sub-categories' cards
        parent = [('Sillcock', '117-12'), ('Sillcock', '117-13'), ('Sillcock', '118-02'), ('Sillcock', '118-03'), ('Drain', '832-2')]
        sub_copper = [('Sillcock', '117-12'), ('Sillcock', '117-13'), ('Drain', '832-2')]
        sub_cpvc = [('Sillcock', '118-02'), ('Sillcock', '118-03')]
        pages = [('https://x.example/super/1', category_page(parent)), ('https://x.example/cat/2', category_page(sub_copper)),
                 ('https://x.example/cat/3', category_page(sub_cpvc))]
        spec = {'card_class': 'tile', 'name_class': 'fam'}
        fams = SP.card_families([c for u, s in pages for c in SP.extract_cards(s, u, spec)])
        self.assertEqual(sorted((f['source_pages'][0][-5:], f['members']) for f in fams),
                         [('cat/2', ['117-12', '117-13']), ('cat/2', ['832-2']), ('cat/3', ['118-02', '118-03'])])

    def test_choose_shape(self):
        shapes = {'category_cards': {'coverage': 0.95, 'contradictions': 0.02}, 'family_pages': {'coverage': 0.7}}
        self.assertEqual(SP.choose(shapes, 600)[0], 'category_cards')
        shapes['category_cards']['contradictions'] = 0.3
        self.assertEqual(SP.choose(shapes, 600)[0], 'family_pages')
        self.assertEqual(SP.choose({'category_cards': {'coverage': 0}, 'family_pages': {'coverage': 0.1}}, 0)[0], 'part_number_rules')
        self.assertEqual(SP.choose({'category_cards': {'coverage': 0}, 'family_pages': {'coverage': 0.1},
                                    'model_pages': {'coverage': 0.9}}, 0)[0], 'model_pages')

    def test_grouping_follows_profile_and_rules_cannot_join_profile_families(self):
        crumbs = ['Products', 'Valves']
        items = [['Item No'], ['117-12'], ['117-03']]   # item tables list each other: R4 would merge them
        recs = [rec('https://x.example/Products/113-32', '113-32', crumbs), rec('https://x.example/Products/113-33', '113-33', crumbs),
                rec('https://x.example/Products/117-12', '117-12', crumbs, items), rec('https://x.example/Products/117-03', '117-03', crumbs, items),
                rec('https://x.example/Products/999-01', '999-01', crumbs)]
        profile = {'family_shape': 'category_cards', 'families': [
            {'name': 'Ball Valve', 'source_pages': ['c1'], 'members': ['113-32', '113-33']},
            {'name': 'Sillcock', 'source_pages': ['c1'], 'members': ['117-12']},
            {'name': 'Vacuum Breaker', 'source_pages': ['c2'], 'members': ['117-03']}]}
        fixed, ev = SP.profile_assignments(profile, recs)
        self.assertEqual(fixed, {0: 0, 1: 0, 2: 1, 3: 2})
        groups, evidence, unsure = G.group_pages(recs, fixed=fixed, fixed_ev=ev)
        self.assertEqual(sorted(sorted(r.url.rsplit('/', 1)[1] for r in g) for g in groups),
                         [['113-32', '113-33'], ['117-03'], ['117-12'], ['999-01']])
        merged = next(i for i, g in enumerate(groups) if len(g) == 2)
        self.assertTrue(evidence[merged][0].startswith('P1 site profile'))
        self.assertFalse(any({u['group'], u['other_group']} <= {i for i, g in enumerate(groups) if g[0].url.endswith(('117-12', '117-03'))}
                             for u in unsure))

    def test_no_profile_changes_nothing(self):
        self.assertEqual(SP.profile_assignments({'family_shape': 'family_pages', 'families': []}, [rec('u', 'n', [])]), ({}, {}))
        self.assertEqual(SP.profile_assignments(None, []), ({}, {}))


if __name__ == '__main__':
    unittest.main()
