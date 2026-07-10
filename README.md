<h1 align="center">WhiteIntel-MCP</h1>

<p align="center">基于 <code>FastMCP</code> 编写的 WhiteIntel 威胁情报 MCP Server，覆盖凭证泄露、暗网情报、近似域名、监控列表、供应商安全和审计日志</p>

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

API Key 获取入口：`https://whiteintel.io`

## 工具列表

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
| `watchlist_manage` | Watchlist | 管理监控列表条目 |
| `supplier` | Supplier Security | 管理供应商安全条目 |
| `audit_logs` | Audit | 查询 API Key 调用审计日志 |

## 开发

```bash
uv sync --extra dev
uv run pytest
```

项目使用 Pydantic 在调用上游前进行参数校验，并使用内存限流器按 `(endpoint, apikey)` 控制请求间隔，避免 MCP 客户端并发调用时过快触发 WhiteIntel 上游限制。
