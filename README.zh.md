# pandas-ai-local

> [English](./README.md) · **中文**

自然语言驱动的自动化数据分析工具。上传 CSV / Excel / SQLite / MySQL,用一句中文(或英文)提问,
就能拿到 pandas 跑出的答案、图表和报告 —— 后端可选 Claude、OpenAI 或本地 Ollama。

> 多后端 LLM • CLI + Web UI • 自动数据画像 • 多轮对话 •
> 沙箱代码执行 • 数据库连接器 • 自动报告生成 • 会话历史持久化

---

## 为什么做这个

平时做数据分析,流程基本是:

1. 看一遍列。
2. 写 pandas / matplotlib 模板代码。
3. 反复改图。
4. 把结果粘贴进报告。

`pandas-ai-local` 把这些都收进了一个聊天框。你描述目标,LLM 写 pandas 代码,
沙箱执行,你直接看到结果 —— 包括图表和一键导出的报告。

和那些只能上云的 SaaS 工具不同,后端可以随便切:Anthropic Claude、OpenAI,
或者完全本地的 Ollama —— 数据不出你的机器。

## 功能

- **多后端 LLM** — `claude` / `openai` / `ollama`,通过配置或 CLI 参数切换。
- **两套前端** — Typer 实现的 CLI(`nlda chat`)和 Streamlit Web UI(`nlda web`)。
- **自动数据画像** — 每个加载的数据集都会被自动总结(dtype、空值、范围、Top 值),
  这份摘要会作为上下文喂给 LLM。
- **多轮对话** — 同一会话内,Agent 记得之前的问题、dataframe 和结果。
- **沙箱执行** — 生成的代码在受限命名空间中运行,无 `os` / `subprocess` / `open` / 网络。
- **数据库连接器** — 用连接字符串直接从 SQLite 或 MySQL 加载表。
- **错误自动重试** — 生成的代码报错时,把 traceback 喂回 LLM 修(可配置最大次数)。
- **报告导出** — 整个会话可以导出成 Markdown 或独立 HTML。
- **会话持久化** — 每次对话都以 JSON 形式保存到 `~/.nlda/sessions/`,可恢复继续。

## 架构

```
┌─────────────┐  ┌─────────────┐
│   CLI       │  │  Streamlit  │
│ (Typer)     │  │   Web UI    │
└──────┬──────┘  └──────┬──────┘
       │                │
       └────────┬───────┘
                ▼
        ┌──────────────┐
        │ AnalysisAgent│   多轮对话 + 重试循环
        └──────┬───────┘
               │
   ┌───────────┼───────────────────┐
   ▼           ▼                   ▼
┌────────┐ ┌────────┐         ┌─────────────┐
│Provider│ │Loader  │         │   Sandbox   │
│ (LLM)  │ │ (data) │         │ (执行代码)  │
└───┬────┘ └────────┘         └─────────────┘
    │
 ┌──┴──┬────────┬────────┐
 ▼     ▼        ▼        ▼
Claude OpenAI Ollama  (可扩展)
```

## 快速开始

```bash
git clone https://github.com/ablek757/pandas-ai-local.git
cd pandas-ai-local
pip install -e .
cp .env.example .env       # 把你实际要用的 key 填进去
```

### CLI

```bash
nlda chat examples/data/sales.csv
> 按销售额排前 5 的产品是什么?
> 画一下 2024 年的月度销售额。
> Save report report.md
```

### Web UI

```bash
nlda web
# 浏览器打开 http://localhost:8501
```

### 切换后端

```bash
nlda chat sales.csv --provider claude   --model claude-sonnet-4-6
nlda chat sales.csv --provider openai   --model gpt-4o-mini
nlda chat sales.csv --provider ollama   --model llama3.1
```

## 配置

配置是分层的(后者覆盖前者):

1. 包内置的默认值
2. `~/.nlda/config.toml`
3. 环境变量 / `.env`
4. CLI 参数

`.env.example`:

```
NLDA_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OLLAMA_BASE_URL=http://localhost:11434
```

## 安全

沙箱:

- 在一个全新的 dict 里执行代码,只暴露 `pd`、`np`、`plt` 和加载好的 dataframe;
- 通过静态 AST 检查,屏蔽 `import os` / `import subprocess` / `open` / `eval` / `exec` /
  `__import__` 以及 dunder 属性访问;
- 每次执行有挂钟超时。

这**不是**对抗有备而来的攻击者的安全边界 —— 把 LLM 视作不可信*输入*,
只在你愿意暴露给所选后端的数据上使用本工具。

## Roadmap

- [ ] PDF 报告导出
- [ ] DuckDB / Postgres 连接器
- [ ] 图表类型推荐
- [ ] 缓存数据画像 + LLM 调用结果

## License

MIT —— 见 [LICENSE](LICENSE)。
