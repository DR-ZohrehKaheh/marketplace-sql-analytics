"""One-command, reproducible local analytics run; zero third-party dependencies."""
from __future__ import annotations
import argparse
from pathlib import Path
if __package__:
    from .build_db import BASE, build_olist_database, build_synthetic_database
    from .run_queries import run_queries
else:
    from build_db import BASE, build_olist_database, build_synthetic_database
    from run_queries import run_queries

def main():
    p = argparse.ArgumentParser(description='Build database and export all SQL analyses')
    p.add_argument('--mode', choices=['synthetic', 'olist'], default='synthetic')
    p.add_argument('--dataset-dir', type=Path, default=BASE/'data'/'olist')
    p.add_argument('--db', type=Path, default=BASE/'data'/'marketplace.sqlite')
    p.add_argument('--output-dir', type=Path, help='New output directory; defaults to reports/<mode>')
    p.add_argument('--overwrite', action='store_true', help='Explicitly replace an existing database')
    p.add_argument('--quiet', action='store_true', help='Do not print query result samples')
    args = p.parse_args()
    destination = args.output_dir or BASE/'reports'/args.mode
    if destination.exists() or destination.is_symlink():
        p.error('Reports already exist; select a new --output-dir before rebuilding the database')
    if args.mode == 'olist':
        build_olist_database(args.db, args.dataset_dir, overwrite=args.overwrite)
    else:
        build_synthetic_database(args.db, overwrite=args.overwrite)
    names = sorted(x.name for x in (BASE/'sql').glob('*.sql'))
    run_queries(args.db, names, export_csv=True, output_dir=destination, quiet=args.quiet)
    print(f'\nFinished: {len(names)} analyses; mode={args.mode}; reports={destination}')

if __name__ == '__main__':
    main()
