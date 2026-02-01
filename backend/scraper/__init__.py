"""
kogisGDP スクレイパーモジュール

競輪関連サイトからデータを取得するスクレイパー
"""

from .exceptions import ScraperError, EventNotFoundError, NetworkError
from .base import BaseClient

__all__ = [
    "ScraperError",
    "EventNotFoundError",
    "NetworkError",
    "BaseClient",
]
