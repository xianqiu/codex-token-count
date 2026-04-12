# CLI Usage

`codex-token` 用来查看本机 Codex 的 token 使用情况。

支持三类查询：

- 全局总览
- 最近 N 天趋势
- 项目排行和单项目详情

## Install

全局安装：

```bash
make install
```

卸载：

```bash
make uninstall
```

如果安装后提示 `codex-token: command not found`，确保你的 shell 配置里有：

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Configuration

CLI 优先读取当前目录向上最近的一份 `.codex-token.toml`；如果找不到，会回退到 `codex-token` 项目根目录下的 `.codex-token.toml`。

示例：

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

字段说明：

- `codex.home`: Codex 数据目录，默认是 `~/.codex`
- `defaults.trend_days`: `trend` 命令默认天数
- `defaults.project_limit`: `project` 列表默认条数
- `defaults.include_archived`: 是否把 archived session 纳入统计，默认 `false`
- `pricing.*`: 费用估算单价；未配置时不显示费用

## Commands

默认情况下，`codex-token` 不带子命令时等价于 `codex-token summary`。

### `summary`

查看全局总览。

```bash
codex-token
codex-token summary
codex-token --json
codex-token --json summary
```

文本输出包含：

- session 数量
- 总 token 数
- 最近 7 天 token
- 最近 30 天 token
- 费用估算（如果已配置 pricing）

### `trend`

查看最近 N 天的每日 token 趋势。

```bash
codex-token trend
codex-token trend --days 30
codex-token --json trend
codex-token --json trend --days 30
```

参数：

- `--days N`: 指定时间窗口；未传时使用 `defaults.trend_days`

### `project`

查看项目排行。

```bash
codex-token project
codex-token project --limit 10
codex-token --json project
codex-token --json project --limit 10
```

参数：

- `--limit N`: 返回前 N 个项目；未传时使用 `defaults.project_limit`

### `project <project_ref>`

查看单个项目详情。

```bash
codex-token project /Users/example/work/foo/api
codex-token project foo/api
codex-token --json project /Users/example/work/foo/api
```

`project_ref` 支持两种值：

- `project_id`: 稳定标识，当前为项目完整 `cwd`
- `project_name`: 展示名，例如 `foo/api`

命令会优先按 `project_id` 查找，也兼容 `project_name`。

## JSON Output

所有命令都支持全局参数 `--json`：

```bash
codex-token --json summary
codex-token --json trend
codex-token --json project
codex-token --json project /Users/example/work/foo/api
```

JSON 返回结构见 [api.md](./api.md)。

## Related Docs

- JSON 接口：[`api.md`](./api.md)
- 统计口径：[`statistics.md`](./statistics.md)
