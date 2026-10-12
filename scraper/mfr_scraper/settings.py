"""Paths, limits, and access to the shared harness code (URL normalization, site config)."""
import logging
import sys
from pathlib import Path

SCRAPER_ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SCRAPER_ROOT.parent
HARNESS_ROOT = PROJECT_ROOT / 'harness'
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from mfr_harness import normalize as N  # noqa: E402  (shared with the evaluation harness)
from mfr_harness.config import load_sites  # noqa: E402

logging.getLogger('pypdf').setLevel(logging.ERROR)   # font/encoding warnings are noise here

AGENT_NAME = 'mfr-scraper'
AGENT_VERSION = '0.1.0'
# Identifies the crawler honestly; carries no personal data.
USER_AGENT = f'{AGENT_NAME}/{AGENT_VERSION} (product-index research crawler)'

CACHE_DIR = SCRAPER_ROOT / 'cache'
RUNS_DIR = HARNESS_ROOT / 'runs'

HOLDOUT_SPLITS = {'test', 'challenge'}

MIN_DELAY_PER_HOST = 1.0          # seconds between requests to one host
REQUEST_TIMEOUT = 30
DOWNLOAD_DEADLINE = 300            # seconds for a whole response body; a trickling server can't stall a run
MAX_BYTES = {'html': 10_000_000, 'pdf': 40_000_000, 'zip': 60_000_000, 'image': 15_000_000, 'other': 10_000_000}

TEMPLATE_SAMPLE_PAGES = 4         # pages fetched per URL template to decide if it is a product template
MIN_TEMPLATE_URLS = 2
PRODUCT_SCORE_THRESHOLD = 4.0
MAX_PDFS_PER_FAMILY = 30
MAX_IMAGES_PER_FAMILY = 12
PHASH_SAME_IMAGE = 2           # renditions of one image; sibling-SKU photos are usually 4+ apart
PDF_TEXT_PAGES = 8
PDF_PARSE_MEM_BYTES = 64_000_000   # in-memory cap for parsed PDF results (the rest stays on disk)
CHROME_SHARE = 0.20               # asset on more than this share of product pages = site chrome
CHROME_MIN_PAGES = 5


def site_config(site, input_url=None):
    """Config for an evaluation site, or a minimal config for any other manufacturer (only a URL needed)."""
    cfg = load_sites()
    s = cfg['sites'].get(site)
    if s is None:
        if not input_url:
            raise SystemExit(f"unknown site '{site}': pass --input-url (or add it to harness/config/sites.json)")
        s = {'split': None, 'input_url': input_url, 'allowed_hosts': None}
    elif input_url:
        s = {**s, 'input_url': input_url}
    return {**s, 'cad_viewer_hosts': cfg['global_cad_viewer_hosts'] + s.get('cad_viewer_hosts', [])}
