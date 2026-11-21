"""wordfilter —— 敏感词/关键词 DFA 过滤库。"""
from .core import DEFAULT_IGNORE, Match, WordFilter, snippet

__version__ = "0.1.0"

__all__ = ["DEFAULT_IGNORE", "Match", "WordFilter", "snippet", "__version__"]
