"""
test_predict_integration.py - predict.py の統合テスト（Anthropic クライアントをモック）

実際の API 呼び出しは行わない。
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def make_mock_response(text: str) -> MagicMock:
    """Anthropic API のレスポンスをモックする"""
    content = MagicMock()
    content.text = text
    response = MagicMock()
    response.content = [content]
    return response


class TestPredictIntegration:
    """predict.py の統合テスト"""

    def setup_method(self):
        self.sample_prediction = (FIXTURES_DIR / "sample_prediction.json").read_text(encoding="utf-8")
        self.sample_raceentry = (FIXTURES_DIR / "sample_raceentry.html").read_text(encoding="utf-8")

    def _make_raw_dir(self, tmpdir: Path, date_str: str) -> Path:
        """テスト用の data/raw/{date}/ ディレクトリを作成する"""
        formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        raw_dir = tmpdir / "data" / "raw" / formatted
        raw_dir.mkdir(parents=True)

        # 出走表 JSON を作成（最小限）
        race_data = {
            "raceInfo": {
                "date": formatted,
                "venue": "平塚",
                "venueCode": "35",
                "raceNumber": 11,
                "raceName": "GI",
                "grade": "GI",
                "startTime": "16:30",
            },
            "entries": [
                {"frameNumber": i, "carNumber": i, "name": f"選手{i}", "prefecture": "神奈川",
                 "age": 30, "term": 99, "rank": "SS", "style": "逃", "gear": 3.92,
                 "score": 120.0, "winRate": 33.3, "top2Rate": 55.5, "top3Rate": 70.0}
                for i in range(1, 10)
            ],
            "lineUp": {"comment": "テスト並び予想"},
            "parseWarnings": [],
        }

        race_file = raw_dir / "35_11.json"
        race_file.write_text(json.dumps(race_data, ensure_ascii=False), encoding="utf-8")

        # index.json
        index = {
            "date": formatted,
            "scrapedAt": "2026-03-29T07:00:00+09:00",
            "totalRaces": 1,
            "races": [
                {
                    "venueCode": "35",
                    "venueName": "平塚",
                    "raceNumber": 11,
                    "grade": "GI",
                    "filename": "35_11.json",
                    "entryCount": 9,
                }
            ],
        }
        index_file = raw_dir / "index.json"
        index_file.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")

        return raw_dir

    def test_predict_date_creates_output_files(self):
        """predict_date() が予想JSONとsummary.jsonを生成すること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            date_str = "20260329"
            self._make_raw_dir(tmpdir, date_str)

            # パスをモンキーパッチ
            import scripts.predict as predict_module
            orig_data_dir = predict_module.DATA_DIR
            orig_docs_dir = predict_module.DOCS_PREDICTIONS_DIR

            predict_module.DATA_DIR = tmpdir / "data"
            predict_module.DOCS_PREDICTIONS_DIR = tmpdir / "docs" / "predictions"

            try:
                with patch("scripts.predict.anthropic.Anthropic") as mock_anthropic_cls:
                    mock_client = MagicMock()
                    mock_client.messages.create.return_value = make_mock_response(self.sample_prediction)
                    mock_anthropic_cls.return_value = mock_client

                    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
                        predict_module.predict_date(date_str)

                # 予想JSONが生成されたか確認
                out_dir = predict_module.DOCS_PREDICTIONS_DIR / "2026-03-29"
                assert (out_dir / "35_11.json").exists()
                assert (out_dir / "summary.json").exists()

                # 予想JSONの内容確認
                with open(out_dir / "35_11.json", encoding="utf-8") as f:
                    pred = json.load(f)
                assert pred["venue"] == "平塚"
                assert pred["race_number"] == 11
                assert "prediction" in pred

                # summary.json の内容確認
                with open(out_dir / "summary.json", encoding="utf-8") as f:
                    summary = json.load(f)
                assert summary["totalRaces"] == 1
                assert len(summary["venues"]) == 1

            finally:
                predict_module.DATA_DIR = orig_data_dir
                predict_module.DOCS_PREDICTIONS_DIR = orig_docs_dir

    def test_predict_date_creates_error_sentinel_on_api_failure(self):
        """API エラー時にエラーセンチネルファイルが作成されること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            date_str = "20260329"
            self._make_raw_dir(tmpdir, date_str)

            import scripts.predict as predict_module
            orig_data_dir = predict_module.DATA_DIR
            orig_docs_dir = predict_module.DOCS_PREDICTIONS_DIR

            predict_module.DATA_DIR = tmpdir / "data"
            predict_module.DOCS_PREDICTIONS_DIR = tmpdir / "docs" / "predictions"

            try:
                with patch("scripts.predict.anthropic.Anthropic") as mock_anthropic_cls:
                    mock_client = MagicMock()
                    mock_client.messages.create.side_effect = RuntimeError("API障害テスト")
                    mock_anthropic_cls.return_value = mock_client

                    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
                        predict_module.predict_date(date_str)

                out_dir = predict_module.DOCS_PREDICTIONS_DIR / "2026-03-29"
                # エラーセンチネルが作成されること
                assert (out_dir / "35_11.error.json").exists()
                # summary.json は作成されること（0件）
                assert (out_dir / "summary.json").exists()

            finally:
                predict_module.DATA_DIR = orig_data_dir
                predict_module.DOCS_PREDICTIONS_DIR = orig_docs_dir

    def test_predict_date_handles_invalid_json_response(self):
        """Claude が不正な JSON を返した場合も継続すること"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            date_str = "20260329"
            self._make_raw_dir(tmpdir, date_str)

            import scripts.predict as predict_module
            orig_data_dir = predict_module.DATA_DIR
            orig_docs_dir = predict_module.DOCS_PREDICTIONS_DIR

            predict_module.DATA_DIR = tmpdir / "data"
            predict_module.DOCS_PREDICTIONS_DIR = tmpdir / "docs" / "predictions"

            try:
                with patch("scripts.predict.anthropic.Anthropic") as mock_anthropic_cls:
                    mock_client = MagicMock()
                    mock_client.messages.create.return_value = make_mock_response("申し訳ありませんが予想できません。")
                    mock_anthropic_cls.return_value = mock_client

                    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
                        predict_module.predict_date(date_str)

                out_dir = predict_module.DOCS_PREDICTIONS_DIR / "2026-03-29"
                # error フィールド付き JSON が作成されること（parse_failed）
                pred_file = out_dir / "35_11.json"
                if pred_file.exists():
                    with open(pred_file, encoding="utf-8") as f:
                        pred = json.load(f)
                    assert "error" in pred

            finally:
                predict_module.DATA_DIR = orig_data_dir
                predict_module.DOCS_PREDICTIONS_DIR = orig_docs_dir
