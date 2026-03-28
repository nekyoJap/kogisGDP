"""
formatter.py - 予想JSON の検証・整形

Claude Haiku の出力JSONを検証し、フィールドが不足している場合はデフォルト値で補完する。
"""

import json
import logging
import re
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))

# 有効な車番の範囲
VALID_CAR_NUMBERS = set(range(1, 10))


def _extract_json(text: str) -> dict | None:
    """
    テキストから JSON を抽出する。
    Claude が余分な説明文やコードフェンスを付けた場合に対応。
    """
    # コードフェンスを除去
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    text = re.sub(r"```\s*$", "", text).strip()

    # JSON オブジェクトを抽出（最初の { から最後の } まで）
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None

    json_str = text[start : end + 1]
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON デコードエラー: {e}")
        return None


def _validate_top3(top3: list) -> list[int]:
    """top3 フィールドを検証し 3 要素の int リストを返す"""
    if not isinstance(top3, list):
        return []
    result = []
    for item in top3[:3]:
        try:
            n = int(item)
            if n in VALID_CAR_NUMBERS:
                result.append(n)
        except (ValueError, TypeError):
            pass
    return result


def _validate_bets(bets: dict) -> dict:
    """recommended_bets を検証する"""
    if not isinstance(bets, dict):
        return {"sanrentan": [], "wide": []}

    sanrentan = []
    for combo in bets.get("sanrentan", []):
        if isinstance(combo, list) and len(combo) == 3:
            try:
                nums = [int(n) for n in combo]
                if all(n in VALID_CAR_NUMBERS for n in nums) and len(set(nums)) == 3:
                    sanrentan.append(nums)
            except (ValueError, TypeError):
                pass

    wide = []
    for combo in bets.get("wide", []):
        if isinstance(combo, list) and len(combo) == 2:
            try:
                nums = [int(n) for n in combo]
                if all(n in VALID_CAR_NUMBERS for n in nums) and nums[0] != nums[1]:
                    wide.append(nums)
            except (ValueError, TypeError):
                pass

    # sanrentan は 12〜16 点に収める
    if len(sanrentan) > 16:
        logger.warning(f"3連単が16点超 ({len(sanrentan)}点) → 16点に切り詰め")
        sanrentan = sanrentan[:16]

    return {"sanrentan": sanrentan, "wide": wide}


def validate_and_format(
    raw_text: str,
    race_meta: dict,
    venue_code: str,
    race_number: int,
) -> dict:
    """
    Claude の応答テキストを検証・整形して最終的な予想JSONを返す。

    Args:
        raw_text: Claude の応答テキスト（JSON文字列）
        race_meta: スクレイピング済みの raceInfo dict
        venue_code: 場コード
        race_number: レース番号

    Returns:
        整形済み予想 dict。JSON デコード失敗時は error フィールドを含む。
    """
    race_id = f"{venue_code}_{race_number:02d}"
    base = {
        "generated_at": datetime.now(JST).isoformat(),
        "model": "claude-haiku-4-5-20251001",
        "venue": race_meta.get("venue", ""),
        "venueCode": venue_code,
        "race_number": race_number,
        "grade": race_meta.get("grade", ""),
        "race_id": race_id,
    }

    raw = _extract_json(raw_text)
    if raw is None:
        logger.error(f"JSON 抽出失敗: {race_id}")
        return {**base, "error": "parse_failed", "raw_response": raw_text[:500]}

    pred = raw.get("prediction", {})
    if not pred:
        # トップレベルにフィールドがある場合にも対応
        pred = raw

    top3 = _validate_top3(pred.get("top3", []))
    bets = _validate_bets(pred.get("recommended_bets", {}))

    try:
        confidence = float(pred.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))
    except (ValueError, TypeError):
        confidence = 0.5

    formation = pred.get("formation", [])
    if isinstance(formation, str):
        formation = [formation]
    elif not isinstance(formation, list):
        formation = []

    return {
        **base,
        "prediction": {
            "formation": [str(f) for f in formation],
            "top3": top3,
            "confidence": confidence,
            "reasoning": str(pred.get("reasoning", "")),
            "recommended_bets": bets,
            "excluded_reason": str(pred.get("excluded_reason", "")),
        },
    }
