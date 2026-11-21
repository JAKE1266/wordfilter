# wordfilter

零依赖的敏感词 / 关键词 DFA 过滤库 —— 适用于聊天审核、评论过滤、内容质检等场景。

- **变体识别**：全角↔半角、大小写、零宽字符、插分隔符（`敏.感.词` / `敏 感 词` / `敏*感*词`）都能命中
- **最长优先**：词库同时有「敏感」「敏感词」时，命中更长的那个
- **精确还原**：命中区间映射回**原文**下标，打码不偏移
- **两种模式**：`find_all` 默认互不重叠（打码用）；`overlap=True` 逐一报告嵌套命中（审计用）
- **DFA 字典树**：一次扫描完成匹配，词库构建后匹配 O(文本长度)

零第三方依赖，Python ≥ 3.8。

## 安装

```bash
pip install .
```

## 作为库使用

```python
from wordfilter import WordFilter

wf = WordFilter(["敏感词", "违禁品", " spam "])

wf.contains("这里有个敏感词")            # True
wf.contains("buy SPAM now")             # True —— 大小写 + 词表空格被归一化
wf.contains("敏.感.词")                 # True —— 拆词符被忽略

m = wf.find_all("这里有个敏感词")[0]
m.start, m.end, m.word                  # (4, 7, '敏感词')
text[4:7]                               # '敏感词' —— 精确还原原文区间

wf.mask("别买违禁品，也别当坏蛋。")       # '别买***，也别当**。'

# 审计模式：报告嵌套命中
audit = WordFilter(["敏感", "敏感词", "词库"])
[w.word for w in audit.find_all("敏感词库", overlap=True)]
# ['敏感', '敏感词', '词库']
```

## 管道工具

词表 `samples/words.txt`（一行一个词，`#` 注释）：

```console
$ echo "这里出现了敏感词，还有敏.感.词变体，但这句话是干净的。" | python -m wordfilter check --words samples/words.txt
命中 2 处：
  [5:8) 敏感词  …这里出现了敏感词，还有敏.感…
  [11:16) 敏感词  …敏感词，还有敏.感.词变体，但这句…
(exit code 1，命中即非零，方便接入 CI 或脚本)

$ echo "这里出现了敏感词，还有敏.感.词变体，但这句话是干净的。" | python -m wordfilter mask --words samples/words.txt
这里出现了***，还有*****变体，但这句话是干净的。
```

`--no-ignore` 关闭拆词符容忍；`mask --char #` 自定义打码字符。

## 设计取舍

- **逐字符 NFKC + 位置映射**：不整串归一化（NFKC 可能改变长度），而是逐字符展开并记录
  `归一化位置 → 原文区间`，命中后能精确切回原文
- **掩码整段覆盖**：命中区间连分隔符一起打码（`敏.感.词 → *****`），不给复原留线索；区间长度始终等于原文长度
- **默认忽略集可配置**：`WordFilter(..., ignore="")` 一键关闭全部变体容忍，做严格字面匹配
- **零依赖**：`pip install wordfilter` 不拉任何包

## 运行测试

```bash
python -m unittest discover -s tests
# Ran 21 tests ... OK
```

## License

MIT
