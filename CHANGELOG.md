# 更新日志

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式,
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.1] - 2026-11-26

### 修复
- CLI 的 stdin/stdout/stderr 显式使用 UTF-8，Windows 旧编码下不再误读或崩溃
- NFKC 归一化后再过滤忽略字符，全角空格、全角标点等兼容拆词写法不再漏检
- `--no-ignore` 严格字面匹配保持不变

### 变更
- 发行包名改为 `wordfilter-kit`，避免与 PyPI 同名英文项目冲突；import 与 CLI 名称不变
- CI 固定 Ubuntu 22.04，覆盖三系统 Python 3.8/3.9/3.11/3.13，并安装真实 wheel 后运行冒烟与测试
- 单元测试增至 24 个，sdist 包含冒烟脚本、更新日志与示例词表

## [0.1.0] - 2026-11-21

### 新增
- 核心功能实现(纯标准库,零第三方依赖)
- CLI 命令行入口
- 21 个单元测试
- GitHub Actions 三系统 × 多版本 CI
- 中文 README 与 MIT 许可证

### 变更
- 补齐徽章、项目结构与本日志,与其他仓库文档标准统一
