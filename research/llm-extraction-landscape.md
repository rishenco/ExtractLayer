# LLM extraction on GitHub: who builds `llm(system, raw_text) -> structured_data`

Survey of 3,133 GitHub repositories, August 2026.

## The short version

The primitive is solved and commoditised. Turning raw text into a typed object is now
three lines against a provider API, and roughly a dozen mature libraries wrap it.

What is *not* solved is everything around the call: knowing whether an extraction was
right, correcting it when it wasn't, and running it over a corpus at a price you can
predict. The corpus splits sharply — a small head of serious infrastructure, and a very
long tail of one-off pipelines rebuilding the same call. Median star count of the 2,149
relevant repos is **2**.

## Corpus at a glance

| | |
|---|---|
| Unique repos found | 3,133 |
| Passed relevance filter | 2,149 |
| READMEs fetched and parsed | 3,025 |
| Distinct search queries | 106 |
| Created 2025 or later | 1,712 of 2,149 (80%) |
| Pushed since Dec 2025 | 1,827 of 2,149 (85%) |
| Archived | 26 |

Star distribution of the relevant set:

| Stars | Repos |
|---|---|
| < 10 | 1,548 (72%) |
| 10–99 | 367 |
| 100–999 | 144 |
| ≥ 1,000 | 90 |

Languages: Python 1,290 (60%), TypeScript 225, Jupyter 175, JavaScript 95, Rust 56, Go 52.

Schema is written as a Pydantic model in 727 repos, as literal JSON Schema in 474, and as
Zod in 114. Pydantic is the de facto schema language of this space; Zod is its TypeScript
equivalent and trails by roughly 6×.

Providers named: OpenAI 1,134, local runtimes (Ollama / llama.cpp / vLLM) 871,
Anthropic 719, Google 575, LiteLLM/OpenRouter 195. Local inference is not a niche here —
it appears in 41% of relevant repos, mostly where documents cannot leave the building.

## What actually enforces the structure

Per-repo READMEs rarely show the mechanism — 1,675 of 2,149 (78%) describe the capability
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
bulk of the corpus by count and the thinnest by substance.

Domain is tagged from the repo description and README tagline only, not the README body —
scoping it to the body inflated every vertical by 25–50%, because general-purpose
libraries like BAML and Mirascope use "extract a resume" as their headline example.

| Domain | Repos | Comment |
|---|---|---|
| Invoices / finance | 191 | Densest vertical; invoice-to-JSON is the canonical demo |
| Jobs / recruiting | 160 | Resume/ATS parsers outnumber job-posting parsers ~2:1 |
| Research papers | 100 | Often academic tooling |
| Medical / clinical | 93 | Local models heavily favoured |
| Knowledge graphs | 80 | Entity + relation extraction into a graph |
| Legal | 35 | Contract clause extraction |
| E-commerce | 22 | |
| Logs / security | 17 | |
| News / media | 13 | |
| Real estate | 10 | |
| ID / forms | 8 | |

The two densest verticals are almost entirely hobby work. Across the 191 invoice repos the
median star count is 1 and only 4 clear 100 stars; across the 160 job/recruiting repos the
median is 1 and exactly one clears 100. Nobody has consolidated either vertical — which is
either an opportunity or a warning that per-vertical extraction does not hold value on its
own.

**L5 — Research.** 30 repos: benchmarks, paper implementations, evaluation harnesses.
[urchade/GLiNER](https://github.com/urchade/GLiNER) (3,537) is the notable non-LLM
alternative — a small dedicated NER model that is far cheaper than a generative call.

## What almost nobody does

Signal prevalence across the 2,149 relevant repos, measured from README and manifest text:

| Capability | Repos | Share |
|---|---|---|
| Batch / concurrent processing | 1,201 | 56% |
| PDF handling | 850 | 40% |
| Any evaluation or accuracy discussion | 700 | 33% |
| OCR / vision | 583 | 27% |
| Cost or token tracking | 566 | 26% |
| Human review / correction loop | 514 | 24% |
| Retry on validation failure | 386 | 18% |

These are *mentions*, not audited capabilities — a repo counted under "evaluation" may only
say the word once. That makes them an upper bound, which sharpens the finding rather than
softening it: even counting generously, two thirds of these projects never raise the
question of whether the extraction is correct, three quarters describe no correction path
when it isn't, and 82% never mention retrying on validation failure.

Only [google/langextract](https://github.com/google/langextract) treats source grounding —
mapping each extracted field back to a character span in the input — as a first-class
feature. For any extraction a human must audit, that is the difference between a
reviewable output and an unfalsifiable one.

## Method

GitHub repository search via 106 queries across four families: mechanism vocabulary
(`structured output`, `constrained decoding`, `json schema`), extraction vocabulary
(`information extraction`, `unstructured to structured`), modality (`pdf`, `ocr`, `web
scraping`), and vertical (`invoice`, `resume`, `clinical`, `contract`). Star-sliced
queries (`stars:20..80`, `stars:81..400`) reached past the 1,000-result ranking cap.

Every repo was then independently validated by fetching its README from
`raw.githubusercontent.com` — 3,025 of 3,133 returned content, and a 12-repo sample of the
remainder confirmed all exist but have no README file. Classification signals were
computed by regex over README plus package manifest. Star counts were spot-checked against
fresh API queries and matched exactly.

Reproduce from `data/corpus.csv` (all 3,133) and `data/shortlist.csv` (the 2,149 relevant).

## Limits

- **Layer assignment is ~67% accurate.** Measured by hand-labelling a 30-repo held-out
  sample. Use the layer column for shape, not for per-repo truth. The named projects in
  the tables above were verified individually.
- **Coverage is broad but not saturated.** 82% of repos were surfaced by exactly one
  query, meaning more queries would still find more repos. Keyword search also has a
  systematic blind spot: it initially missed 32 of 49 known landmark projects, including
  `instructor`, because repo search matches name, description, and topics — and much of
  this ecosystem does not describe itself in the words a searcher would use. Those were
  backfilled explicitly.
- **Code-search counts are file counts**, inflated by forks and vendored dependencies.
- **Mechanism per repo is a lower bound** — it can only be seen where a README shows code.
