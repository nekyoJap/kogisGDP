"""
WINTICKET 開催日程スクレイパー

指定した開催日と競輪場に一致するレースカードURLを取得する
"""

import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional, Union

from bs4 import BeautifulSoup

from ..base import BaseClient
from ..exceptions import EventNotFoundError, NetworkError
from .models import EventInfo

logger = logging.getLogger(__name__)

# 定数
BASE_URL = "https://www.winticket.jp"
SCHEDULE_URL_TEMPLATE = "{base}/keirin/{venue}/schedule/{yyyymm}"
RACECARD_PATH_PATTERN = re.compile(r"/keirin/([^/]+)/racecard/(\d+)")

# 日付パターン: "1月29日 〜 2月2日" or "12月30日 〜 1月3日"
DATE_RANGE_PATTERN = re.compile(
    r"(\d{1,2})月(\d{1,2})日\s*[〜~]\s*(\d{1,2})月(\d{1,2})日"
)

# グレードパターン: "G1", "G2", "G3", "F1", "F2" など
GRADE_PATTERN = re.compile(r"^(GP|G[1-3]|F[1-2])")


@dataclass
class _EventCandidate:
    """開催候補（内部用）"""
    href: str
    link_text: str
    start_date: date
    end_date: date
    event_name: str
    grade: Optional[str]


def _parse_date_range(
    text: str,
    reference_year: int
) -> tuple[Optional[date], Optional[date]]:
    """
    日付範囲テキストから開始日・終了日を抽出

    Args:
        text: "1月29日 〜 2月2日" のような文字列
        reference_year: 基準年（target_dateの年）

    Returns:
        (start_date, end_date) のタプル。パース失敗時は (None, None)
    """
    match = DATE_RANGE_PATTERN.search(text)
    if not match:
        return None, None

    start_month = int(match.group(1))
    start_day = int(match.group(2))
    end_month = int(match.group(3))
    end_day = int(match.group(4))

    # 年の補完
    start_year = reference_year
    end_year = reference_year

    # 年越し判定: 開始月が終了月より大きい場合
    if start_month > end_month:
        # 例: 12月30日 〜 1月3日
        # reference_yearが1月の場合: start=前年12月, end=当年1月
        # reference_yearが12月の場合: start=当年12月, end=翌年1月
        if reference_year and datetime(reference_year, 1, 1).month <= 6:
            # 前半の年（1-6月）の場合、開始は前年
            start_year = reference_year - 1
        else:
            # 後半の年（7-12月）の場合、終了は翌年
            end_year = reference_year + 1

    try:
        start_date = date(start_year, start_month, start_day)
        end_date = date(end_year, end_month, end_day)

        # 開始日が終了日より後ならば年越し補正
        if start_date > end_date:
            end_year += 1
            end_date = date(end_year, end_month, end_day)

        return start_date, end_date

    except ValueError:
        return None, None


def _extract_event_name(text: str) -> str:
    """
    リンクテキストから開催名称を抽出

    日付範囲を除去し、カテゴリラベル等も可能な限り除去
    """
    # 日付範囲を除去
    text = DATE_RANGE_PATTERN.sub("", text)
    # グレードを除去
    text = GRADE_PATTERN.sub("", text)
    # 前後の空白・改行を除去
    text = text.strip()
    # カテゴリラベル（末尾）を除去: 「ガールズ」「ミッドナイト」「モーニング」等
    # ただし開催名に含まれる場合もあるので、末尾のみ
    for suffix in ["ガールズ", "ミッドナイト", "モーニング", "ナイター"]:
        if text.endswith(suffix) and len(text) > len(suffix):
            text = text[:-len(suffix)].strip()
            break

    return text


def _extract_grade(text: str) -> Optional[str]:
    """リンクテキストからグレードを抽出"""
    match = GRADE_PATTERN.search(text)
    return match.group(1) if match else None


def _fetch_schedule_page(
    client: BaseClient,
    venue_slug: str,
    year: int,
    month: int
) -> list[_EventCandidate]:
    """
    指定年月のスケジュールページから開催候補を取得

    Args:
        client: HTTPクライアント
        venue_slug: 競輪場スラッグ
        year: 年
        month: 月

    Returns:
        開催候補のリスト
    """
    yyyymm = f"{year:04d}{month:02d}"
    url = SCHEDULE_URL_TEMPLATE.format(
        base=BASE_URL,
        venue=venue_slug,
        yyyymm=yyyymm
    )

    logger.info(f"スケジュールページを取得: {url}")

    try:
        soup = client.get_soup(url)
    except NetworkError as e:
        logger.warning(f"スケジュールページの取得に失敗: {e}")
        return []

    candidates = []

    # racecard リンクを抽出
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]

        # racecard パスを含むリンクのみ対象
        if f"/keirin/{venue_slug}/racecard/" not in href:
            continue

        link_text = a_tag.get_text(strip=True)

        # "〜" を含むもののみ（開催期間を示すリンク）
        if "〜" not in link_text and "~" not in link_text:
            continue

        # 日付範囲を抽出
        start_date, end_date = _parse_date_range(link_text, year)
        if not start_date or not end_date:
            logger.debug(f"日付パース失敗: {link_text}")
            continue

        # 開催名称を抽出
        event_name = _extract_event_name(link_text)

        # グレードを抽出
        grade = _extract_grade(link_text)

        candidate = _EventCandidate(
            href=href,
            link_text=link_text,
            start_date=start_date,
            end_date=end_date,
            event_name=event_name,
            grade=grade,
        )
        candidates.append(candidate)
        logger.debug(
            f"候補: {event_name} ({start_date} ~ {end_date}) "
            f"grade={grade} href={href}"
        )

    return candidates


def _select_best_candidate(
    candidates: list[_EventCandidate],
    target: date,
    title_keyword: Optional[str] = None,
    grade: Optional[str] = None,
) -> Optional[_EventCandidate]:
    """
    候補リストから最適な開催を選択

    Args:
        candidates: 開催候補リスト
        target: 対象日
        title_keyword: 開催名称キーワード（優先フィルタ）
        grade: グレード（優先フィルタ）

    Returns:
        選択された候補。見つからない場合はNone
    """
    if not candidates:
        return None

    # 1. target_date が開催期間内のものに絞り込み
    matching = [
        c for c in candidates
        if c.start_date <= target <= c.end_date
    ]

    if not matching:
        return None

    if len(matching) == 1:
        return matching[0]

    # 2. title_keyword でフィルタ
    if title_keyword:
        keyword_matches = [
            c for c in matching
            if title_keyword in c.event_name
        ]
        if len(keyword_matches) == 1:
            return keyword_matches[0]
        if keyword_matches:
            matching = keyword_matches

    # 3. grade でフィルタ
    if grade:
        grade_matches = [
            c for c in matching
            if c.grade and c.grade.upper() == grade.upper()
        ]
        if len(grade_matches) == 1:
            return grade_matches[0]
        if grade_matches:
            matching = grade_matches

    # 4. target_date に最も近い開催を選択（開始日・終了日からの距離）
    def distance(c: _EventCandidate) -> int:
        # 開始日と終了日からの距離の合計が小さいほど近い
        d_start = abs((target - c.start_date).days)
        d_end = abs((target - c.end_date).days)
        return d_start + d_end

    matching.sort(key=distance)
    return matching[0]


def get_racecard_url(
    target_date: Union[str, date, datetime],
    venue_slug: str,
    title_keyword: Optional[str] = None,
    grade: Optional[str] = None,
) -> Optional[dict]:
    """
    指定した開催日と競輪場に一致するレースカードURLを取得

    Args:
        target_date: 開催日（"YYYY-MM-DD" 形式の文字列、またはdate/datetimeオブジェクト）
        venue_slug: 競輪場スラッグ（例: "komatsushima"）
        title_keyword: 開催名称キーワード（複数候補がある場合の絞り込み用）
        grade: グレード（複数候補がある場合の絞り込み用、例: "G3"）

    Returns:
        dict: {
            "racecard_base_url": str,  # レースカードのベースURL
            "start_date": str,         # 開催開始日 (YYYY-MM-DD)
            "end_date": str,           # 開催終了日 (YYYY-MM-DD)
            "event_name": str,         # 開催名称
            "grade": str | None,       # グレード
        }
        該当開催が見つからない場合は EventNotFoundError を送出

    Raises:
        EventNotFoundError: 該当する開催が見つからない場合
        NetworkError: ネットワークエラー
    """
    # target_date を date オブジェクトに変換
    if isinstance(target_date, str):
        target = datetime.strptime(target_date, "%Y-%m-%d").date()
    elif isinstance(target_date, datetime):
        target = target_date.date()
    else:
        target = target_date

    logger.info(
        f"レースカードURL取得: venue={venue_slug}, "
        f"date={target}, keyword={title_keyword}, grade={grade}"
    )

    all_candidates: list[_EventCandidate] = []

    with BaseClient() as client:
        # 当月のスケジュールを取得
        candidates = _fetch_schedule_page(
            client, venue_slug, target.year, target.month
        )
        all_candidates.extend(candidates)

        # 該当候補を選択
        selected = _select_best_candidate(
            candidates, target, title_keyword, grade
        )

        # 見つからない場合、前月も確認（月初の年越し開催対応）
        if not selected and target.day <= 7:
            prev_month = target.replace(day=1) - timedelta(days=1)
            logger.info(f"前月のスケジュールも確認: {prev_month.year}/{prev_month.month}")

            prev_candidates = _fetch_schedule_page(
                client, venue_slug, prev_month.year, prev_month.month
            )
            all_candidates.extend(prev_candidates)

            selected = _select_best_candidate(
                prev_candidates, target, title_keyword, grade
            )

    if not selected:
        # 候補一覧をログ出力
        if all_candidates:
            logger.warning("候補一覧:")
            for c in all_candidates:
                logger.warning(
                    f"  - {c.event_name} ({c.start_date} ~ {c.end_date}) "
                    f"grade={c.grade}"
                )

        raise EventNotFoundError(
            f"該当する開催が見つかりません: "
            f"venue={venue_slug}, date={target}",
            candidates=[
                {
                    "event_name": c.event_name,
                    "start_date": c.start_date.isoformat(),
                    "end_date": c.end_date.isoformat(),
                    "grade": c.grade,
                }
                for c in all_candidates
            ]
        )

    # 結果を構築
    racecard_base_url = BASE_URL + selected.href
    result = EventInfo(
        racecard_base_url=racecard_base_url,
        start_date=selected.start_date.isoformat(),
        end_date=selected.end_date.isoformat(),
        event_name=selected.event_name,
        grade=selected.grade,
        href=selected.href,
    )

    logger.info(f"取得成功: {result.event_name} -> {racecard_base_url}")

    return result.to_dict()


# --- CLI実行用 ---
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # テスト実行: 小松島競輪 2026年1月31日
    # 期待: G3 玉藻杯争覇戦 in 小松島 (1/29 ~ 2/2)
    test_date = "2026-01-31"
    test_venue = "komatsushima"

    print(f"\n{'='*60}")
    print(f"テスト実行: {test_venue} / {test_date}")
    print(f"{'='*60}\n")

    try:
        result = get_racecard_url(test_date, test_venue)
        print("結果:")
        for key, value in result.items():
            print(f"  {key}: {value}")

        # 期待される出力例:
        # racecard_base_url: https://www.winticket.jp/keirin/komatsushima/racecard/2026012973
        # start_date: 2026-01-29
        # end_date: 2026-02-02
        # event_name: 玉藻杯争覇戦in小松島
        # grade: G3

    except EventNotFoundError as e:
        print(f"エラー: {e}")
        if e.candidates:
            print("候補:")
            for c in e.candidates:
                print(f"  - {c}")
        sys.exit(1)

    except Exception as e:
        print(f"予期しないエラー: {e}")
        sys.exit(1)
