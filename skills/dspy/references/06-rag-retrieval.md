# DSPy — Retrieval & RAG

> Source: https://dspy.ai/learn/programming/modules/#retrieval — Written for DSPy v2.5.x

## Overview

DSPy treats retrieval as a first-class, composable module. `dspy.Retrieve` is the base interface; concrete retriever backends plug into `dspy.configure(rm=...)`. Any DSPy module can then invoke retrieval as a submodule, and optimizers compile the whole pipeline — including the prompts that *generate* search queries — end to end.

## Configuring a retriever

```python
import dspy

# ColBERTv2 hosted server (classic DSPy tutorial retriever)
colbert = dspy.ColBERTv2(url="http://20.102.90.50:2017/wiki17_abstracts")
dspy.configure(lm=dspy.LM("openai/gpt-4o-mini"), rm=colbert)
```

Once configured, `dspy.Retrieve` uses it by default:

```python
retrieve = dspy.Retrieve(k=5)
result = retrieve("Who wrote the theory of general relativity?")
print(result.passages)   # list[str]
```

## Vector-DB retrievers

DSPy ships (or integrates with) retriever classes for most popular stores:

| Backend | Class | Notes |
|---------|-------|-------|
| ColBERTv2 | `dspy.ColBERTv2` | Hosted HTTP endpoint |
| Qdrant | `dspy.QdrantRM` | `pip install 'dspy[qdrant]'` |
| Chroma | `dspy.ChromadbRM` | `pip install 'dspy[chromadb]'` |
| Weaviate | `dspy.WeaviateRM` | `pip install 'dspy[weaviate]'` |
| Pinecone | `dspy.PineconeRM` | `pip install 'dspy[pinecone]'` |
| LanceDB | `dspy.LanceDBRM` | `pip install 'dspy[lancedb]'` |
| FAISS | `dspy.retrievers.FaissRM` | Local, in-process |
| HuggingFace / custom | Subclass `dspy.Retrieve` | Anything with an `embed + search` API |

### Qdrant example

```python
from qdrant_client import QdrantClient
import dspy

client = QdrantClient("http://localhost:6333")
rm = dspy.QdrantRM(
    qdrant_collection_name="docs",
    qdrant_client=client,
    k=5,
)
dspy.configure(rm=rm)

retrieve = dspy.Retrieve(k=5)
result = retrieve("How does DSPy compile a program?")
for p in result.passages:
    print("-", p[:80])
```

### Chroma example

```python
import chromadb
import dspy

client = chromadb.PersistentClient(path="./chroma_db")
rm = dspy.ChromadbRM(
    collection_name="my_docs",
    persist_directory="./chroma_db",
    k=5,
)
dspy.configure(rm=rm)
```

## Writing a custom retriever

Subclass `dspy.Retrieve` and implement `forward(query_or_queries, k)`:

```python
import dspy

class MyRetriever(dspy.Retrieve):
    def __init__(self, index, k: int = 5):
        super().__init__(k=k)
        self.index = index

    def forward(self, query_or_queries, k: int | None = None):
        k = k or self.k
        queries = [query_or_queries] if isinstance(query_or_queries, str) else query_or_queries
        passages: list[str] = []
        for q in queries:
            hits = self.index.search(q, top_k=k)
            passages.extend(hit.text for hit in hits)
        return dspy.Prediction(passages=passages)
```

Return a `dspy.Prediction` with a `passages` field (list of strings) so downstream modules can consume it idiomatically.

## Single-step RAG

```python
import dspy

class RAG(dspy.Module):
    def __init__(self, num_passages: int = 3):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=num_passages)
        self.generate = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question: str) -> dspy.Prediction:
        context = self.retrieve(question).passages
        return self.generate(context=context, question=question)

rag = RAG()
print(rag(question="What does DSPy stand for?").answer)
```

You can then compile it like any other module:

```python
from dspy.teleprompt import BootstrapFewShot

def answer_match(example, pred, trace=None) -> bool:
    return example.answer.lower() in pred.answer.lower()

compiler = BootstrapFewShot(metric=answer_match, max_bootstrapped_demos=4)
compiled = compiler.compile(rag, trainset=trainset)
```

The optimizer will bootstrap demos for *both* the retrieval-conditioned reasoning step and (indirectly) the queries DSPy sends — huge lift over a hand-written prompt.

## Multi-hop RAG

For questions that require chaining multiple searches, generate a follow-up query from the accumulated context:

```python
import dspy

class MultiHopRAG(dspy.Module):
    def __init__(self, passages_per_hop: int = 3, max_hops: int = 2):
        super().__init__()
        self.max_hops = max_hops
        self.generate_query = [
            dspy.ChainOfThought("context, question -> search_query")
            for _ in range(max_hops)
        ]
        self.retrieve = dspy.Retrieve(k=passages_per_hop)
        self.generate_answer = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question: str) -> dspy.Prediction:
        context: list[str] = []
        for hop in range(self.max_hops):
            query = self.generate_query[hop](
                context=context, question=question
            ).search_query
            context.extend(self.retrieve(query).passages)
        return self.generate_answer(context=context, question=question)
```

Note: using *separate* `ChainOfThought` instances per hop lets the optimizer tune different demos per hop, which empirically beats a single shared query generator on HotpotQA-style tasks.

## Using a reranker

DSPy has no built-in reranker but you can slot one in:

```python
class RerankedRAG(dspy.Module):
    def __init__(self, k: int = 20, final_k: int = 4):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=k)
        self.final_k = final_k
        self.score = dspy.Predict("passage, question -> score: float")
        self.answer = dspy.ChainOfThought("context, question -> answer")

    def forward(self, question: str) -> dspy.Prediction:
        passages = self.retrieve(question).passages
        scored = [(p, float(self.score(passage=p, question=question).score)) for p in passages]
        scored.sort(key=lambda x: x[1], reverse=True)
        context = [p for p, _ in scored[: self.final_k]]
        return self.answer(context=context, question=question)
```

For production you probably want a dedicated reranker model (Cohere Rerank, bge-reranker) rather than an LM-based scorer; wrap it in a custom `dspy.Retrieve` subclass.

## Retrieval-augmented compile — the HotpotQA recipe

The canonical DSPy tutorial compiles a `MultiHopRAG` on HotpotQA dev with `BootstrapFewShotWithRandomSearch` against an exact-match metric. Rough shape:

```python
from dspy.datasets.hotpotqa import HotPotQA
from dspy.teleprompt import BootstrapFewShotWithRandomSearch
from dspy.evaluate import answer_exact_match, Evaluate

dataset = HotPotQA(train_seed=1, train_size=200, eval_seed=2023, dev_size=50)
train = [x.with_inputs("question") for x in dataset.train]
dev = [x.with_inputs("question") for x in dataset.dev]

program = MultiHopRAG()
opt = BootstrapFewShotWithRandomSearch(
    metric=answer_exact_match,
    max_bootstrapped_demos=2,
    num_candidate_programs=6,
)
compiled = opt.compile(program, trainset=train, valset=dev)

evaluator = Evaluate(devset=dev, metric=answer_exact_match, num_threads=4)
print("compiled:", evaluator(compiled))
```

## Common pitfalls

- **Retriever returns duplicate passages across hops.** Deduplicate in `forward` before extending `context`.
- **Pasting 20 passages into the context and expecting the LM to handle them.** Keep `k` small; add a reranker if you need more recall.
- **Using a single `ChainOfThought` for every hop.** The optimizer can't specialise per-hop demos. Use a list.
- **Calling `dspy.Retrieve` with raw user input containing PII.** Retrieval queries are logged and cached; sanitise if needed.
- **Forgetting to configure `rm`.** `dspy.Retrieve` will raise `AssertionError: No RM is loaded.` — configure globally or pass `rm=` explicitly.
- **Using the wrong embedding model in the index vs the retriever.** Indexing with BGE and querying with MiniLM returns garbage. Keep them in lock step.

## Related topics

- **Composing retrieval with other modules:** `02-modules.md`
- **Compiling a RAG pipeline:** `04-optimizers.md`
- **Writing metrics that measure retrieval quality, not just answer correctness:** `05-metrics-evaluation.md`
- **Deploying a compiled RAG:** `08-deployment.md`
