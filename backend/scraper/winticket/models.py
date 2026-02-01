"""
WINTICKETスクレイパー用データモデル
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional


# 競輪場スラッグの定義
class VenueSlug:
    """競輪場のスラッグ（URLパス用識別子）"""

    # 北日本
    HAKODATE = "hakodate"           # 函館
    AOMORI = "aomori"               # 青森
    IWAKI_TAIRA = "iwakitaira"      # いわき平

    # 関東
    MITO = "mito"                   # 水戸
    TORIDE = "toride"               # 取手
    UTSUNOMIYA = "utsunomiya"       # 宇都宮
    OMIYA = "omiya"                 # 大宮
    NISHITOKYO = "nishitokyo"       # 西武園
    KEIOKAKU = "keiokaku"           # 京王閣
    TACHIKAWA = "tachikawa"         # 立川

    # 南関東
    MATSUDO = "matsudo"             # 松戸
    CHIBA = "chiba"                 # 千葉
    KAWASAKI = "kawasaki"           # 川崎
    HIRATSUKA = "hiratsuka"         # 平塚
    ODAWARA = "odawara"             # 小田原
    IZU = "izu"                     # 伊豆（修善寺）

    # 中部
    SHIZUOKA = "shizuoka"           # 静岡
    HAMAMATSU = "hamamatsu"         # 浜松（ジャンボ）
    NAGOYA = "nagoya"               # 名古屋
    GIFU = "gifu"                   # 岐阜
    TOYOHASHI = "toyohashi"         # 豊橋
    FUKUI = "fukui"                 # 福井

    # 近畿
    KISHIWADA = "kishiwada"         # 岸和田
    NARA = "nara"                   # 奈良（大和郡山）
    WAKAYAMA = "wakayama"           # 和歌山

    # 中国
    TAMANO = "tamano"               # 玉野
    HIROSHIMA = "hiroshima"         # 広島

    # 四国
    KOCHI = "kochi"                 # 高知
    MATSUYAMA = "matsuyama"         # 松山
    KOMATSUSHIMA = "komatsushima"   # 小松島

    # 九州
    KOKURA = "kokura"               # 小倉
    KURUME = "kurume"               # 久留米
    TAKEO = "takeo"                 # 武雄
    SASEBO = "sasebo"               # 佐世保
    BEPPU = "beppu"                 # 別府
    KUMAMOTO = "kumamoto"           # 熊本


@dataclass
class EventInfo:
    """開催イベント情報"""

    racecard_base_url: str      # レースカードのベースURL
    start_date: str             # 開催開始日 (YYYY-MM-DD)
    end_date: str               # 開催終了日 (YYYY-MM-DD)
    event_name: str             # 開催名称
    grade: Optional[str] = None # グレード (G1, G3, F1, F2など)
    href: Optional[str] = None  # 元のhref（デバッグ用）

    def to_dict(self) -> dict:
        """辞書形式で返す"""
        return {
            "racecard_base_url": self.racecard_base_url,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "event_name": self.event_name,
            "grade": self.grade,
        }
