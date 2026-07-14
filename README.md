<h1 align="center">WhiteIntel-MCP</h1>

<p align="center">将 WhiteIntel 的凭证泄露、暗网情报、品牌保护和支付欺诈能力接入 MCP 客户端</p>

<p align="center">
  <img src="https://img.shields.io/pypi/v/whiteintel-mcp?label=PyPI&color=3775A9" alt="PyPI 版本"/>
  <img src="https://img.shields.io/badge/Python-%3E%3D3.10-3776AB" alt="Python >=3.10"/>
  <img src="https://img.shields.io/badge/MCP%20SDK-%3E%3D1.28.1-6F42C1" alt="MCP SDK >=1.28.1"/>
  <img src="https://img.shields.io/pypi/dm/whiteintel-mcp?label=Downloads&color=2EA44F" alt="PyPI 下载量"/>
  <img src="https://img.shields.io/github/license/helGayhub233/WhiteIntel-MCP?label=License&color=blue" alt="许可证"/>
</p>

## 支持能力

| 模块 | 主要能力 |
| --- | --- |
| 凭证泄露 | 查询近期泄露、消费者凭证、企业凭证及第三方数据库泄露 |
| 实体检索 | 按 IP、主机名、用户名、邮箱或日志 ID 定位泄露记录 |
| 威胁情报 | 查询暗网动态、公开安全新闻，以及可用的类别、行业和网络分类 |
| 品牌保护 | 发现近似域名、拼写仿冒和品牌冒用域名 |
| 监控列表 | 查询和管理域名、邮箱等持续监控目标 |
| 供应商安全 | 管理供应商并按状态、风险层级等条件筛选 |
| 审计 | 查询当前 API Key 的调用审计日志 |
| 支付欺诈 | 按 BIN、发卡机构、国家及卡片属性检索泄露支付卡情报 |

## 快速开始

### 使用 uvx（推荐）

要求 Python `>=3.10`。将以下配置加入支持 MCP 的客户端即可，无需预先安装：

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

### 使用 pip

也可以从 PyPI 安装后运行：

```bash
python -m pip install -U whiteintel-mcp
whiteintel-mcp
```

此时将客户端配置中的 `command` 改为 `whiteintel-mcp`，并将 `args` 设为 `[]`。

### 从源码运行

```bash
git clone https://github.com/helGayhub233/WhiteIntel-MCP.git
cd WhiteIntel-MCP
uv sync
uv run whiteintel-mcp
```

## HTTP 部署

本地客户端通常使用默认的 `stdio` 传输。需要向其他进程提供服务时，可以启动
Streamable HTTP endpoint：

```bash
WHITEINTEL_API_KEY=YOUR_KEY whiteintel-mcp \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8000 \
  --streamable-http-path /mcp
```

HTTP/SSE 默认只允许绑定 loopback 地址。对外监听前必须通过前置代理或嵌入式
FastMCP Host 完成认证；`WHITEINTEL_MCP_ALLOW_INSECURE_REMOTE=true` 仅用于已有可信
认证代理的场景。嵌入部署时，`create_server()` 支持 MCP SDK 的 `AuthSettings` 和
`TokenVerifier`。

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

API Key 可从 [WhiteIntel](https://whiteintel.io) 获取。完整配置示例见
`mcp.json.example` 和 `.env.example`。

## 工具列表

默认仅暴露只读工具。设置 `WHITEINTEL_ENABLE_WRITE_TOOLS=true` 后才会注册 Watchlist
和 Supplier 写工具；HTTP 部署仍需按调用者身份和 scope 授权。

| 工具名称 | 模块 | 说明 |
| --- | --- | --- |
| `last_leaks` | 凭证泄露 | 查询目标域名最近 1-30 天的泄露记录 |
| `threat_feed` | 威胁情报 | 查询暗网情报、公开新闻，或获取类别、行业、网络分类及记录数 |
| `threat_feed_darkweb_chatters` | 威胁情报 | 查询 Darkweb Chatters 数据（需单独授权） |
| `consumer_leaks` | 凭证泄露 | 查询消费者侧窃密日志和组合密码列表 |
| `corporate_leaks` | 凭证泄露 | 查询企业邮箱域相关凭证 |
| `database_leaks` | 凭证泄露 | 查询第三方数据库泄露中的企业凭证 |
| `overall_stats` | 统计分析 | 查询聚合指标和事件时间线 |
| `ip_leaks` | 实体检索 | 按 IP 查询窃密日志中的凭证记录 |
| `computer_leaks` | 实体检索 | 按主机名查询窃密日志中的凭证记录 |
| `username_leaks` | 实体检索 | 按用户名或邮箱精确查询凭证记录 |
| `lookalike_domains` | 品牌保护 | 查询近似域名和品牌仿冒域名 |
| `leaks_by_id` | 实体检索 | 按单个或最多 5 个日志 ID 查询完整记录 |
| `watchlist_list` | 监控列表 | 查询监控条目 |
| `watchlist_add` | 监控列表 | 添加监控条目（需启用写工具） |
| `watchlist_remove` | 监控列表 | 移除监控条目（需启用写工具） |
| `watchlist_enable` | 监控列表 | 启用监控条目（需启用写工具） |
| `watchlist_disable` | 监控列表 | 禁用监控条目（需启用写工具） |
| `supplier_list` | 供应商安全 | 查询供应商条目 |
| `supplier_add` | 供应商安全 | 添加供应商条目（需启用写工具） |
| `supplier_remove` | 供应商安全 | 停止跟踪供应商（需启用写工具） |
| `supplier_delete` | 供应商安全 | 永久删除供应商（需启用写工具） |
| `audit_logs` | 审计 | 查询 API Key 调用日志 |
| `card_check` | 支付欺诈 | 按 BIN、发卡机构或国家查询泄露支付卡记录 |

工具直接返回 WhiteIntel 的结构化结果。失败响应会转换为 MCP Tool Execution Error
（`isError=true`），并保留上游消息、HTTP 状态和限流信息。稳定错误码包括
`AUTH_INVALID`、`ENTITLEMENT_REQUIRED`、`QUOTA_EXHAUSTED`、`RATE_LIMITED`、
`INVALID_REQUEST`、`FORBIDDEN`、`UPSTREAM_UNAVAILABLE` 和 `UPSTREAM_ERROR`。

### 按套餐限制工具范围

项目不会通过逐接口试探来猜测账号权限。部署者可以按套餐显式限制可用模块：

```bash
WHITEINTEL_ENABLED_MODULES=credential_exposure,entity_lookup,analytics \
  whiteintel-mcp
```

支持的模块为：`credential_exposure`、`entity_lookup`、`threat_feed`、`analytics`、
`brand_protection`、`watchlist`、`supplier_security`、`audit`、`payment_fraud`。

## 文档资源

`docs/*.md` 会以 `whiteintel://docs/{filename}` 形式暴露为 MCP Resource。客户端可以按需
读取接口说明，例如：

- `whiteintel://docs/consumer-leaks-api.md`
- `whiteintel://docs/threat-feed-api.md`
- `whiteintel://docs/watchlists-api.md`
- `whiteintel://docs/card-check-api.md`

## 请求限制

项目在请求上游前执行参数校验和进程内节流；API Key 权限、套餐、额度和风控结果以
WhiteIntel 返回为准。

| 范围 | 控制方式 |
| --- | --- |
| 全部 WhiteIntel HTTP 请求 | 进程内节流，按 `(endpoint, apikey)` 控制，默认 `0.2 QPS`（同一接口、同一 API Key 每 5 秒 1 次请求） |
| 全部工具 | API Key 从 `WHITEINTEL_API_KEY` 环境变量读取，不暴露为 MCP 工具参数 |
| 分页类接口 | 本地 schema 限制页码为正整数，并按接口文档限制 `limit` 范围 |
| 日期范围参数 | 本地校验 `YYYY-MM-DD` 格式，且 `start_date` / `end_date` 必须成对出现 |
| `leaks_by_id` | 本地限制批量 ID 数量不超过 5 个 |
| `card_check` | 本地限制必须且只能提供一个主选择器：`bin`、`issuer` 或 `country` |

频率控制仅在单个 MCP 进程内生效，多进程之间不共享状态。

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

## 开发与构建

```bash
uv sync --extra dev
uv run pytest
uv run python -m compileall src/whiteintel_mcp
uv build --wheel
```

版本记录见 `CHANGELOG.md`。

## 合规使用

请仅在合法授权范围内查询和处理威胁情报数据，并遵守 WhiteIntel 的 API 服务条款、
订阅权限和额度限制。

使用者应自行确保其数据处理行为符合适用法律和组织政策。

## 许可证

MIT License，见 `LICENSE`。
