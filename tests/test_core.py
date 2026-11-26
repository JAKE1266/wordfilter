import unittest

from wordfilter.core import DEFAULT_IGNORE, Match, WordFilter, snippet

WORDS = ["敏感词", "违禁品", "坏蛋", " spam "]


class TestBasic(unittest.TestCase):
    def setUp(self):
        self.wf = WordFilter(WORDS)

    def test_len_and_add_dedup(self):
        self.assertEqual(len(self.wf), 4)
        self.wf.add("敏感词")  # 重复添加不计数
        self.assertEqual(len(self.wf), 4)
        self.wf.add("")        # 空词忽略
        self.assertEqual(len(self.wf), 4)

    def test_contains(self):
        self.assertTrue(self.wf.contains("这里有个敏感词请处理"))
        self.assertFalse(self.wf.contains("完全干净的内容"))

    def test_find_all_positions(self):
        text = "这里有个敏感词请处理"
        m = self.wf.find_all(text)[0]
        self.assertEqual((m.start, m.end), (4, 7))
        self.assertEqual(text[m.start:m.end], "敏感词")

    def test_longest_match_wins(self):
        wf = WordFilter(["敏感", "敏感词"])
        text = "包含敏感词的一句话"
        self.assertEqual([m.word for m in wf.find_all(text)], ["敏感词"])
        # 仅有前缀时也命中
        self.assertEqual([m.word for m in wf.find_all("这是敏感话题")], ["敏感"])
        self.assertEqual(wf.find_all("这是敏感话题")[0].end, 4)

    def test_mask(self):
        text = "别买违禁品，也别当坏蛋。"
        out = self.wf.mask(text)
        self.assertEqual(out, "别买***，也别当**。")
        self.assertEqual(len(out), len(text))

    def test_mask_custom_char(self):
        self.assertEqual(self.wf.mask("违禁品", char="#"), "###")

    def test_word_with_spaces_normalized(self):
        # 词表里的 " spam " 归一化为 "spam"
        self.assertTrue(self.wf.contains("buy SPAM now"))
        m = self.wf.find_all("buy spam now")[0]
        self.assertEqual((m.start, m.end), (4, 8))


class TestVariants(unittest.TestCase):
    def setUp(self):
        self.wf = WordFilter(["敏感词"])

    def test_separators_tolerated(self):
        for text in ["敏.感.词", "敏 感 词", "敏-感-词", "敏_感_词", "敏·感·词"]:
            self.assertTrue(self.wf.contains(text), text)
            # 掩码按命中区间整段覆盖（包括夹在词里的分隔符），长度不变
            self.assertEqual(self.wf.mask(text), "*" * len(text))
            self.assertEqual(self.wf.mask("敏感词"), "***")

    def test_zero_width_chars(self):
        text = "敏\u200b感\u200c词"
        self.assertTrue(self.wf.contains(text))

    def test_fullwidth_separators_normalized_before_ignore(self):
        variants = ["敏　感词", "敏．感．词", "敏－感－词", "敏＊感＊词", "敏，感，词"]
        strict = WordFilter(["敏感词"], ignore="")
        for text in variants:
            with self.subTest(text=text):
                self.assertTrue(self.wf.contains(text))
                self.assertEqual(self.wf.mask(text), "*" * len(text))
                self.assertFalse(strict.contains(text))

    def test_custom_ignore_character_is_still_supported(self):
        wf = WordFilter(["敏感词"], ignore="　")
        self.assertTrue(wf.contains("敏　感词"))
        self.assertEqual(wf.mask("敏　感词"), "****")

    def test_fullwidth_and_case(self):
        wf = WordFilter(["badword"])
        self.assertTrue(wf.contains("ＢＡＤＷＯＲＤ"))
        self.assertTrue(wf.contains("BadWord"))
        m = wf.find_all("xxＢＡＤＷＯＲＤyy")[0]
        self.assertEqual((m.start, m.end), (2, 9))  # 映射回原文区间（7 个全角字符）

    def test_no_ignore_mode(self):
        wf = WordFilter(["敏感词"], ignore="")
        self.assertFalse(wf.contains("敏.感.词"))
        self.assertTrue(wf.contains("敏感词"))


class TestOverlapAudit(unittest.TestCase):
    def test_overlap_mode_reports_nested(self):
        wf = WordFilter(["敏感", "敏感词", "词库"])
        text = "敏感词库"
        # 贪婪模式：只有一个互不重叠命中
        self.assertEqual([m.word for m in wf.find_all(text)], ["敏感词"])
        # 审计模式：报告起点 0 的 "敏感"/"敏感词" 与起点 2 的 "词库"
        words = [m.word for m in wf.find_all(text, overlap=True)]
        self.assertEqual(words, ["敏感", "敏感词", "词库"])

    def test_adjacent_hits_both_found(self):
        wf = WordFilter(["坏蛋", "坏"])
        text = "坏蛋坏蛋"
        self.assertEqual([m.word for m in wf.find_all(text)], ["坏蛋", "坏蛋"])


class TestHelpers(unittest.TestCase):
    def test_snippet(self):
        wf = WordFilter(["违禁品"])
        text = "前面铺垫文字，然后出现违禁品这个词，后面还有内容"
        m = wf.find_all(text)[0]
        self.assertIn("违禁品", snippet(text, m, ctx=4))
        self.assertLessEqual(len(snippet(text, m, ctx=4)), len(text))

    def test_match_repr(self):
        r = repr(Match(1, 2, "x"))
        self.assertIn("start=1", r)

    def test_default_ignore_constant(self):
        self.assertIn(" ", DEFAULT_IGNORE)
        self.assertIn("\u200b", DEFAULT_IGNORE)

    def test_empty_text(self):
        wf = WordFilter(["x"])
        self.assertFalse(wf.contains(""))
        self.assertEqual(wf.find_all(""), [])
        self.assertEqual(wf.mask(""), "")


if __name__ == "__main__":
    unittest.main()
