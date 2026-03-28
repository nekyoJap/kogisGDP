"""
player_lookup.py - 選手評価CSVの読み込みと名前ベースの検索

選手名の表記ゆれ（全角スペース・異体字・半角全角）を吸収してマッチングする。
"""

import csv
import unicodedata
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# 一文字異体字の正規化（str.maketrans は1文字キーのみ）
_KANJI_NORM = str.maketrans({
    "髙": "高",
    "濵": "浜",
    "濱": "浜",
    "嶋": "島",
    "齋": "斎",
    "齊": "斉",
    "邉": "辺",
    "邊": "辺",
    "澤": "沢",
    "黑": "黒",
    "ヶ": "ケ",
})

# 複数文字の異体字（str.maketrans では扱えないため別処理）
_MULTI_KANJI_NORM = [
    ("渡邉", "渡辺"),
    ("渡邊", "渡辺"),
]


def normalize_name(name: str) -> str:
    """
    選手名を正規化する。
    - NFKC正規化（全角英数→半角、全角カナ→半角カナ）
    - 全角スペース・半角スペース除去
    - 異体字・旧字体を標準漢字に統一
    """
    if not name:
        return ""
    # 複数文字の異体字置換（先に行う）
    for old, new in _MULTI_KANJI_NORM:
        name = name.replace(old, new)
    # NFKC正規化
    name = unicodedata.normalize("NFKC", name)
    # スペース除去（全角・半角・改行）
    name = name.replace("\u3000", "").replace(" ", "").replace("\u00a0", "").strip()
    # 一文字異体字置換
    name = name.translate(_KANJI_NORM)
    return name


def load_player_db(csv_path: str | Path) -> dict[str, dict]:
    """
    選手評価CSVを読み込み {正規化名: 評価dict} を返す。

    CSVの想定列（ヘッダーは柔軟に対応）:
    選手名, 年齢, 級班, 府県, ホーム, 期別, タイプ１, タイプ２,
    先行意欲, 番手経験, スピード, 仕掛け, スタミナ, 競輪IQ, コメント 等
    """
    db: dict[str, dict] = {}
    csv_path = Path(csv_path)

    if not csv_path.exists():
        logger.warning(f"選手評価CSV が見つかりません: {csv_path}")
        return db

    try:
        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_name = row.get("選手名", "").strip()
                if not raw_name:
                    continue
                key = normalize_name(raw_name)
                if key:
                    db[key] = dict(row)
    except Exception as e:
        logger.error(f"選手評価CSV 読み込みエラー: {e}")

    logger.info(f"選手評価DB ロード完了: {len(db)} 選手")
    return db


def lookup_player(db: dict[str, dict], name: str) -> dict | None:
    """
    選手名で評価DBを検索する。
    1) 正規化後の完全一致
    2) スペース除去後の完全一致（念のため）
    一致しない場合は None を返す。
    """
    if not name or not db:
        return None

    key = normalize_name(name)
    if key in db:
        return db[key]

    # フォールバック: スペースを詰めた状態で再検索
    key_nospace = key.replace(" ", "")
    for stored_key, val in db.items():
        if stored_key.replace(" ", "") == key_nospace:
            return val

    return None


def enrich_entry(entry: dict, db: dict[str, dict]) -> dict:
    """
    出走表エントリーに選手評価データを付加して返す。
    評価が見つからない場合は evalFound=False を付加する。

    付加するフィールド（評価CSVから）:
    - type1, type2: タイプ
    - leadWill: 先行意欲（◎◯△✕）
    - banteExp: 番手経験
    - speed, attack, stamina, keirinIQ: 各評価
    - comment: コメント
    - compatTrack: 相性◯バンク
    - incompatTrack: 相性✕バンク
    """
    name = entry.get("name", "")
    player = lookup_player(db, name)

    enriched = dict(entry)

    if player:
        enriched["evalFound"] = True
        enriched["type1"] = player.get("タイプ１", "")
        enriched["type2"] = player.get("タイプ２", "")
        enriched["leadWill"] = player.get("先行意欲", "")
        enriched["banteExp"] = player.get("番手経験", "")
        enriched["speed"] = player.get("スピード", "")
        enriched["attack"] = player.get("仕掛け", "")
        enriched["stamina"] = player.get("スタミナ", "")
        enriched["keirinIQ"] = player.get("競輪IQ", "")
        enriched["comment"] = player.get("コメント", "")
        enriched["compatTrack"] = player.get("相性◯バンク", "")
        enriched["incompatTrack"] = player.get("相性✕バンク", "")
    else:
        enriched["evalFound"] = False
        logger.debug(f"選手評価 未ヒット: {name}")

    return enriched
