"""Independent Python/Decimal reconciliation of all nine bundled SQL analyses.

Reads base tables only, then uses Python sets, dictionaries and Decimal sums.
It verifies transformations, not the truth or completeness of source records.
"""
from __future__ import annotations

import argparse
import json
import math
import sqlite3
from collections import Counter, defaultdict
from contextlib import closing
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def money(value):
    return float(Decimal(value).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))


def percent(numerator, denominator):
    return money(Decimal(100)*numerator/denominator) if denominator else None


def tiles(rows, key):
    ordered = sorted(rows, key=key)
    size, remainder = divmod(len(ordered), 4)
    scores, start = {}, 0
    for bucket in range(1, 5):
        end = start+size+(bucket <= remainder)
        for row in ordered[start:end]:
            scores[row[0]] = bucket
        start = end
    return scores


def reference_results(conn):
    customers = {r[0]: r for r in conn.execute('SELECT * FROM customers')}
    products = {r[0]: r for r in conn.execute('SELECT * FROM products')}
    orders = {r[0]: r for r in conn.execute('SELECT * FROM orders')}
    items = list(conn.execute('SELECT * FROM order_items'))
    delivered = [r for r in orders.values() if r[2] == 'delivered']
    values, item_orders = defaultdict(Decimal), set()
    category, sellers, months = {}, defaultdict(lambda: defaultdict(Decimal)), {}
    missing_product = missing_category = nonpositive = negative_freight = 0
    for oid, _, pid, sid, price, freight in items:
        value = Decimal(str(price))
        values[oid] += value
        item_orders.add(oid)
        missing_product += pid not in products
        cat = ((products.get(pid, (None, None))[1] or '').strip() or 'unknown')
        missing_category += pid not in products or not (products[pid][1] or '').strip()
        nonpositive += price <= 0
        negative_freight += freight < 0
        order = orders[oid]
        if order[2] != 'delivered':
            continue
        customer = customers[order[1]]
        key = (customer[3], cat)
        entry = category.setdefault(key, {'orders':set(), 'sellers':set(), 'value':Decimal(0)})
        entry['orders'].add(oid); entry['sellers'].add(sid); entry['value'] += value
        sellers[key][sid] += value
        if order[3]:
            month = months.setdefault(order[3][:7], {'orders':set(), 'customers':set(), 'items':0, 'value':Decimal(0)})
            month['orders'].add(oid); month['customers'].add(customer[1])
            month['items'] += 1; month['value'] += value
    result = {}
    result[1] = [(s,c,len(v['orders']),money(v['value'])) for (s,c),v in category.items()]
    result[2] = [(s,c,len(v['orders']),len(v['sellers']),money(v['value'])) for (s,c),v in category.items()]
    result[3] = []
    for (s,c), seller_values in sellers.items():
        total = sum(seller_values.values())
        for rank,(sid,value) in enumerate(sorted(seller_values.items(), key=lambda x:(-x[1],x[0]))[:3],1):
            result[3].append((s,c,sid,rank,money(value),percent(value,total)))
    counts = Counter(customers[o[1]][1] for o in delivered if customers[o[1]][1])
    repeat = sum(n>=2 for n in counts.values())
    result[4] = [(len(counts),repeat,percent(Decimal(repeat),len(counts)))]
    histories, future = defaultdict(list), set()
    rfm_history = defaultdict(list)
    for order in delivered:
        oid, cid, _, timestamp = order
        uid = customers[cid][1]
        if not timestamp:
            continue
        if '2018-07-01' <= timestamp < '2018-07-31':
            future.add(uid)
        if oid in item_orders and timestamp < '2018-07-01':
            histories[uid].append(order)
        if oid in item_orders and timestamp < '2018-09-01':
            rfm_history[uid].append(order)
    result[5] = [(uid,len(history),money(sum(values[o[0]] for o in history)),
                  (date(2018,7,1)-date.fromisoformat(max(o[3] for o in history)[:10])).days,
                  int(uid in future)) for uid,history in histories.items()]
    result[6] = []
    for state in {k[0] for k in category}:
        groups = [(c,v) for (s,c),v in category.items() if s==state]
        total = sum(v['value'] for _,v in groups)
        for rank,(cat,v) in enumerate(sorted(groups,key=lambda x:(-x[1]['value'],x[0])),1):
            result[6].append((state,cat,len(v['orders']),money(v['value']),percent(v['value'],total),rank))
    result[7] = [(month,len(v['orders']),len(v['customers']),v['items'],money(v['value']),
                  money(v['value']/len(v['orders']))) for month,v in months.items()]
    rfm = [(uid,(date(2018,9,1)-date.fromisoformat(max(o[3] for o in history)[:10])).days,
            len(history),sum(values[o[0]] for o in history)) for uid,history in rfm_history.items()]
    rs = tiles(rfm,lambda r:(-r[1],r[0])); fs = tiles(rfm,lambda r:(r[2],r[0])); ms = tiles(rfm,lambda r:(r[3],r[0]))
    result[8] = []
    for uid, recency, frequency, value in rfm:
        r,f,m = rs[uid],fs[uid],ms[uid]
        label = ('recent_and_frequent' if r==4 and f>=3 else 'recent' if r==4
                 else 'frequent_historical' if f>=3 else 'other_historical')
        result[8].append((uid,recency,frequency,money(value),r,f,m,label))
    invalid = 0
    for order in orders.values():
        if order[3]:
            try:
                parsed = datetime.strptime(order[3],'%Y-%m-%d %H:%M:%S')
                invalid += parsed.strftime('%Y-%m-%d %H:%M:%S') != order[3]
            except ValueError:
                invalid += 1
    result[9] = list({'orders_total':len(orders),'orders_delivered':len(delivered),
        'items_total':len(items),'items_missing_product_record':missing_product,
        'items_missing_category':missing_category,'items_nonpositive_price':nonpositive,
        'orders_missing_purchase_timestamp':sum(not o[3] for o in orders.values()),
        'orders_invalid_purchase_timestamp':invalid,'orders_without_items':len(set(orders)-item_orders),
        'delivered_orders_without_items':sum(o[0] not in item_orders for o in delivered),
        'items_negative_freight':negative_freight,
        'customers_missing_unique_id':sum(not c[1] for c in customers.values())}.items())
    return result


def validate(db):
    with closing(sqlite3.connect(Path(db).resolve().as_uri()+'?mode=ro',uri=True)) as conn:
        conn.execute('BEGIN')
        expected = reference_results(conn)
        checked = {}
        for number, query in enumerate(sorted((BASE/'sql').glob('*.sql')),1):
            actual = conn.execute(query.read_text(encoding='utf-8')).fetchall()
            reference = expected[number]
            # Stable dimensional keys; numeric tolerances only below displayed precision.
            dimensions = {1:2,2:2,3:3,4:0,5:1,6:2,7:1,8:1,9:1}[number]
            actual.sort(key=lambda r:r[:dimensions]); reference.sort(key=lambda r:r[:dimensions])
            if len(actual)!=len(reference):
                raise ValueError(f'{query.name}: row count differs')
            for row, wanted in zip(actual,reference):
                for value, target in zip(row,wanted):
                    equal = (math.isclose(value,target,rel_tol=0,abs_tol=0.000001)
                             if isinstance(value,(int,float)) and isinstance(target,(int,float)) else value==target)
                    if not equal:
                        raise ValueError(f'{query.name}: independent reconciliation failed')
            checked[query.name] = len(actual)
        return checked


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps({'independent_python_reconciliation':'passed','rows_checked':validate(args.db)},indent=2))
