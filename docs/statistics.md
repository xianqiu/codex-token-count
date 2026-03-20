# Statistics Semantics

本文档定义 `codex-token` 当前版本的统计口径。

## Scope

所有命令都基于同一组 session 集合计算：

- `summary`
- `trend`
- `project`

默认情况下：

- 只统计未归档 session
- 若配置 `defaults.include_archived = true`，则将 archived session 一并纳入

## Source Of Truth

统计依赖两类本地数据：

- `state_5.sqlite` 中的 `threads`
- `sessions/**/*.jsonl` 中的 token events

集合规则：

1. 先从 `threads` 中读取符合 archived 配置的 session
2. 再只保留这些 session 对应的 token events

因此：

- session 数量
- project 聚合
- usage 汇总
- trend 窗口

都必须基于同一批 session 计算，不允许 thread 集合和 token event 集合口径不一致。

## Usage Semantics

### Total Usage

全量 usage 以每个 session 的最新 token snapshot 为准。

定义：

- 对每个 `session_id`，取时间最新的一条 `token_count` event
- 将这些最新 snapshot 按字段求和

衍生字段：

- `non_cached_input_tokens = max(input_tokens - cached_input_tokens, 0)`
- `non_reasoning_output_tokens = max(output_tokens - reasoning_output_tokens, 0)`

### Daily Trend

按天趋势不使用最终 snapshot 直接分桶，而是使用同一 session 相邻 snapshot 的增量。

定义：

- 按时间顺序遍历 token events
- 对同一 session，相邻两条 snapshot 取字段增量
- 首条 snapshot 的增量等于其自身值
- 每日汇总这些增量

因此：

- `summary.usage.total_tokens` 表示当前累计总量
- `trend.rows[*].usage.total_tokens` 表示窗口内每天新增量
- `tokens_last_7_days` / `tokens_last_30_days` 是 trend 增量求和，不是全量 snapshot

## Project Identity

项目有两个不同概念：

- `project_id`：稳定标识，当前定义为完整 `cwd`
- `project_name`：展示名，由路径压缩生成，要求在当前结果集中唯一，但不承诺跨时间稳定

约束：

- JSON 输出对外提供 `project_id`
- 文本输出默认展示 `project_name`
- 单项目查询优先按 `project_id` 解析，也兼容 `project_name`

## Cost Semantics

费用估算基于 usage 计算：

- non-cached input 按 `input_per_million_usd`
- cached input 按 `cached_input_per_million_usd`
- output 按 `output_per_million_usd`

当前不区分 reasoning / non-reasoning output 的不同费率。
