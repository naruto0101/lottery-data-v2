import csv
import os
import requests

API_KEY = os.environ.get("API_KEY", "")
API_URL = f"http://vip.lkag3.com/{API_KEY}/p/10.json"
CSV_FILE = "lottery.csv"

# ★ 表头必须和前端 HTML 的 parseCloudCSV 一致
FIELDNAMES = ["market", "issue", "opendate", "w", "q", "b", "s", "g"]

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
                "w": digits[0], "q": digits[1], "b": digits[2],
                "s": digits[3], "g": digits[4]
            })
    return all_rows


def load_existing():
    """读旧 CSV。兼容旧表头 d1~d5 和新表头 w~g 两种格式。"""
    existing = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 兼容旧格式：如果 d1~d5 存在，映射成 w~g
                if "d1" in row and row.get("d1") not in (None, ""):
                    row["w"] = row.get("d1", "")
                    row["q"] = row.get("d2", "")
                    row["b"] = row.get("d3", "")
                    row["s"] = row.get("d4", "")
                    row["g"] = row.get("d5", "")
                key = f"{row.get('market','')}_{row.get('issue','')}"
                existing[key] = row
    return existing


def save_csv(rows_dict):
    all_rows = sorted(rows_dict.values(), key=lambda x: (x["market"], x["issue"]))
    with open(CSV_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in all_rows:
            # 只保留 FIELDNAMES 里的字段，缺的填空，多的忽略
            safe = {k: row.get(k, "") for k in FIELDNAMES}
            writer.writerow(safe)
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
