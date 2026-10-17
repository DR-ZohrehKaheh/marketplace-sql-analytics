"""Independent business expectations and input/output failure regressions."""
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from build_db import _read_csv, _write, build_synthetic_database
from run_queries import run_queries, spreadsheet_safe
from validate_results import validate


class TestEdgeCases(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.folder=Path(self.tmp.name)
        self.db=self.folder/'case.sqlite'
        self.customers=[('C1','U1',None,'SP'),('C2','U1',None,'SP'),('C3','U2',None,'SP')]
        self.sellers=[('S1',None,'SP'),('S2',None,'SP')]
        self.products=[('P1','books'),('P2','  ')]
        self.orders=[('O1','C1','delivered','2018-06-30 23:59:59'),
                     ('O2','C2','delivered','2018-07-01 00:00:00'),
                     ('O3','C3','delivered','2018-07-31 00:00:00'),
                     ('O4','C3','canceled','2018-06-20 12:00:00')]
        self.items=[('O1',1,'P1','S1',10,1),('O1',2,'P2','S2',20,2),
                    ('O2',1,'P1','S1',30,1),('O3',1,'P1','S2',0,0),
                    ('O4',1,'P1','S1',100,1)]

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, **kwargs):
        _write(self.db,self.customers,self.sellers,self.products,self.orders,self.items,**kwargs)

    def query(self, number):
        path=next((ROOT/'sql').glob(f'{number:02d}_*.sql'))
        with closing(sqlite3.connect(self.db)) as conn:
            return conn.execute(path.read_text()).fetchall()

    def test_all_nine_queries_match_independent_python_on_synthetic_data(self):
        build_synthetic_database(self.db)
        self.assertEqual(len(validate(self.db)),9)

    def test_all_nine_queries_match_independent_python_on_controlled_edges(self):
        self.build()
        self.assertEqual(len(validate(self.db)),9)

    def test_distinct_customer_identity_and_multi_category_order_grains(self):
        self.build()
        self.assertEqual(self.query(4),[(2,1,50.0)])
        self.assertEqual({r[1]:r[2:] for r in self.query(1)}, {'books':(3,40.0),'unknown':(1,20.0)})
        self.assertEqual(self.query(7),[('2018-06',1,1,2,30.0,30.0),('2018-07',2,2,2,30.0,15.0)])

    def test_exact_cutoff_and_half_open_future_window(self):
        self.build()
        self.assertEqual(self.query(5),[('U1',1,30.0,1,1)])
        # An event exactly at the upper boundary is outside the 30-day label window.
        self.orders[1]=('O2','C2','delivered','2018-07-31 00:00:00')
        self.build(overwrite=True)
        self.assertEqual(self.query(5),[('U1',1,30.0,1,0)])

    def test_empty_database_has_zero_counts_and_undefined_percentage(self):
        _write(self.db,[],[],[],[],[])
        self.assertEqual(self.query(4),[(0,0,None)])
        self.assertEqual(len(validate(self.db)),9)

    def test_zero_monetary_denominators_return_null_shares(self):
        self.items=[(o,i,p,s,0,0) for o,i,p,s,_,_ in self.items]
        self.build()
        self.assertTrue(all(r[-1] is None for r in self.query(3)))
        self.assertTrue(all(r[4] is None for r in self.query(6)))
        self.assertEqual(len(validate(self.db)),9)

    def test_missing_timestamp_is_retained_profiled_and_excluded_from_temporal_metrics(self):
        self.orders[0]=('O1','C1','delivered',None)
        self.build()
        self.assertEqual(dict(self.query(9))['orders_missing_purchase_timestamp'],1)
        self.assertEqual(sum(r[4] for r in self.query(7)),30.0)
        self.assertEqual(sum(r[3] for r in self.query(1)),60.0)
        self.assertEqual(len(validate(self.db)),9)

    def test_itemless_delivered_order_is_explicitly_profiled(self):
        self.orders.append(('O5','C3','delivered','2018-06-20 00:00:00'))
        self.build()
        self.assertEqual(dict(self.query(9))['delivered_orders_without_items'],1)
        self.assertEqual(self.query(4),[(2,2,100.0)])
        self.assertEqual(len(validate(self.db)),9)

    def test_rfm_small_cohorts_use_available_tiles(self):
        self.build()
        rows=sorted(self.query(8))
        self.assertEqual(rows[0][:4],('U1',62,2,60.0))
        self.assertEqual(rows[1][:4],('U2',32,1,0.0))
        self.assertEqual({r[4] for r in rows},{1,2})
        self.assertEqual(rows,sorted(self.query(8)))

    def test_rfm_equal_values_use_customer_id_tie_breaker(self):
        self.orders=[('O1','C1','delivered','2018-06-30 12:00:00'),
                     ('O2','C3','delivered','2018-06-30 12:00:00')]
        self.items=[('O1',1,'P1','S1',10,0),('O2',1,'P1','S1',10,0)]
        self.build()
        rows=sorted(self.query(8))
        self.assertEqual(rows[0][1:4],rows[1][1:4])
        self.assertEqual(rows[0][4:7],(1,1,1))
        self.assertEqual(rows[1][4:7],(2,2,2))
        self.assertEqual(len(validate(self.db)),9)

    def test_existing_database_is_preserved_without_explicit_overwrite(self):
        self.build()
        before=self.db.read_bytes()
        with self.assertRaises(FileExistsError):
            self.build()
        self.assertEqual(before,self.db.read_bytes())

    def test_failed_replacement_preserves_previous_database(self):
        self.build()
        before=self.db.read_bytes()
        self.orders.append(self.orders[0])
        with self.assertRaises(sqlite3.IntegrityError):
            self.build(overwrite=True)
        self.assertEqual(before,self.db.read_bytes())
        self.assertFalse(list(self.folder.glob('.building-*')))

    def test_duplicate_items_and_orphan_foreign_keys_are_rejected(self):
        original=list(self.items)
        for bad in [original+[original[0]], [('MISSING',1,'P1','S1',2,1)],
                    [('O1',1,'MISSING','S1',2,1)], [('O1',1,'P1','MISSING',2,1)]]:
            with self.subTest(records=bad):
                self.items=bad
                with self.assertRaises(sqlite3.IntegrityError):
                    self.build()
                self.assertFalse(self.db.exists())

    def test_blank_identifiers_are_rejected(self):
        for identifier in ['', ' ', None]:
            with self.subTest(identifier=identifier):
                self.customers[0]=('C1',identifier,None,'SP')
                with self.assertRaises(ValueError): self.build()

    def test_invalid_calendar_dates_and_noncanonical_timestamps_are_rejected(self):
        for timestamp in ['invalid','2018-02-30 00:00:00','2018-06-30','2018-6-3 01:02:03']:
            with self.subTest(timestamp=timestamp):
                self.orders[0]=('O1','C1','delivered',timestamp)
                with self.assertRaises(ValueError): self.build()

    def test_invalid_monetary_values_are_rejected(self):
        for value in [float('nan'),float('inf'),float('-inf'),-1,'',None,'0.001',1e13]:
            for column in [4,5]:
                with self.subTest(value=value,column=column):
                    item=['O1',1,'P1','S1',10,1];item[column]=value;self.items=[item]
                    with self.assertRaises(ValueError): self.build()

    def test_invalid_item_numbers_are_rejected(self):
        for value in [0,-1,1.5,'1.0','',None]:
            with self.subTest(value=value):
                self.items=[('O1',value,'P1','S1',10,1)]
                with self.assertRaises(ValueError): self.build()

    def test_malformed_csv_missing_and_duplicate_headers_are_rejected(self):
        path=self.folder/'bad.csv'
        for content in ['a\n1\n','a,b,b\n1,2,3\n','a,b\n1\n','a,b\n1,2,3\n']:
            with self.subTest(content=content):
                path.write_text(content)
                with self.assertRaises(ValueError): _read_csv(path,['a','b'])

    def test_runner_does_not_create_missing_database(self):
        with self.assertRaises(FileNotFoundError): run_queries(self.db,['01_category_demand.sql'])
        self.assertFalse(self.db.exists())

    def test_runner_rejects_paths_and_duplicate_query_names(self):
        self.build()
        for names in [['../sql/01_category_demand.sql'],['01_category_demand.sql']*2,[]]:
            with self.assertRaises(ValueError): run_queries(self.db,names)

    def test_reports_are_complete_labelled_and_not_silently_overwritten(self):
        self.build()
        dest=self.folder/'reports'
        run_queries(self.db,['01_category_demand.sql'],True,dest,quiet=True)
        metadata=json.loads((dest/'run_metadata.json').read_text())
        self.assertEqual(metadata['provenance']['mode'],'custom')
        self.assertIn('01_category_demand.sql',metadata['sql_sha256'])
        with self.assertRaises(FileExistsError): run_queries(self.db,['01_category_demand.sql'],True,dest,quiet=True)

    def test_csv_formula_protection_preserves_numbers(self):
        for text in ['=1+1',' +cmd','-command','@SUM(A1:A2)']:
            self.assertEqual(spreadsheet_safe(text),"'"+text)
        self.assertEqual(spreadsheet_safe(-5),-5)

    def test_cli_runs_outside_repository_and_module_import_works(self):
        output=self.folder/'cli-output'
        result=subprocess.run([sys.executable,str(ROOT/'src/pipeline.py'),'--db',str(self.db),
                               '--output-dir',str(output),'--quiet'],cwd=self.folder,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(len(list(output.glob('*.csv'))),9)
        result=subprocess.run([sys.executable,'-m','src.pipeline','--help'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_synthetic_data_reproducibility(self):
        build_synthetic_database(self.db)
        second=self.folder/'second.sqlite';build_synthetic_database(second)
        with closing(sqlite3.connect(self.db)) as a, closing(sqlite3.connect(second)) as b:
            for table in ['customers','sellers','products','orders','order_items']:
                self.assertEqual(a.execute('SELECT * FROM '+table).fetchall(),b.execute('SELECT * FROM '+table).fetchall())


if __name__=='__main__':
    unittest.main()
