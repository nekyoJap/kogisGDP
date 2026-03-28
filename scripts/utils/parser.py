"""
parser.py - keirin.jp HTML → RaceEntry JSON 変換

keirin.jp のページ構造変更に耐えるため、列ヘッダーを動的に検出する。
全フィールドを try/except でラップし、部分失敗でも処理を継続する。
"""

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

# グレード表記の正規化マッピング（全角・日本語 → 英略称）
GRADE_MAP = {
    "グランプリ": "GP",
    "ＧＲＡＮＤ　ＰＲＩＸ": "GP",
    "GRAND PRIX": "GP",
    "Ｇ１": "GI",
    "G1": "GI",
    "ＧＩ": "GI",
    "Ｇ２": "GII",
    "G2": "GII",
    "ＧＩＩ": "GII",
    "Ｇ３": "GIII",
    "G3": "GIII",
    "ＧＩＩＩ": "GIII",
    "Ｆ１": "FI",
    "F1": "FI",
    "ＦＩ": "FI",
    "Ｆ２": "FII",
    "F2": "FII",
    "ＦＩＩ": "FII",
    "GI": "GI",
    "GII": "GII",
    "GIII": "GIII",
    "FI": "FI",
    "FII": "FII",
    "GP": "GP",
}

# 脚質の正規化
STYLE_MAP = {
    "逃": "逃",
    "追": "追",
    "両": "両",
    "自": "両",  # 自在
}

# 級班の正規化
RANK_MAP = {
    "ＳＳ": "SS",
    "SS": "SS",
    "Ｓ１": "S1",
    "S1": "S1",
    "Ｓ２": "S2",
    "S2": "S2",
    "Ａ１": "A1",
    "A1": "A1",
    "Ａ２": "A2",
    "A2": "A2",
    "Ａ３": "A3",
    "A3": "A3",
    "Ｌ１": "L1",
    "L1": "L1",
}


def _normalize_text(text: str) -> str:
    """テキストのホワイトスペースを正規化する"""
    import unicodedata
    text = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", " ", text).strip()


def _safe_int(text: str, default: int = 0) -> int:
    try:
        return int(re.sub(r"[^\d]", "", text) or str(default))
    except (ValueError, TypeError):
        return default


def _safe_float(text: str, default: float = 0.0) -> float:
    try:
        cleaned = re.sub(r"[^\d.]", "", text)
        return float(cleaned) if cleaned else default
    except (ValueError, TypeError):
        return default


def _detect_grade(soup: BeautifulSoup) -> str:
    """ページ内からグレードを検出する"""
    # グレード要素を複数パターンで探す
    selectors = [
        ".grade", ".race-grade", "[class*='grade']",
        ".race-info", ".race-header", "h1", "h2", ".race-name"
    ]
    for selector in selectors:
        try:
            elements = soup.select(selector)
            for el in elements:
                text = _normalize_text(el.get_text())
                for pattern, grade in GRADE_MAP.items():
                    if pattern in text:
                        return grade
        except Exception:
            continue

    # ページ全体テキストで検索（フォールバック）
    full_text = _normalize_text(soup.get_text())
    for pattern, grade in GRADE_MAP.items():
        if pattern in full_text:
            return grade

    return "FI"  # デフォルト


def _detect_race_info(soup: BeautifulSoup, venue_code: str, race_number: int, date: str) -> dict:
    """レース情報ヘッダーを解析する"""
    race_info = {
        "date": f"{date[:4]}-{date[4:6]}-{date[6:8]}",
        "venue": "",
        "venueCode": venue_code,
        "raceNumber": race_number,
        "raceName": "",
        "grade": _detect_grade(soup),
        "startTime": "",
    }

    try:
        # 開催場名を探す
        venue_selectors = [".venue", ".kaisai", ".place", "[class*='venue']", "[class*='kaisai']"]
        for selector in venue_selectors:
            el = soup.select_one(selector)
            if el:
                race_info["venue"] = _normalize_text(el.get_text())
                break

        # スタート時刻を探す
        time_selectors = ["[class*='time']", "[class*='start']"]
        for selector in time_selectors:
            el = soup.select_one(selector)
            if el:
                text = _normalize_text(el.get_text())
                time_match = re.search(r"\d{1,2}:\d{2}", text)
                if time_match:
                    race_info["startTime"] = time_match.group()
                    break

        # レース名を探す
        name_selectors = [".race-name", ".race-title", "h1", "h2", ".title"]
        for selector in name_selectors:
            el = soup.select_one(selector)
            if el:
                text = _normalize_text(el.get_text())
                if text and len(text) < 50:
                    race_info["raceName"] = text
                    break
    except Exception as e:
        logger.warning(f"レース情報解析エラー: {e}")

    return race_info


def _find_entry_table(soup: BeautifulSoup) -> Optional[Tag]:
    """出走表テーブルを検出する"""
    # ヘッダーに「車番」「選手名」を含むテーブルを探す
    for table in soup.find_all("table"):
        headers = [_normalize_text(th.get_text()) for th in table.find_all("th")]
        header_text = " ".join(headers)
        if ("車番" in header_text or "選手名" in header_text) and len(headers) >= 3:
            return table

    # クラス名でフォールバック
    selectors = [
        "table.entry", "table.race-entry", "table[class*='entry']",
        ".entry-table table", "#entry table"
    ]
    for selector in selectors:
        table = soup.select_one(selector)
        if table:
            return table

    # 最大の表をフォールバック
    tables = soup.find_all("table")
    if tables:
        return max(tables, key=lambda t: len(t.find_all("tr")))

    return None


def _build_column_map(header_row: Tag) -> dict[str, int]:
    """
    ヘッダー行から列名→インデックスのマッピングを構築する。
    列順が変わっても動作する。
    """
    col_map: dict[str, int] = {}
    cells = header_row.find_all(["th", "td"])

    keywords = {
        "frame": ["枠", "枠番"],
        "car": ["車番", "車", "番"],
        "name": ["選手名", "氏名", "選手"],
        "pref": ["府県", "都道府県", "所属"],
        "age": ["年齢", "齢"],
        "term": ["期別", "期"],
        "rank": ["級班", "級", "班"],
        "style": ["脚質"],
        "gear": ["ギア", "ギヤ"],
        "score": ["競走得点", "得点", "ポイント"],
        "winRate": ["勝率"],
        "top2Rate": ["2連対率", "２連対率", "連対率"],
        "top3Rate": ["3連対率", "３連対率"],
        "back": ["バック", "B数"],
    }

    for idx, cell in enumerate(cells):
        text = _normalize_text(cell.get_text())
        for field, kws in keywords.items():
            if any(kw in text for kw in kws) and field not in col_map:
                col_map[field] = idx
                break

    return col_map


def _parse_entry_table(table: Tag) -> list[dict]:
    """出走表テーブルの各行を選手エントリーとして解析する"""
    entries = []

    rows = table.find_all("tr")
    if not rows:
        return entries

    # ヘッダー行を検出（最初の th を含む行）
    header_row = None
    data_start = 0
    for i, row in enumerate(rows):
        if row.find("th"):
            header_row = row
            data_start = i + 1
            break

    col_map = _build_column_map(header_row) if header_row else {}

    for row in rows[data_start:]:
        cells = row.find_all(["td", "th"])
        if len(cells) < 3:
            continue

        def get(field: str, default: str = "") -> str:
            idx = col_map.get(field)
            if idx is None or idx >= len(cells):
                return default
            return _normalize_text(cells[idx].get_text())

        try:
            car_text = get("car") or (cells[1].get_text() if len(cells) > 1 else "")
            car_num = _safe_int(car_text)
            if car_num < 1 or car_num > 9:
                continue  # 有効な車番でない行はスキップ

            name_text = get("name")
            if not name_text:
                # 車番以外の列から選手名を推定
                for cell in cells:
                    t = _normalize_text(cell.get_text())
                    if re.match(r"[\u4e00-\u9fff\u3040-\u30ff]{2,5}", t) and len(t) <= 8:
                        name_text = t
                        break

            raw_rank = get("rank")
            rank = RANK_MAP.get(raw_rank, raw_rank or "")

            raw_style = get("style")
            style = STYLE_MAP.get(raw_style, raw_style or "")

            entry = {
                "frameNumber": _safe_int(get("frame"), default=0),
                "carNumber": car_num,
                "name": name_text,
                "prefecture": get("pref"),
                "age": _safe_int(get("age")),
                "term": _safe_int(get("term")),
                "rank": rank,
                "style": style,
                "gear": _safe_float(get("gear")),
                "score": _safe_float(get("score")),
                "winRate": _safe_float(get("winRate")),
                "top2Rate": _safe_float(get("top2Rate")),
                "top3Rate": _safe_float(get("top3Rate")),
            }
            entries.append(entry)

        except Exception as e:
            logger.warning(f"行解析エラー（車番 {car_num if 'car_num' in dir() else '?'}）: {e}")
            continue

    return entries


def _parse_lineup_comment(soup: BeautifulSoup) -> str:
    """並び予想コメントを取得する"""
    selectors = [
        "[class*='narabi']", "[class*='lineup']", "[class*='formation']",
        ".comment", "#comment", ".race-comment"
    ]
    for selector in selectors:
        el = soup.select_one(selector)
        if el:
            text = _normalize_text(el.get_text())
            if text:
                return text

    return ""


def parse_race_entry(
    html: str,
    venue_code: str,
    race_number: int,
    date: str,
) -> dict:
    """
    keirin.jp 出走表HTMLを RaceEntry JSON に変換する。

    Args:
        html: 出走表ページのHTML文字列
        venue_code: 場コード（2桁文字列、例: "35"）
        race_number: レース番号（1-12）
        date: 日付文字列 YYYYMMDD

    Returns:
        RaceEntry 形式の dict。解析失敗フィールドはデフォルト値。
    """
    soup = BeautifulSoup(html, "lxml")

    race_info = _detect_race_info(soup, venue_code, race_number, date)

    table = _find_entry_table(soup)
    entries = _parse_entry_table(table) if table else []

    if not entries:
        logger.warning(f"出走表 エントリー取得 0件: venue={venue_code} race={race_number}")

    lineup_comment = _parse_lineup_comment(soup)

    return {
        "raceInfo": race_info,
        "entries": entries,
        "lineUp": {"comment": lineup_comment},
        "parseWarnings": [] if entries else ["no_entries_found"],
    }


def parse_race_list(html: str) -> list[dict]:
    """
    keirin.jp レース一覧ページ（racetop）から開催場・レース番号リストを抽出する。

    Returns:
        [{"venueCode": "35", "venueName": "平塚", "raceNumbers": [1,2,...,11]}]
    """
    soup = BeautifulSoup(html, "lxml")
    venues = []

    # 出走表リンクから venue_code と race_number を抽出
    # URL パターン例: /pc/raceentry?hd=20260329&k=35&r=11
    entry_links = soup.find_all("a", href=re.compile(r"raceentry.*[?&]k=(\d+).*[?&]r=(\d+)"))

    venue_race_map: dict[str, set] = {}
    venue_name_map: dict[str, str] = {}

    for link in entry_links:
        href = link.get("href", "")
        k_match = re.search(r"[?&]k=(\d+)", href)
        r_match = re.search(r"[?&]r=(\d+)", href)
        if k_match and r_match:
            k = k_match.group(1).zfill(2)
            r = int(r_match.group(1))
            if k not in venue_race_map:
                venue_race_map[k] = set()
                # 場名を親要素から推定
                parent = link.find_parent(["div", "td", "li", "section"])
                if parent:
                    text = _normalize_text(parent.get_text())
                    venue_name_map[k] = text[:10]  # 最大10文字
            venue_race_map[k].add(r)

    for k, race_set in venue_race_map.items():
        venues.append({
            "venueCode": k,
            "venueName": venue_name_map.get(k, ""),
            "raceNumbers": sorted(race_set),
        })

    return venues
