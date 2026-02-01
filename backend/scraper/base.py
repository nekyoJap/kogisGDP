"""
共通HTTPクライアント
"""

import logging
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .exceptions import NetworkError

logger = logging.getLogger(__name__)


class BaseClient:
    """HTTPリクエストの共通クライアント"""

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRY_COUNT = 2
    DEFAULT_RETRY_DELAY = 1.0

    def __init__(
        self,
        user_agent: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        retry_count: int = DEFAULT_RETRY_COUNT,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or self.DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        })
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay

    def get(self, url: str) -> requests.Response:
        """
        GETリクエストを送信（リトライ付き）

        Args:
            url: リクエスト先URL

        Returns:
            Response オブジェクト

        Raises:
            NetworkError: リクエスト失敗時
        """
        last_error = None

        for attempt in range(self.retry_count + 1):
            try:
                logger.debug(f"GET {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response

            except requests.exceptions.HTTPError as e:
                # 4xx エラーはリトライしない
                if e.response is not None and 400 <= e.response.status_code < 500:
                    raise NetworkError(f"HTTPエラー: {e.response.status_code} - {url}") from e
                last_error = e

            except requests.exceptions.RequestException as e:
                last_error = e

            if attempt < self.retry_count:
                time.sleep(self.retry_delay * (attempt + 1))

        raise NetworkError(f"リクエスト失敗: {url}") from last_error

    def get_soup(self, url: str, parser: str = "lxml") -> BeautifulSoup:
        """
        URLからBeautifulSoupオブジェクトを取得

        Args:
            url: リクエスト先URL
            parser: パーサー（デフォルト: lxml）

        Returns:
            BeautifulSoup オブジェクト
        """
        response = self.get(url)
        return BeautifulSoup(response.content, parser)

    def close(self):
        """セッションを閉じる"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
