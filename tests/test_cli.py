import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

WORDS_FILE = ROOT / "samples" / "words.txt"
TEXT = "这里出现了敏感词，还有敏.感.词变体，但这句话是干净的。"


def run_pipe(cmd, text, *extra, expect=0):
    r = subprocess.run([PY, "-m", "wordfilter", cmd, *extra],
                       input=text, capture_output=True, text=True,
                       encoding="utf-8", cwd=ROOT)
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

    def test_missing_words_file(self):
        r = run_pipe("mask", TEXT, "--words", "nope.txt", expect=2)
        self.assertIn("无法读取词表文件", r.stderr)


if __name__ == "__main__":
    unittest.main()
