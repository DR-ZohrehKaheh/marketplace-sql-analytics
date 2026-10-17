"""Run included SQL queries, show sample rows and optionally export CSV files."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import platform
import shutil
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]

def spreadsheet_safe(value):
    """Prevent text fields being interpreted as formulas when CSVs are opened."""
    if isinstance(value, str) and (value.startswith(('\t', '\r', '\n')) or value.lstrip().startswith(('=', '+', '-', '@'))):
        return "'" + value
    return value


def run_queries(db: Path, names: list[str], export_csv: bool = False,
                output_dir: Path | None = None, *, quiet: bool = False) -> dict[str, list[tuple]]:
    db = Path(db).resolve()
    if not db.is_file():
        raise FileNotFoundError(f'Database not found: {db}')
    if sqlite3.sqlite_version_info < (3,25,0):
        raise RuntimeError('SQLite 3.25 or newer is required for window functions')
    available = {p.name: p for p in (BASE/'sql').glob('*.sql') if not p.is_symlink()}
    if not names or len(names) != len(set(names)) or any(n not in available for n in names):
        raise ValueError('Select distinct, included SQL filenames')
    destination = Path(output_dir or BASE/'reports'/db.stem).absolute()
    if export_csv and (destination.exists() or destination.is_symlink()):
        raise FileExistsError(f'Choose a new report directory: {destination}')
    result, columns = {}, {}
    with closing(sqlite3.connect(db.as_uri()+'?mode=ro', uri=True)) as conn:
        conn.execute('PRAGMA query_only=ON')
        conn.execute('BEGIN')  # One consistent read snapshot across all queries.
        for name in names:
            cur=conn.execute(available[name].read_text(encoding='utf-8'))
            fields=[description[0] for description in cur.description]
            records=cur.fetchall()
            result[name]=records
            columns[name]=fields
            if not quiet:
                print(f'\n{name}: {len(records)} result rows')
                print(' | '.join(fields))
                for row in records[:5]:
                    print(' | '.join(map(str,row)))
        has_provenance = conn.execute("SELECT 1 FROM sqlite_master WHERE name='provenance'").fetchone()
        provenance = ({k: json.loads(v) for k,v in conn.execute('SELECT key,value FROM provenance')}
                      if has_provenance else {'mode': 'unverified_external'})
    if export_csv:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix='.reports-', dir=destination.parent))
        try:
            for name, records in result.items():
                with (temporary/f'{Path(name).stem}.csv').open('w', newline='', encoding='utf-8') as f:
                    w=csv.writer(f)
                    w.writerow(columns[name])
                    w.writerows(tuple(spreadsheet_safe(v) for v in row) for row in records)
            metadata = {'provenance': provenance, 'python': platform.python_version(),
                        'sqlite': sqlite3.sqlite_version, 'rows': {n:len(v) for n,v in result.items()},
                        'sql_sha256': {n:hashlib.sha256(available[n].read_bytes()).hexdigest() for n in names},
                        'historical_feature_cutoff': '2018-07-01',
                        'observed_label_window': '[2018-07-01, 2018-07-31)',
                        'rfm_cutoff': '2018-09-01',
                        'csv_text_policy': 'Formula-like strings prefixed with apostrophe; SQL values unchanged.'}
            (temporary/'run_metadata.json').write_text(json.dumps(metadata, indent=2)+'\n', encoding='utf-8')
            if destination.exists() or destination.is_symlink():
                raise FileExistsError(f'Report directory already exists: {destination}')
            os.rename(temporary, destination)
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
        if not quiet:
            print(f'Exported complete report set: {destination}')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--db',type=Path, default=BASE/'data'/'marketplace.sqlite')
    p.add_argument('--all',action='store_true',help='Run every bundled query')
    p.add_argument('--query',help='Run one named .sql file, e.g. 01_category_demand.sql')
    p.add_argument('--export-csv',action='store_true')
    p.add_argument('--output-dir',type=Path,help='New directory for reports and provenance')
    args=p.parse_args()
    if not args.db.exists():
        p.error('Database not found: first run python src/build_db.py --mode synthetic')
    available=sorted(p.name for p in (BASE/'sql').glob('*.sql'))
    if args.query:
        if args.query not in available:
            p.error('Choose a bundled query: '+', '.join(available))
        selection=[args.query]
    elif args.all:
        selection=available
    else:
        p.error('Select --all or --query NAME.sql')
    run_queries(args.db, selection, args.export_csv, args.output_dir)
