"""命令行管道工具：

    cat text.txt | python -m wordfilter check --words words.txt   # 命中输出明细，exit 1
    cat text.txt | python -m wordfilter mask  --words words.txt   # 打码后输出到 stdout

词表文件：一行一个词，# 开头为注释。
"""
from __future__ import annotations

import argparse
import sys

from . import __version__
from .core import DEFAULT_IGNORE, WordFilter, snippet


def _configure_standard_streams() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def load_words(path: str) -> list[str]:
    out = []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line)
    return out


def main(argv: list[str] | None = None) -> int:
    _configure_standard_streams()
    ap = argparse.ArgumentParser(prog="wordfilter", description="敏感词 DFA 过滤管道工具")
    ap.add_argument("--version", action="version", version=f"wordfilter {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_common(sp):
        sp.add_argument("--words", required=True, help="词表文件（一行一个词，# 注释）")
        sp.add_argument("--no-ignore", action="store_true",
                        help="关闭分隔符容忍（默认容忍 敏.感.词 这类拆词写法）")

    sp = sub.add_parser("check", help="检查 stdin 是否命中，命中打印明细并以 1 退出")
    add_common(sp)
    sp = sub.add_parser("mask", help="把 stdin 中的命中打码后写到 stdout")
    add_common(sp)
    sp.add_argument("--char", default="*", help="打码字符（默认 *）")

    args = ap.parse_args(argv)
    try:
        words = load_words(args.words)
    except OSError as e:
        print(f"无法读取词表文件：{e.filename or e}", file=sys.stderr)
        return 2
    wf = WordFilter(words, ignore="" if args.no_ignore else DEFAULT_IGNORE)
    text = sys.stdin.read()

    if args.cmd == "check":
        matches = wf.find_all(text, overlap=True)
        if not matches:
            return 0
        print(f"命中 {len(matches)} 处：", file=sys.stderr)
        for m in matches:
            print(f"  [{m.start}:{m.end}) {m.word}  …{snippet(text, m)}…", file=sys.stderr)
        return 1
    sys.stdout.write(wf.mask(text, char=args.char))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
