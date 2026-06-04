# Integrations

> Source: [docs.wandb.ai/models/integrations](https://docs.wandb.ai/models/integrations/) | [docs.wandb.ai/weave/guides/integrations](https://docs.wandb.ai/weave/guides/integrations/) | wandb 0.27.1

## Table of Contents

- [Overview](#overview)
- [PyTorch](#pytorch)
- [PyTorch Lightning](#pytorch-lightning)
- [Hugging Face Transformers](#hugging-face-transformers)
- [Keras](#keras)
- [TensorFlow](#tensorflow)
- [XGBoost](#xgboost)
- [scikit-learn](#scikit-learn)
- [OpenAI (Weave)](#openai-weave)
- [Anthropic (Weave)](#anthropic-weave)
- [LangChain (Weave)](#langchain-weave)
- [LlamaIndex (Weave)](#llamaindex-weave)
- [Other Weave Integrations](#other-weave-integrations)
- [Generic SDK Integration](#generic-sdk-integration)

## Overview

W&B provides two types of integrations:

**W&B Models integrations** — callbacks and hooks for ML training frameworks (PyTorch, Hugging Face, Keras). These log metrics, config, and artifacts during training.

**W&B Weave integrations** — automatic tracing for LLM providers and orchestration frameworks (OpenAI, Anthropic, LangChain). These log inputs, outputs, costs, and latency at inference time.

## PyTorch

Native integration via `wandb.watch()` and manual logging:

```python
import torch
import wandb

with wandb.init(project="pytorch-demo", config={"lr": 0.01}) as run:
    model = MyModel()
    
    # Log gradients and parameters
    run.watch(model, log="all", log_freq=100)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=run.config["lr"])
    
    for epoch in range(100):
        for batch in train_loader:
            loss = train_step(model, batch, optimizer)
        
        val_loss, val_acc = evaluate(model, val_loader)
        run.log({"train/loss": loss, "val/loss": val_loss, "val/accuracy": val_acc})
    
    # Save model as artifact
    torch.save(model.state_dict(), "model.pt")
    run.log_artifact("model.pt", name="pytorch-model", type="model")
    
    # Stop gradient logging
    run.unwatch(model)
```

### wandb.watch Options

| Parameter | Description |
|-----------|-------------|
| `log="gradients"` | Log gradient histograms only |
| `log="parameters"` | Log parameter histograms only |
| `log="all"` | Log both gradients and parameters |
| `log_freq=100` | Log every N training steps |
| `log_graph=True` | Log the model computational graph |

## PyTorch Lightning

Use the built-in `WandbLogger`:

```python
from pytorch_lightning import Trainer
from pytorch_lightning.loggers import WandbLogger

wandb_logger = WandbLogger(
    project="lightning-demo",
    name="resnet-run",
    log_model="all",  # Log model checkpoints as artifacts
)

trainer = Trainer(
    max_epochs=100,
    logger=wandb_logger,
    callbacks=[
        ModelCheckpoint(monitor="val/loss", mode="min"),
    ],
)

trainer.fit(model, train_dataloader, val_dataloader)
```

Auto-logged: training/validation metrics, learning rate, model checkpoints, hyperparameters.

## Hugging Face Transformers

Zero-code integration — W&B is auto-detected by the HF Trainer:

```python
import wandb
from transformers import Trainer, TrainingArguments

wandb.login()

training_args = TrainingArguments(
    output_dir="./results",
    report_to="wandb",             # Enable W&B logging
    run_name="bert-fine-tune",
    logging_steps=10,
    evaluation_strategy="epoch",
    save_strategy="epoch",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
)

trainer.train()
wandb.finish()
```

### Environment Variables for HF

```bash
export WANDB_PROJECT="huggingface-training"
export WANDB_WATCH="all"        # Log gradients: "gradients", "all", "false"
export WANDB_LOG_MODEL="true"   # Log model checkpoints as artifacts
```

Auto-logged: training loss, eval metrics, learning rate schedule, model config, system metrics.

### OpenAI Fine-Tuning

```python
from openai import OpenAI

client = OpenAI()

# W&B integration for OpenAI fine-tuning
job = client.fine_tuning.jobs.create(
    training_file="file-abc123",
    model="gpt-4o-mini-2024-07-18",
    integrations=[{
        "type": "wandb",
        "wandb": {
            "project": "openai-finetune",
            "name": "gpt4o-mini-custom",
            "tags": ["production"],
        },
    }],
)
```

## Keras

```python
import wandb
from wandb.integration.keras import WandbMetricsLogger, WandbModelCheckpoint

with wandb.init(project="keras-demo", config={"epochs": 50}) as run:
    model = build_model()
    model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
    
    model.fit(
        x_train, y_train,
        validation_data=(x_val, y_val),
        epochs=run.config["epochs"],
        callbacks=[
            WandbMetricsLogger(log_freq="epoch"),
            WandbModelCheckpoint("models/", save_best_only=True),
        ],
    )
```

## TensorFlow

```python
import tensorflow as tf
import wandb
from wandb.integration.keras import WandbMetricsLogger

with wandb.init(project="tf-demo") as run:
    model = tf.keras.Sequential([...])
    model.compile(...)
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=50,
        callbacks=[WandbMetricsLogger()],
    )
```

## XGBoost

```python
import xgboost as xgb
from wandb.integration.xgboost import WandbCallback

with wandb.init(project="xgboost-demo") as run:
    bst = xgb.train(
        params={"max_depth": 3, "eta": 0.1, "objective": "binary:logistic"},
        dtrain=dtrain,
        num_boost_round=100,
        evals=[(dtest, "test")],
        callbacks=[WandbCallback(log_model=True)],
    )
```

## scikit-learn

Manual integration — log metrics and models explicitly:

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score

with wandb.init(project="sklearn-demo", config={"n_estimators": 100}) as run:
    model = RandomForestClassifier(n_estimators=run.config["n_estimators"])
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    run.log({
        "accuracy": accuracy_score(y_test, y_pred),
        "f1": f1_score(y_test, y_pred, average="weighted"),
    })
    
    # Log model as artifact
    import joblib
    joblib.dump(model, "model.pkl")
    run.log_artifact("model.pkl", name="rf-model", type="model")
```

## OpenAI (Weave)

```python
import weave
from openai import OpenAI

weave.init("openai-app")
client = OpenAI()

# All calls automatically traced
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Explain transformers"}],
)

# Streaming also supported
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Write a poem"}],
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")
```

Auto-traced: model, messages, response, tokens, cost, latency, tool calls, structured outputs.

## Anthropic (Weave)

```python
import weave
from anthropic import Anthropic

weave.init("claude-app")
client = Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Explain attention mechanisms"}],
)

# Tool use auto-tracked
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=[{"name": "calculator", "description": "...", "input_schema": {...}}],
    messages=[{"role": "user", "content": "What is 15% of 340?"}],
)
```

## LangChain (Weave)

```python
import weave
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

weave.init("langchain-app")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("user", "{input}"),
])

llm = ChatOpenAI(model="gpt-4o")
chain = prompt | llm
result = chain.invoke({"input": "What is LangChain?"})
```

## LlamaIndex (Weave)

```python
import weave
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

weave.init("llamaindex-app")

documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()

response = query_engine.query("What is the main topic?")
```

## Other Weave Integrations

| Framework | Auto-Traced |
|-----------|-------------|
| CrewAI | Agent execution, tool calls, delegation |
| DSPy | Module calls, optimizations, evaluations |
| Instructor | Structured output extraction |
| LiteLLM | All provider calls through the proxy |
| Groq | Chat completions |
| Together AI | Chat completions |

## Generic SDK Integration

For unsupported frameworks, use `@weave.op()` manually:

```python
@weave.op()
def my_custom_llm_call(prompt: str) -> str:
    response = custom_api.generate(prompt)
    return response.text
```

For training frameworks, use `wandb.log()` directly:

```python
with wandb.init() as run:
    for step in range(1000):
        metrics = custom_trainer.step()
        run.log(metrics)
```

## Related

- Weave Tracing → `references/09-weave-tracing.md`
- Experiment Tracking → `references/01-experiment-tracking.md`
- Weave Evaluations → `references/10-weave-evaluations.md`
