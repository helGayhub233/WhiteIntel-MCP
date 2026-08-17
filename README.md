<!-- mcp-name: io.github.helGayhub233/whiteintel-mcp -->

<h1 align="center">WhiteIntel-MCP</h1>

<p align="center">将 WhiteIntel 的凭证泄露、暗网情报、品牌保护和支付欺诈能力接入 MCP 客户端</p>

<p align="center">
  <img src="https://badgen.net/pypi/v/whiteintel-mcp?label=PyPI&color=3775A9&cache=300&version=0.5.0" alt="PyPI v0.5.0"/>
  <img src="https://badgen.net/badge/Python/%3E%3D3.10/3776AB" alt="Python >=3.10"/>
  <img src="https://badgen.net/badge/MCP%20SDK/2.0.0/6F42C1" alt="MCP SDK 2.0.0"/>
  <img src="https://badgen.net/pypi/dm/whiteintel-mcp?label=Downloads&color=2EA44F&cache=86400" alt="PyPI 下载量"/>
  <img src="https://badgen.net/github/license/helGayhub233/WhiteIntel-MCP?label=License&color=blue" alt="许可证"/>
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

### 1. 安装 uv

`uvx`（uv 自带）是 Python 生态中 `npx` 的等价物——在临时隔离环境中下载并运行包，无需全局安装。

```bash
# Linux / macOS（官方安装脚本）
curl -LsSf https://astral.sh/uv/install.sh | sh

# macOS（Homebrew）
brew install uv
```

### 2. 配置 MCP 客户端

将以下配置加入支持 MCP 的客户端（Claude Desktop、Cursor 等），无需预先安装 WhiteIntel-MCP：

```json
{
  "mcpServers": {
    "whiteintel": {
      "command": "uvx",
      "args": ["whiteintel-mcp"],
      "env": {
        "WHITEINTEL_API_KEY": "your_whiteintel_api_key"
      }
    }
  }
}
```

> **版本锁定**（生产环境推荐）：将 `args` 替换为 `["--from", "whiteintel-mcp==0.5.0", "whiteintel-mcp"]`，避免随发布版本浮动。

API Key 可从 [WhiteIntel](https://whiteintel.io) 获取。完整配置示例见 `mcp.json.example` 和 `.env.example`。

### 其他安装方式

**pip：**

```bash
python -m pip install -U whiteintel-mcp
whiteintel-mcp
```

将客户端配置中的 `command` 改为 `whiteintel-mcp`，`args` 设为 `[]`。

**pipx：**

```bash
pipx install whiteintel-mcp
whiteintel-mcp
```

**从源码：**

```bash
git clone https://github.com/helGayhub233/WhiteIntel-MCP.git
cd WhiteIntel-MCP
uv sync
uv run whiteintel-mcp
```

## 配置

### 环境变量

| 环境变量 | 说明 | 默认值 |
| --- | --- | --- |
| `WHITEINTEL_API_KEY` | WhiteIntel API Key，推荐通过客户端 env 注入 | — |
| `WHITEINTEL_BASE_URL` | 上游 API 地址 | `https://api.whiteintel.io` |
| `WHITEINTEL_UPSTREAM_QPS` | 进程内保守节流速率，可按账号合同调整 | `0.2` |
| `WHITEINTEL_MCP_TRANSPORT` | 传输方式：`stdio`、`sse` 或 `streamable-http` | `stdio` |
| `WHITEINTEL_MCP_HOST` | HTTP/SSE 监听地址 | `127.0.0.1` |
| `WHITEINTEL_MCP_PORT` | HTTP/SSE 监听端口 | `8000` |
| `WHITEINTEL_MCP_HTTP_PATH` | Streamable HTTP 路径 | `/mcp` |
| `WHITEINTEL_MCP_SSE_PATH` | SSE 路径 | `/sse` |
| `WHITEINTEL_ENABLED_MODULES` | 逗号分隔的模块 allowlist；留空时开放全部 | — |
| `WHITEINTEL_ENABLE_WRITE_TOOLS` | 是否暴露写工具 | `false` |
| `WHITEINTEL_MCP_ALLOW_INSECURE_REMOTE` | 允许绑定非 loopback 地址（仅可信认证代理场景） | `false` |

### 启用写工具

写工具（watchlist 和 supplier 的增删改操作）默认不暴露，防止意外修改远程资源。

```bash
WHITEINTEL_ENABLE_WRITE_TOOLS=true whiteintel-mcp
```

或在客户端配置中设置：

```json
"env": {
  "WHITEINTEL_API_KEY": "your_key",
  "WHITEINTEL_ENABLE_WRITE_TOOLS": "true"
}
```

启用后注册的 7 个写工具：

| 工具 | 操作 | 风险 |
| --- | --- | --- |
| `watchlist_add` | 新增监控条目 | 可能触发邮件/Slack/Jira 通知 |
| `watchlist_remove` | 永久删除监控条目 | 不可逆 |
| `watchlist_enable` | 恢复已暂停监控 | 幂等 |
| `watchlist_disable` | 暂停监控 | 幂等，保留条目 |
| `supplier_add` | 添加供应商跟踪 | 消耗 supplier credit |
| `supplier_remove` | 停止跟踪供应商 | 保留记录 |
| `supplier_delete` | 永久删除供应商 | 不可逆，数据丢失 |

> HTTP/SSE 部署启用写工具后，仍需通过 MCP OAuth 或认证代理按调用者身份授权。

### 按套餐限制工具范围

部署者可按套餐显式限制可用模块，无需逐接口试探权限：

```bash
WHITEINTEL_ENABLED_MODULES=credential_exposure,entity_lookup,analytics \
  whiteintel-mcp
```

支持的模块：`credential_exposure`、`entity_lookup`、`threat_feed`、`analytics`、`brand_protection`、`watchlist`、`supplier_security`、`audit`、`payment_fraud`。

## 工具列表

默认暴露 16 个只读工具；启用写工具后额外注册 7 个写工具（见[启用写工具](#启用写工具)）。

| 工具名称 | 模块 | 说明 |
| --- | --- | --- |
| `last_leaks` | 凭证泄露 | 查询目标域名最近 1-30 天的泄露记录 |
| `consumer_leaks` | 凭证泄露 | 查询消费者侧窃密日志和组合密码列表 |
| `corporate_leaks` | 凭证泄露 | 查询企业邮箱域相关凭证 |
| `database_leaks` | 凭证泄露 | 查询第三方数据库泄露中的企业凭证 |
| `threat_feed` | 威胁情报 | 查询暗网情报、公开新闻，或获取类别、行业、网络分类及记录数 |
| `threat_feed_darkweb_chatters` | 威胁情报 | 查询 Darkweb Chatters 数据（需单独授权） |
| `overall_stats` | 统计分析 | 查询聚合指标和事件时间线 |
| `ip_leaks` | 实体检索 | 按 IP 查询窃密日志中的凭证记录 |
| `computer_leaks` | 实体检索 | 按主机名查询窃密日志中的凭证记录 |
| `username_leaks` | 实体检索 | 按用户名或邮箱精确查询凭证记录 |
| `leaks_by_id` | 实体检索 | 按单个或最多 5 个日志 ID 查询完整记录 |
| `lookalike_domains` | 品牌保护 | 查询近似域名和品牌仿冒域名 |
| `watchlist_list` | 监控列表 | 查询监控条目 |
| `watchlist_add` | 监控列表 | 添加监控条目（默认关闭） |
| `watchlist_remove` | 监控列表 | 移除监控条目（默认关闭） |
| `watchlist_enable` | 监控列表 | 启用监控条目（默认关闭） |
| `watchlist_disable` | 监控列表 | 禁用监控条目（默认关闭） |
| `supplier_list` | 供应商安全 | 查询供应商条目 |
| `supplier_add` | 供应商安全 | 添加供应商条目（默认关闭） |
| `supplier_remove` | 供应商安全 | 停止跟踪供应商（默认关闭） |
| `supplier_delete` | 供应商安全 | 永久删除供应商（默认关闭） |
| `audit_logs` | 审计 | 查询 API Key 调用日志 |
| `card_check` | 支付欺诈 | 按 BIN、发卡机构或国家查询泄露支付卡记录 |

工具直接返回 WhiteIntel 的结构化结果。失败响应会转换为 MCP Tool Execution Error（`isError: true`），并保留上游消息、HTTP 状态和限流信息。稳定错误码：`AUTH_INVALID`、`ENTITLEMENT_REQUIRED`、`QUOTA_EXHAUSTED`、`RATE_LIMITED`、`INVALID_REQUEST`、`FORBIDDEN`、`UPSTREAM_UNAVAILABLE`、`UPSTREAM_ERROR`。

## HTTP 部署

本地客户端通常使用默认的 `stdio` 传输。需要向其他进程提供服务时，可启动 Streamable HTTP endpoint：

```bash
WHITEINTEL_API_KEY=YOUR_KEY whiteintel-mcp \
  --transport streamable-http \
  --host 127.0.0.1 \
  --port 8000 \
  --streamable-http-path /mcp
```

HTTP/SSE 默认只允许绑定 loopback 地址。对外监听前必须通过前置代理或嵌入式 MCP Host 完成认证；`WHITEINTEL_MCP_ALLOW_INSECURE_REMOTE=true` 仅用于已有可信认证代理的场景。嵌入部署时，`create_server()` 支持 MCP SDK 的 `AuthSettings` 和 `TokenVerifier`。

SDK 2.0.0 已移除 `mount_path`。需要挂载到现有 ASGI 应用时，请使用 `streamable_http_app()` 并由宿主应用管理 lifespan。

## 请求限制

项目在请求上游前执行参数校验和进程内节流；API Key 权限、套餐、额度和风控结果以 WhiteIntel 返回为准。

| 范围 | 控制方式 |
| --- | --- |
| 全部 HTTP 请求 | 进程内保守节流，按 `(上游路径, apikey)` 控制，默认 `0.2 QPS` |
| 全部工具 | API Key 从环境变量读取，不暴露为工具参数 |
| 分页类接口 | 本地 schema 限制页码为正整数，并按接口文档限制 `limit` 范围 |
| 日期范围参数 | 本地校验 `YYYY-MM-DD`；泄露检索要求成对，Threat Feed 允许独立提供 |
| `leaks_by_id` | 本地限制批量 ID 不超过 5 个 |
| `card_check` | 本地限制必须且只能提供一个主选择器：`bin`、`issuer` 或 `country` |

频率控制仅在单个 MCP 进程内生效，多进程之间不共享状态。

## 文档资源

`docs/*.md` 以 `whiteintel://docs/{filename}` 形式暴露为 MCP Resource，客户端可按需读取：

- `whiteintel://docs/consumer-leaks-api.md`
- `whiteintel://docs/threat-feed-api.md`
- `whiteintel://docs/watchlists-api.md`
- `whiteintel://docs/card-check-api.md`

## 项目结构

```text
src/whiteintel_mcp/
  server.py                    # MCPServer 入口、工具注册、resources 注册
  cli.py                       # CLI 兼容入口
  tool_errors.py               # 上游错误分类和 MCP ToolError 转换
  tool_policy.py               # 模块 allowlist 和写工具暴露策略
  models/
    common.py                  # 共享 Pydantic mixin 和字段校验
    endpoints.py               # 各 WhiteIntel endpoint 请求模型
    responses.py               # 稳定的 MCP 输出包装
  services/
    whiteintel_client.py       # 上游 HTTP client 和 429 延迟重试处理
    upstream_rate_limiter.py   # 进程内请求节流
```

## 开发

```bash
# 编译检查
python -m compileall src/whiteintel_mcp

# 运行测试
uv run python -m unittest discover -s tests -v

# 构建 wheel
uv build --wheel
```

项目兼容 MCP `2026-07-28` 和 `2025-11-25`；版本记录见 `CHANGELOG.md`。

## 合规使用

请仅在合法授权范围内查询和处理威胁情报数据，并遵守 WhiteIntel 的 API 服务条款、订阅权限和额度限制。使用者应自行确保其数据处理行为符合适用法律和组织政策。

## 许可证

MIT License，见 `LICENSE`。
