"""
test_player_lookup.py - player_lookup.py のユニットテスト
"""

import csv
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.utils.player_lookup import (
    enrich_entry,
    load_player_db,
    lookup_player,
    normalize_name,
)


class TestNormalizeName:
    def test_fullwidth_space(self):
        assert normalize_name("郡司\u3000浩平") == "郡司浩平"

    def test_halfwidth_space(self):
        assert normalize_name("郡司 浩平") == "郡司浩平"

    def test_nfkc_fullwidth_alpha(self):
        # 全角英字は半角に変換
        assert normalize_name("ＳＳ") == "SS"

    def test_kanji_variant_high(self):
        assert normalize_name("髙橋") == "高橋"

    def test_kanji_variant_hama(self):
        assert normalize_name("濵田") == "浜田"

    def test_empty_string(self):
        assert normalize_name("") == ""

    def test_none_like_empty(self):
        assert normalize_name("") == ""


class TestLoadPlayerDb:
    def _make_csv(self, rows: list[dict]) -> str:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8-sig"
        )
        if rows:
            writer = csv.DictWriter(tmp, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        tmp.close()
        return tmp.name

    def test_loads_basic_csv(self):
        path = self._make_csv([
            {"選手名": "郡司 浩平", "級班": "SS", "先行意欲": "◎", "スピード": "A", "仕掛け": "A", "スタミナ": "B", "競輪IQ": "A", "コメント": "地元番長"}
        ])
        try:
            db = load_player_db(path)
            assert "郡司浩平" in db
            assert db["郡司浩平"]["先行意欲"] == "◎"
        finally:
            os.unlink(path)

    def test_handles_missing_file(self):
        db = load_player_db("/nonexistent/path.csv")
        assert db == {}

    def test_bom_handling(self):
        # utf-8-sig で書いたファイルを読めること
        path = self._make_csv([{"選手名": "脇本 雄太", "級班": "SS", "先行意欲": "◎", "スピード": "S", "仕掛け": "S", "スタミナ": "A", "競輪IQ": "A", "コメント": ""}])
        try:
            db = load_player_db(path)
            assert "脇本雄太" in db
        finally:
            os.unlink(path)


class TestLookupPlayer:
    def setup_method(self):
        self.db = {
            "郡司浩平": {"選手名": "郡司 浩平", "先行意欲": "◎"},
            "脇本雄太": {"選手名": "脇本 雄太", "先行意欲": "◎"},
        }

    def test_exact_match(self):
        result = lookup_player(self.db, "郡司浩平")
        assert result is not None
        assert result["先行意欲"] == "◎"

    def test_match_with_space(self):
        # スペースあり表記でもヒットする
        result = lookup_player(self.db, "郡司 浩平")
        assert result is not None

    def test_match_fullwidth_space(self):
        result = lookup_player(self.db, "郡司　浩平")
        assert result is not None

    def test_no_match_returns_none(self):
        result = lookup_player(self.db, "存在しない選手")
        assert result is None

    def test_empty_name(self):
        result = lookup_player(self.db, "")
        assert result is None

    def test_empty_db(self):
        result = lookup_player({}, "郡司浩平")
        assert result is None


class TestEnrichEntry:
    def setup_method(self):
        self.db = {
            "郡司浩平": {
                "選手名": "郡司 浩平",
                "先行意欲": "◎",
                "スピード": "S",
                "仕掛け": "A",
                "スタミナ": "A",
                "競輪IQ": "S",
                "番手経験": "◯",
                "タイプ１": "先行",
                "タイプ２": "",
                "コメント": "地元番長",
                "相性◯バンク": "平塚",
                "相性✕バンク": "",
            }
        }

    def test_enrich_found(self):
        entry = {"carNumber": 1, "name": "郡司 浩平"}
        result = enrich_entry(entry, self.db)
        assert result["evalFound"] is True
        assert result["leadWill"] == "◎"
        assert result["speed"] == "S"
        assert result["keirinIQ"] == "S"

    def test_enrich_not_found(self):
        entry = {"carNumber": 2, "name": "存在しない選手"}
        result = enrich_entry(entry, self.db)
        assert result["evalFound"] is False
        assert result["name"] == "存在しない選手"
        # 元のエントリーフィールドは保持される
        assert result["carNumber"] == 2
