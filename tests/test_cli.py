import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

WORDS_FILE = ROOT / "samples" / "words.txt"
TEXT = "这里出现了敏感词，还有敏.感.词变体，但这句话是干净的。"


def run_pipe(cmd, text, *extra, expect=0):
    r = subprocess.run([PY, "-m", "wordfilter", cmd, *extra],
                       input=text, capture_output=True, text=True,
                       encoding="utf-8")
    if r.returncode != expect:
        raise AssertionError(f"exit={r.returncode} (expect {expect})\n"
                             f"stdout={r.stdout}\nstderr={r.stderr}")
    return r


class TestCli(unittest.TestCase):
    def test_check_clean_exit0(self):
        r = run_pipe("check", "完全干净的一句话", "--words", str(WORDS_FILE))
        self.assertEqual(r.stdout, "")

    def test_check_hit_exit1(self):
        r = run_pipe("check", TEXT, "--words", str(WORDS_FILE), expect=1)
        self.assertIn("命中", r.stderr)
        self.assertIn("敏感词", r.stderr)

    def test_mask_output(self):
        r = run_pipe("mask", TEXT, "--words", str(WORDS_FILE))
        self.assertNotIn("敏感词", r.stdout)
        self.assertIn("***", r.stdout)
        self.assertIn("这句话是干净的", r.stdout)

    def test_utf8_bytes_pipe_under_legacy_windows_encoding(self):
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "cp1252"
        env.pop("PYTHONUTF8", None)
        for cmd, expected in (("check", 1), ("mask", 0)):
            with self.subTest(cmd=cmd):
                r = subprocess.run(
                    [PY, "-m", "wordfilter", cmd, "--words", str(WORDS_FILE)],
                    input=TEXT.encode("utf-8"), capture_output=True, env=env,
                )
                self.assertEqual(r.returncode, expected)
                stdout = r.stdout.decode("utf-8")
                stderr = r.stderr.decode("utf-8")
                self.assertNotIn("Traceback", stderr)
                if cmd == "check":
                    self.assertIn("命中 2 处", stderr)
                    self.assertEqual(stdout, "")
                else:
                    self.assertEqual(stdout, "这里出现了***，还有*****变体，但这句话是干净的。")
                    self.assertEqual(len(stdout), len(TEXT))

    def test_missing_words_file(self):
        r = run_pipe("mask", TEXT, "--words", "nope.txt", expect=2)
        self.assertIn("无法读取词表文件", r.stderr)


if __name__ == "__main__":
    unittest.main()
