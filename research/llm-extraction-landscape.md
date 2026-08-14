# LLM extraction on GitHub: who builds `llm(system, raw_text) -> structured_data`

Survey of 2,641 GitHub repositories, August 2026.

## The short version

The primitive is solved and commoditised. Turning raw text into a typed object is now
three lines against a provider API, and roughly a dozen mature libraries wrap it.

What is *not* solved is everything around the call: knowing whether an extraction was
right, correcting it when it wasn't, and running it over a corpus at a price you can
predict. The corpus splits sharply — a small head of serious infrastructure, and a very
long tail of one-off pipelines rebuilding the same call. Median star count of the 1,738
relevant repos is **2**.

## Corpus at a glance

| | |
|---|---|
| Unique repos found | 2,641 |
| Passed relevance filter | 1,738 |
| READMEs fetched and parsed | 2,235 |
| Distinct search queries | 92 |
| Created 2025 or later | 1,375 of 1,738 (79%) |
| Pushed since Dec 2025 | 1,488 of 1,738 (86%) |
| Archived | 18 |

Star distribution of the relevant set:

| Stars | Repos |
|---|---|
| < 10 | 1,215 (70%) |
| 10–99 | 305 |
| 100–999 | 131 |
| ≥ 1,000 | 87 |

Languages: Python 1,054 (61%), TypeScript 172, Jupyter 143, JavaScript 73, Rust 46, Go 38.

Schema is written as a Pydantic model in 614 repos, as literal JSON Schema in 382, and as
Zod in 84. Pydantic is the de facto schema language of this space; Zod is its TypeScript
equivalent and trails by roughly 7×.

Providers named: OpenAI 928, local runtimes (Ollama / llama.cpp / vLLM) 714,
Anthropic 591, Google 480, LiteLLM/OpenRouter 165. Local inference is not a niche here —
it appears in 41% of relevant repos, mostly where documents cannot leave the building.

## What actually enforces the structure

Per-repo READMEs rarely show the mechanism — 1,354 of 1,738 (78%) describe the capability
without showing the call. So mechanism adoption is better measured across GitHub by code
search. Counts are files, not projects, and include forks and vendored copies; treat them
as relative magnitudes.

| Mechanism | Marker searched | Files |
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
| OpenAI structured outputs (TS helper) | `zodResponseFormat` (ts) | 4,960 |
| Outlines | `from outlines` (py) | 2,456 |
| Marvin | `import marvin` (py) | 2,296 |
| Mirascope | `from mirascope` (py) | 1,632 |
| LangExtract | `import langextract` (py) | 1,042 |
| LM Format Enforcer | `lm_format_enforcer` (py) | 1,040 |
| Jsonformer | `jsonformer` (py) | 551 |

Two things stand out. Provider-side enforcement plus LangChain accounts for the
overwhelming majority of real usage, while the constrained-decoding libraries that
dominate technical discussion are two orders of magnitude smaller. And `json_repair` at
17k files is a good measure of how often the structured path is *not* trusted — people
still parse and patch strings in production.

## The five layers

Named projects below were checked by hand. Star counts are from the GitHub API at survey
time.

**L1 — Enforcement engines.** Constrain the decoder so invalid tokens cannot be emitted.
Used mostly through a serving stack rather than directly.

| Repo | Stars | Note |
|---|---|---|
| [guidance-ai/guidance](https://github.com/guidance-ai/guidance) | 21,713 | Control language for LLM generation |
| [dottxt-ai/outlines](https://github.com/dottxt-ai/outlines) | 15,617 | Regex/JSON-Schema guided generation |
| [1rgs/jsonformer](https://github.com/1rgs/jsonformer) | 4,934 | Fills schema fields token by token |
| [eth-sri/lmql](https://github.com/eth-sri/lmql) | 4,203 | Constraint-guided query language |
| [noamgat/lm-format-enforcer](https://github.com/noamgat/lm-format-enforcer) | 2,028 | Backend for vLLM and others |
| [mlc-ai/xgrammar](https://github.com/mlc-ai/xgrammar) | 1,818 | Fast grammar engine, C++ |
| [structuredllm/syncode](https://github.com/structuredllm/syncode) | 339 | Grammar-based syntactical decoding |
| [Dan-wanna-M/formatron](https://github.com/Dan-wanna-M/formatron) | 237 | Low-overhead format control |
| [epfl-dlab/transformers-CFG](https://github.com/epfl-dlab/transformers-CFG) | 140 | CFG constraints for HF models |

**L2 — Extraction primitives.** Schema in, typed object out, with validation and retries.
This is the layer the question describes.

| Repo | Stars | Note |
|---|---|---|
| [google/langextract](https://github.com/google/langextract) | 38,378 | Few-shot examples, grounds fields to source spans |
| [stanfordnlp/dspy](https://github.com/stanfordnlp/dspy) | 37,187 | Typed signatures, optimises the prompt itself |
| [pydantic/pydantic-ai](https://github.com/pydantic/pydantic-ai) | 19,298 | Typed agent outputs from the Pydantic team |
| [567-labs/instructor](https://github.com/567-labs/instructor) | 13,729 | The reference implementation; patches the provider SDK |
| [BoundaryML/baml](https://github.com/BoundaryML/baml) | 9,004 | Schema as a DSL, generates a typed client |
| [microsoft/TypeChat](https://github.com/microsoft/TypeChat) | 8,677 | TypeScript types as the schema |
| [guardrails-ai/guardrails](https://github.com/guardrails-ai/guardrails) | 7,285 | Validation and correction policies |
| [PrefectHQ/marvin](https://github.com/PrefectHQ/marvin) | 6,189 | `marvin.extract(text, type)` |
| [mangiucugna/json_repair](https://github.com/mangiucugna/json_repair) | 5,070 | Repairs malformed JSON; the fallback everyone keeps |
| [jackmpcollins/magentic](https://github.com/jackmpcollins/magentic) | 2,413 | LLM calls as decorated Python functions |
| [shcherbak-ai/contextgem](https://github.com/shcherbak-ai/contextgem) | 1,983 | Declarative Aspects/Concepts over documents |
| [eyurtsev/kor](https://github.com/eyurtsev/kor) | 1,685 | Early schema-first extraction |
| [Mirascope/mirascope](https://github.com/Mirascope/mirascope) | 1,521 | Provider-agnostic typed calls |
| [567-labs/instructor-js](https://github.com/567-labs/instructor-js) | 802 | Instructor for TypeScript |
| [jndiogo/sibila](https://github.com/jndiogo/sibila) | 55 | `model.extract(Schema, text)`, local-first |

**L3 — Ingestion.** Bytes to text, then text to structure. Crowded and well funded.

| Repo | Stars | Note |
|---|---|---|
| [microsoft/markitdown](https://github.com/microsoft/markitdown) | 173,793 | Any office format to Markdown |
| [docling-project/docling](https://github.com/docling-project/docling) | 64,773 | Layout-aware document conversion |
| [datalab-to/marker](https://github.com/datalab-to/marker) | 38,746 | PDF to Markdown + JSON |
| [Unstructured-IO/unstructured](https://github.com/Unstructured-IO/unstructured) | 15,311 | Long-standing preprocessing toolkit |
| [getomni-ai/zerox](https://github.com/getomni-ai/zerox) | 12,265 | OCR via vision models |
| [Zipstack/unstract](https://github.com/Zipstack/unstract) | 7,140 | Extraction platform with API deployment |
| [katanaml/sparrow](https://github.com/katanaml/sparrow) | 5,196 | Document extraction with agentic workflows |
| [NanoNets/docstrange](https://github.com/NanoNets/docstrange) | 1,520 | Any document to structured data |

**L3 — Web.** The same shape with HTML as the input.

| Repo | Stars | Note |
|---|---|---|
| [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) | 167,436 | Scrape/search API with schema extraction |
| [ScrapeGraphAI/Scrapegraph-ai](https://github.com/ScrapeGraphAI/Scrapegraph-ai) | 29,543 | Graph-based scraping pipelines |
| [mishushakov/llm-scraper](https://github.com/mishushakov/llm-scraper) | 6,909 | Webpage to typed object, Zod schemas |
| [adbar/trafilatura](https://github.com/adbar/trafilatura) | 6,634 | Text and metadata extraction |
| [lightfeed/extractor](https://github.com/lightfeed/extractor) | 320 | Robust web data extraction |

**L4 — Vertical applications.** Where the job-posting-parser example lives. This is the
bulk of the corpus by count and the thinnest by substance: overwhelmingly single-author
repos under 10 stars.

| Domain | Repos | Comment |
|---|---|---|
| Invoices / finance | 229 | Densest vertical; invoice-to-JSON is the canonical demo |
| Jobs / recruiting | 228 | Resume parsers dominate; job-posting parsers are mostly scrapers |
| Research papers | 167 | Often academic tooling |
| Medical / clinical | 97 | Local models heavily favoured |
| Knowledge graphs | 96 | Entity + relation extraction into a graph |
| E-commerce | 46 | |
| Legal | 46 | Contract clause extraction |
| News / media | 26 | |
| Logs / security | 23 | |
| Real estate | 13 | |
| ID / forms | 11 | |

**L5 — Research.** 30 repos: benchmarks, paper implementations, evaluation harnesses.
[urchade/GLiNER](https://github.com/urchade/GLiNER) (3,537) is the notable non-LLM
alternative — a small dedicated NER model that is far cheaper than a generative call.

## What almost nobody does

Signal prevalence across the 1,738 relevant repos, measured from README and manifest text:

| Capability | Repos | Share |
|---|---|---|
| Batch / concurrent processing | 1,006 | 58% |
| PDF handling | 738 | 42% |
| Any evaluation or accuracy discussion | 579 | 33% |
| OCR / vision | 501 | 29% |
| Cost or token tracking | 467 | 27% |
| Human review / correction loop | 437 | 25% |
| Retry on validation failure | 317 | 18% |

The gap is consistent. Two thirds of these projects never mention measuring whether the
extraction is correct, three quarters have no correction path when it isn't, and 82% do
not retry on validation failure. Almost none version their schemas — a schema change and
a model change are indistinguishable in every repo examined.

Only [google/langextract](https://github.com/google/langextract) treats source grounding —
mapping each extracted field back to a character span in the input — as a first-class
feature. For any extraction a human must audit, that is the difference between a
reviewable output and an unfalsifiable one.

## Method

GitHub repository search via 92 queries across four families: mechanism vocabulary
(`structured output`, `constrained decoding`, `json schema`), extraction vocabulary
(`information extraction`, `unstructured to structured`), modality (`pdf`, `ocr`, `web
scraping`), and vertical (`invoice`, `resume`, `clinical`, `contract`). Star-sliced
queries (`stars:20..80`, `stars:81..400`) reached past the 1,000-result ranking cap.

Every repo was then independently validated by fetching its README from
`raw.githubusercontent.com` — 2,235 of 2,641 returned content, and a 12-repo sample of the
remainder confirmed all exist but have no README file. Classification signals were
computed by regex over README plus package manifest. Star counts were spot-checked against
fresh API queries and matched exactly.

Reproduce from `data/corpus.csv` (all 2,641) and `data/shortlist.csv` (the 1,738 relevant).

## Limits

- **Layer assignment is ~67% accurate.** Measured by hand-labelling a 30-repo held-out
  sample. Use the layer column for shape, not for per-repo truth. The named projects in
  the tables above were verified individually.
- **Coverage is broad but not saturated.** 83% of repos were surfaced by exactly one
  query, meaning more queries would still find more repos. Keyword search also has a
  systematic blind spot: it initially missed 32 of 49 known landmark projects, including
  `instructor`, because repo search matches name, description, and topics — and much of
  this ecosystem does not describe itself in the words a searcher would use. Those were
  backfilled explicitly.
- **Code-search counts are file counts**, inflated by forks and vendored dependencies.
- **Mechanism per repo is a lower bound** — it can only be seen where a README shows code.
