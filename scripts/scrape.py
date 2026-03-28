"""
scrape.py - keirin.jp 出走表スクレイピング

使用方法:
    python scripts/scrape.py --date 20260329

出力:
    data/raw/2026-03-29/{venue_code}_{race_number:02d}.json
    data/raw/2026-03-29/index.json
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

# プロジェクトルートを sys.path に追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.parser import parse_race_entry, parse_race_list

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

BASE_URL = "https://keirin.jp/pc"
JST = timezone(timedelta(hours=9))
REQUEST_INTERVAL = 1.5  # seconds between requests
MAX_RETRIES = 3

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _today_jst() -> str:
    """今日の JST 日付を YYYYMMDD 形式で返す"""
    return datetime.now(JST).strftime("%Y%m%d")


def _fetch(session: requests.Session, url: str) -> str | None:
    """
    URLをフェッチし、HTMLを返す。
    429/5xx は指数バックオフで最大 MAX_RETRIES 回リトライ。
    404 はスキップ（None を返す）。
    """
    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, timeout=30, headers=HEADERS)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 404:
                logger.debug(f"404 スキップ: {url}")
                return None
            elif resp.status_code in (429, 500, 502, 503, 504):
                wait = 2 ** attempt
                logger.warning(
                    f"HTTP {resp.status_code}: {url} — {wait}秒後リトライ ({attempt+1}/{MAX_RETRIES})"
                )
                time.sleep(wait)
            else:
                logger.warning(f"HTTP {resp.status_code}: {url}")
                return None
        except requests.RequestException as e:
            wait = 2 ** attempt
            logger.warning(f"接続エラー: {url} — {e} — {wait}秒後リトライ ({attempt+1}/{MAX_RETRIES})")
            time.sleep(wait)

    logger.error(f"最大リトライ到達: {url}")
    return None


def scrape_date(date_str: str, output_dir: Path) -> list[dict]:
    """
    指定日の全レース出走表をスクレイピングし JSON ファイルに保存する。

    Returns:
        保存したファイルのメタデータリスト
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    scraped = []

    # Step 1: レース一覧ページから開催場・レース番号を取得
    list_url = f"{BASE_URL}/racetop?hd={date_str}"
    logger.info(f"レース一覧取得: {list_url}")
    list_html = _fetch(session, list_url)

    if not list_html:
        logger.error("レース一覧ページの取得に失敗しました")
        return scraped

    venues = parse_race_list(list_html)

    if not venues:
        logger.warning(f"開催場が見つかりません: {date_str} (非開催日の可能性)")
        return scraped

    logger.info(f"開催場: {len(venues)} 場 — {[v['venueCode'] for v in venues]}")

    # Step 2: 各レース出走表をスクレイピング
    total = sum(len(v["raceNumbers"]) for v in venues)
    done = 0

    for venue in venues:
        venue_code = venue["venueCode"]
        for race_num in venue["raceNumbers"]:
            done += 1
            url = f"{BASE_URL}/raceentry?hd={date_str}&k={int(venue_code)}&r={race_num}"
            logger.info(f"[{done}/{total}] 出走表取得: {venue_code} {race_num}R")

            html = _fetch(session, url)
            if not html:
                logger.warning(f"出走表 スキップ: venue={venue_code} race={race_num}")
                time.sleep(REQUEST_INTERVAL)
                continue

            try:
                race_data = parse_race_entry(html, venue_code, race_num, date_str)
            except Exception as e:
                logger.error(f"出走表 解析エラー venue={venue_code} race={race_num}: {e}")
                time.sleep(REQUEST_INTERVAL)
                continue

            # 場名が取れなかった場合は venue から補完
            if not race_data["raceInfo"].get("venue") and venue.get("venueName"):
                race_data["raceInfo"]["venue"] = venue["venueName"]

            filename = f"{venue_code}_{race_num:02d}.json"
            filepath = output_dir / filename
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(race_data, f, ensure_ascii=False, indent=2)

            scraped.append({
                "venueCode": venue_code,
                "venueName": race_data["raceInfo"].get("venue", ""),
                "raceNumber": race_num,
                "grade": race_data["raceInfo"].get("grade", ""),
                "filename": filename,
                "entryCount": len(race_data.get("entries", [])),
            })

            time.sleep(REQUEST_INTERVAL)

    return scraped


def main():
    parser = argparse.ArgumentParser(description="keirin.jp 出走表スクレイパー")
    parser.add_argument(
        "--date",
        default=_today_jst(),
        help="取得日 YYYYMMDD（デフォルト: JST今日）",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="出力ディレクトリ（デフォルト: data/raw/YYYY-MM-DD）",
    )
    args = parser.parse_args()

    date_str = args.date
    if len(date_str) != 8 or not date_str.isdigit():
        logger.error(f"日付フォーマットエラー: {date_str} (YYYYMMDD 形式で指定)")
        sys.exit(1)

    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    output_dir = Path(args.output_dir or f"data/raw/{formatted_date}")

    logger.info(f"スクレイピング開始: {formatted_date}")
    scraped = scrape_date(date_str, output_dir)

    # index.json を書き出し
    index = {
        "date": formatted_date,
        "scrapedAt": datetime.now(JST).isoformat(),
        "totalRaces": len(scraped),
        "races": scraped,
    }
    index_path = output_dir / "index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    logger.info(f"完了: {len(scraped)} レース → {output_dir}")

    if not scraped:
        logger.warning("スクレイピング結果が 0 件です")
        sys.exit(0)  # 非開催日は正常終了


if __name__ == "__main__":
    main()
