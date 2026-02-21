# Workflow Visualization — Diagrams, Mermaid, GraphViz

## Overview

Visualize workflow structure and execution flow using Mermaid diagrams, GraphViz, and built-in helper functions. Visualization aids debugging, documentation, and understanding complex workflows.

## get_mermaid_diagram() Method

Generate Mermaid diagram from workflow:

```python
from agent_framework.workflows import Workflow

# Build workflow
workflow = Workflow()
workflow.add_node("input", input_processor)
workflow.add_node("process", processor)
workflow.add_node("output", output_handler)

workflow.connect("input", "process")
workflow.connect("process", "output")

workflow.set_entry_node("input")
workflow.set_exit_node("output")

# Generate Mermaid diagram
mermaid_diagram = workflow.get_mermaid_diagram()
print(mermaid_diagram)

# Output:
# graph LR
#     input[input]
#     process[process]
#     output[output]
#     input --> process
#     process --> output
#     style input fill:#4CAF50
#     style output fill:#FF5722
```

## Mermaid Diagram Generation from Workflow Graph

### Basic Diagram

```python
def generate_mermaid_diagram(workflow: Workflow) -> str:
    """Generate Mermaid diagram from workflow."""
    lines = ["graph LR"]

    # Add nodes
    for node_name in workflow.nodes:
        lines.append(f'    {node_name}["{node_name}"]')

    # Add edges
    for edge in workflow.edges:
        lines.append(f"    {edge.source} --> {edge.target}")

    # Style entry/exit
    lines.append(f"    style {workflow.entry_node} fill:#4CAF50,stroke:#333,stroke-width:2px")
    lines.append(f"    style {workflow.exit_node} fill:#FF5722,stroke:#333,stroke-width:2px")

    return "\n".join(lines)

# Usage
diagram = generate_mermaid_diagram(workflow)

# Render in Mermaid Live Editor or markdown
print(f"""
```mermaid
{diagram}
```
""")
```

### With Edge Labels (Conditions)

```python
def generate_mermaid_with_conditions(workflow: Workflow) -> str:
    """Generate Mermaid diagram with conditional edge labels."""
    lines = ["graph LR"]

    # Add nodes
    for node_name in workflow.nodes:
        lines.append(f'    {node_name}["{node_name}"]')

    # Add edges with conditions
    for edge in workflow.edges:
        if hasattr(edge, 'condition') and edge.condition:
            # Conditional edge with label
            label = edge.condition.replace('"', "'")
            lines.append(f'    {edge.source} -->|{label}| {edge.target}')
        else:
            # Regular edge
            lines.append(f"    {edge.source} --> {edge.target}")

    # Styling
    lines.append(f"    style {workflow.entry_node} fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff")
    lines.append(f"    style {workflow.exit_node} fill:#FF5722,stroke:#333,stroke-width:2px,color:#fff")

    return "\n".join(lines)

# Example workflow with conditions
workflow = Workflow()
workflow.add_node("input", input_proc)
workflow.add_node("classify", classifier)
workflow.add_node("urgent", urgent_handler)
workflow.add_node("normal", normal_handler)
workflow.add_node("output", output_formatter)

# Edges with conditions
workflow.connect("input", "classify")
workflow.add_edge("classify", "urgent", condition='priority == "high"')
workflow.add_edge("classify", "normal", condition='priority == "normal"')
workflow.connect("urgent", "output")
workflow.connect("normal", "output")

diagram = generate_mermaid_with_conditions(workflow)
```

## GraphViz Export

Generate DOT format for GraphViz:

```python
def generate_graphviz(workflow: Workflow) -> str:
    """Generate GraphViz DOT format from workflow."""
    lines = [
        "digraph workflow {",
        '    rankdir="LR";',
        '    node [shape=box, style=filled, fillcolor=lightblue];',
    ]

    # Add nodes with styling
    for node_name in workflow.nodes:
        if node_name == workflow.entry_node:
            lines.append(f'    {node_name} [label="{node_name}", fillcolor=lightgreen];')
        elif node_name == workflow.exit_node:
            lines.append(f'    {node_name} [label="{node_name}", fillcolor=lightcoral];')
        else:
            lines.append(f'    {node_name} [label="{node_name}"];')

    # Add edges
    for edge in workflow.edges:
        if hasattr(edge, 'condition') and edge.condition:
            lines.append(f'    {edge.source} -> {edge.target} [label="{edge.condition}"];')
        else:
            lines.append(f"    {edge.source} -> {edge.target};")

    lines.append("}")
    return "\n".join(lines)

# Usage
dot_graph = generate_graphviz(workflow)

# Save and render
with open("workflow.dot", "w") as f:
    f.write(dot_graph)

# Render with: dot -Tpng workflow.dot -o workflow.png
```

## pip install agent-framework[viz]

Install visualization support:

```bash
pip install agent-framework[viz]
```

This installs:
- `mermaid-cli` for rendering Mermaid to images
- `graphviz` Python bindings
- Additional visualization utilities

## visualize_workflow() Helper Function

Convenience function for visualization:

```python
from agent_framework.workflows import visualize_workflow, VisualizationFormat

# Generate diagram (auto-detect format)
mermaid_diagram = visualize_workflow(workflow, format="mermaid")
print(mermaid_diagram)

# Generate GraphViz
graphviz_diagram = visualize_workflow(workflow, format="graphviz")
print(graphviz_diagram)

# Generate PlantUML
plantuml_diagram = visualize_workflow(workflow, format="plantuml")
```

### Advanced Visualization Helper

```python
def visualize_workflow_with_options(
    workflow: Workflow,
    format: str = "mermaid",
    include_timing: bool = False,
    include_descriptions: bool = False,
    output_file: str = None
) -> str:
    """
    Generate workflow visualization with options.

    Args:
        workflow: The workflow to visualize
        format: "mermaid", "graphviz", or "plantuml"
        include_timing: Add timing info if available
        include_descriptions: Add executor descriptions
        output_file: Optional file to save to

    Returns:
        Visualization string
    """
    if format == "mermaid":
        diagram = generate_mermaid_diagram(workflow)
    elif format == "graphviz":
        diagram = generate_graphviz(workflow)
    else:
        diagram = generate_mermaid_diagram(workflow)

    if output_file:
        with open(output_file, "w") as f:
            f.write(diagram)

    return diagram

# Usage
diagram = visualize_workflow_with_options(
    workflow,
    format="mermaid",
    include_descriptions=True,
    output_file="workflow.mmd"
)
```

## Styling Entry/Exit Nodes

Control visual styling of special nodes:

```python
def style_workflow_diagram(
    workflow: Workflow,
    entry_color: str = "#4CAF50",
    exit_color: str = "#FF5722",
    node_color: str = "#2196F3"
) -> str:
    """Generate Mermaid diagram with custom styling."""
    lines = ["graph LR"]

    # Add nodes
    for node_name in workflow.nodes:
        lines.append(f'    {node_name}["{node_name}"]')

    # Add edges
    for edge in workflow.edges:
        lines.append(f"    {edge.source} --> {edge.target}")

    # Apply styling
    for node_name in workflow.nodes:
        if node_name == workflow.entry_node:
            color = entry_color
            label = "🟢 Entry"
        elif node_name == workflow.exit_node:
            color = exit_color
            label = "🔴 Exit"
        else:
            color = node_color
            label = node_name

        lines.append(f"    style {node_name} fill:{color},stroke:#333,stroke-width:2px,color:#fff")

    return "\n".join(lines)

# Usage with custom colors
diagram = style_workflow_diagram(
    workflow,
    entry_color="#00AA00",
    exit_color="#AA0000",
    node_color="#0099FF"
)
```

## Concurrent Workflow Visualization

Visualize parallel execution paths:

```python
def visualize_concurrent_workflow(workflow: Workflow) -> str:
    """Visualize workflow with parallel execution indicators."""
    lines = ["graph LR"]

    # Add nodes
    for node_name in workflow.nodes:
        lines.append(f'    {node_name}["{node_name}"]')

    # Detect fan-out nodes (multiple outgoing edges)
    outgoing_edges = {}
    for edge in workflow.edges:
        outgoing_edges.setdefault(edge.source, []).append(edge.target)

    # Add edges with parallel indicators
    for edge in workflow.edges:
        target_count = len(outgoing_edges.get(edge.source, []))
        if target_count > 1:
            # Parallel edge indicator
            lines.append(f'    {edge.source} -->|parallel| {edge.target}')
        else:
            lines.append(f"    {edge.source} --> {edge.target}")

    # Highlight fan-out nodes
    for node, targets in outgoing_edges.items():
        if len(targets) > 1:
            lines.append(f"    style {node} fill:#FFC107,stroke:#333,stroke-width:2px")

    # Highlight merge nodes (multiple incoming edges)
    incoming_edges = {}
    for edge in workflow.edges:
        incoming_edges.setdefault(edge.target, []).append(edge.source)

    for node, sources in incoming_edges.items():
        if len(sources) > 1:
            lines.append(f"    style {node} fill:#9C27B0,stroke:#333,stroke-width:2px,color:#fff")

    # Entry/exit styling
    lines.append(f"    style {workflow.entry_node} fill:#4CAF50,stroke:#333,stroke-width:2px")
    lines.append(f"    style {workflow.exit_node} fill:#FF5722,stroke:#333,stroke-width:2px")

    return "\n".join(lines)

# Example concurrent workflow
concurrent_wf = Workflow()
concurrent_wf.add_node("input", input_proc)
concurrent_wf.add_node("branch_a", processor_a)
concurrent_wf.add_node("branch_b", processor_b)
concurrent_wf.add_node("branch_c", processor_c)
concurrent_wf.add_node("merge", merger)
concurrent_wf.add_node("output", output_proc)

# Fan-out
concurrent_wf.connect("input", "branch_a")
concurrent_wf.connect("input", "branch_b")
concurrent_wf.connect("input", "branch_c")

# Fan-in
concurrent_wf.connect("branch_a", "merge")
concurrent_wf.connect("branch_b", "merge")
concurrent_wf.connect("branch_c", "merge")

concurrent_wf.connect("merge", "output")
concurrent_wf.set_entry_node("input")
concurrent_wf.set_exit_node("output")

diagram = visualize_concurrent_workflow(concurrent_wf)
```

## Map-Reduce Visualization

Visualize map-reduce patterns:

```python
def visualize_mapreduce_workflow(
    workflow: Workflow,
    mapper_nodes: list,
    reducer_node: str
) -> str:
    """Visualize map-reduce pattern in workflow."""
    lines = ["graph LR"]

    # Add all nodes
    for node_name in workflow.nodes:
        lines.append(f'    {node_name}["{node_name}"]')

    # Add edges
    for edge in workflow.edges:
        lines.append(f"    {edge.source} --> {edge.target}")

    # Highlight mappers
    for mapper in mapper_nodes:
        lines.append(f"    style {mapper} fill:#FF9800,stroke:#333,stroke-width:2px,color:#fff")

    # Highlight reducer
    lines.append(f"    style {reducer_node} fill:#9C27B0,stroke:#333,stroke-width:2px,color:#fff")

    # Entry/exit
    lines.append(f"    style {workflow.entry_node} fill:#4CAF50,stroke:#333,stroke-width:2px")
    lines.append(f"    style {workflow.exit_node} fill:#FF5722,stroke:#333,stroke-width:2px")

    # Add legend
    lines.append("    subgraph legend[Legend]")
    lines.append('        entry["🟢 Entry/Exit"]')
    lines.append('        mapper["🟠 Mapper"]')
    lines.append('        reducer["🟣 Reducer"]')
    lines.append("    end")

    return "\n".join(lines)

# Example
mapreduce_wf = Workflow()
mapreduce_wf.add_node("split", splitter)
mapreduce_wf.add_node("map_1", mapper_1)
mapreduce_wf.add_node("map_2", mapper_2)
mapreduce_wf.add_node("map_3", mapper_3)
mapreduce_wf.add_node("reduce", reducer)
mapreduce_wf.add_node("output", output_fmt)

mapreduce_wf.connect("split", "map_1")
mapreduce_wf.connect("split", "map_2")
mapreduce_wf.connect("split", "map_3")
mapreduce_wf.connect("map_1", "reduce")
mapreduce_wf.connect("map_2", "reduce")
mapreduce_wf.connect("map_3", "reduce")
mapreduce_wf.connect("reduce", "output")

diagram = visualize_mapreduce_workflow(
    mapreduce_wf,
    mapper_nodes=["map_1", "map_2", "map_3"],
    reducer_node="reduce"
)
```

## Saving Diagrams as Images

Render and save visualization to image files:

```python
from pathlib import Path
import subprocess

def save_mermaid_as_image(
    diagram: str,
    output_file: str,
    format: str = "png"
) -> None:
    """Save Mermaid diagram as image."""
    # Write diagram to temp file
    temp_file = Path(output_file).stem + ".mmd"
    with open(temp_file, "w") as f:
        f.write(diagram)

    # Render with mermaid-cli
    subprocess.run([
        "mmdc",
        "-i", temp_file,
        "-o", output_file,
        "-t", "dark"  # or "default", "dark", "forest", "neutral"
    ])

    # Cleanup
    Path(temp_file).unlink()
    print(f"Diagram saved to {output_file}")

def save_graphviz_as_image(
    dot_graph: str,
    output_file: str,
    format: str = "png"
) -> None:
    """Save GraphViz graph as image."""
    from graphviz import Source

    src = Source(dot_graph)
    src.render(
        filename=output_file.replace(f".{format}", ""),
        format=format,
        cleanup=True
    )
    print(f"Graph saved to {output_file}")

# Usage
diagram = generate_mermaid_diagram(workflow)
save_mermaid_as_image(diagram, "workflow.png", format="png")

graph = generate_graphviz(workflow)
save_graphviz_as_image(graph, "workflow.png")
```

## Using Visualization for Debugging

Interactive debugging with visualizations:

```python
import webbrowser
import http.server
import socketserver
from pathlib import Path

def debug_workflow_with_visualization(workflow: Workflow) -> None:
    """Launch web visualization for debugging."""
    diagram = generate_mermaid_diagram(workflow)

    # Create HTML with Mermaid rendering
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Workflow Visualizer</title>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <style>
            body {{ font-family: Arial; margin: 20px; }}
            .diagram {{ border: 1px solid #ccc; padding: 10px; }}
        </style>
    </head>
    <body>
        <h1>Workflow: {workflow.id}</h1>
        <div class="diagram">
            <div class="mermaid">
{diagram}
            </div>
        </div>
        <h2>Details</h2>
        <ul>
            <li>Entry Node: {workflow.entry_node}</li>
            <li>Exit Node: {workflow.exit_node}</li>
            <li>Total Nodes: {len(workflow.nodes)}</li>
            <li>Total Edges: {len(workflow.edges)}</li>
        </ul>
    </body>
    </html>
    """

    # Write to file
    html_file = Path("workflow_debug.html")
    html_file.write_text(html_content)

    # Open in browser
    webbrowser.open(f"file://{html_file.absolute()}")
    print(f"Opened visualization at {html_file.absolute()}")

# Usage
debug_workflow_with_visualization(workflow)
```

## Visualization with Real-Time Execution

Show workflow execution progress:

```python
async def visualize_workflow_execution(workflow: Workflow, input_data):
    """Visualize workflow with execution progress."""
    diagram = generate_mermaid_diagram(workflow)
    executed_nodes = set()
    errors = {}

    print(f"""
Initial Workflow:
```mermaid
{diagram}
```
    """)

    async for event in workflow.run_stream(input_data):
        if event.type == "output":
            executed_nodes.add(event.executor_id)
            print(f"✓ Executed: {event.executor_id}")

        elif event.type == "error":
            errors[event.executor_id] = str(event.data)
            print(f"✗ Error in {event.executor_id}: {event.data}")

    # Generate final diagram with execution state
    final_diagram = generate_execution_state_diagram(
        workflow,
        executed_nodes,
        errors
    )

    print(f"""
Final Execution State:
```mermaid
{final_diagram}
```
    """)

def generate_execution_state_diagram(
    workflow: Workflow,
    executed_nodes: set,
    errors: dict
) -> str:
    """Generate diagram showing execution state."""
    lines = ["graph LR"]

    for node_name in workflow.nodes:
        if node_name in errors:
            # Error state
            lines.append(f'    {node_name}["❌ {node_name}"]')
        elif node_name in executed_nodes:
            # Success state
            lines.append(f'    {node_name}["✓ {node_name}"]')
        else:
            # Not executed
            lines.append(f'    {node_name}["⊘ {node_name}"]')

    for edge in workflow.edges:
        lines.append(f"    {edge.source} --> {edge.target}")

    # Styling
    for node_name in workflow.nodes:
        if node_name in errors:
            lines.append(f"    style {node_name} fill:#FF5252,color:#fff")
        elif node_name in executed_nodes:
            lines.append(f"    style {node_name} fill:#4CAF50,color:#fff")
        else:
            lines.append(f"    style {node_name} fill:#9E9E9E,color:#fff")

    return "\n".join(lines)

# Usage
await visualize_workflow_execution(workflow, "input data")
```

## Complete Visualization Example

```python
from agent_framework.workflows import Workflow
from pathlib import Path

class WorkflowVisualizer:
    """Complete workflow visualization toolkit."""

    def __init__(self, workflow: Workflow, output_dir: str = "./diagrams"):
        self.workflow = workflow
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_all(self) -> dict:
        """Generate all visualization formats."""
        results = {}

        # Mermaid
        mermaid = generate_mermaid_diagram(self.workflow)
        mermaid_file = self.output_dir / "workflow.mmd"
        mermaid_file.write_text(mermaid)
        results["mermaid"] = str(mermaid_file)

        # GraphViz
        graphviz = generate_graphviz(self.workflow)
        graphviz_file = self.output_dir / "workflow.dot"
        graphviz_file.write_text(graphviz)
        results["graphviz"] = str(graphviz_file)

        # Save images
        save_mermaid_as_image(mermaid, str(self.output_dir / "workflow.png"))
        results["mermaid_image"] = str(self.output_dir / "workflow.png")

        return results

# Usage
visualizer = WorkflowVisualizer(workflow)
files = visualizer.generate_all()
print("Generated files:", files)
```
