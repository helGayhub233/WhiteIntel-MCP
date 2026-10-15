<!-- mcp-name: io.github.helGayhub233/whiteintel-mcp -->

<h1 align="center">WhiteIntel-MCP</h1>

<p align="center">将 WhiteIntel 的凭证泄露、暗网情报、品牌保护和支付欺诈能力接入 MCP 客户端</p>

<p align="center">
  <img src="https://badgen.net/pypi/v/whiteintel-mcp?label=PyPI&color=3775A9&cache=300&version=0.6.0" alt="PyPI v0.6.0"/>
  <img src="https://badgen.net/badge/Python/%3E%3D3.10/3776AB" alt="Python >=3.10"/>
  <img src="https://badgen.net/badge/MCP%20SDK/2.3.0/6F42C1" alt="MCP SDK 2.3.0"/>
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

> **版本锁定**（生产环境推荐）：将 `args` 替换为 `["--from", "whiteintel-mcp==0.6.0", "whiteintel-mcp"]`，避免随发布版本浮动。

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
| `WHITEINTEL_UPSTREAM_QPS` | 进程内保守节流速率，可按账号合同调整 | `0.3` |
| `WHITEINTEL_MCP_TRANSPORT` | 本地使用 `stdio`，HTTP 部署使用 `streamable-http`；`sse` 已废弃，仅作旧客户端兼容 | `stdio` |
| `WHITEINTEL_MCP_HOST` | HTTP/SSE 监听地址 | `127.0.0.1` |
| `WHITEINTEL_MCP_PORT` | HTTP/SSE 监听端口 | `8000` |
| `WHITEINTEL_MCP_HTTP_PATH` | Streamable HTTP 路径 | `/mcp` |
| `WHITEINTEL_MCP_SSE_PATH` | 已废弃的旧版 HTTP+SSE 路径 | `/sse` |
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
| `username_leaks` | 实体检索 | 按用户名或邮箱精确查询凭证记录（`type=database` 可含第三方数据库泄露） |
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

工具使用统一的 `WhiteIntelResponse` 信封，`structuredContent` 与 `json.loads(content[0].text)` 完全相同。参数校验、未知工具及上游失败均返回 `success:false`、`isError:true` 和结构化 `error`，其中 `error.code`、`error.message`、`error.retryable` 可直接读取；限流错误还提供 `error.retry_after`。校验详情不包含被拒绝的参数值或 API Key。

稳定错误码：`AUTH_INVALID`、`ENTITLEMENT_REQUIRED`、`QUOTA_EXHAUSTED`、`RATE_LIMITED`、`INVALID_REQUEST`、`FORBIDDEN`、`UPSTREAM_UNAVAILABLE`、`UPSTREAM_ERROR`、`TOOL_NOT_FOUND`、`INTERNAL_ERROR`。协议级 JSON-RPC 错误保留其原始错误码。

每份公开 JSON 最多 64 KiB，单个字符串最多保留 4096 字符；预算针对文本和结构化内容共享的 JSON，传输两份内容的总字节数可能更大。本地裁剪会返回 `truncated:true`、`completeness:partial`、`next_action:refine_query`，并在 `output` 中报告收到的记录数、省略数和裁剪字段数。此时应缩小查询范围或减少单页条数，再考虑翻页，避免跳过本页被省略的记录。失败详情被裁剪时仍保持 `next_action:stop`。

`tools/list` 的 `outputSchema` 仅声明 `{"type":"object"}`，避免为每个工具重复发送完整信封定义。每个工具的 `_meta["whiteintel/outputSchema"]` 指向 `whiteintel://schemas/response`；需要字段定义或完整校验时，按需读取该 resource。服务端仍使用完整 `WhiteIntelResponse` 校验所有公开结果，输入 schema 仍保留参数约束。在现代协议下，工具清单、发现结果及其他清单可私有缓存 5 分钟，静态文档和 schema 资源可私有缓存 1 小时；工具调用结果不启用缓存。

未知工具继续返回 `isError:true` 和结构化 `TOOL_NOT_FOUND`，与 SDK 的执行错误处理保持一致；这项兼容选择与现代类型文档中 `InvalidParamsError` 的描述存在差异。

### 查询与可访问内容工作流

相关只读工具的 `description` 内置“按实际输入选源 → 合并多源结果 → 核验 URL 与内容 → 输出实际读取的原始片段（不脱敏）”的客户端工作流，入口使用 WhiteIntel 自身支持的参数：

| 用户输入 | 查询与后续来源 |
| --- | --- |
| 域名 / 邮件域名 | `consumer_leaks`、`corporate_leaks`、`database_leaks` 按用途互补查询；近期记录用 `last_leaks`，品牌仿冒用 `lookalike_domains` |
| 单个 IPv4 / IPv6 | `ip_leaks`；仅使用结果实际给出的主机名、用户名和泄露 ID，继续调用对应实体工具 |
| 主机名 / 用户名 / 邮箱 | `computer_leaks` / `username_leaks`；按返回的 IP、主机名或 ID 选择后续来源 |
| 1–5 个已知泄露 ID | `leaks_by_id` 获取详情，再按返回的实体值补充查询 |
| 搜索词与情报过滤条件 | `threat_feed`；有对应权限时补充 `threat_feed_darkweb_chatters`，保留帖子或新闻来源链接；taxonomy 仅返回分类标签 |
| 域名 + 指标 | `overall_stats` 提供概况；需要 URL 证据时再查询对应原始记录工具 |
| BIN / 发卡机构 / 国家 | `card_check`，按卡片数据本身筛选；无来源 URL 时标记 `not_applicable` |
| 监控 / 供应商列表过滤条件 | `watchlist_list` / `supplier_list`，根据列表中的实体类型转入对应查询工具 |

1. 只查询当前 `tools/list` 中已开放且有权限的相关来源。WhiteIntel 不提供 `user_info` 预检，额度与失败分类以返回的 quota 字段和 `error.code` 为准；记录覆盖缺口。不同数据集可能重叠，不作为独立来源的重复佐证。
2. 每个来源先取一页，支持 `limit` 时先用 20；默认整体最多 100 条记录、3 个由结果派生的查询及 5 个 URL 检查。根据 `completeness` / `next_action` 决定后续，不自动穷举分页。
3. 合并结果并保留工具名、记录 ID、时间和原始 URL，去重候选链接。帖子和新闻优先使用 `published_url` / `link`；凭证记录的 `url` 是曾使用凭证的站点，不能据此认定该站点公开托管泄露数据。仅有域名时，可构造首页候选 URL，但需标记为“派生”。
4. 用 curl / wget 等轻量命令行 HTTP 命令检查公开 HTTP(S) 页面（不使用浏览器等重工具），记录最终 URL、HTTP 状态及检查时间，并读取实际内容。HTTP 200 不等于内容验证；登录、验证码或拦截页面标记 `restricted`，请求失败标记 `unreachable`。无法用命令行命令获取的源（包括不支持的 `.onion` 传输）标记 `unverified`，无 URL 时标记 `not_applicable`；不能编造片段。
5. 最终答复列出来源工具 / 记录 ID、原始及最终 URL、`checked_at`、HTTP 状态、可访问性和实际读取到的简短相关片段（按原文原样输出，不脱敏）。API 记录摘要与网页片段分开呈现；没有可核验的片段时明确说明，失败和未验证链接保留状态。

URL 核验及最终报告是客户端编排步骤（使用 curl/wget 等命令行命令）；WhiteIntel MCP 工具本身返回 API 数据，不执行网页访问。

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

`--transport sse` 是已废弃的旧版 HTTP+SSE 兼容入口。新部署使用 `--transport streamable-http`；该传输本身仍可使用 SSE 流式响应，区别见 [MCP 传输规范](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)。

SDK 2.3.0 不提供 `mount_path`。需要挂载到现有 ASGI 应用时，请使用 `streamable_http_app()` 并由宿主应用管理 lifespan。

## 请求限制

项目在请求上游前执行参数校验和进程内节流；API Key 权限、套餐、额度和风控结果以 WhiteIntel 返回为准。

| 范围 | 控制方式 |
| --- | --- |
| 全部 HTTP 请求 | 进程内保守节流，按 `(上游路径, apikey)` 控制，默认 `0.3 QPS` |
| 全部工具 | API Key 从环境变量读取，不暴露为工具参数 |
| 分页类接口 | 本地 schema 限制页码为正整数，并按接口文档限制 `limit` 范围 |
| 日期范围参数 | 本地校验 `YYYY-MM-DD`；泄露检索要求成对，Threat Feed 允许独立提供 |
| `leaks_by_id` | 本地限制批量 ID 不超过 5 个 |
| `card_check` | 本地限制必须且只能提供一个主选择器：`bin`、`issuer` 或 `country` |
| 所有工具输入 | 拒绝额外参数；BIN 仅允许 6 或 8 位数字；日期配对和批量 ID 数量也体现在输入 schema 中 |

429 重试遵守完整的 `Retry-After`，并与后续同路径、同 API Key 请求共享冷却状态。每次重试重新经过本地节流；等待超过 30 秒时直接返回 `RATE_LIMITED` 和剩余冷却时间，不提前重试。短冷却最多自动重试一次。

频率控制仅在单个 MCP 进程内生效，多进程之间不共享状态。

## 文档资源

`docs/*.md` 以 `whiteintel://docs/{filename}` 形式暴露为 MCP Resource，客户端可按需读取（已镜像官方 2026-10 新增的 API Sandbox 全套页面）：

- `whiteintel://docs/consumer-leaks-api.md`
- `whiteintel://docs/threat-feed-api.md`
- `whiteintel://docs/watchlists-api.md`
- `whiteintel://docs/card-check-api.md`
- `whiteintel://docs/sandbox-environment-overview.md`
- `whiteintel://docs/sandbox-database-leaks.md`

提示：将 `WHITEINTEL_BASE_URL` 设为 `https://api.whiteintel.io/sandbox` 即可指向官方沙箱（覆盖 9 个合成数据端点，不消耗生产配额；沙箱未提供的端点会返回 404）。

## 项目结构

```text
src/whiteintel_mcp/
  server.py                    # MCPServer 入口、工具注册、resources 注册
  mcp_server.py                # SDK 2.3 错误信封、严格输入和缓存配置
  responses.py                 # 结果计数、分页判断和公开 JSON 输出预算
  cli.py                       # CLI 兼容入口
  tool_errors.py               # 上游错误分类和结构化错误信封
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
# 安装锁定的运行和测试依赖（dev 组显式声明 jsonschema）
uv sync --locked --dev

# 编译检查
python -m compileall src/whiteintel_mcp

# 运行测试
uv run --locked --no-sync python -m unittest discover -s tests -v

# 构建 wheel
uv build --wheel
```

上述 unittest 测试包含协议协商、完整输出 schema 校验、缓存提示及工具清单体积回归检查，可在 Python 3.10–3.13 上本地运行。

版本记录见 `CHANGELOG.md`。

发布到官方 MCP Registry 前，还需补充并校验 `server.json`，完成包归属验证并执行发布；README 的 `mcp-name` 注释和用于 Glama 的 `glama.json` 均不能替代官方清单。具体步骤见 [官方发布指南](https://modelcontextprotocol.io/registry/quickstart)。

## 合规使用

请仅在合法授权范围内查询和处理威胁情报数据，并遵守 WhiteIntel 的 API 服务条款、订阅权限和额度限制。使用者应自行确保其数据处理行为符合适用法律和组织政策。

## 许可证

MIT License，见 `LICENSE`。
