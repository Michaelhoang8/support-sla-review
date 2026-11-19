"""Independent reconciliation of published analysis artifacts."""
from pathlib import Path
import hashlib,json,sqlite3,unittest
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

class PortfolioChecks(unittest.TestCase):
    def test_media_manifest(self):
        manifest=json.loads((ROOT/'docs/recordings/captures.json').read_text())
        hashes=[]
        for frame in manifest['frames']:
            digest=hashlib.sha256((ROOT/frame['path']).read_bytes()).hexdigest()
            self.assertEqual(digest,frame['sha256'])
            hashes.append(digest)
        self.assertEqual(len(hashes),len(set(hashes)), 'Each step must show a distinct capture')
        self.assertGreater((ROOT/'docs/recordings/walkthrough.mp4').stat().st_size,10000)

    def test_data_manifest(self):
        for name,digest in json.loads((ROOT/'analysis/data_sha256.json').read_text()).items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest,name)

    def test_sql_outputs_match_warehouse(self):
        with sqlite3.connect(ROOT/'analysis/warehouse.sqlite3') as connection:
            for sql in (ROOT/'sql').glob('*.sql'):
                expected=pd.read_sql_query(sql.read_text(),connection)
                actual=pd.read_csv(ROOT/f'analysis/{sql.stem}.csv')
                # CSV may infer a year string as integer; compare numeric values tolerantly.
                for column in expected:
                    if expected[column].dtype=='object':
                        self.assertEqual(expected[column].astype(str).tolist(),actual[column].astype(str).tolist())
                    else: pd.testing.assert_series_equal(expected[column],actual[column],check_dtype=False,rtol=1e-10,atol=1e-10)

    def test_notebook_executed_without_errors(self):
        nb=json.loads((ROOT/'analysis/analysis.ipynb').read_text(encoding='utf-8'))
        for cell in nb['cells']:
            if cell['cell_type']=='code':
                self.assertIsNotNone(cell['execution_count'])
                self.assertFalse(any(o['output_type']=='error' for o in cell.get('outputs',[])))

    def test_business_rules(self):
        if 'retail' in ROOT.name:
            f=pd.read_csv(ROOT/'data/clean/orders.csv')
            self.assertEqual(len(f),12000);self.assertTrue(f.order_id.is_unique)
            self.assertTrue(((f.returned_units>=0)&(f.returned_units<=f.quantity)).all())
            self.assertEqual(int(f.gross_sales_cents.sum()-f.discount_cents.sum()-f.refund_cents.sum()),int(f.net_revenue_cents.sum()))
            self.assertEqual(int(f.net_revenue_cents.sum()-f.net_cogs_cents.sum()-f.shipping_cents.sum()-f.return_handling_cents.sum()),int(f.contribution_cents.sum()))
            self.assertEqual(int(f.net_revenue_cents.sum()),202053500)
            self.assertEqual(int(f.contribution_cents.sum()),56502195)
            self.assertTrue(f.customer_id.isin(pd.read_csv(ROOT/'data/clean/customers.csv').customer_id).all())
            self.assertTrue(f.product_id.isin(pd.read_csv(ROOT/'data/clean/products.csv').product_id).all())
        else:
            f=pd.read_csv(ROOT/'data/clean/tickets.csv')
            self.assertEqual(len(f),6000);self.assertTrue(f.ticket_id.is_unique)
            # Independent timestamp-based oracle for the entire SLA denominator.
            now=pd.Timestamp('2026-01-01');opened=pd.to_datetime(f.opened_at)
            for kind,field in [('response','first_response_at'),('resolution','resolved_at')]:
                observed=pd.to_datetime(f[field]);deadline=opened+pd.to_timedelta(f[kind+'_sla_hours'],unit='h')
                eligible=observed.notna()|(deadline<=now)
                breach=(observed>deadline)|(observed.isna()&(deadline<=now))
                self.assertEqual(eligible.astype(int).tolist(),f[kind+'_eligible'].tolist())
                self.assertEqual(breach.astype(int).tolist(),f[kind+'_breach'].tolist())
                self.assertTrue((f[kind+'_breach']<=f[kind+'_eligible']).all())
            self.assertEqual(int(f.overdue_open.sum()),199)
            self.assertEqual(int(f.response_breach.sum()),1221)
            self.assertEqual(int(f.response_eligible.sum()),5995)
            self.assertEqual(int(f.csat_responded.sum()),int(f.csat.notna().sum()))
            self.assertTrue(f.team_id.isin(pd.read_csv(ROOT/'data/clean/teams.csv').team_id).all())

    def test_model_data_and_relationships(self):
        model=next((ROOT/'powerbi').glob('*.SemanticModel/model.bim'))
        model=json.loads(model.read_text(encoding='utf-8'))['model']
        tables={t['name']:t for t in model['tables']}
        for rel in model['relationships']:
            left=pd.read_csv(ROOT/f'data/clean/{rel["fromTable"]}.csv')
            right=pd.read_csv(ROOT/f'data/clean/{rel["toTable"]}.csv')
            self.assertTrue(right[rel['toColumn']].is_unique)
            self.assertTrue(left[rel['fromColumn']].isin(right[rel['toColumn']]).all())
            self.assertEqual(rel['crossFilteringBehavior'],'oneDirection')
        for table in tables.values():
            self.assertEqual(set(c['name'] for c in table['columns']),set(pd.read_csv(ROOT/f'data/clean/{table["name"]}.csv',nrows=0).columns))

if __name__=='__main__': unittest.main()
