"""CLI.

    python -m mfr_scraper run --site bray --limit 10          # quick dev run (evenly spaced sample)
    python -m mfr_scraper run --site bray                     # full site
    python -m mfr_scraper run --site bray --url <product-url> # specific pages
    python -m mfr_scraper discover --site bray                # templates + product URL count only

Sites in the test/challenge splits are held out: running on them requires --allow-holdout,
which should only be used for final evaluation, never while tuning the scraper.
"""
import argparse
import json
import sys

from .pipeline import SiteRun, write_outputs
from .settings import HOLDOUT_SPLITS, RUNS_DIR, site_config


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['run', 'discover'])
    ap.add_argument('--site', required=True, help='name for outputs; an evaluation site, or any name with --input-url')
    ap.add_argument('--input-url', help="manufacturer homepage (needed for sites not in harness/config/sites.json)")
    ap.add_argument('--use-config-hosts', action='store_true', help='use configured allowed hosts instead of auto-detection')
    ap.add_argument('--limit', type=int, help='process at most N product pages (evenly spaced)')
    ap.add_argument('--url', action='append', dest='urls', help='process only these product URLs')
    ap.add_argument('--refresh', action='store_true', help='ignore the fetch cache')
    ap.add_argument('--out', default=str(RUNS_DIR))
    ap.add_argument('--allow-holdout', action='store_true', help='permit test/challenge sites (final eval only)')
    args = ap.parse_args(argv)

    split = site_config(args.site, args.input_url).get('split')
    if split in HOLDOUT_SPLITS and not args.allow_holdout:
        print(f"'{args.site}' is in the {split} split (held out). Use --allow-holdout only for final evaluation.")
        return 2

    runner = SiteRun(args.site, limit=args.limit, only_urls=args.urls, refresh=args.refresh, out_dir=args.out,
                     input_url=args.input_url, use_config_hosts=args.use_config_hosts)
    if args.command == 'discover':
        profile, urls = runner.discover()
        print(json.dumps({'product_templates': profile['product_templates'], 'product_urls': len(urls),
                          'platform': profile['platform'], 'blocked': profile['blocked'],
                          'flags': [f'{k}: {v}' for k, v in runner.flags.items()], 'examples': urls[:10]}, indent=2))
        if profile['blocked']:
            print(f"\n{args.site} blocks automated HTTP requests (HTTP 403/429). A browser-based fetch mode is "
                  "needed; this scraper does not try to get around bot protection.")
        return 0 if urls else 1
    run = runner.run()
    path = write_outputs(run, args.out)
    print(f'\nwrote {path}')
    print(json.dumps(run['coverage'], indent=2))
    for f in run['flags']:
        print('  flag:', f)
    return 0


if __name__ == '__main__':
    sys.exit(main())
