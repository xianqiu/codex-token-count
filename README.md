# codex-token-count

`codex-token-count` 是一个本地 CLI 工具，用来统计和查看你机器上 Codex 的 token 使用情况。

它主要解决这些问题：

- 最近用了多少 token
- 哪些本地项目最耗 token
- 哪些 session 消耗最高
- 最近 7 天或 30 天的使用趋势如何
- input、output、cached input、reasoning output 分别是多少

这个工具直接读取你本机已有的 Codex 数据，不会上传数据，也不会额外保存一份统计数据库。

## 快速开始

### 1. 安装

在当前项目目录执行：

```bash
make install
```

这会用 editable 模式安装当前项目，并在你的 Python 环境中注册 `codex-token` 命令。

如果你不想用 `make`，等价命令是：

```bash
pip install -e .
```

### 2. 先跑几个最常用的命令

查看全局汇总：

```bash
codex-token summary
```

查看最耗 token 的 session：

```bash
codex-token top --limit 10
```

查看项目维度排行：

```bash
codex-token projects
```

查看某个项目的详细情况：

```bash
codex-token project /你的项目绝对路径
```

查看某个 session 的详细情况：

```bash
codex-token session 019cf082 --events 10
```

查看最近趋势：

```bash
codex-token trend --days 30
```

## 数据来源

默认情况下，CLI 会读取本机的 Codex 数据目录：

```bash
~/.codex
```

当前主要使用这两类数据：

- `state_5.sqlite`：用于读取 session 级别的总量统计
- `sessions/**/*.jsonl`：用于读取更细的 token 事件和趋势数据

补充说明：

- `cached input` 已经包含在 `input tokens` 中
- `reasoning output` 已经包含在 `output tokens` 中

如果你想读取别的 Codex 数据目录，可以手动指定：

```bash
codex-token --codex-home /path/to/another/.codex summary
```

## JSON 输出

如果你想把 CLI 输出接到脚本里处理，可以加 `--json`：

```bash
codex-token --json summary
codex-token --json projects
codex-token --json session 019cf082
```

## 推荐使用流程

先从全局开始：

```bash
codex-token summary
codex-token projects
```

然后下钻到最耗 token 的项目：

```bash
codex-token project /项目绝对路径
```

最后查看具体的高消耗 session：

```bash
codex-token session <session-id-前缀>
```

## 开发

重新安装或刷新当前 editable 安装：

```bash
make install
```

运行测试：

```bash
make test
```

运行冒烟检查：

```bash
make smoke
make smoke-project
make smoke-session
```
