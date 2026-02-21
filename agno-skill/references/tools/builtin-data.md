# Data Toolkits

Pre-built toolkits for databases, data analysis, and structured data operations.

## DuckDB

In-process SQL analytics with full-text search and S3 support.

```bash
uv pip install -U duckdb
```

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.duckdb import DuckDbTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[DuckDbTools(db_path="analytics.db")],
    show_tool_calls=True,
)
agent.print_response("Show me all tables and summarize the users table")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_path` | `str` | `None` | Database file path (None = in-memory) |
| `connection` | `DuckDBPyConnection` | `None` | Existing connection |
| `init_commands` | `list[str]` | `None` | SQL commands to run on init |
| `read_only` | `bool` | `False` | Read-only mode |
| `enable_show_tables` | `bool` | `True` | List tables |
| `enable_describe_table` | `bool` | `True` | Table structure |
| `enable_run_query` | `bool` | `True` | Execute SQL |
| `enable_inspect_query` | `bool` | `True` | Query plan |
| `enable_summarize_table` | `bool` | `True` | Compute aggregates |
| `enable_create_table_from_path` | `bool` | `True` | Load from files |
| `enable_export_table_to_path` | `bool` | `True` | Export tables |
| `enable_create_fts_index` | `bool` | `False` | Full-text search index |
| `enable_full_text_search` | `bool` | `False` | Full-text search |

**Functions:** `show_tables`, `describe_table`, `run_query`, `inspect_query`, `summarize_table`, `create_table_from_path`, `export_table_to_path`, `load_s3_path_to_table`, `load_s3_csv_to_table`, `create_fts_index`, `full_text_search`

---

## CSV

Query and analyze CSV files using DuckDB SQL engine.

```python
from agno.tools.csv_tools import CsvTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[CsvTools(csvs=["data/sales.csv", "data/customers.csv"])],
)
agent.print_response("What are the top 10 customers by total sales?")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `csvs` | `list` | `[]` | CSV file paths to process |
| `row_limit` | `int` | `None` | Max rows to process |
| `enable_read_csv_file` | `bool` | `True` | Read file contents |
| `enable_list_csv_files` | `bool` | `True` | List available files |
| `enable_get_columns` | `bool` | `True` | Get column names |
| `enable_query_csv_file` | `bool` | `True` | SQL queries on CSV data |

**Functions:** `list_csv_files`, `read_csv_file`, `get_columns`, `query_csv_file`

---

## Pandas

DataFrame operations for data analysis and transformation.

```python
from agno.tools.pandas import PandasTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[PandasTools()],
)
agent.print_response("Create a dataframe with monthly revenue data and calculate growth rates")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_create_pandas_dataframe` | `bool` | `True` | Create DataFrames |
| `enable_run_dataframe_operation` | `bool` | `True` | Run operations |

**Functions:** `create_pandas_dataframe`, `run_dataframe_operation`

---

## SQL (Generic)

Execute SQL queries against any database via SQLAlchemy.

```python
from agno.tools.sql import SQLTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[SQLTools(db_url="sqlite:///mydb.sqlite")],
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db_url` | `str` | required | SQLAlchemy connection string |
| `db_engine` | `Engine` | `None` | Existing SQLAlchemy engine |
| `enable_run_sql` | `bool` | `True` | Execute SQL queries |
| `enable_list_tables` | `bool` | `True` | List database tables |
| `enable_describe_table` | `bool` | `True` | Table schema |

---

## Postgres

PostgreSQL-specific toolkit with connection pooling.

```python
from agno.tools.postgres import PostgresTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[PostgresTools(
        host="localhost",
        port=5432,
        db_name="mydb",
        user="admin",
        password="secret",
    )],
)
agent.print_response("Show all tables and describe the users table")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | `str` | `"localhost"` | Database host |
| `port` | `int` | `5432` | Database port |
| `db_name` | `str` | required | Database name |
| `user` | `str` | required | Username |
| `password` | `str` | required | Password |
| `enable_run_sql` | `bool` | `True` | Execute SQL |
| `enable_list_tables` | `bool` | `True` | List tables |
| `enable_describe_table` | `bool` | `True` | Describe tables |

---

## Other Data Toolkits

| Toolkit | Import | Install | Description |
|---------|--------|---------|-------------|
| Redshift | `from agno.tools.redshift import RedshiftTools` | — | AWS Redshift queries |
| BigQuery | `from agno.tools.bigquery import BigQueryTools` | `uv pip install google-cloud-bigquery` | Google BigQuery |
| Neo4j | `from agno.tools.neo4j import Neo4jTools` | `uv pip install neo4j` | Graph database queries |
| Snowflake | `from agno.tools.snowflake import SnowflakeTools` | `uv pip install snowflake-connector-python` | Snowflake data warehouse |
| MCP Toolbox | `from agno.tools.mcp_toolbox import MCPToolboxTools` | — | MCP-based database access |
