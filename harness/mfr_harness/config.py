import json
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = HARNESS_ROOT / 'schema' / 'siterun.schema.json'
SITES_PATH = HARNESS_ROOT / 'config' / 'sites.json'

PRIMARY_DOC_TYPES = {'spec_sheet', 'submittal', 'price_list'}


def load_sites():
    with open(SITES_PATH) as f:
        return json.load(f)


def site_hosts(site):
    """(allowed_hosts, cad_viewer_hosts) for a site name."""
    cfg = load_sites()
    s = cfg['sites'].get(site)
    if s is None:
        raise KeyError(f"unknown site '{site}'; add it to {SITES_PATH}")
    return s['allowed_hosts'], cfg['global_cad_viewer_hosts'] + s.get('cad_viewer_hosts', [])


def load_json(path):
    with open(path) as f:
        return json.load(f)
