# OpenClaw 安装与使用

这个文档面向 OpenClaw 用户，说明如何安装 `local-rag-kb` skill、如何首次配置，以及如何通过 AI 对话方式导入文件和查询本地知识库。

仓库地址：

- [https://github.com/Perry0077/local-rag-kb-skill](https://github.com/Perry0077/local-rag-kb-skill)

如果你要手动下载 Release，请优先使用 OpenClaw 版本压缩包：

- `local-rag-kb-openclaw.zip`

## 适用场景

安装后，这个 skill 可以用于：

- 把 `.md`、`.txt`、`.zip`、`.tar`、`.tar.gz`、`.tgz` 导入本地知识库
- 向已有知识库追加单文件或压缩包
- 从本地知识库检索并回答问题
- 列出、查看、重建、删除知识库

默认规则：

- 未指定 KB 名时，导入到 `default`
- 查询时优先使用 `default`
- 默认输出答案和引用，不展示原始 chunk 细节

## 前提条件

需要满足这些前提：

- OpenClaw 可以安装本地 skill
- OpenClaw 在调用 skill 时能够运行本地命令
- 你有一个 OpenAI-compatible embedding API key
- 如果要通过“上传附件直接入库”，OpenClaw 需要把附件暴露为可读的本地路径

当前 v1 中：

- embedding 必须配置
- chat 默认由宿主主模型负责回答
- 支持的文档类型只有 markdown 和 txt

## 安装方式

### 方式一：从 GitHub Release 安装

这是最适合普通 OpenClaw 用户的方式。

思路是：

1. 从 GitHub Releases 下载 `local-rag-kb-openclaw.zip`
2. 解压到 OpenClaw 的 skills 目录
3. 初始化 skill 自己的 `.venv`
4. 配置 `.env`

如果宿主环境不支持创建 `.venv`，也可以退回系统 `python3` 直接运行，但前提是系统 Python 已安装依赖。

默认安装目录：

- `~/.agents/skills/local-rag-kb`

默认数据目录：

- `~/.agents/data/local-rag-kb`

如果 OpenClaw 已经支持“从 GitHub / Release 自动安装 skill”，可以直接让它做这些动作。

### 方式二：从 GitHub 仓库源码安装

适合 OpenClaw 具备 shell 能力、但没有现成 Release 安装器的情况。

标准流程是：

1. clone 仓库
2. 创建 `.venv`
3. 执行 `tools/build_targets.py --host openclaw`
4. 执行 `tools/sync_targets.py --host openclaw`

如果系统不支持 `python3 -m venv`，可以跳过第 2 步，但需要确保系统 `python3` 已安装依赖。

## 首次配置

安装完成后，skill 目录下应当至少有这些文件：

- `SKILL.md`
- `scripts/`
- `runtime/`
- `.env.example`
- `requirements.txt`

首次使用前需要准备：

1. 复制 `.env.example` 为 `.env`
2. 填入 `EMBEDDING_API_KEY`
3. 如果你不是走默认 OpenAI 接口，可同时设置：
   - `EMBEDDING_BASE_URL`
   - `EMBEDDING_MODEL`
4. 首次运行前执行：
   - `python3 scripts/kb_bootstrap.py`

bootstrap 完成后，宿主应优先用 skill 自己的解释器：

- `.venv/bin/python`

也就是说，后续所有命令都应通过：

- `.venv/bin/python scripts/kb_ingest.py ...`
- `.venv/bin/python scripts/kb_query.py ...`

### `.venv` 创建失败时的 fallback

如果 OpenClaw 提示：

- `ensurepip is not available`
- `python3 -m venv` 不可用

不要把这当成 skill 无法运行。

此时改用下面的策略：

1. 不再强制创建 `.venv`
2. 检查系统 `python3` 是否已安装依赖：
   - `openai`
   - `chromadb`
   - `dotenv`
   - `tqdm`
3. 如果缺少依赖，并且宿主允许安装用户级 Python 包，执行：
   - `python3 -m pip install --user openai chromadb python-dotenv tqdm`
4. 后续直接用系统 `python3` 运行：
   - `python3 scripts/kb_ingest.py ...`
   - `python3 scripts/kb_query.py ...`
   - `python3 scripts/kb_status.py ...`

结论：

- 优先使用 `.venv`
- `.venv` 不可用时，允许 fallback 到系统 `python3`
- fallback 成立的前提是依赖已经可导入

## OpenClaw 对话安装提示词

下面这些提示词适用于“OpenClaw 具备 GitHub 下载 / shell / 文件操作能力”的情况。

### 中文：从 GitHub Release 下载并安装

```text
从 GitHub 仓库 https://github.com/Perry0077/local-rag-kb-skill 下载 OpenClaw 版 skill。
优先使用 GitHub Releases 里的 local-rag-kb-openclaw.zip。
把它安装到 ~/.agents/skills/local-rag-kb。
如果目录里没有 .env，就用 .env.example 创建一份 .env。
然后运行 python3 scripts/kb_bootstrap.py 初始化这个 skill 的本地 .venv。
如果因为 ensurepip 或 python3 -m venv 不可用而失败，不要停止。
改为检查系统 python3 是否已安装 openai、chromadb、python-dotenv、tqdm。
如果缺少依赖，就尝试运行 python3 -m pip install --user openai chromadb python-dotenv tqdm。
之后直接用系统 python3 运行这个 skill。
完成后告诉我还需要我提供哪些环境变量。
```

### 中文：从 GitHub 仓库源码安装

```text
从 GitHub 仓库 https://github.com/Perry0077/local-rag-kb-skill 拉取源码并安装 OpenClaw 版 skill。
在仓库里创建 .venv，安装 requirements.txt，运行 tools/build_targets.py --host openclaw，
再运行 tools/sync_targets.py --host openclaw，把 skill 安装到 ~/.agents/skills/local-rag-kb。
安装完成后检查 ~/.agents/skills/local-rag-kb 下是否存在 SKILL.md、scripts、runtime、.env.example。
```

### English: install from GitHub Release

```text
Install the OpenClaw version of the local-rag-kb skill from https://github.com/Perry0077/local-rag-kb-skill.
Prefer the GitHub Release asset named local-rag-kb-openclaw.zip.
Install it into ~/.agents/skills/local-rag-kb.
If .env does not exist, create it from .env.example.
Then run python3 scripts/kb_bootstrap.py inside the installed skill directory.
If bootstrap fails because ensurepip or python3 -m venv is unavailable, do not stop.
Check whether system python3 already has openai, chromadb, python-dotenv, and tqdm.
If needed, try python3 -m pip install --user openai chromadb python-dotenv tqdm,
then run the skill with system python3 instead of a local virtualenv.
After that, tell me which environment variables still need values.
```

### English: install from the GitHub repository

```text
Clone https://github.com/Perry0077/local-rag-kb-skill and install the OpenClaw target of this skill.
Create a local virtualenv, install requirements.txt, run tools/build_targets.py --host openclaw,
then run tools/sync_targets.py --host openclaw so the skill is installed into ~/.agents/skills/local-rag-kb.
Verify that the installed skill contains SKILL.md, scripts, runtime, and .env.example.
```

## OpenClaw 对话配置提示词

如果 OpenClaw 已经安装好 skill，但还没配置 embedding key，可以直接说：

### 中文

```text
帮我配置 local-rag-kb 这个 skill。
在 ~/.agents/skills/local-rag-kb/.env 中保留 LOCAL_RAG_KB_HOST=openclaw，
并写入我的 EMBEDDING_API_KEY。
如果我没有指定 EMBEDDING_BASE_URL 和 EMBEDDING_MODEL，
就使用 https://api.openai.com/v1 和 text-embedding-3-small。
配置完成后不要开始导入，先告诉我已经就绪。
```

### English

```text
Configure the local-rag-kb skill for OpenClaw.
Keep LOCAL_RAG_KB_HOST=openclaw in ~/.agents/skills/local-rag-kb/.env and write my EMBEDDING_API_KEY there.
If I do not specify EMBEDDING_BASE_URL or EMBEDDING_MODEL, use https://api.openai.com/v1 and text-embedding-3-small.
If .venv cannot be created, use system python3 instead of failing, as long as the required Python packages are installed.
Do not ingest anything yet. Just confirm when the skill is ready.
```

## OpenClaw 使用提示词

### 导入一个 zip 到默认知识库

```text
Use $local-rag-kb to ingest this zip into my default knowledge base.
If the uploaded file has a readable local path, use it directly.
If not, tell me clearly that the attachment path is unavailable.
If .venv is unavailable, use system python3 instead of failing.
```

### 导入一个 markdown 文件到指定知识库

```text
Use $local-rag-kb to add this markdown file to the knowledge base named startup-notes.
If startup-notes does not exist yet, create it by ingesting this file.
```

### 追加一个 txt 文件

```text
Use $local-rag-kb to append this txt file to my existing default knowledge base.
```

### 查询本地知识库

```text
Use $local-rag-kb to answer this question from my local knowledge base:
为什么一个上游依赖故障会同时影响很多 AI 产品？
Answer with citations and keep the response concise.
If .venv is unavailable, use system python3 instead of failing.
```

### 查询指定知识库

```text
Use $local-rag-kb to query the knowledge base named startup-notes:
What is the recommended sequence for launching a new content site?
Return a concise answer with references only.
```

### 查看知识库状态

```text
Use $local-rag-kb to show the status of my default knowledge base.
```

### 列出所有知识库

```text
Use $local-rag-kb to list all local knowledge bases managed by this skill.
```

### 重建某个知识库

```text
Use $local-rag-kb to rebuild the knowledge base named default.
```

### 删除某个知识库

```text
Use $local-rag-kb to delete the knowledge base named default and ask me to confirm before doing it.
```

## 期望的宿主行为

OpenClaw 编排这个 skill 时，推荐遵循下面的顺序：

1. 如果 `.venv/bin/python` 不存在，先运行 `python3 scripts/kb_bootstrap.py`
2. 如果 `.venv` 因 `ensurepip` 或 `python3 -m venv` 不可用而创建失败，回退到系统 `python3`
3. 只有在系统 `python3` 能导入 `openai`、`chromadb`、`dotenv`、`tqdm` 时，fallback 才成立
4. 后续优先使用 `.venv/bin/python`，否则使用系统 `python3`
5. 查询时运行 `kb_query.py --emit-host-bundle`
6. 最终答案由宿主主模型根据 bundle 生成
7. 默认只展示答案和引用，不展示 raw chunk

## 常见问题

### 1. 为什么我上传了文件，但 skill 没开始导入？

最常见原因有两个：

- `EMBEDDING_API_KEY` 还没配置
- OpenClaw 没有把附件暴露成可读本地路径

### 2. 为什么它说附件路径不可用？

当前 skill 不是直接读取聊天消息里的二进制附件对象，而是依赖宿主把附件落成可读文件路径。如果宿主拿不到这个路径，就必须显式报错，而不是假装导入成功。

### 3. 数据会写到哪里？

默认写到：

- `~/.agents/data/local-rag-kb`

如果需要自定义目录，可以设置：

- `LOCAL_RAG_KB_DATA_DIR=/your/path`

### 4. 不用虚拟环境能运行吗？

可以。

当前 skill 不是强制要求 `.venv` 才能运行。`.venv` 只是优先路径，不是唯一运行方式。

如果系统 `python3` 已安装这些依赖：

- `openai`
- `chromadb`
- `python-dotenv`
- `tqdm`

那么 OpenClaw 可以直接使用系统 `python3` 调用：

- `python3 scripts/kb_ingest.py`
- `python3 scripts/kb_query.py`
- `python3 scripts/kb_status.py`
