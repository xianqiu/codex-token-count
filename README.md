# codex-token-count

`codex-token-count` 是一个本地 CLI，用来查看本机 Codex 的 token 使用情况。

它提供三类信息：

- 全局总览
- 最近 N 天趋势
- 项目排行和单项目详情

工具直接读取本机已有的 Codex 数据，不上传数据，也不维护额外的统计数据库。

当前状态：

- macOS：已验证
- Linux：预期可用，但尚未专门验证
- Windows：暂不考虑

## Quick Start

```bash
make install
```

安装完成后，可以直接运行：

```bash
codex-token summary
```

如需自定义默认行为，在项目目录或其父目录放置 `.codex-token.toml`：

```toml
[codex]
home = "~/.codex"

[defaults]
trend_days = 7
project_limit = 3
include_archived = false

[pricing]
input_per_million_usd = 2.5
cached_input_per_million_usd = 0.25
output_per_million_usd = 15.0
```

默认情况下：

- 配置文件从当前目录向上查找最近的一份
- `pricing` 未配置时，不显示费用
- `include_archived = false` 时，不统计 archived session

## Data Sources

默认读取以下 Codex 数据：

- `state_5.sqlite`
- `sessions/**/*.jsonl`

## Docs

- CLI 命令用法：[docs/cli.md](docs/cli.md)
- JSON 接口：[docs/api.md](docs/api.md)
- 统计口径：[docs/statistics.md](docs/statistics.md)

## Development

运行测试：

```bash
make test
```

使用本机真实 Codex 数据做轻量冒烟检查：

```bash
make smoke
```

运行冒烟检查：

```bash
make smoke-trend
make smoke-projects
```
