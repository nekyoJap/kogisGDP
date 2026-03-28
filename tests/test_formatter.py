"""
test_formatter.py - formatter.py のユニットテスト
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.formatter import _extract_json, _validate_bets, _validate_top3, validate_and_format

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture_text(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


class TestExtractJson:
    def test_plain_json(self):
        text = '{"race_id": "35_11", "prediction": {}}'
        result = _extract_json(text)
        assert result is not None
        assert result["race_id"] == "35_11"

    def test_json_with_codefence(self):
        text = '```json\n{"race_id": "35_11"}\n```'
        result = _extract_json(text)
        assert result is not None
        assert result["race_id"] == "35_11"

    def test_json_with_preamble(self):
        text = '以下がJSON予想です。\n{"race_id": "35_11"}'
        result = _extract_json(text)
        assert result is not None

    def test_invalid_json_returns_none(self):
        result = _extract_json("これはJSONではありません")
        assert result is None

    def test_empty_string_returns_none(self):
        result = _extract_json("")
        assert result is None


class TestValidateTop3:
    def test_valid_top3(self):
        assert _validate_top3([1, 6, 8]) == [1, 6, 8]

    def test_coerces_strings(self):
        assert _validate_top3(["2", "1", "5"]) == [2, 1, 5]

    def test_truncates_to_3(self):
        assert _validate_top3([1, 2, 3, 4, 5]) == [1, 2, 3]

    def test_removes_invalid_car_numbers(self):
        assert _validate_top3([0, 1, 10]) == [1]

    def test_empty_list(self):
        assert _validate_top3([]) == []

    def test_non_list_returns_empty(self):
        assert _validate_top3(None) == []


class TestValidateBets:
    def test_valid_sanrentan(self):
        bets = {"sanrentan": [[1, 6, 8], [1, 6, 9]], "wide": [[1, 6]]}
        result = _validate_bets(bets)
        assert len(result["sanrentan"]) == 2
        assert result["sanrentan"][0] == [1, 6, 8]

    def test_truncates_sanrentan_to_16(self):
        bets = {"sanrentan": [[1, 2, 3]] * 20, "wide": []}
        result = _validate_bets(bets)
        assert len(result["sanrentan"]) == 16

    def test_rejects_duplicate_car_in_combo(self):
        bets = {"sanrentan": [[1, 1, 3]], "wide": []}
        result = _validate_bets(bets)
        assert len(result["sanrentan"]) == 0

    def test_rejects_invalid_car_number(self):
        bets = {"sanrentan": [[0, 1, 2]], "wide": []}
        result = _validate_bets(bets)
        assert len(result["sanrentan"]) == 0

    def test_non_dict_returns_empty(self):
        result = _validate_bets(None)
        assert result == {"sanrentan": [], "wide": []}


class TestValidateAndFormat:
    def setup_method(self):
        self.race_meta = {
            "venue": "平塚",
            "grade": "GI",
            "raceNumber": 11,
        }

    def test_valid_fixture(self):
        raw_text = load_fixture_text("sample_prediction.json")
        result = validate_and_format(raw_text, self.race_meta, "35", 11)
        assert "error" not in result
        assert result["venue"] == "平塚"
        assert result["grade"] == "GI"
        assert result["race_number"] == 11
        assert len(result["prediction"]["top3"]) == 3
        assert len(result["prediction"]["recommended_bets"]["sanrentan"]) <= 16

    def test_confidence_clamped(self):
        raw = json.dumps({
            "race_id": "35_11",
            "prediction": {"confidence": 1.5, "top3": [1, 2, 3]}
        })
        result = validate_and_format(raw, self.race_meta, "35", 11)
        assert result["prediction"]["confidence"] == 1.0

    def test_missing_confidence_defaults_to_05(self):
        raw = json.dumps({"race_id": "35_11", "prediction": {"top3": [1, 2, 3]}})
        result = validate_and_format(raw, self.race_meta, "35", 11)
        assert result["prediction"]["confidence"] == 0.5

    def test_invalid_json_returns_error(self):
        result = validate_and_format("not json", self.race_meta, "35", 11)
        assert "error" in result
        assert result["error"] == "parse_failed"

    def test_generated_at_is_in_output(self):
        raw_text = load_fixture_text("sample_prediction.json")
        result = validate_and_format(raw_text, self.race_meta, "35", 11)
        assert "generated_at" in result
        # ISO8601 形式であること
        from datetime import datetime
        datetime.fromisoformat(result["generated_at"])

    def test_model_field(self):
        raw_text = load_fixture_text("sample_prediction.json")
        result = validate_and_format(raw_text, self.race_meta, "35", 11)
        assert result["model"] == "claude-haiku-4-5-20251001"
