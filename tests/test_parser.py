"""
test_parser.py - parser.py のユニットテスト
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.parser import (
    GRADE_MAP,
    _normalize_text,
    _safe_float,
    _safe_int,
    parse_race_entry,
    parse_race_list,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


class TestNormalizeText:
    def test_removes_extra_whitespace(self):
        assert _normalize_text("  郡司  浩平  ") == "郡司 浩平"

    def test_nfkc_fullwidth(self):
        assert _normalize_text("ＳＳ") == "SS"


class TestSafeInt:
    def test_basic(self):
        assert _safe_int("99") == 99

    def test_with_garbage(self):
        assert _safe_int("期別: 99") == 99

    def test_empty(self):
        assert _safe_int("", default=0) == 0

    def test_non_numeric(self):
        assert _safe_int("abc", default=-1) == -1


class TestSafeFloat:
    def test_basic(self):
        assert _safe_float("119.50") == 119.50

    def test_with_units(self):
        assert _safe_float("3.92倍") == pytest.approx(3.92)

    def test_empty(self):
        assert _safe_float("") == 0.0


class TestGradeMap:
    def test_fullwidth_g1(self):
        assert GRADE_MAP.get("Ｇ１") == "GI"

    def test_grandprix(self):
        assert GRADE_MAP.get("グランプリ") == "GP"

    def test_f2(self):
        assert GRADE_MAP.get("Ｆ２") == "FII"


class TestParseRaceEntry:
    def test_returns_dict_with_required_keys(self):
        html = load_fixture("sample_raceentry.html")
        result = parse_race_entry(html, "35", 11, "20260329")
        assert "raceInfo" in result
        assert "entries" in result
        assert "lineUp" in result

    def test_race_info_fields(self):
        html = load_fixture("sample_raceentry.html")
        result = parse_race_entry(html, "35", 11, "20260329")
        info = result["raceInfo"]
        assert info["venueCode"] == "35"
        assert info["raceNumber"] == 11
        assert info["date"] == "2026-03-29"

    def test_extracts_9_entries(self):
        html = load_fixture("sample_raceentry.html")
        result = parse_race_entry(html, "35", 11, "20260329")
        assert len(result["entries"]) == 9

    def test_entry_car_numbers(self):
        html = load_fixture("sample_raceentry.html")
        result = parse_race_entry(html, "35", 11, "20260329")
        car_numbers = [e["carNumber"] for e in result["entries"]]
        assert sorted(car_numbers) == list(range(1, 10))

    def test_entry_has_name(self):
        html = load_fixture("sample_raceentry.html")
        result = parse_race_entry(html, "35", 11, "20260329")
        names = [e["name"] for e in result["entries"]]
        assert all(n for n in names), "全選手名が空でないこと"

    def test_lineup_comment_extracted(self):
        html = load_fixture("sample_raceentry.html")
        result = parse_race_entry(html, "35", 11, "20260329")
        assert "並び" in result["lineUp"]["comment"]

    def test_handles_empty_html_gracefully(self):
        result = parse_race_entry("<html></html>", "35", 11, "20260329")
        assert result["entries"] == []
        assert "no_entries_found" in result.get("parseWarnings", [])


class TestParseRaceList:
    def test_returns_venues(self):
        html = load_fixture("sample_racetop.html")
        venues = parse_race_list(html)
        assert len(venues) >= 2

    def test_venue_codes(self):
        html = load_fixture("sample_racetop.html")
        venues = parse_race_list(html)
        codes = {v["venueCode"] for v in venues}
        assert "35" in codes
        assert "38" in codes

    def test_race_numbers(self):
        html = load_fixture("sample_racetop.html")
        venues = parse_race_list(html)
        venue_35 = next(v for v in venues if v["venueCode"] == "35")
        assert 11 in venue_35["raceNumbers"]
        assert 1 in venue_35["raceNumbers"]

    def test_empty_html(self):
        venues = parse_race_list("<html></html>")
        assert venues == []
