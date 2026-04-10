# local-rag-kb-skill

一个面向 Codex、OpenClaw、Claude Code 的通用本地 RAG skill 项目。

它可以从单文件或压缩包中导入 Markdown / 文本资料，写入本地 ChromaDB，维护增量更新注册表，并产出带引用的检索上下文或最终回答。

English README: [README.md](README.md)

## 功能

- 支持从 `.md`、`.txt`、`.zip`、`.tar`、`.tar.gz`、`.tgz` 构建本地知识库
- 所有知识库状态写入 skill 自己的数据目录，不污染当前工作区
- 默认追加到 `default` 知识库，也支持显式指定 KB 名
- 对未变化文档自动去重，对已变化文档自动重建
- 检索链路包含 chunk 检索、同文 regroup、cluster、扩窗、短文全文
- 支持两种回答模式：
  - `CHAT_BACKEND=host`：脚本只输出 host bundle，由宿主编排层生成最终答案
  - `CHAT_BACKEND=openai-compatible`：脚本直接调用 OpenAI-compatible chat 接口
- 可构建三套安装产物：
  - Codex
  - OpenClaw
  - Claude Code

## 项目结构

```text
local-rag-kb-skill/
├── core/
│   ├── runtime/
│   └── skill/
├── wrappers/
├── tools/
├── fixtures/
├── tests/
└── dist/
```

## 快速开始

创建虚拟环境并安装依赖：

```bash
cd /Users/perry/Projects/local-rag-kb-skill
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

复制环境变量模板：

```bash
cp .env.example .env
```

最少需要配置 embedding：

```env
EMBEDDING_API_KEY=your_key
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
CHAT_BACKEND=host
```

如果只是本地测试流程，可直接使用 `--local-test-embeddings`，不走真实向量接口。

## 使用方式

导入单文件：

```bash
.venv/bin/python core/skill/scripts/kb_ingest.py \
  --input /path/to/doc.md \
  --local-test-embeddings
```

导入压缩包：

```bash
.venv/bin/python core/skill/scripts/kb_ingest.py \
  --input /path/to/docs.zip \
  --local-test-embeddings
```

查询并输出 host orchestration bundle：

```bash
.venv/bin/python core/skill/scripts/kb_query.py \
  --question "Why can one broken provider affect many products?" \
  --emit-host-bundle \
  --local-test-embeddings
```

如果需要由 Python 直接调用远端对话模型：

```bash
CHAT_BACKEND=openai-compatible \
CHAT_API_KEY=... \
CHAT_BASE_URL=https://api.openai.com/v1 \
CHAT_MODEL=gpt-5.4 \
.venv/bin/python core/skill/scripts/kb_query.py \
  --question "Why can one broken provider affect many products?" \
  --answer
```

查看 KB：

```bash
.venv/bin/python core/skill/scripts/kb_list.py
.venv/bin/python core/skill/scripts/kb_status.py --kb default
```

## 构建与分发

构建全部宿主产物：

```bash
.venv/bin/python tools/build_targets.py --host all
```

打包 GitHub Release 附件：

```bash
.venv/bin/python tools/package_releases.py --host all
```

同步到本地宿主目录：

```bash
.venv/bin/python tools/sync_targets.py --host all
```

构建产物输出到：

- `dist/codex/local-rag-kb`
- `dist/openclaw/local-rag-kb`
- `dist/claude-code/local-rag-kb`

发布压缩包输出到：

- `release/`

## OpenClaw 使用建议

如果目标是让 OpenClaw 用户通过 AI 对话方式安装，而不是手动复制文件，GitHub 仓库应当作为完整源仓库发布，而不是只上传部分文件。建议做法：

1. 上传完整源码仓库
2. 通过 GitHub Releases 附上 `local-rag-kb-openclaw.zip`
3. 后续接入 OpenClaw 的 skill registry 或 install-from-GitHub 流程

仅有 GitHub 仓库本身，通常还不等于“纯对话安装”；这一步仍取决于 OpenClaw 是否提供仓库安装或 registry 分发能力。

## 验证

运行测试：

```bash
.venv/bin/python -m unittest discover -s tests -v
```

当前测试覆盖：

- 单文件导入
- zip / tar.gz 导入
- 增量重导入
- host bundle 查询输出
- 多宿主构建
