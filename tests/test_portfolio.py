"""Business-level assertions: data grain, window metrics, and missing categories."""
from __future__ import annotations
import sqlite3
from contextlib import closing
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from build_db import build_synthetic_database


def sql(name: str) -> str:
    return (ROOT / 'sql' / name).read_text(encoding='utf-8')


class TestPortfolioMetrics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        cls.db = Path(cls.tempdir.name) / 'portfolio.sqlite'
        build_synthetic_database(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.tempdir.cleanup()

    def test_category_value_reconciles_to_delivered_items(self):
        with closing(sqlite3.connect(self.db)) as con:
            expected = con.execute('''SELECT SUM(oi.price)
                FROM orders o JOIN order_items oi USING (order_id)
                WHERE o.order_status = 'delivered' ''').fetchone()[0]
            actual = sum(row[3] for row in con.execute(sql('01_category_demand.sql')))
            self.assertAlmostEqual(actual, expected, places=6)

    def test_category_share_per_state_is_approximately_100_pct(self):
        with closing(sqlite3.connect(self.db)) as con:
            shares = defaultdict(list)
            for state, category, orders, value, pct, rank in con.execute(
                    sql('06_state_category_share.sql')):
                self.assertGreaterEqual(value, 0)
                self.assertGreater(orders, 0)
                self.assertGreaterEqual(pct, 0)
                self.assertLessEqual(pct, 100)
                shares[state].append(pct)
            self.assertGreater(len(shares), 0)
            for state, percentages in shares.items():
                with self.subTest(state=state):
                    self.assertAlmostEqual(sum(percentages), 100, delta=0.06)

    def test_monthly_sales_reconciles(self):
        with closing(sqlite3.connect(self.db)) as con:
            direct_value = con.execute('''SELECT SUM(oi.price)
                FROM orders o JOIN order_items oi USING(order_id)
                WHERE o.order_status='delivered' AND o.purchase_ts IS NOT NULL''').fetchone()[0]
            monthly = con.execute(sql('07_monthly_sales_trend.sql')).fetchall()
            self.assertGreater(len(monthly), 1)
            self.assertAlmostEqual(sum(row[4] for row in monthly), direct_value, delta=.06)
            self.assertTrue(all(row[1] <= row[3] for row in monthly))

    def test_rfm_one_record_per_observed_customer(self):
        with closing(sqlite3.connect(self.db)) as con:
            rows = con.execute(sql('08_rfm_customer_segments.sql')).fetchall()
            self.assertGreater(len(rows), 0)
            self.assertEqual(len({r[0] for r in rows}), len(rows))
            for r in rows:
                self.assertGreaterEqual(r[1], 0)  # recency
                self.assertGreaterEqual(r[2], 1)  # frequency
                self.assertGreaterEqual(r[3], 0)  # monetary
                self.assertTrue(all(1 <= s <= 4 for s in r[4:7]))

    def test_quality_checks_have_expected_synthetic_results(self):
        with closing(sqlite3.connect(self.db)) as con:
            checks = dict(con.execute(sql('09_data_quality_checks.sql')))
            self.assertEqual(checks['items_nonpositive_price'], 0)
            self.assertEqual(checks['items_missing_product_record'], 0)
            self.assertEqual(checks['items_missing_category'], 0)
            self.assertEqual(checks['orders_missing_purchase_timestamp'], 0)
            self.assertGreater(checks['orders_delivered'], 0)

    def test_multi_item_order_and_missing_product_are_not_dropped(self):
        # Controlled minimal case: intentionally omitted product lookup record.
        with closing(sqlite3.connect(':memory:')) as con:
            con.executescript('''
                CREATE TABLE customers (customer_id TEXT, customer_state TEXT);
                CREATE TABLE orders (order_id TEXT, customer_id TEXT, order_status TEXT);
                CREATE TABLE order_items (order_id TEXT, product_id TEXT, price REAL);
                CREATE TABLE products (product_id TEXT, product_category_name TEXT);
                INSERT INTO customers VALUES ('C1','SP');
                INSERT INTO orders VALUES ('O1','C1','delivered');
                INSERT INTO orders VALUES ('O2','C1','canceled');
                INSERT INTO products VALUES ('P1','books');
                INSERT INTO products VALUES ('P2','  ');
                INSERT INTO order_items VALUES ('O1','P1',10);
                INSERT INTO order_items VALUES ('O1','P1',20);
                INSERT INTO order_items VALUES ('O1','P2',15);
                INSERT INTO order_items VALUES ('O1','P3',30);
                INSERT INTO order_items VALUES ('O2','P1',200);
            ''')
            result = {row[1]: row for row in con.execute(sql('01_category_demand.sql'))}
            self.assertEqual(result['books'][2], 1)      # two rows, only one order
            self.assertEqual(result['books'][3], 30.0)
            self.assertEqual(result['unknown'][2], 1)    # blank or missing category
            self.assertEqual(result['unknown'][3], 45.0)  # 15 + 30, no dropped item
            self.assertEqual(sum(r[3] for r in result.values()), 75.0)  # excludes canceled
            share = con.execute(sql('06_state_category_share.sql')).fetchall()
            self.assertAlmostEqual(sum(r[4] for r in share), 100, delta=.01)


class TestOptionalOlistImporter(unittest.TestCase):
    def test_minimal_olist_csv_import(self):
        import csv
        from build_db import build_olist_database
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            fixtures = {
                'olist_customers_dataset.csv': (
                    ['customer_id', 'customer_unique_id', 'customer_city', 'customer_state'],
                    [('C1', 'U1', 'sample_city', 'SP')]),
                'olist_sellers_dataset.csv': (
                    ['seller_id', 'seller_city', 'seller_state'],
                    [('S1', 'sample_city', 'SP')]),
                'olist_products_dataset.csv': (
                    ['product_id', 'product_category_name'],
                    [('P1', 'books')]),
                'olist_orders_dataset.csv': (
                    ['order_id', 'customer_id', 'order_status', 'order_purchase_timestamp'],
                    [('O1', 'C1', 'delivered', '2018-04-01 12:00:00')]),
                'olist_order_items_dataset.csv': (
                    ['order_id', 'order_item_id', 'product_id', 'seller_id', 'price', 'freight_value'],
                    [('O1', '1', 'P1', 'S1', '20.5', '2.0')]),
            }
            for name, (header, rows) in fixtures.items():
                with (folder / name).open('w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    writer.writerows(rows)
            db = folder / 'olist.sqlite'
            build_olist_database(db, folder)
            with closing(sqlite3.connect(db)) as con:
                rows = con.execute(sql('01_category_demand.sql')).fetchall()
                self.assertEqual(rows, [('SP', 'books', 1, 20.5)])

if __name__ == '__main__':
    unittest.main()
