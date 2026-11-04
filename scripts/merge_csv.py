#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
去重补齐：把 new.csv 合并进 lottery.csv
- 按期号(market+issue)去重，新数据优先
- 按 market, issue 排序
- 不删除旧数据，只追加缺失的
用法：python merge_csv.py new.csv lottery.csv
"""
import csv, sys, os

HEADER = ['market', 'issue', 'opendate', 'w', 'q', 'b', 's', 'g']

def read_csv(path):
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for r in reader:
            if not r.get('market') or not r.get('issue'):
                continue
            rows.append({k: (r.get(k) or '').strip() for k in HEADER})
    return rows

def key_of(r):
    return (r['market'], r['issue'])

def main():
    if len(sys.argv) < 3:
        print('用法: python merge_csv.py new.csv lottery.csv')
        sys.exit(1)
    new_path, target_path = sys.argv[1], sys.argv[2]

    old_rows = read_csv(target_path)
    new_rows = read_csv(new_path)

    merged = {}
    for r in old_rows:
        merged[key_of(r)] = r
    added = 0
    for r in new_rows:
        k = key_of(r)
        if k not in merged:
            added += 1
        merged[k] = r

    market_order = {'NEWHASH3FC': 0, 'HASH3FC': 1, 'ET3FC': 2}
    out = sorted(merged.values(), key=lambda r: (
        market_order.get(r['market'], 99), r['issue']
    ))

    with open(target_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        for r in out:
            w.writerow(r)

    print(f'旧文件 {len(old_rows)} 行，新文件 {len(new_rows)} 行，新增 {added} 行，合并后 {len(out)} 行')

if __name__ == '__main__':
    main()
