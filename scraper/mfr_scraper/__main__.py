"""CLI.

    python -m mfr_scraper run --site <site> --limit 10       # quick dev run (evenly spaced sample)
    python -m mfr_scraper run --site <site>                   # full site
    python -m mfr_scraper run --site <site> --url <product-url> # specific pages
    python -m mfr_scraper discover --site <site>              # templates + product URL count only
    python -m mfr_scraper process --site <site> --links <file> # Approach B: link file (L0 csv / L1 jsonl) -> SiteRun
    python -m mfr_scraper resolve --site <site> --decisions <run>/<site>.decisions.jsonl  # Phase 3: answer unsure items

Sites in the test/challenge splits are held out: running on them requires --allow-holdout,
which should only be used for final evaluation, never while tuning the scraper.
"""
import argparse
import json
import sys

from .pipeline import SiteRun, write_outputs
from .settings import HOLDOUT_SPLITS, RUNS_DIR, site_config


def peak_rss_mb():
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024   # Linux reports KiB


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('command', choices=['run', 'discover', 'process', 'resolve', 'profile'])
    ap.add_argument('--site', required=True, help='name for outputs; an evaluation site, or any name with --input-url')
    ap.add_argument('--input-url', help="manufacturer homepage (needed for sites not in harness/config/sites.json)")
    ap.add_argument('--use-config-hosts', action='store_true', help='use configured allowed hosts instead of auto-detection')
    ap.add_argument('--limit', type=int, help='process at most N product pages (evenly spaced)')
    ap.add_argument('--url', action='append', dest='urls', help='process only these product URLs')
    ap.add_argument('--refresh', action='store_true', help='ignore the fetch cache')
    ap.add_argument('--out', default=str(RUNS_DIR))
    ap.add_argument('--links', help='process: link file, L0 (url,url_type CSV) or L1 (JSONL)')
    ap.add_argument('--level', choices=['L0', 'L1'], help='process: link file level (default: by extension)')
    ap.add_argument('--offline', action='store_true', help='process: never request; use only cached responses')
    ap.add_argument('--profile', help='process: group families by this site profile (<site>.profile.json from the profile command)')
    ap.add_argument('--resolutions', help='process: apply verified resolver answers (<site>.resolutions.jsonl)')
    ap.add_argument('--decisions', help='resolve: the run\'s <site>.decisions.jsonl')
    ap.add_argument('--model', default='claude-sonnet-4-5', help='resolve: model id')
    ap.add_argument('--backend', choices=['api', 'claude-code'], default='api',
                    help='resolve: Anthropic API (ANTHROPIC_API_KEY) or a signed-in Claude Code CLI')
    ap.add_argument('--budget-usd', type=float, default=10.0, help='resolve: stop asking new questions past this spend')
    ap.add_argument('--usd-per-mtok', type=float, nargs=2, default=[3.0, 15.0], metavar=('IN', 'OUT'),
                    help='resolve: model price per million input / output tokens')
    ap.add_argument('--allow-holdout', action='store_true', help='permit test/challenge sites (final eval only)')
    args = ap.parse_args(argv)

    split = site_config(args.site, args.input_url).get('split')
    if split in HOLDOUT_SPLITS and not args.allow_holdout:
        print(f"'{args.site}' is in the {split} split (held out). Use --allow-holdout only for final evaluation.")
        return 2

    if args.command == 'resolve':
        if not args.decisions:
            ap.error('resolve needs --decisions <file>')
        from pathlib import Path
        from .process.resolve import anthropic_backend, claude_code_backend, resolve
        out = Path(args.decisions).with_name(f'{args.site}.resolutions.jsonl')
        resolve(args.site, args.decisions, out, (claude_code_backend if args.backend == 'claude-code' else anthropic_backend)(args.model), args.model,
                Path(args.out) / 'resolver-cache' / f'{args.site}.json', args.budget_usd, *args.usd_per_mtok, limit=args.limit)
        print(f'wrote {out}')
        return 0

    if args.command == 'profile':
        if not args.links:
            ap.error('profile needs --links <file>')
        from .process.profile import build_profile, write_profile
        from .process.run import ProcessRun
        runner = ProcessRun(args.site, args.links, level=args.level, out_dir=args.out, input_url=args.input_url,
                            refresh=args.refresh, offline=args.offline)
        prof = build_profile(runner)
        path = write_profile(prof, args.out)
        print(json.dumps({k: prof[k] for k in ('family_shape', 'reason', 'summary', 'sample', 'shapes')}, indent=1))
        print(f'{len(prof["families"])} card families; wrote {path}')
        return 0

    if args.command == 'process':
        if not args.links:
            ap.error('process needs --links <file>')
        from .process.run import ProcessRun, write_process_outputs
        runner = ProcessRun(args.site, args.links, level=args.level, out_dir=args.out, input_url=args.input_url,
                            refresh=args.refresh, offline=args.offline, resolutions=args.resolutions,
                            profile=args.profile)
        run = runner.run()
        path = write_process_outputs(run, runner.decisions, args.out)
        print(f'\nwrote {path} and {args.site}.decisions.jsonl')
        print(json.dumps(run['coverage'], indent=2))
        print(json.dumps({k: run['run_stats'][k] for k in ('requests', 'cache_hits', 'wall_seconds', 'requests_by_purpose',
                                                            'blocked_requests', 'unsure_by_kind')}, indent=2))
        print('parsed-pdf cache:', json.dumps(runner.pdf_cache.stats))
        print(f'peak memory: {peak_rss_mb():.0f} MB')
        return 0

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
    print('parsed-pdf cache:', json.dumps(runner.pdf_cache.stats))
    print(f'peak memory: {peak_rss_mb():.0f} MB')
    return 0


if __name__ == '__main__':
    sys.exit(main())
