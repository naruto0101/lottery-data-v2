import csv
import os
import requests

API_KEY = os.environ.get("API_KEY", "")
API_URL = f"http://vip.lkag3.com/{API_KEY}/p/10.json"
CSV_FILE = "lottery.csv"
FIELDNAMES = ["market", "issue", "opendate", "d1", "d2", "d3", "d4", "d5"]

MARKETS = ["HASH3FC", "NEWHASH3FC", "ET3FC"]

def normalize_issue(issue_str):
    s = str(issue_str).strip()
    if "-" in s:
        return s
    if len(s) >= 11 and s.isdigit():
        return s[:8] + "-" + s[8:].zfill(4)
    return s

def parse_response(json_data):
    all_rows = []
    for market_key in MARKETS:
        market_data = json_data.get(market_key, [])
        if not isinstance(market_data, list):
            continue
        for item in market_data:
            code_field = item.get("code", {})
            code_str = str(code_field.get("code", "")) if isinstance(code_field, dict) else ""
            parts = [p.strip() for p in code_str.split(",") if p.strip()]
            if len(parts) < 5:
                continue
            digits = parts[-5:]
            if not all(d.isdigit() and 0 <= int(d) <= 9 for d in digits):
                continue
            all_rows.append({
                "market": market_key,
                "issue": normalize_issue(item.get("issue", "")),
                "opendate": str(item.get("opendate", "")).strip(),
                "d1": digits[0], "d2": digits[1], "d3": digits[2],
                "d4": digits[3], "d5": digits[4]
            })
    return all_rows

def load_existing():
    existing = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = f"{row.get('market','')}_{row.get('issue','')}"
                existing[key] = row
    return existing

def save_csv(rows_dict):
    all_rows = sorted(rows_dict.values(), key=lambda x: (x["market"], x["issue"]))
    with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"成功写入 {len(all_rows)} 行到 {CSV_FILE}")

def main():
    if not API_KEY:
        print("错误：没有读取到 API_KEY，请检查 Secret 配置")
        return

    print(f"开始从 {API_URL} 拉取最近 10 期...")
    try:
        resp = requests.get(API_URL, timeout=30)
        resp.raise_for_status()
        json_data = resp.json()
    except Exception as e:
        print(f"请求API失败: {e}")
        return

    new_rows = parse_response(json_data)
    print(f"本次从API解析出 {len(new_rows)} 条数据")

    if not new_rows:
        print("API没有返回有效数据，任务结束。")
        return

    existing = load_existing()
    added_list = []
    for row in new_rows:
        key = f"{row['market']}_{row['issue']}"
        if key not in existing:
            existing[key] = row
            added_list.append(f"{row['market']}  {row['issue']}")

    if added_list:
        print(f"补入 {len(added_list)} 条（最近10期内的缺口）：")
        for x in added_list:
            print(f"  {x}")
        save_csv(existing)
    else:
        print("最近10期数据完整，无需更新。")

if __name__ == "__main__":
    main()
