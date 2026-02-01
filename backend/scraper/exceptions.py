"""
スクレイパー用カスタム例外
"""


class ScraperError(Exception):
    """スクレイパーの基底例外"""
    pass


class NetworkError(ScraperError):
    """ネットワーク関連のエラー"""
    pass


class EventNotFoundError(ScraperError):
    """開催イベントが見つからない場合のエラー"""

    def __init__(self, message: str, candidates: list | None = None):
        super().__init__(message)
        self.candidates = candidates or []
