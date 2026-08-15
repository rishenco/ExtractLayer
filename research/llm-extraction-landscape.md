# LLM extraction on GitHub: who builds `llm(system, raw_text) -> structured_data`

Survey of 3,133 GitHub repositories, August 2026.

## The short version

The *primitive* is finished. Turning raw text into a typed object is three lines against a
provider API, and roughly a dozen mature libraries wrap it with validation and retries.

The *practice* has not caught up, and the gap is wider than it looks. Of the 2,150
repositories in this corpus that actually do LLM extraction, **3.0% show any named
extraction library** — no instructor, no outlines, no BAML, no LangChain structured output.
The long tail calls provider APIs directly and parses the result by hand. The most-used
Python package in the whole space after the providers themselves is `json_repair`, which
exists to patch malformed model output.

So the honest summary is not "solved and commoditised". It is: **solved at the head,
re-implemented from scratch almost everywhere else** — and largely without the parts that
make extraction trustworthy. Only 10% of these repos mention human review, 7% mention
retrying on a validation failure, and 12% mention tracking cost.

## Corpus at a glance

| | |
|---|---|
| Unique repos found | 3,133 |
| Passed relevance filter | 2,150 |
| READMEs fetched and parsed | 3,027 of 3,133 |
| Repos with no usable README | 106 (103 verified as 404 on every filename variant) |
| Distinct search queries | 106 |
| Created 2025 or later | 1,712 of 2,150 (80%) |
| Created in 2026 alone | 1,117 of 2,150 (52%) |
| Archived | 26 of 2,150 relevant (37 corpus-wide) |

More than half the relevant corpus was created this year. That is the single clearest fact
about this space: it is being rebuilt continuously.

Star distribution of the relevant set — median **2**:

| Stars | Repos |
|---|---|
| < 10 | 1,548 (72%) |
| 10–99 | 367 |
| 100–999 | 145 |
| ≥ 1,000 | 90 |

Languages: Python 1,291 (60%), TypeScript 225, Jupyter 175, JavaScript 95, Rust 56,
Go 52, HTML 48; 101 repos report no language.

**Schema language.** 728 repos (34%) mention Pydantic, but only 98 (5%) visibly author a
`class X(BaseModel)`. The gap is transitive dependencies — FastAPI, LangChain and
LlamaIndex all pull Pydantic in without the author ever writing a schema. Zod appears in
114 (5%). Read these as ecosystem presence, not as authorship.

**Providers.** OpenAI 1,135, Anthropic 719, Google 575, LiteLLM/OpenRouter 195. For local
inference the loose signal (which counts any `transformers`/`huggingface` mention) gives
872, but restricting to actual local runtimes — Ollama, llama.cpp, vLLM, LM Studio, SGLang
— gives **548 (25%)**. A quarter of this space runs models locally.

## How the call is actually written

Six distinct API shapes have emerged for the same operation. Every snippet is copied from
that project's own README.

**1 — Patch the provider SDK.** The call site stays familiar; one extra argument carries
the schema. This is `instructor`, the shape most others are measured against.

```python
client = instructor.from_provider("openai/gpt-4o-mini")
user = client.chat.completions.create(
    response_model=User,
    messages=[{"role": "user", "content": "John is 25 years old"}],
)
```

**2 — Schema-first method.** The literal `llm(schema, text)` signature. `sibila`:

```python
model = Models.create("llamacpp:openchat")
model.extract(Info, "Who was the first man in the moon?")
```

**3 — Type-first function.** No schema class at all; the return type *is* the schema.
`marvin`:

```python
result = marvin.extract("i found $30 on the ground and bought 5 bagels for $10",
                        int, instructions="only USD")
```

**4 — Examples instead of a schema.** Few-shot examples define the shape, and extracted
fields are grounded back to source spans. `langextract`:

```python
result = lx.extract(text_or_documents=input_text, prompt_description=prompt,
                    examples=examples, model_id="gemini-3.5-flash")
```

**5 — Declarative document model.** You attach what you want to a document rather than
calling an extractor. `contextgem`:

```python
aspect = Aspect(name="Term and termination",
                description="Clauses on contract term and termination")
concept = BooleanConcept(name="NDA check", description="Is the contract an NDA?")
document.add_aspects([aspect]); document.add_concepts([concept])
```

**6 — Schema as a separate language.** The schema lives in its own DSL and compiles to a
typed client. `BAML`:

```python
from baml_client import b
resume = b.ExtractResume(resume_text)
```

The trend across the head of the corpus runs away from prompt strings and toward a typed
function boundary. BAML goes furthest by moving the prompt out of the host language
entirely — the only approach here that makes the prompt diffable and testable on its own.

## What enforces the structure

Two measurements, and they disagree in an informative way.

**Inside this corpus**, mechanism is visible only where a README shows code, so these are
lower bounds — 1,675 of 2,150 repos (78%) show none at all:

| Mechanism | Repos | Share |
|---|---|---|
| Provider structured outputs | 216 | 10.0% |
| Function / tool calling | 129 | 6.0% |
| Constrained decoding | 116 | 5.4% |
| JSON mode (legacy) | 95 | 4.4% |
| Prompt and parse | 67 | 3.1% |
| LangChain `with_structured_output` | 20 | 0.9% |
| Instructor | 18 | 0.8% |
| BAML | 17 | 0.8% |
| Outlines | 10 | 0.5% |

**Across all of GitHub**, by code search. These are file counts, inflated by forks,
vendored dependencies, SDK source and tests. GitHub returns approximate totals — nine of
the seventeen are exact multiples of 32 — so read them as magnitudes only:

| Mechanism | Marker searched | Files (approx.) |
|---|---|---|
| Function / tool calling | `tool_choice` (py) | 230,400 |
| JSON mode (legacy) | `response_format` + `json_object` (py) | 195,584 |
| Provider structured outputs | `response_format` + `json_schema` (py) | 86,289 |
| LangChain | `with_structured_output` (py) | 72,448 |
| PydanticAI | `from pydantic_ai` (py) | 37,888 |
| Provider structured outputs (TS) | `response_format` + `json_schema` (ts) | 26,720 |
| Post-hoc repair | `json_repair` (py) | 16,992 |
| Instructor | `import instructor` + `response_model` (py) | 6,976 |
| XGrammar | `xgrammar` (py) | 6,704 |
| BAML | `baml_client` | 6,320 |
| OpenAI structured outputs (TS) | `zodResponseFormat` (ts) | 4,960 |
| Outlines | `from outlines` (py) | 2,456 |
| Marvin | `import marvin` (py) | 2,296 |
| Mirascope | `from mirascope` (py) | 1,632 |
| LangExtract | `import langextract` (py) | 1,042 |
| LM Format Enforcer | `lm_format_enforcer` (py) | 1,040 |
| Jsonformer | `jsonformer` (py) | 551 |

These two tables are not directly comparable and the gap between them should not be
over-read. `tool_choice` is a parameter in every agent framework, mostly used for tool
dispatch rather than extraction. And the constrained-decoding engines are undercounted
here: Outlines and XGrammar are consumed mostly *through* vLLM and SGLang's `guided_json`
parameter, a marker this table does not search. What the two tables jointly support is
narrower and safer: provider-side enforcement is the default path, and dedicated
extraction libraries are a minority practice at both scales.

## Which mechanism, and why

Mechanism choice tracks one variable more than any other: **whether the project has raw
access to the decoder.** All four projects that constrain decoding ship a local backend
with logits access; all four that rely purely on a provider-side mechanism have none. The
eight adaptive projects are the ones spanning both worlds, and they respond by making the
mechanism swappable rather than picking one.

Models column lists what each project can drive, not what it recommends. Rationale is drawn
from each project's own documentation; the profiles behind it are in
`data/landmark-profiles.csv`.

### Constrained decoding — they own the decoder

| Repo | Models / backends | Why this mechanism |
|---|---|---|
| [1rgs/jsonformer](https://github.com/1rgs/jsonformer) | single (local HuggingFace transformers models only; needs raw logits access) | Drives decoding itself, so it needs raw logits — which is why it is local-HF-only. Braces, quotes and keys are emitted by the driver and only values are sampled, making invalid JSON structurally impossible. |
| [eth-sri/lmql](https://github.com/eth-sri/lmql) | OpenAI, Azure OpenAI, HuggingFace Transformers, llama.cpp, Replicate | A query language needs to enforce arbitrary constraints (types, regex, stop conditions, set membership), not just JSON, so it compiles them to eager token masks. Logits access also gives it `distribution` for P(value). |
| [mlc-ai/xgrammar](https://github.com/mlc-ai/xgrammar) | HF transformers, vLLM, SGLang, TensorRT-LLM, MLC-LLM, OpenVINO GenAI, Modular MAX, WebLLM | Built as an engine for serving stacks, so latency is the product. Bitmask generation on CPU overlaps the GPU forward pass, making masking near-free — only possible inside the decode loop. |
| [noamgat/lm-format-enforcer](https://github.com/noamgat/lm-format-enforcer) | HF transformers, vLLM, llama.cpp, ExLlamaV2, TensorRT-LLM, LangChain, LlamaIndex, Haystack | Deliberately permissive constrained decoding: it allows any token sequence that still parses, so the model keeps control of whitespace and field order. The stated goal is enforcement without the quality loss of rigid masking. |

### Fine-tuned model

| Repo | Models / backends | Why this mechanism |
|---|---|---|
| [docling-project/docling](https://github.com/docling-project/docling) | single (local HF transformers VLM: numind/NuExtract-2.0-2B default, … | Ships a fine-tuned VLM rather than constraining a general one. The Pydantic template is rendered into a filled example JSON and prompted, betting a model trained on the task beats constraining one that wasn't. |

### Adaptive — mechanism swaps per backend

| Repo | Models / backends | Why this mechanism |
|---|---|---|
| [567-labs/instructor](https://github.com/567-labs/instructor) | OpenAI, Anthropic, Google/Gemini, Vertex AI, Mistral, Cohere, Groq, Ollama, Bedrock, … | Supports 15+ providers, so no single mechanism is available everywhere — it adapts per provider and retries on validation failure. Patching the provider's own SDK keeps `create()` native, so the mechanism can change without the call site changing. |
| [dottxt-ai/outlines](https://github.com/dottxt-ai/outlines) | transformers, llama.cpp, vLLM, SGLang, Ollama, MLX, LM Studio, TGI, OpenAI, Anthropic, … | Presents one `model(prompt, output_type)` call across 13 backends and silently swaps enforcement underneath: logit masking where it owns the decoder, provider `response_format` where it doesn't. |
| [guardrails-ai/guardrails](https://github.com/guardrails-ai/guardrails) | LiteLLM (100+ models), OpenAI, Anthropic, HuggingFace pipelines/models, Manifest, … | Enforcement is per-field validators rather than one schema constraint, so on failure it reasks only the bad values instead of regenerating the whole object. |
| [guidance-ai/guidance](https://github.com/guidance-ai/guidance) | Transformers, llama.cpp, OpenAI, Azure AI, ONNX Runtime GenAI, Mock | Interleaves grammar with prompt so tokens the grammar already determines are fast-forwarded, skipping forward passes. That is a speed argument, and it only pays off on backends it controls. |
| [jndiogo/sibila](https://github.com/jndiogo/sibila) | local llama.cpp/GGUF, OpenAI, Anthropic, Mistral, Groq, Fireworks, Together | Ships its own JSON-Schema-to-GBNF converter so local models get real grammar constraints instead of prompt-coaxing, while API providers fall back to their native support. |
| [Mirascope/mirascope](https://github.com/Mirascope/mirascope) | openai, anthropic, google, mlx/local, plus openai-compatible endpoints | Formatting mode is pluggable per call — strict, tool, json, or a custom parser — defaulting to strict. The library treats mechanism as a per-call decision, not a library-wide one. |
| [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) | OpenAI, Anthropic, Google, Groq, Mistral, Cohere, DeepSeek, Bedrock, Ollama, HuggingFace, … | Exposes the choice rather than hiding it: three selectable output modes — tool call (default), native JSON schema, prompted — picked per type via marker classes, because provider support is uneven across 25+ backends. |
| [ScrapeGraphAI/Scrapegraph-ai](https://github.com/ScrapeGraphAI/Scrapegraph-ai) | OpenAI, Azure, Groq, Gemini, Mistral, Bedrock, Ollama, NVIDIA (via LangChain) | Mechanism follows the backend: prompt instructions on OpenAI, native JSON-schema decoding on Ollama. Chunk-parallel-merge means partial failures matter less than throughput. |

### Provider structured outputs

| Repo | Models / backends | Why this mechanism |
|---|---|---|
| [google/langextract](https://github.com/google/langextract) | Gemini, OpenAI, Ollama, plus pluggable custom/community providers | Needs exact character offsets to fuzzy-align every extracted value back to the source, so it takes structured JSON from the provider and does the grounding work itself. |
| [mishushakov/llm-scraper](https://github.com/mishushakov/llm-scraper) | OpenAI, Anthropic, Google, Groq, Ollama (any Vercel AI SDK provider) | A thin wrapper over the Vercel AI SDK, so it inherits whatever that SDK's structured-output support provides rather than implementing its own. |

### Function / tool calling

| Repo | Models / backends | Why this mechanism |
|---|---|---|
| [jackmpcollins/magentic](https://github.com/jackmpcollins/magentic) | OpenAI, Anthropic, LiteLLM (100+); OpenAI-compatible: Ollama, Gemini, xAI, Mistral, OpenRouter | There is no extract() call at all: the schema is the decorated stub's return annotation. Tool calling is what lets structured output stream while still typed. |
| [PrefectHQ/marvin](https://github.com/PrefectHQ/marvin) | openai (default), anthropic, google, groq, mistral, bedrock, cohere, … | Every extraction is an agent task, so the result arrives as a forced end-turn tool call — reusing the agent loop's existing tool mechanism instead of a separate extraction path. |

### Prompt and parse — no enforcement

| Repo | Models / backends | Why this mechanism |
|---|---|---|
| [BoundaryML/baml](https://github.com/BoundaryML/baml) | OpenAI, OpenAI Responses, Anthropic, Google AI/Gemini, Vertex, AWS Bedrock, Azure, … | The only project here that rejects enforcement on principle. Schema-Aligned Parsing coerces malformed output into the schema, on the argument that a tolerant parser beats a constrained decoder and works on every provider including ones with no structured-output support. |
| [eyurtsev/kor](https://github.com/eyurtsev/kor) | any LangChain BaseLanguageModel (OpenAI, Anthropic, local, etc.) | Predates provider structured outputs. Uses a swappable output encoder (CSV/JSON/XML) and returns errors beside partial data rather than retrying, treating extraction as best-effort. |
| [katanaml/sparrow](https://github.com/katanaml/sparrow) | MLX, Ollama, vLLM, Hugging Face Spaces, local GPU, … | Schema is a JSON example with type tokens rather than a formal schema, so there is nothing to constrain against; validation is post-hoc and reported as a field. |
| [microsoft/TypeChat](https://github.com/microsoft/TypeChat) | OpenAI, Azure OpenAI; any other via custom TypeChatLanguageModel | Schema is TypeScript source pasted into the prompt, and the TypeScript compiler validates the reply — reusing an existing type checker instead of building an enforcement layer. One repair turn fixes failures. |
| [shcherbak-ai/contextgem](https://github.com/shcherbak-ai/contextgem) | LiteLLM-backed: OpenAI, Anthropic, Google, Azure, Ollama, LM Studio, etc. | You never write a prompt or schema — natural-language concept descriptions generate the prompts, references and justifications. Generated prompts can't be constrained, so parsing is the only option. |
| [Zipstack/unstract](https://github.com/Zipstack/unstract) | OpenAI, Azure OpenAI, OpenAI-compatible, Anthropic, AWS Bedrock, Google Gemini, Ollama, … | Schema lives server-side in Prompt Studio and the API call ships only the document, so enforcement can't be a client-side decoder concern. |

### No LLM (baseline)

| Repo | Models / backends | Why this mechanism |
|---|---|---|
| [Unstructured-IO/unstructured](https://github.com/Unstructured-IO/unstructured) | none (no LLM provider in the OSS core) | No LLM and no schema input in the OSS core — deterministic per-format parsers plus a layout model emit a fixed element taxonomy. Included as the non-generative baseline. |

## The stack

Layers are ordered by pipeline position, decoder outward. **These tables are hand-curated
landmarks, not a sample of the corpus** — nine entries below (`lmql`, `dspy`, `TypeChat`,
`Mirascope`, `markitdown`, `docling`, `marker`, `zerox`, `GLiNER`) score below the
automated relevance cut, and for 15 of the 38 the layer shown here overrides the
classifier's own label. The aggregate percentages elsewhere in this report describe the
2,150-repo relevant set, which is a different population.

Two layers the classifier produced are omitted from the narrative below and should not be
forgotten: `L0-runtime` (83 repos — vLLM, SGLang and friends, the serving tier through
which most constrained decoding is actually consumed) and `unclassified` (347 repos, 16%).

**L1 — Enforcement engines.** Make invalid tokens unemittable.

| Repo | Stars | Note |
|---|---|---|
| [guidance-ai/guidance](https://github.com/guidance-ai/guidance) | 21,713 | Control language for generation |
| [dottxt-ai/outlines](https://github.com/dottxt-ai/outlines) | 15,617 | Regex/JSON-Schema guided generation |
| [1rgs/jsonformer](https://github.com/1rgs/jsonformer) | 4,934 | Fills schema fields token by token |
| [eth-sri/lmql](https://github.com/eth-sri/lmql) | 4,203 | Constraint-guided query language |
| [noamgat/lm-format-enforcer](https://github.com/noamgat/lm-format-enforcer) | 2,028 | Backend for vLLM and others |
| [mlc-ai/xgrammar](https://github.com/mlc-ai/xgrammar) | 1,818 | Fast grammar engine, C++ |
| [structuredllm/syncode](https://github.com/structuredllm/syncode) | 339 | Grammar-based syntactical decoding |
| [Dan-wanna-M/formatron](https://github.com/Dan-wanna-M/formatron) | 237 | Low-overhead format control |
| [epfl-dlab/transformers-CFG](https://github.com/epfl-dlab/transformers-CFG) | 140 | CFG constraints for HF models |

**L2 — Extraction primitives.** Schema in, typed object out.

| Repo | Stars | Note |
|---|---|---|
| [google/langextract](https://github.com/google/langextract) | 38,378 | Few-shot; grounds fields to source spans |
| [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) | 37,187 | Typed signatures; optimises the prompt |
| [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) | 19,298 | Typed outputs from the Pydantic team |
| [567-labs/instructor](https://github.com/567-labs/instructor) | 13,729 | Reference implementation; patches the SDK |
| [BoundaryML/baml](https://github.com/BoundaryML/baml) | 9,004 | Schema as a DSL, generates a typed client |
| [microsoft/TypeChat](https://github.com/microsoft/TypeChat) | 8,677 | TypeScript types as the schema |
| [guardrails-ai/guardrails](https://github.com/guardrails-ai/guardrails) | 7,285 | Validation and correction policies |
| [PrefectHQ/marvin](https://github.com/PrefectHQ/marvin) | 6,189 | `marvin.extract(text, type)` |
| [mangiucugna/json_repair](https://github.com/mangiucugna/json_repair) | 5,070 | Repairs malformed JSON; the universal fallback |
| [jackmpcollins/magentic](https://github.com/jackmpcollins/magentic) | 2,413 | LLM calls as decorated functions |
| [shcherbak-ai/contextgem](https://github.com/shcherbak-ai/contextgem) | 1,983 | Declarative concepts; sentence-level references |
| [eyurtsev/kor](https://github.com/eyurtsev/kor) | 1,685 | Early schema-first extraction |
| [Mirascope/mirascope](https://github.com/Mirascope/mirascope) | 1,521 | Provider-agnostic typed calls |
| [567-labs/instructor-js](https://github.com/567-labs/instructor-js) | 802 | Instructor for TypeScript |
| [jndiogo/sibila](https://github.com/jndiogo/sibila) | 55 | `model.extract(Schema, text)`, local-first |

**L3 — Document ingestion.** Bytes to text, then text to structure. The largest star counts
in the corpus, but note that the top two do *conversion*, not extraction: markitdown and
marker produce Markdown, and the `llm(schema, text)` step happens downstream of them.

| Repo | Stars | Note |
|---|---|---|
| [microsoft/markitdown](https://github.com/microsoft/markitdown) | 173,793 | Format conversion only — no extraction step |
| [docling-project/docling](https://github.com/docling-project/docling) | 64,773 | Layout-aware document conversion |
| [run-llama/llama_index](https://github.com/run-llama/llama_index) | 51,642 | Document agents; LlamaExtract for schemas |
| [datalab-to/marker](https://github.com/datalab-to/marker) | 38,746 | PDF to Markdown + JSON |
| [Unstructured-IO/unstructured](https://github.com/Unstructured-IO/unstructured) | 15,311 | Long-standing preprocessing toolkit |
| [getomni-ai/zerox](https://github.com/getomni-ai/zerox) | 12,265 | OCR via vision models |
| [Zipstack/unstract](https://github.com/Zipstack/unstract) | 7,140 | Extraction platform with API deployment |
| [katanaml/sparrow](https://github.com/katanaml/sparrow) | 5,196 | Agentic document workflows |
| [NanoNets/docstrange](https://github.com/NanoNets/docstrange) | 1,520 | Any document to structured data |

**L3 — Web.** The same shape with HTML as the input.

| Repo | Stars | Note |
|---|---|---|
| [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) | 167,436 | Scrape/search API with schema extraction |
| [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai) | 78,130 | LLM-oriented crawler |
| [ScrapeGraphAI/Scrapegraph-ai](https://github.com/ScrapeGraphAI/Scrapegraph-ai) | 29,543 | Graph-based scraping pipelines |
| [mishushakov/llm-scraper](https://github.com/mishushakov/llm-scraper) | 6,909 | Webpage to typed object, Zod schemas |
| [adbar/trafilatura](https://github.com/adbar/trafilatura) | 6,634 | Rule-based, no LLM — the pre-LLM baseline |
| [lightfeed/extractor](https://github.com/lightfeed/extractor) | 320 | Robust web data extraction |

**L4 — Vertical applications.** Where the job-posting-parser example lives. At 509 repos
this is the largest single layer (24% of the relevant set; 32% counting tutorials), though
not a majority. Domain is tagged from description and tagline only — scoping it to README
bodies inflated every vertical by 25–50%, because general-purpose libraries like BAML and
Mirascope use "extract a resume" as their headline example.

| Domain | Repos | Comment |
|---|---|---|
| Invoices / finance | 191 | Densest vertical; invoice-to-JSON is the canonical demo |
| Jobs / recruiting | 160 | Resume/ATS parsers outnumber job-posting parsers ~2:1 |
| Research papers | 100 | Often academic tooling |
| Medical / clinical | 93 | |
| Knowledge graphs | 80 | Highest local-runtime share of any vertical (58%) |
| Legal | 35 | Contract clause extraction; 56% local |
| E-commerce | 22 | |
| Logs / security | 17 | |
| News / media | 13 | |
| Real estate | 10 | |
| ID / forms | 8 | |

The two densest verticals are almost entirely hobby work. Across the 191 invoice repos the
median star count is 1 and only four clear 100 stars; across the 160 job/recruiting repos
the median is 1 and exactly one clears 100. Nobody has consolidated either vertical — which
is either an opportunity, or a warning that per-vertical extraction does not hold value on
its own.

**L5 — Research.** 23 repos in the relevant set: paper implementations, datasets,
evaluation harnesses. [urchade/GLiNER](https://github.com/urchade/GLiNER) (3,537) is the
notable non-LLM alternative — a small dedicated NER model, far cheaper than a generative
call.

## What almost nobody does

Signal prevalence across the 2,150 relevant repos. These count *mentions* in README and
manifest text, so they are an upper bound on the real capability — which makes the small
numbers the meaningful ones.

| Capability | Repos | Share |
|---|---|---|
| Any evaluation or accuracy language | 868 | 40% |
| PDF handling | 850 | 40% |
| Batch / concurrency | 755 | 35% |
| OCR / vision | 583 | 27% |
| Web scraping | 430 | 20% |
| Source grounding / provenance | 198 | 9% |
| Cost or token tracking | 250 | 12% |
| Human review / correction loop | 208 | 10% |
| Retry on validation failure | 161 | 7% |

Even counting every passing mention as a feature, nine in ten of these projects have no
human correction path, and more than nine in ten never mention retrying when validation
fails. The trustworthiness layer is missing almost everywhere.

### The head does what the tail doesn't

Reading the docs and source of 24 of the landmark projects above and recording what each
one actually supports gives a sharp contrast with the corpus-wide numbers. Each profile was
then checked by an independent pass instructed to refute its two central claims — the
literal call signature and the enforcement mechanism — against primary sources. None of the
24 was overturned.

| | Landmark projects | Whole corpus |
|---|---|---|
| Retry on validation failure | 9 of 24 | 7% |
| Source grounding | 5 of 24 | 9% |

Nine of the twenty-four re-ask on a validation failure — instructor, pydantic-ai,
guardrails, marvin, magentic, mirascope, TypeChat, contextgem and jsonformer — against 7%
of the corpus. The capability exists; it just isn't reaching the people rebuilding this by
hand.

Enforcement across the 24 is more varied than the discourse suggests: 8 use a mix that
adapts to the backend, 6 prompt-and-parse, 4 constrained decoding, 2 provider structured
outputs, 2 function calling, 1 a fine-tuned model. There is no settled answer even at the
top of this space.

Grounding splits by tier rather than by quality. The document tools carry it because they
must — unstructured, unstract and sparrow all trace values back to a page or region — while
in the plain-text tier only langextract and contextgem do.

One design note worth recording: BAML, the most opinionated project in the set, does *not*
use constrained decoding or provider structured outputs. It generates freely and parses
with its own error-tolerant parser, on the argument that a good parser beats a constrained
decoder. That is a live disagreement at the top of this space, not a settled question.

Source grounding — mapping each extracted field back to a span in the input — is the one
capability with a visible champion. [langextract](https://github.com/google/langextract)
built its whole API around it, and [contextgem](https://github.com/shcherbak-ai/contextgem)
advertises sentence-level references as its headline feature. At 9% mentioning it at all,
it remains the exception rather than the default, and for any extraction a human must
audit it is the difference between a reviewable output and an unfalsifiable one.

## Method

GitHub repository search across 106 queries in four families: mechanism vocabulary,
extraction vocabulary, modality, and vertical. Star-sliced queries (`stars:20..80`,
`stars:81..400`) reached past the 1,000-result ranking cap. 22 landmark projects that
keyword search missed were backfilled by exact-name lookup and are tagged `landmark` in the
data rather than attributed to a query.

Every repo was then independently validated by fetching its README from
`raw.githubusercontent.com`, retrying transient failures across twelve filename variants:
3,027 of 3,133 returned content; of the remaining 106, 103 were confirmed to 404 on every
variant and 3 returned only whitespace. Star counts were spot-checked against fresh API queries and matched exactly.

Reproduce from `data/corpus.csv` (all 3,133, including the raw `signals` and `queries`
columns) and `data/shortlist.csv` (the 2,150 relevant). The hand-labelled accuracy sample
is in `data/layer-accuracy-sample.csv`, and the 24 verified landmark profiles behind the
head-vs-tail comparison are in `data/landmark-profiles.csv`.

## Limits

- **Everything except stars, dates and languages is a keyword measurement.** Domain,
  capability, mechanism and layer are regex signals over README and manifest text. They
  measure what a repo *says*, not what it does. Where a loose pattern inflated a number it
  has been tightened and the tighter figure reported — mention-of-Pydantic (34%) versus
  authored-`BaseModel` (5%), and loose-local (41%) versus actual-local-runtime (25%), are
  both reported so the inflation is visible.
- **Layer assignment is ~60% accurate.** Hand-labelling a fresh 30-repo sample against the
  final classification gives 18/30 (`data/layer-accuracy-sample.csv`); pooling the two
  held-out samples taken after tuning gives 38/60, so call it 60% ± 9. Use it for shape,
  not per-repo truth. Errors are not random — the common failures are vertical apps read as
  generic primitives, and demos read as products.
- **The relevance filter carries roughly 10% false positives.** Three of those same 30
  repos are not LLM data extraction at all: a text-guided *speech* separation model, an
  ISO-8583 payments simulator, and a Go serialization library, each matching on shared
  vocabulary. Percentages over the 2,150 should be read with that slack.
- **The landmark tables and the aggregate percentages are different populations.** Nine
  named repos fall below the relevance cut, and the relevance filter itself is keyword-based
  — it admits `trafilatura`, which uses no LLM at all, and excludes `markitdown`, which is
  pure format conversion. Both are listed above for context, marked as such.
- **Coverage is broad but not saturated.** 82% of repos were surfaced by exactly one query,
  so more queries would still find more. Keyword search has a systematic blind spot here:
  an initial landmark check found only 17 of 49 known projects, though roughly a third of
  those "misses" were stale aliases of repos that had been renamed (`instructor-ai` →
  `567-labs`, `outlines-dev` → `dottxt-ai`, and four others) rather than true gaps. After
  resolving renames and backfilling, 39 of 49 were present. Repo search matches only name,
  description and topics, and much of this ecosystem does not describe itself in the words
  a searcher would use.
- **Code-search counts are approximate**, file-scoped, and undercount libraries consumed
  through a serving layer.
- **Not measured at all:** schema versioning, contributor counts, and whether any project's
  extraction is actually accurate. No claim in this report rests on them.
