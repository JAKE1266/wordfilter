"""DFA 词库与匹配核心。

思路：
1. 归一化：逐字符做 NFKC + 小写，丢弃「可忽略字符」（零宽字符、常见分隔符），
   同时记录 归一化位置 → 原文位置 的映射，命中后能精确还原原文区间。
2. Trie（字典树）匹配：文本向前走，每个位置取最长命中。
3. ``find_all`` 报告所有命中；``overlap=True`` 逐一报告每个起点的命中（审计用）。
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass

# 默认忽略：零宽字符 + 常见的「插在词里」的分隔符
DEFAULT_IGNORE = "".join(["\u200b", "\u200c", "\u200d", "\ufeff",
                          "\u00b7", "\u2022", "\u30fb", " ", ".", "*", "-", "_", ","])

_END = "$"


@dataclass(frozen=True)
class Match:
    """一次命中：原文区间 [start, end) 与命中的词（归一化形式）。"""

    start: int
    end: int
    word: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"Match(start={self.start}, end={self.end}, word={self.word!r})"


def snippet(text: str, m: Match, ctx: int = 6) -> str:
    """命中点的原文片段（前后各 ``ctx`` 个字符），便于日志展示。"""
    lo, hi = max(0, m.start - ctx), min(len(text), m.end + ctx)
    return text[lo:hi]


class _Node(dict):
    """Trie 节点：键是下一个字符（或 ``$`` 表示词尾）。"""

    __slots__ = ()


class WordFilter:
    """敏感词/关键词过滤器。

    Parameters
    ----------
    words:
        初始词表（可迭代字符串）。
    ignore:
        匹配时无视的字符集合（出现在词中间也会跳过）。传空串关闭；
        默认忽略零宽字符、空格、点、星号、连字符、逗号等常见「拆词符」。
    """

    def __init__(self, words=(), ignore: str = DEFAULT_IGNORE):
        self._root: _Node = _Node()
        self._count = 0
        self.ignore = ignore
        self.add_words(words)

    # ---------- 词库维护 ----------
    def add(self, word: str) -> None:
        """加入一个词（自动归一化；空词忽略）。"""
        word = self._normalize_word(word)
        if not word:
            return
        node = self._root
        for ch in word:
            node = node.setdefault(ch, _Node())
        if _END not in node:
            self._count += 1
        node[_END] = True

    def add_words(self, words) -> None:
        for w in words:
            self.add(w)

    def __len__(self) -> int:
        return self._count

    def __contains__(self, text: str) -> bool:
        return next(self._iter_matches(text, first_only=True), None) is not None

    # ---------- 归一化 ----------
    def _normalize_word(self, word: str) -> str:
        out = []
        for ch in word:
            if ch in self.ignore:
                continue
            piece = unicodedata.normalize("NFKC", ch).lower()
            out.extend(out_ch for out_ch in piece if out_ch not in self.ignore)
        return "".join(out)

    def _normalize_text(self, text: str):
        """返回 (归一化串, 映射表)；映射表[i] = 原文中该归一化字符的区间 (start, end)。"""
        norm: list[str] = []
        spans: list[tuple[int, int]] = []
        for i, ch in enumerate(text):
            if ch in self.ignore:
                continue
            piece = unicodedata.normalize("NFKC", ch).lower()
            for out_ch in piece:
                if out_ch in self.ignore:
                    continue
                norm.append(out_ch)
                spans.append((i, i + 1))
        return "".join(norm), spans

    # ---------- 匹配 ----------
    def _iter_matches(self, text: str, first_only: bool = False):
        """最长优先、互不重叠的命中流。"""
        norm, spans = self._normalize_text(text)
        n = len(norm)
        i = 0
        while i < n:
            node = self._root
            j = i
            last = None
            while j < n and norm[j] in node:
                node = node[norm[j]]
                j += 1
                if _END in node:
                    last = (j, norm[i:j])
            if last:
                end_norm, word = last
                yield Match(spans[i][0], spans[end_norm - 1][1], word)
                if first_only:
                    return
                i = end_norm
            else:
                i += 1

    def contains(self, text: str) -> bool:
        """是否存在命中。"""
        return text in self

    def find_all(self, text: str, overlap: bool = False) -> list[Match]:
        """返回全部命中。

        默认按「最长优先、互不重叠」返回（打码场景）；
        ``overlap=True`` 时从每个起点逐一报告命中（审计复查用）。
        """
        if not overlap:
            return list(self._iter_matches(text))
        norm, spans = self._normalize_text(text)
        out: list[Match] = []
        for i in range(len(norm)):
            node, j = self._root, i
            while j < len(norm) and norm[j] in node:
                node = node[norm[j]]
                j += 1
                if _END in node:  # 每个词尾前缀都报告（如「敏感」「敏感词」都算命中）
                    out.append(Match(spans[i][0], spans[j - 1][1], norm[i:j]))
        return out

    def mask(self, text: str, char: str = "*") -> str:
        """把命中替换为等宽的 ``char``，返回新文本。"""
        chars = list(text)
        for m in self.find_all(text):
            for k in range(m.start, m.end):
                chars[k] = char
        return "".join(chars)
