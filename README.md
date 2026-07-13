<h1 align="center">WhiteIntel-MCP</h1>

<p align="center">基于 <code>FastMCP</code> 编写的 WhiteIntel 威胁情报 MCP Server，覆盖凭证泄露、暗网情报、近似域名等查询能力</p>

<p align="center">
  <img src="https://img.shields.io/pypi/v/whiteintel-mcp?label=PyPI&color=3775A9" alt="PyPI 版本"/>
  <img src="https://img.shields.io/badge/Python-%3E%3D3.10-3776AB" alt="Python >=3.10"/>
  <img src="https://img.shields.io/badge/MCP%20SDK-%3E%3D1.28.1-6F42C1" alt="MCP SDK >=1.28.1"/>
  <img src="https://img.shields.io/pypi/dm/whiteintel-mcp?label=Downloads&color=2EA44F" alt="PyPI 下载量"/>
  <img src="https://img.shields.io/github/license/helGayhub233/WhiteIntel-MCP?label=License&color=blue" alt="许可证"/>
</p>

## 支持能力

| 模块 | 能力 |
| --- | --- |
| Credential Exposure | 最近泄露、消费者凭证、企业凭证、第三方数据库泄露 |
| Entity Lookup | IP、主机名、用户名/邮箱、日志 ID 精确查询 |
| Threat Feed | 暗网情报、公开新闻、分类/行业/网络 taxonomy |
| Brand Protection | 近似域名和品牌仿冒域名 |
| Watchlist | 监控列表查询、添加、移除、启用、禁用 |
| Supplier Security | 供应商列表、添加、移除、删除和风险筛选 |
| Audit | API Key 调用审计日志 |
| Payment Fraud | compromised payment card 查询 |

## 快速开始

### 通过 pip 安装

要求 Python `>=3.10`，MCP Python SDK `>=1.28.1`。用户无需 clone 源码，可直接从 PyPI 安装：

```bash
python -m pip install -U whiteintel-mcp
```

安装后可直接启动 MCP Server：

```bash
whiteintel-mcp
```

MCP 客户端配置：

```json
{
  "mcpServers": {
    "whiteintel": {
      "command": "whiteintel-mcp",
      "args": [],
      "env": {
        "WHITEINTEL_API_KEY": "your_whiteintel_api_key"
      }
    }
  }
}
```

### 通过 uvx 免安装运行

如果不想提前安装，也可以在 MCP 客户端中使用 `uvx` 直接运行 PyPI 包：

```json
{
  "mcpServers": {
    "whiteintel": {
      "command": "uvx",
      "args": [
        "whiteintel-mcp"
      ],
      "env": {
        "WHITEINTEL_API_KEY": "your_whiteintel_api_key"
      }
    }
  }
}
```

### 从源码运行

```bash
git clone https://github.com/helGayhub233/WhiteIntel-MCP.git
cd WhiteIntel-MCP
uv sync
uv run whiteintel-mcp
```

## MCP 配置

从源码运行时，推荐使用 `uv --directory` 固定项目目录。使用 PyPI 包时可直接参考上方 `pip` 或 `uvx` 配置。

```json
{
  "mcpServers": {
    "whiteintel": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/WhiteIntel-MCP",
        "run",
        "whiteintel-mcp"
      ],
      "env": {
        "WHITEINTEL_API_KEY": "your_whiteintel_api_key",
        "WHITEINTEL_BASE_URL": "https://api.whiteintel.io"
      }
    }
  }
}
```

也可以暴露一个共享 Streamable HTTP MCP endpoint：

```bash
WHITEINTEL_API_KEY=YOUR_KEY whiteintel-mcp \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8000 \
  --streamable-http-path /mcp
```

HTTP/SSE 默认只允许绑定到 loopback 地址。对外监听时必须在前置代理或嵌入式
FastMCP Host 中完成认证；仅当认证由可信代理提供时，才可设置
`WHITEINTEL_MCP_ALLOW_INSECURE_REMOTE=true` 允许 CLI 绑定非 loopback 地址。
`create_server()` 同时接受 MCP SDK 标准的 `AuthSettings` 和 `TokenVerifier`，用于
将服务器接入符合 MCP Authorization 规范的 OAuth 2.1 Resource Server。

## 环境变量

| 环境变量 | 说明 |
| --- | --- |
| `WHITEINTEL_API_KEY` | WhiteIntel API Key。推荐通过 MCP 客户端环境变量注入 |
| `WHITEINTEL_BASE_URL` | 可选，上游 API 地址，默认 `https://api.whiteintel.io` |
| `WHITEINTEL_MCP_TRANSPORT` | 可选，`stdio`、`sse` 或 `streamable-http`，默认 `stdio` |
| `WHITEINTEL_MCP_HOST` | 可选，HTTP/SSE 监听地址，默认 `127.0.0.1` |
| `WHITEINTEL_MCP_PORT` | 可选，HTTP/SSE 监听端口，默认 `8000` |
| `WHITEINTEL_MCP_HTTP_PATH` | 可选，Streamable HTTP 路径，默认 `/mcp` |
| `WHITEINTEL_MCP_SSE_PATH` | 可选，SSE 路径，默认 `/sse` |
| `WHITEINTEL_MCP_MOUNT_PATH` | 可选，挂载路径 |
| `WHITEINTEL_ENABLED_MODULES` | 可选，逗号分隔的模块 allowlist；未设置或留空时开放全部已配置模块 |
| `WHITEINTEL_ENABLE_WRITE_TOOLS` | 可选，是否暴露 Watchlist/Supplier 写工具，默认 `false` |
| `WHITEINTEL_MCP_ALLOW_INSECURE_REMOTE` | 仅可信认证代理场景使用；允许 CLI 绑定非 loopback HTTP/SSE 地址 |

API Key 获取入口：`https://whiteintel.io`

`mcp.json.example` 和 `.env.example` 提供了可直接修改的示例。

## 工具列表

默认仅暴露只读工具。写工具需要显式设置
`WHITEINTEL_ENABLE_WRITE_TOOLS=true`；该开关只控制工具暴露范围，HTTP 部署仍须在
服务端按调用者身份和 scope 授权。

| 工具名称 | 模块 | 说明 |
| --- | --- | --- |
| `last_leaks` | Credential Exposure | 查询目标域名最近 1-30 天凭证泄露 |
| `threat_feed` | Threat Feed | 查询暗网情报、公开新闻或 taxonomy |
| `consumer_leaks` | Credential Exposure | 查询消费者侧 stealer/combolist 泄露 |
| `corporate_leaks` | Credential Exposure | 查询企业邮箱域相关凭证泄露 |
| `database_leaks` | Credential Exposure | 查询第三方数据库泄露中的企业凭证 |
| `overall_stats` | Analytics | 查询聚合指标和事件时间线 |
| `ip_leaks` | Entity Lookup | 按 IP 查询 stealer 凭证记录 |
| `computer_leaks` | Entity Lookup | 按主机名查询 stealer 凭证记录 |
| `username_leaks` | Entity Lookup | 按用户名或邮箱精确查询凭证记录 |
| `lookalike_domains` | Brand Protection | 查询近似域名和品牌仿冒域名 |
| `leaks_by_id` | Entity Lookup | 按单个或最多 5 个日志 ID 查询完整记录 |
| `watchlist_list` | Watchlist | 查询监控列表条目 |
| `watchlist_add` | Watchlist | 添加监控列表条目（需启用写工具） |
| `watchlist_remove` | Watchlist | 移除监控列表条目（需启用写工具） |
| `watchlist_enable` | Watchlist | 启用监控列表条目（需启用写工具） |
| `watchlist_disable` | Watchlist | 禁用监控列表条目（需启用写工具） |
| `supplier_list` | Supplier Security | 查询供应商安全条目 |
| `supplier_add` | Supplier Security | 添加供应商安全条目（需启用写工具） |
| `supplier_remove` | Supplier Security | 移除供应商安全条目（需启用写工具） |
| `supplier_delete` | Supplier Security | 删除供应商安全条目（需启用写工具） |
| `audit_logs` | Audit | 查询 API Key 调用审计日志 |
| `card_check` | Payment Fraud | 查询 compromised payment card 记录 |

工具返回 WhiteIntel 上游结构化 JSON：成功时通常包含 `success=true`、结果字段和剩余额度字段；失败时保留上游返回的 `error`、`message`、`http_status` 或限流信息，便于 MCP 客户端区分鉴权错误、套餐权限不足、额度耗尽、限流、超时和参数校验失败。

失败响应会转换为 MCP Tool Execution Error（`isError=true`），并提供稳定错误码：
`AUTH_INVALID`、`ENTITLEMENT_REQUIRED`、`QUOTA_EXHAUSTED`、`RATE_LIMITED`、
`INVALID_REQUEST`、`FORBIDDEN`、`UPSTREAM_UNAVAILABLE` 或 `UPSTREAM_ERROR`。

工具使用 MCP Tool Annotations 标识只读、写入和破坏性操作。公共参数使用枚举、
范围、数组和布尔类型；上游的 `sortBy`、逗号分隔列表和 `0/1` 布尔约定不会直接
泄漏到对应的新工具参数中。

### 按套餐限制工具范围

WhiteIntel 当前没有稳定的账号 capability 查询接口，因此本项目不通过逐接口试探
来猜测权限，也不会把额度耗尽误判为永久无权限。部署者应根据账号套餐显式配置模块：

```bash
WHITEINTEL_ENABLED_MODULES=credential_exposure,entity_lookup,analytics \
  whiteintel-mcp
```

支持的模块为：`credential_exposure`、`entity_lookup`、`threat_feed`、`analytics`、
`brand_protection`、`watchlist`、`supplier_security`、`audit`、`payment_fraud`。

## 资源提示

`docs/*.md` 会以 `whiteintel://docs/{filename}` 形式暴露为 MCP Resources。模型需要接口细节时读取 Resource，需要执行查询时调用 Tool，避免把静态文档塞进工具参数。

资源示例：

- `whiteintel://docs/consumer-leaks-api.md`
- `whiteintel://docs/corporate-leaks-api.md`
- `whiteintel://docs/database-leaks-api.md`
- `whiteintel://docs/last-leaks-api.md`
- `whiteintel://docs/threat-feed-api.md`
- `whiteintel://docs/threat-feed-darkweb-chatters-api.md`
- `whiteintel://docs/watchlists-api.md`
- `whiteintel://docs/supplier-api.md`
- `whiteintel://docs/card-check-api.md`

## 请求限制

项目会对可在本地判断的参数做 Pydantic 校验，并在请求上游前做进程内节流。API Key 权限、订阅等级、每日额度和上游风控仍以 WhiteIntel 返回为准。

| 范围 | 控制方式 |
| --- | --- |
| 全部 WhiteIntel HTTP 请求 | 进程内节流，按 `(endpoint, apikey)` 控制，默认 `0.2 QPS`（同一接口、同一 API Key 每 5 秒 1 次请求） |
| 全部工具 | API Key 从 `WHITEINTEL_API_KEY` 环境变量读取，不暴露为 MCP 工具参数 |
| 分页类接口 | 本地 schema 限制页码为正整数，并按接口文档限制 `limit` 范围 |
| 日期范围参数 | 本地校验 `YYYY-MM-DD` 格式，且 `start_date` / `end_date` 必须成对出现 |
| `leaks_by_id` | 本地限制批量 ID 数量不超过 5 个 |
| `card_check` | 本地限制必须且只能提供一个主选择器：`bin`、`issuer` 或 `country` |

频率控制是单 MCP 进程内的内存状态；如果同时启动多个 MCP 进程，进程之间不会共享这些状态。

## API 文档

已整理的接口文档位于 `docs/`，并会打包进 wheel 作为 MCP Resources 暴露。

版本发布和迭代记录见 `CHANGELOG.md`。

## 项目结构

```text
src/
  whiteintel_mcp/
    server.py                    # FastMCP 入口、工具注册、resources 注册
    cli.py                       # CLI 兼容入口
    models/
      common.py                  # 共享 Pydantic mixin 和字段校验
      endpoints.py               # 各 WhiteIntel endpoint 请求模型
    services/
      whiteintel_client.py       # 上游 HTTP client 和 429 Retry-After 处理
      upstream_rate_limiter.py   # 进程内请求节流
```

## 手动编译

```bash
uv sync
uv run python -m compileall src/whiteintel_mcp
uv build --wheel
```

## 开发测试

```bash
uv sync --extra dev
uv run pytest
```

项目使用 Pydantic 在调用上游前进行参数校验，并使用轻量内存 pacer 按 `(endpoint, apikey)` 控制请求间隔。默认节流为 `0.2 QPS`（同一接口、同一 API Key 每 5 秒 1 次请求），这是综合上游常见拦截阈值、MCP 客户端并发调用和批量翻页速度后的折中值；所有接口统一使用该默认值，避免并发调用时过快触发 WhiteIntel 上游限制。

## 注意事项

**本项目仅供学习和技术研究使用，严禁用于任何商业或非法用途。**

请只在合法授权范围内使用本项目，并遵守 WhiteIntel 的 API 服务条款、订阅权限和额度限制。

## 许可证

MIT License，见 `LICENSE`。
