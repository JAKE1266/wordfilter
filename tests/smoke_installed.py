import os
import subprocess
import sys
import tempfile
from importlib.metadata import distribution
from pathlib import Path

import wordfilter
from wordfilter import WordFilter

ROOT = Path(__file__).resolve().parents[1]


def run_cli(console, args, payload, cwd, expect=0):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"
    env.pop("PYTHONUTF8", None)
    result = subprocess.run(
        [str(console), *args], input=payload.encode("utf-8"),
        capture_output=True, cwd=cwd, env=env,
    )
    stdout = result.stdout.decode("utf-8")
    stderr = result.stderr.decode("utf-8")
    if result.returncode != expect:
        raise RuntimeError(
            f"exit={result.returncode} (expect {expect})\nstdout={stdout}\nstderr={stderr}"
        )
    return stdout, stderr


def main():
    module_path = Path(wordfilter.__file__).resolve()
    if module_path == (ROOT / "wordfilter" / "__init__.py").resolve():
        raise RuntimeError(f"wordfilter 仍从源码目录导入：{module_path}")

    package = distribution("wordfilter-kit")
    if package.version != "0.1.1":
        raise RuntimeError(f"版本不符：{package.version}")

    scripts_dir = Path(sys.executable).parent
    console = scripts_dir / ("wordfilter.exe" if os.name == "nt" else "wordfilter")
    if not console.exists():
        raise RuntimeError(f"控制台脚本不存在：{console}")

    wf = WordFilter(["敏感词"])
    variants = ["敏　感词", "敏．感．词", "敏－感－词", "敏＊感＊词", "敏，感，词"]
    for text in variants:
        if not wf.contains(text) or wf.mask(text) != "*" * len(text):
            raise RuntimeError(f"全角拆词变体未命中：{text!r}")
    strict = WordFilter(["敏感词"], ignore="")
    if any(strict.contains(text) for text in variants):
        raise RuntimeError("--no-ignore 语义发生回归")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        words = work / "words.txt"
        words.write_text("敏感词\n", encoding="utf-8")
        text = "敏　感　词"

        version, _ = run_cli(console, ["--version"], "", work)
        if "wordfilter 0.1.1" not in version:
            raise RuntimeError(f"控制台脚本版本检查失败：{version!r}")

        stdout, stderr = run_cli(
            console, ["check", "--words", str(words)], text, work, expect=1,
        )
        if "命中 1 处" not in stderr or stdout:
            raise RuntimeError(f"UTF-8 管道检查异常：stdout={stdout!r}, stderr={stderr!r}")

        stdout, stderr = run_cli(
            console, ["mask", "--words", str(words)], text, work,
        )
        if stdout != "*****" or stderr:
            raise RuntimeError(f"UTF-8 打码异常：stdout={stdout!r}, stderr={stderr!r}")

        _, stderr = run_cli(
            console, ["check", "--no-ignore", "--words", str(words)], text, work,
        )
        if stderr:
            raise RuntimeError(f"--no-ignore 模式异常：{stderr!r}")

    print("Installed wheel smoke test passed")


if __name__ == "__main__":
    main()
