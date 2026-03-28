"""
predict.py - Claude Haiku による競輪予想生成

使用方法:
    python scripts/predict.py --date 20260329

前提:
    - 環境変数 ANTHROPIC_API_KEY が設定されていること
    - scripts/scrape.py が先に実行済みで data/raw/YYYY-MM-DD/index.json が存在すること

出力:
    docs/predictions/2026-03-29/{venue_code}_{race_number:02d}.json
    docs/predictions/2026-03-29/summary.json
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import anthropic

# プロジェクトルートを sys.path に追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.formatter import validate_and_format
from scripts.utils.player_lookup import enrich_entry, load_player_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

JST = timezone(timedelta(hours=9))
MAX_RETRIES = 3

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
DATA_DIR = PROJECT_ROOT / "data"
DOCS_PREDICTIONS_DIR = PROJECT_ROOT / "docs" / "predictions"

# 選手評価 CSV のパス（ファイル名が固定）
PLAYER_CSV_GLOB = "SS〜*評価*.csv"


def _load_system_prompt() -> str:
    """keirin-agent.md を読み込みシステムプロンプトを構築する"""
    agent_md = KNOWLEDGE_DIR / "keirin-agent.md"
    if not agent_md.exists():
        logger.warning("knowledge/keirin-agent.md が見つかりません")
        return "あなたは競輪予想AIです。構造化JSONで予想を返してください。"
    return agent_md.read_text(encoding="utf-8")


def _load_track_profiles() -> dict:
    """track-profiles.json を読み込む"""
    path = KNOWLEDGE_DIR / "track-profiles.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_grade_rules() -> dict:
    """grade-rules.json を読み込む"""
    path = KNOWLEDGE_DIR / "grade-rules.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _find_player_csv() -> Path | None:
    """data/ 以下から選手評価 CSV を探す"""
    for csv_path in DATA_DIR.glob(PLAYER_CSV_GLOB):
        return csv_path
    # サブディレクトリも検索
    for csv_path in DATA_DIR.rglob(PLAYER_CSV_GLOB):
        return csv_path
    return None


def _get_track_info(venue_code: str, tracks: dict) -> dict:
    """場コードからバンク情報を取得する"""
    track = tracks.get("tracks", {}).get(venue_code, {})
    bias_map = tracks.get("bias", {})

    if not track:
        return {"length": 400, "straight": 56.0, "cant": 30.0, "roof": False, "bias": ""}

    length = track.get("length", 400)
    straight = track.get("straight", 56.0)

    # バンク補正コメントを決定
    if length <= 333:
        bias = bias_map.get("333", "先行有利")
    elif length >= 500 or straight >= 70:
        bias = bias_map.get("500", "追い込み有利")
    elif straight >= 60:
        bias = bias_map.get("longstraight", "やや追い込み有利")
    else:
        bias = bias_map.get("400", "バランス型")

    if track.get("roof"):
        bias += " " + bias_map.get("roof", "屋根あり（風影響なし）")

    return {**track, "bias": bias}


def _build_user_prompt(race_data: dict, track_info: dict, grade_info: dict) -> str:
    """Claude Haiku へのユーザープロンプトを構築する"""
    race_info = race_data.get("raceInfo", {})
    entries = race_data.get("entries", [])
    lineup = race_data.get("lineUp", {})

    date = race_info.get("date", "")
    venue = race_info.get("venue", "")
    race_number = race_info.get("raceNumber", 0)
    grade = race_info.get("grade", "")
    venue_code = race_info.get("venueCode", "")

    track_length = track_info.get("length", 400)
    track_straight = track_info.get("straight", 56.0)
    track_bias = track_info.get("bias", "")
    track_roof = "屋根あり" if track_info.get("roof") else "屋根なし"

    grade_notes = grade_info.get("notes", "") if grade_info else ""

    # 選手テーブルを構築
    table_rows = []
    for e in entries:
        eval_mark = "" if e.get("evalFound", True) else "※評価なし"
        row = (
            f"| {e.get('carNumber', '')} "
            f"| {e.get('name', '')} "
            f"| {e.get('prefecture', '')} "
            f"| {e.get('rank', '')} "
            f"| {e.get('style', '')} "
            f"| {e.get('score', 0):.1f} "
            f"| {e.get('leadWill', eval_mark)} "
            f"| {e.get('speed', eval_mark)} "
            f"| {e.get('attack', eval_mark)} "
            f"| {e.get('stamina', eval_mark)} "
            f"| {e.get('keirinIQ', eval_mark)} "
            f"| {e.get('comment', '')} |"
        )
        table_rows.append(row)

    table_str = "\n".join(table_rows)
    lineup_comment = lineup.get("comment", "（並び情報なし）")

    prompt = f"""以下の競輪レースの予想をJSONで出力してください。

## レース情報
- 開催日: {date}
- 開催場: {venue}（場コード: {venue_code}）
- バンク周長: {track_length}m、みなし直線: {track_straight}m、{track_roof}
- バンク特性: {track_bias}
- レース番号: {race_number}R
- グレード: {grade}（{grade_notes}）

## 出走選手（{len(entries)}名）

| 車番 | 選手名 | 府県 | 級班 | 脚質 | 競走得点 | 先行意欲 | スピード | 仕掛け | スタミナ | 競輪IQ | コメント |
|-----|--------|------|------|------|---------|---------|---------|-------|---------|-------|--------|
{table_str}

## 並び予想コメント
{lineup_comment}

## 出力形式
race_id は "{venue_code}_{race_number:02d}" として、JSONスキーマ通りに出力してください。"""

    return prompt


def _call_claude(client: anthropic.Anthropic, system_prompt: str, user_prompt: str) -> str:
    """Claude Haiku を呼び出し応答テキストを返す。レート制限時はリトライする。"""
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text
        except anthropic.RateLimitError:
            wait = 60 * (attempt + 1)
            logger.warning(f"レート制限 — {wait}秒後リトライ ({attempt+1}/{MAX_RETRIES})")
            time.sleep(wait)
        except anthropic.APIStatusError as e:
            if e.status_code >= 500:
                wait = 30 * (attempt + 1)
                logger.warning(f"APIエラー {e.status_code} — {wait}秒後リトライ ({attempt+1}/{MAX_RETRIES})")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Claude API 最大リトライ回数到達")


def predict_date(date_str: str) -> None:
    """
    指定日の全レース予想を生成し docs/predictions/ に保存する。
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("環境変数 ANTHROPIC_API_KEY が設定されていません")
        sys.exit(1)

    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    raw_dir = DATA_DIR / "raw" / formatted_date
    index_path = raw_dir / "index.json"

    if not index_path.exists():
        logger.error(f"index.json が見つかりません: {index_path}")
        logger.error("先に scripts/scrape.py を実行してください")
        sys.exit(1)

    with open(index_path, encoding="utf-8") as f:
        index = json.load(f)

    races = index.get("races", [])
    if not races:
        logger.warning(f"予想対象レースが 0 件です: {formatted_date}")
        return

    # リソース読み込み
    system_prompt = _load_system_prompt()
    tracks = _load_track_profiles()
    grade_rules = _load_grade_rules()

    csv_path = _find_player_csv()
    player_db = load_player_db(csv_path) if csv_path else {}
    if not player_db:
        logger.warning("選手評価DBが空です（評価なし選手として処理します）")

    client = anthropic.Anthropic(api_key=api_key)

    output_dir = DOCS_PREDICTIONS_DIR / formatted_date
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_venues: dict[str, dict] = {}
    success_count = 0

    for race_meta in races:
        venue_code = race_meta["venueCode"]
        race_number = race_meta["raceNumber"]
        filename = race_meta["filename"]
        grade = race_meta.get("grade", "")

        logger.info(f"予想生成: {venue_code} {race_number}R ({grade})")

        # 出走表 JSON 読み込み
        race_json_path = raw_dir / filename
        try:
            with open(race_json_path, encoding="utf-8") as f:
                race_data = json.load(f)
        except Exception as e:
            logger.error(f"出走表 JSON 読み込みエラー: {race_json_path} — {e}")
            continue

        # 選手評価を enrich
        if player_db:
            race_data["entries"] = [
                enrich_entry(entry, player_db)
                for entry in race_data.get("entries", [])
            ]

        # バンク・グレード情報取得
        track_info = _get_track_info(venue_code, tracks)
        grade_info = grade_rules.get("grades", {}).get(grade, {})

        # Claude 呼び出し
        user_prompt = _build_user_prompt(race_data, track_info, grade_info)

        try:
            raw_response = _call_claude(client, system_prompt, user_prompt)
        except Exception as e:
            logger.error(f"Claude API エラー: venue={venue_code} race={race_number} — {e}")
            # エラーセンチネル書き出し
            error_path = output_dir / f"{venue_code}_{race_number:02d}.error.json"
            with open(error_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"error": str(e), "venue_code": venue_code, "race_number": race_number},
                    f, ensure_ascii=False
                )
            continue

        # 予想JSONを検証・整形
        race_info = race_data.get("raceInfo", {})
        prediction = validate_and_format(raw_response, race_info, venue_code, race_number)

        # 保存
        out_filename = f"{venue_code}_{race_number:02d}.json"
        out_path = output_dir / out_filename
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(prediction, f, ensure_ascii=False, indent=2)

        success_count += 1
        logger.info(f"  → 保存: {out_path}")

        # summary 用データ収集
        venue_name = race_info.get("venue", "")
        if venue_code not in summary_venues:
            summary_venues[venue_code] = {
                "code": venue_code,
                "name": venue_name,
                "races": [],
            }
        summary_venues[venue_code]["races"].append(race_number)

    # summary.json 書き出し
    summary = {
        "date": formatted_date,
        "generatedAt": datetime.now(JST).isoformat(),
        "totalRaces": success_count,
        "venues": list(summary_venues.values()),
    }
    summary_path = output_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    logger.info(f"予想生成完了: {success_count}/{len(races)} レース → {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="競輪 AI 予想生成")
    parser.add_argument(
        "--date",
        required=True,
        help="予想対象日 YYYYMMDD",
    )
    args = parser.parse_args()

    date_str = args.date
    if len(date_str) != 8 or not date_str.isdigit():
        logger.error(f"日付フォーマットエラー: {date_str} (YYYYMMDD 形式で指定)")
        sys.exit(1)

    predict_date(date_str)


if __name__ == "__main__":
    main()
