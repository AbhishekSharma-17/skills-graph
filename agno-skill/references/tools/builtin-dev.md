# Developer Toolkits

Pre-built toolkits for code execution, file operations, DevOps, and developer services.

## Python

Execute Python code, manage files, and install packages.

```python
from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools.python import PythonTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[PythonTools(base_dir="/home/user/projects")],
    show_tool_calls=True,
)
agent.print_response("Create a script that generates Fibonacci numbers and run it")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_dir` | `str` | `None` | Base directory for operations |
| `safe_globals` | `dict` | `None` | Safe global variables for execution |
| `safe_locals` | `dict` | `None` | Safe local variables for execution |

**Functions:** `save_to_file_and_run`, `run_python_file_return_variable`, `read_file`, `list_files`, `run_python_code`, `pip_install_package`

---

## Shell

Execute shell commands with directory scoping.

```python
from agno.tools.shell import ShellTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[ShellTools(base_dir="/home/user")],
)
agent.print_response("List all Python files in the current directory")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_dir` | `str` | `None` | Base directory for execution |
| `enable_run_shell_command` | `bool` | `True` | Enable shell execution |
| `all` | `bool` | `False` | Enable all functions |

**Functions:** `run_shell_command`

---

## File

File system operations — read, write, search, and manage files.

```python
from agno.tools.file import FileTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[FileTools(base_dir="/home/user/documents")],
)
agent.print_response("Read the contents of config.yaml and list all .py files")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_dir` | `str` | `None` | Base directory for operations |
| `enable_save_file` | `bool` | `True` | Save/create files |
| `enable_read_file` | `bool` | `True` | Read file contents |
| `enable_read_file_chunks` | `bool` | `True` | Read large files in chunks |
| `enable_replace_file_chunk` | `bool` | `True` | Replace content chunks |
| `enable_delete_file` | `bool` | `False` | Delete files (disabled by default) |
| `enable_list_files` | `bool` | `True` | List directory contents |
| `enable_search_files` | `bool` | `True` | Search file contents |
| `expose_base_directory` | `bool` | `False` | Show base dir to agent |
| `max_file_length` | `int` | `10000000` | Max file size (bytes) |
| `max_file_lines` | `int` | `100000` | Max file lines |

**Functions:** `save_file`, `read_file`, `read_file_chunks`, `replace_file_chunk`, `delete_file`, `list_files`

---

## Calculator

Basic math operations for agents that need arithmetic.

```python
from agno.tools.calculator import CalculatorTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[CalculatorTools()],
)
agent.print_response("What is the factorial of 20?")
```

**Functions:** `add`, `subtract`, `multiply`, `divide`, `exponentiate`, `factorial`, `is_prime`, `square_root`

---

## GitHub

Repository management, pull requests, issues, and code search.

```bash
uv pip install -U PyGithub
export GITHUB_ACCESS_TOKEN=your_token
```

```python
from agno.tools.github import GithubTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[GithubTools()],
)
agent.print_response("Search for popular Python AI agent frameworks on GitHub")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `access_token` | `str` | env var | GitHub personal access token |
| `base_url` | `str` | `None` | GitHub Enterprise base URL |

**Functions:** `search_repositories`, `list_repositories`, `get_repository`, `list_pull_requests`, `get_pull_request`, `get_pull_request_changes`, `create_issue`

---

## Docker

Container, image, volume, and network management.

```bash
uv pip install -U docker
```

```python
from agno.tools.docker import DockerTools

agent = Agent(
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[DockerTools(
        enable_container_management=True,
        enable_image_management=True,
        enable_volume_management=True,
        enable_network_management=True,
    )],
)
agent.print_response("List all running containers and their status")
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_container_management` | `bool` | `True` | Container ops |
| `enable_image_management` | `bool` | `True` | Image ops |
| `enable_volume_management` | `bool` | `False` | Volume ops |
| `enable_network_management` | `bool` | `False` | Network ops |

**Container functions:** `list_containers`, `start_container`, `stop_container`, `remove_container`, `get_container_logs`, `inspect_container`, `run_container`, `exec_in_container`

**Image functions:** `list_images`, `pull_image`, `remove_image`, `build_image`, `tag_image`, `inspect_image`

**Volume functions:** `list_volumes`, `create_volume`, `remove_volume`, `inspect_volume`

**Network functions:** `list_networks`, `create_network`, `remove_network`, `inspect_network`, `connect_container_to_network`, `disconnect_container_from_network`

---

## Other Developer Toolkits

| Toolkit | Import | Install | Description |
|---------|--------|---------|-------------|
| Bitbucket | `from agno.tools.bitbucket import BitbucketTools` | — | Bitbucket repos & PRs |
| E2B | `from agno.tools.e2b import E2BTools` | `uv pip install e2b-code-interpreter` | Sandboxed code execution |
| Sleep | `from agno.tools.sleep import SleepTools` | — | Pause execution |
| Local FS | `from agno.tools.local_fs import LocalFSTools` | — | Local file system access |
