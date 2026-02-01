#!/usr/bin/env python3
"""
WINTICKET スクレイパー動作確認スクリプト

使用方法:
    cd backend
    pip install -r requirements.txt
    python -m scraper.winticket.example

    または:
    python scraper/winticket/example.py
"""

import logging
import sys
from pathlib import Path

# モジュールパスを追加（直接実行用）
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scraper.winticket.schedule_scraper import get_racecard_url
from scraper.exceptions import EventNotFoundError


def main():
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # テストケース
    test_cases = [
        {
            "name": "小松島競輪 G3玉藻杯争覇戦 (2026/01/31)",
            "target_date": "2026-01-31",
            "venue_slug": "komatsushima",
            "expected_grade": "G3",
        },
        {
            "name": "平塚競輪 GPグランプリ (2025/12/30)",
            "target_date": "2025-12-30",
            "venue_slug": "hiratsuka",
            "expected_grade": "GP",
        },
    ]

    print("\n" + "=" * 70)
    print("WINTICKET スクレイパー動作確認")
    print("=" * 70)

    for i, tc in enumerate(test_cases, 1):
        print(f"\n--- テスト {i}: {tc['name']} ---")
        print(f"対象日: {tc['target_date']}")
        print(f"競輪場: {tc['venue_slug']}")

        try:
            result = get_racecard_url(
                target_date=tc["target_date"],
                venue_slug=tc["venue_slug"],
            )

            print("\n結果:")
            print(f"  racecard_base_url: {result['racecard_base_url']}")
            print(f"  start_date: {result['start_date']}")
            print(f"  end_date: {result['end_date']}")
            print(f"  event_name: {result['event_name']}")
            print(f"  grade: {result['grade']}")

            # 期待グレードの検証
            if tc.get("expected_grade"):
                if result["grade"] == tc["expected_grade"]:
                    print(f"\n  [OK] グレード一致: {tc['expected_grade']}")
                else:
                    print(
                        f"\n  [WARN] グレード不一致: "
                        f"期待={tc['expected_grade']}, 実際={result['grade']}"
                    )

        except EventNotFoundError as e:
            print(f"\n[ERROR] 開催が見つかりません: {e}")
            if e.candidates:
                print("候補一覧:")
                for c in e.candidates:
                    print(f"  - {c['event_name']} ({c['start_date']} ~ {c['end_date']})")

        except Exception as e:
            print(f"\n[ERROR] 予期しないエラー: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("テスト完了")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
