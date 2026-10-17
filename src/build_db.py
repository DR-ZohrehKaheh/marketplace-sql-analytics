"""Load 5 Olist CSVs or create clearly synthetic Olist-shaped practice data."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import random
import re
import sqlite3
import tempfile
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE customers (customer_id TEXT PRIMARY KEY NOT NULL CHECK(length(trim(customer_id))>0),
    customer_unique_id TEXT NOT NULL CHECK(length(trim(customer_unique_id))>0),
    customer_city TEXT, customer_state TEXT);
CREATE TABLE sellers (seller_id TEXT PRIMARY KEY NOT NULL, seller_city TEXT, seller_state TEXT);
CREATE TABLE products (product_id TEXT PRIMARY KEY NOT NULL, product_category_name TEXT);
CREATE TABLE orders (order_id TEXT PRIMARY KEY NOT NULL, customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    order_status TEXT NOT NULL, purchase_ts TEXT);
CREATE TABLE order_items (order_id TEXT NOT NULL REFERENCES orders(order_id),
    order_item_id INTEGER NOT NULL CHECK(typeof(order_item_id)='integer' AND order_item_id>0),
    product_id TEXT NOT NULL REFERENCES products(product_id), seller_id TEXT NOT NULL REFERENCES sellers(seller_id),
    price REAL NOT NULL CHECK(price>=0 AND price<=1000000000000),
    freight_value REAL NOT NULL CHECK(freight_value>=0 AND freight_value<=1000000000000),
    PRIMARY KEY(order_id, order_item_id));
CREATE INDEX idx_orders_purchase ON orders(purchase_ts);
CREATE INDEX idx_order_customer ON orders(customer_id);
CREATE INDEX idx_items_seller ON order_items(seller_id);
CREATE INDEX idx_customer_unique ON customers(customer_unique_id);
CREATE TABLE provenance (key TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL);
"""

def build_synthetic_database(db_path: Path, *, overwrite: bool = False) -> None:
    """Create a reproducible fictional dataset; never label this as real evidence."""
    rng = random.Random(47)
    states = ['SP', 'RJ', 'MG', 'RS', 'PR']
    categories = ['electronics', 'home', 'books', 'fashion', 'sports', 'food']
    customers = [(f'C{i:04d}', f'U{(i % 50):04d}', 'fictional_city', states[i % len(states)])
                 for i in range(90)]
    sellers = [(f'S{i:03d}', f'fictional_seller_city_{i%3}', states[i % len(states)])
               for i in range(12)]
    products = [(f'P{i:04d}', categories[i % len(categories)]) for i in range(30)]
    orders = []
    items = []
    for i in range(240):
        order_id = f'O{i:05d}'
        customer = rng.choice(customers)
        purchase_day = date(2018, 4, 1) + timedelta(days=rng.randrange(135))
        status = 'delivered' if rng.random() < 0.9 else 'canceled'
        orders.append((order_id, customer[0], status, f'{purchase_day.isoformat()} 12:00:00'))
        for item_id in range(1, rng.randint(1, 3) + 1):
            product = rng.choice(products)
            seller = rng.choice(sellers)
            items.append((order_id, item_id, product[0], seller[0],
                          round(rng.uniform(9, 210), 2), round(rng.uniform(0, 25), 2)))
    _write(db_path, customers, sellers, products, orders, items,
           overwrite=overwrite, provenance={'mode': 'synthetic', 'seed': 47})

def _read_csv(path: Path, cols: list[str]) -> list[tuple]:
    with path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        missing = set(cols) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'{path.name}: missing columns: {sorted(missing)}')
        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(f'{path.name}: duplicate CSV headers')
        result = []
        for line, row in enumerate(reader, start=2):
            if None in row or any(row[k] is None for k in cols):
                raise ValueError(f'{path.name}: malformed CSV row {line}')
            result.append(tuple(row[k] for k in cols))
        return result

def build_olist_database(db_path: Path, data_dir: Path, *, overwrite: bool = False) -> None:
    required = {
        'customers': ('olist_customers_dataset.csv', ['customer_id','customer_unique_id','customer_city','customer_state']),
        'sellers': ('olist_sellers_dataset.csv', ['seller_id','seller_city','seller_state']),
        'products': ('olist_products_dataset.csv', ['product_id','product_category_name']),
        'orders': ('olist_orders_dataset.csv', ['order_id','customer_id','order_status','order_purchase_timestamp']),
        'items': ('olist_order_items_dataset.csv', ['order_id','order_item_id','product_id','seller_id','price','freight_value']),
    }
    missing = [fname for fname, _ in required.values() if not (data_dir/fname).exists()]
    if missing:
        raise FileNotFoundError('Download and extract Olist CSVs into '+str(data_dir)+': '+', '.join(missing))
    data = {table: _read_csv(data_dir/fname, cols) for table, (fname, cols) in required.items()}
    hashes = {fname: hashlib.sha256((data_dir/fname).read_bytes()).hexdigest()
              for fname, _ in required.values()}
    _write(db_path, data['customers'], data['sellers'], data['products'], data['orders'], data['items'],
           overwrite=overwrite, provenance={'mode': 'olist', 'input_sha256': hashes,
           'source': 'https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce'})

def _text(value, *, required=False):
    text = str(value).strip() if value is not None else ''
    if required and not text:
        raise ValueError('required identifier/status is blank')
    return text or None


def _money(value):
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or not 0 <= amount <= Decimal('1000000000000'):
            raise ValueError('monetary value must be finite and between 0 and 1e12 BRL')
        if amount != amount.quantize(Decimal('.01')):
            raise ValueError('monetary value has more than two decimal places')
        return float(amount)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError('invalid monetary value') from exc


def _timestamp(value):
    text = _text(value)
    if text is None:
        return None  # Retained for non-temporal aggregates and reported by QA.
    try:
        parsed = datetime.strptime(text, '%Y-%m-%d %H:%M:%S')
        if parsed.strftime('%Y-%m-%d %H:%M:%S') != text:
            raise ValueError('noncanonical timestamp')
    except ValueError as exc:
        raise ValueError('purchase timestamp must be a valid YYYY-MM-DD HH:MM:SS') from exc
    return text


def _normalise(table, rows):
    cleaned = []
    for number, row in enumerate(rows, start=1):
        try:
            if table == 'customers':
                a,b,c,d = row
                record = (_text(a, required=True), _text(b, required=True), _text(c), _text(d) or 'unknown')
            elif table == 'sellers':
                a,b,c = row
                record = (_text(a, required=True), _text(b), _text(c) or 'unknown')
            elif table == 'products':
                a,b = row
                record = (_text(a, required=True), _text(b))
            elif table == 'orders':
                a,b,c,d = row
                status = _text(c, required=True)
                if status not in {'created','approved','invoiced','processing','shipped','delivered','canceled','unavailable'}:
                    raise ValueError('unrecognised Olist order status')
                record = (_text(a, required=True), _text(b, required=True), status, _timestamp(d))
            else:
                a,b,c,d,e,f = row
                if not re.fullmatch(r'[1-9][0-9]*', str(b)):
                    raise ValueError('order_item_id must be a positive integer')
                record = (_text(a, required=True), int(b), _text(c, required=True),
                          _text(d, required=True), _money(e), _money(f))
            cleaned.append(record)
        except (ValueError, TypeError) as exc:
            raise ValueError(f'{table} row {number}: {exc}') from exc
    return cleaned


def _write(db_path: Path, customers: list, sellers: list, products: list, orders: list, items: list,
           *, overwrite: bool = False, provenance: dict | None = None) -> None:
    """Validate and build beside the destination; failed builds preserve existing data."""
    db_path = Path(db_path).absolute()
    if db_path.is_symlink() or (db_path.exists() and not overwrite):
        raise FileExistsError(f'Refusing to replace {db_path}; choose a new path or use --overwrite')
    tables = [('customers', customers), ('sellers', sellers), ('products', products),
              ('orders', orders), ('order_items', items)]
    tables = [(name, _normalise(name, rows)) for name, rows in tables]
    db_path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.building-', suffix='.sqlite', dir=db_path.parent)
    os.close(fd)
    try:
        with closing(sqlite3.connect(temporary)) as conn:
            conn.executescript(SCHEMA)
            with conn:
                for table, rows in tables:
                    if rows:
                        placeholders = ','.join('?' for _ in rows[0])
                        conn.executemany(f'INSERT INTO {table} VALUES ({placeholders})', rows)
                if conn.execute('PRAGMA foreign_key_check').fetchall():
                    raise ValueError('Foreign key violations')
                metadata = dict(provenance or {'mode': 'custom'})
                metadata.update({'created_utc': datetime.now(timezone.utc).isoformat(),
                                 'schema_version': 1})
                conn.executemany('INSERT INTO provenance VALUES (?, ?)',
                                 [(k, json.dumps(v)) for k,v in metadata.items()])
        if overwrite:
            os.replace(temporary, db_path)
        else:
            os.link(temporary, db_path)  # Atomic no-clobber publication of a complete database.
        print(f'Created {db_path}: {len(orders)} orders, {len(items)} item rows')
    finally:
        Path(temporary).unlink(missing_ok=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description='Build a SQL analytics training database')
    p.add_argument('--mode', choices=['synthetic','olist'], default='synthetic')
    p.add_argument('--dataset-dir', type=Path, default=BASE/'data'/'olist')
    p.add_argument('--db', type=Path, default=BASE/'data'/'marketplace.sqlite')
    p.add_argument('--overwrite', action='store_true', help='Explicitly replace an existing database after successful validation')
    args=p.parse_args()
    if args.mode=='olist':
        build_olist_database(args.db, args.dataset_dir, overwrite=args.overwrite)
    else:
        build_synthetic_database(args.db, overwrite=args.overwrite)
