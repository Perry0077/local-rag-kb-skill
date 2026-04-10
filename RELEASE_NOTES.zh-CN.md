# local-rag-kb-skill 发布文案

仓库：

- [https://github.com/Perry0077/local-rag-kb-skill](https://github.com/Perry0077/local-rag-kb-skill)

建议 Release 标题：

- `local-rag-kb-skill v0.1.0`

## Release 简介

`local-rag-kb-skill` 是一个面向 OpenClaw、Codex、Claude Code 的通用本地知识库 RAG skill。它支持从 markdown、txt、zip、tar、tar.gz、tgz 导入内容，使用本地 ChromaDB 存储向量，并通过宿主编排层生成带引用的回答。

这个版本重点补齐了 OpenClaw 的安装与编排路径：

- 支持 OpenClaw 目标产物构建与打包
- OpenClaw 安装态下可正确 bootstrap 本地 `.venv`
- OpenClaw 产物默认写入 `LOCAL_RAG_KB_HOST=openclaw`
- 查询时输出 host bundle，由宿主主模型生成最终回答
- 提供面向 OpenClaw 用户的安装、配置、导入、查询提示词

## 核心能力

- 支持 `.md`、`.txt`、`.zip`、`.tar`、`.tar.gz`、`.tgz`
- 默认追加到 `default` 知识库
- 支持增量导入、去重、变更重建
- 检索策略包含 chunk 检索、文档 regroup、扩窗、短文全文
- 默认输出答案和引用，不展示调试噪声
- 支持 OpenClaw、Codex、Claude Code 三套打包产物

## Release 附件

建议上传这些附件：

- `local-rag-kb-openclaw.zip`
- `local-rag-kb-codex.zip`
- `local-rag-kb-claude-code.zip`

其中，OpenClaw 用户优先下载：

- `local-rag-kb-openclaw.zip`

## OpenClaw 用户说明

OpenClaw 推荐路径：

1. 下载 `local-rag-kb-openclaw.zip`
2. 安装到 `~/.agents/skills/local-rag-kb`
3. 复制 `.env.example` 为 `.env`
4. 配置 `EMBEDDING_API_KEY`
5. 运行 `python3 scripts/kb_bootstrap.py`
6. 之后由宿主优先使用 `.venv/bin/python`

详细说明见：

- [OPENCLAW.zh-CN.md](OPENCLAW.zh-CN.md)

## 已验证内容

已完成本地验证：

- 构建三套宿主产物
- OpenClaw 安装态 ingest/query smoke test
- `kb_bootstrap.py` 在构建产物中可正确工作
- host bundle 查询输出正常
- 单元测试通过

## 当前限制

- v1 只支持 markdown 和 txt 文档
- embedding 需要 OpenAI-compatible API key
- 如果宿主拿不到附件本地路径，无法直接导入聊天附件
- 目前默认 citation 是文档级，不是句级

## 建议发布说明

```text
local-rag-kb-skill v0.1.0

A reusable local RAG skill for OpenClaw, Codex, and Claude Code.

Highlights:
- build a local knowledge base from .md, .txt, .zip, .tar, .tar.gz, .tgz
- incremental ingestion with document registry + ChromaDB
- host-orchestrated answering with references
- improved OpenClaw installation flow and .venv bootstrap behavior

Recommended assets:
- local-rag-kb-openclaw.zip
- local-rag-kb-codex.zip
- local-rag-kb-claude-code.zip
```
