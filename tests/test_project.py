"""Unit tests for schema, aggregates and bundled SQL."""
import sqlite3
from contextlib import closing
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from build_db import build_synthetic_database

class TestMarketplaceSQL(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = Path(cls.tmp.name) / 'test.sqlite'
        build_synthetic_database(cls.db)
    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()
    def test_tables_have_rows(self):
        with closing(sqlite3.connect(self.db)) as conn:
            for table in ('customers','sellers','products','orders','order_items'):
                self.assertGreater(conn.execute('SELECT COUNT(*) FROM '+table).fetchone()[0],0)
    def test_no_foreign_key_violations(self):
        with closing(sqlite3.connect(self.db)) as conn:
            self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(),[])
    def test_queries_run(self):
        with closing(sqlite3.connect(self.db)) as conn:
            for sql_file in sorted((ROOT/'sql').glob('*.sql')):
                with self.subTest(query=sql_file.name):
                    result=conn.execute(sql_file.read_text(encoding='utf-8')).fetchall()
                    self.assertGreater(len(result),0)
    def test_repeat_share_is_valid(self):
        with closing(sqlite3.connect(self.db)) as conn:
            result=conn.execute((ROOT/'sql'/'04_repeat_customers.sql').read_text()).fetchone()
            self.assertGreater(result[0],0)
            self.assertLessEqual(result[1],result[0])
            self.assertGreaterEqual(result[2],0)
            self.assertLessEqual(result[2],100)
    def test_customer_snapshot_nonnegative_and_binary_label(self):
        with closing(sqlite3.connect(self.db)) as conn:
            rows=conn.execute((ROOT/'sql'/'05_customer_features.sql').read_text()).fetchall()
            self.assertGreater(len(rows),0)
            for row in rows:
                self.assertGreater(row[1],0)
                self.assertGreaterEqual(row[2],0)
                self.assertGreaterEqual(row[3],0)
                self.assertIn(row[4], (0,1))

if __name__=='__main__':
    unittest.main()
