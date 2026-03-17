# JSON API

本文档定义 `codex-token-count --json` 的返回结构。

约束：

- 数值字段返回原始数值，不做格式化
- 时间字段使用 ISO 8601
- 未配置 pricing 时，`cost` 为 `null`

## Shared Objects

### `usage`

```json
{
  "total_tokens": 1234567,
  "input_tokens": 500000,
  "cached_input_tokens": 120000,
  "non_cached_input_tokens": 380000,
  "output_tokens": 734567,
  "reasoning_output_tokens": 100000,
  "non_reasoning_output_tokens": 634567
}
```

### `cost`

```json
{
  "currency": "USD",
  "input_cost_usd": 1.25,
  "cached_input_cost_usd": 0.03,
  "output_cost_usd": 9.82,
  "total_cost_usd": 11.10,
  "pricing": {
    "input_per_million_usd": 2.5,
    "cached_input_per_million_usd": 0.25,
    "output_per_million_usd": 15.0
  }
}
```

### Project Fields

- `project_id`: 稳定标识，当前为完整 `cwd`
- `project_name`: 展示名，要求在当前结果集中唯一，但不保证跨时间稳定

## `summary`

命令：

```bash
codex-token --json summary
```

返回：

```json
{
  "scope": "summary",
  "sessions": 63,
  "projects": 18,
  "last_updated_at": "2026-03-17T10:12:00+00:00",
  "tokens_last_7_days": 120000,
  "tokens_last_30_days": 540000,
  "trend_rows": [
    {
      "date": "2026-03-17",
      "usage": {
        "total_tokens": 1200,
        "input_tokens": 500,
        "cached_input_tokens": 100,
        "non_cached_input_tokens": 400,
        "output_tokens": 700,
        "reasoning_output_tokens": 120,
        "non_reasoning_output_tokens": 580
      }
    }
  ],
  "usage": {
    "total_tokens": 1234567,
    "input_tokens": 500000,
    "cached_input_tokens": 120000,
    "non_cached_input_tokens": 380000,
    "output_tokens": 734567,
    "reasoning_output_tokens": 100000,
    "non_reasoning_output_tokens": 634567
  },
  "cost": {
    "currency": "USD",
    "input_cost_usd": 0.95,
    "cached_input_cost_usd": 0.03,
    "output_cost_usd": 11.36,
    "total_cost_usd": 12.34,
    "pricing": {
      "input_per_million_usd": 2.5,
      "cached_input_per_million_usd": 0.25,
      "output_per_million_usd": 15.0
    }
  }
}
```

字段说明：

- `sessions`: 纳入统计的 session 数量
- `projects`: 纳入统计的项目数量
- `tokens_last_7_days`: 最近 7 天新增 token
- `tokens_last_30_days`: 最近 30 天新增 token
- `trend_rows`: 最近 7 天每日增量
- `usage`: 当前全量累计 usage

## `trend`

命令：

```bash
codex-token --json trend
codex-token --json trend --days 30
```

返回：

```json
{
  "scope": "trend",
  "days": 7,
  "rows": [
    {
      "date": "2026-03-11",
      "usage": {
        "total_tokens": 1200,
        "input_tokens": 500,
        "cached_input_tokens": 100,
        "non_cached_input_tokens": 400,
        "output_tokens": 700,
        "reasoning_output_tokens": 120,
        "non_reasoning_output_tokens": 580
      },
      "cost": {
        "currency": "USD",
        "input_cost_usd": 0.001,
        "cached_input_cost_usd": 0.000025,
        "output_cost_usd": 0.0105,
        "total_cost_usd": 0.011525,
        "pricing": {
          "input_per_million_usd": 2.5,
          "cached_input_per_million_usd": 0.25,
          "output_per_million_usd": 15.0
        }
      }
    }
  ]
}
```

字段说明：

- `days`: 返回窗口天数
- `rows[*].date`: 日期
- `rows[*].usage`: 当日新增 usage
- `rows[*].cost`: 当日 usage 的费用估算；未配置 pricing 时为 `null`

## `project`

命令：

```bash
codex-token --json project
codex-token --json project --limit 10
```

返回：

```json
{
  "scope": "project_list",
  "limit": 3,
  "rows": [
    {
      "project_id": "/Users/example/work/foo/api",
      "project_name": "foo/api",
      "sessions": 12,
      "last_updated_at": "2026-03-17T10:12:00+00:00",
      "usage": {
        "total_tokens": 123456,
        "input_tokens": 50000,
        "cached_input_tokens": 10000,
        "non_cached_input_tokens": 40000,
        "output_tokens": 73456,
        "reasoning_output_tokens": 8000,
        "non_reasoning_output_tokens": 65456
      },
      "cost": {
        "currency": "USD",
        "input_cost_usd": 0.10,
        "cached_input_cost_usd": 0.00,
        "output_cost_usd": 1.10,
        "total_cost_usd": 1.20,
        "pricing": {
          "input_per_million_usd": 2.5,
          "cached_input_per_million_usd": 0.25,
          "output_per_million_usd": 15.0
        }
      }
    }
  ]
}
```

字段说明：

- `limit`: 返回条数上限
- `rows[*].project_id`: 项目稳定标识
- `rows[*].project_name`: 项目展示名
- `rows[*].sessions`: 该项目 session 数

## `project <project_ref>`

命令：

```bash
codex-token --json project /Users/example/work/foo/api
codex-token --json project foo/api
```

返回：

```json
{
  "scope": "project_detail",
  "project": {
    "project_id": "/Users/example/work/foo/api",
    "project_name": "foo/api",
    "cwd": "/Users/example/work/foo/api",
    "sessions": 12,
    "last_updated_at": "2026-03-17T10:12:00+00:00"
  },
  "usage": {
    "total_tokens": 123456,
    "input_tokens": 50000,
    "cached_input_tokens": 10000,
    "non_cached_input_tokens": 40000,
    "output_tokens": 73456,
    "reasoning_output_tokens": 8000,
    "non_reasoning_output_tokens": 65456
  },
  "cost": {
    "currency": "USD",
    "input_cost_usd": 0.10,
    "cached_input_cost_usd": 0.00,
    "output_cost_usd": 1.10,
    "total_cost_usd": 1.20,
    "pricing": {
      "input_per_million_usd": 2.5,
      "cached_input_per_million_usd": 0.25,
      "output_per_million_usd": 15.0
    }
  }
}
```

字段说明：

- `project.project_id`: 项目稳定标识
- `project.project_name`: 项目展示名
- `project.cwd`: 当前项目路径，等同于 `project_id`
