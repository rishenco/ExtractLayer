# Vision

## What it is

ExtractLayer is an open-source project that addresses one problem: LLM-based structured
data extraction. Teams describe intent and business logic in the simplest way, and
ExtractLayer is the layer where extraction quality and cost are observed, tested, and
optimized.

## Who it is for

A team with a table of source columns and derived columns that wants an observable,
trainable, updatable function — an "extractor" — mapping `(source_columns) ->
(derived_columns)`, or a set of such functions over different subsets of those columns.
In practice: startups and mid-size companies already extracting structured data from raw
inputs through an LLM API.

Not for anyone seeking a general fine-tuning platform. ExtractLayer solves data
extraction only.

## The job it replaces

Today these teams call `llm(system_prompt, raw_data) -> structured_data` directly. That
gives them no quality assurance — no observability of historical extractions, no specimen
datasets of human- or SOTA-LLM-defined pairs, no systematic testing of prompt versions,
no corner-case detection — so they stay on expensive 100B+ models, which holds until they
grow and need margins.

## Always true

- Intent and business logic are expressed in the simplest way. Optimizing extraction
  quality and cost happens in ExtractLayer, not in the user's prompts.
- The product is not a black box that magically solves the product owner's problem. It is
  a tool that optimizes for the explicit wishes of the product owner: users formulate
  their desires themselves and vet the datasets. AI assistance — anomaly detection,
  agentic workers that act like data engineers and adapt extractors by guessing and then
  verifying the user's intent — proposes against that explicit intent; it is a plugin on
  top of the core, never the core.
- AI-native: the product exposes a convenient MCP surface so agents can work with
  extractors, datasets, and the rest of the system.
- Good defaults that learn from what users ingest. The system should just work — like
  Apple devices, smart enough to be intuitive for everyone.

## Never

Generic. ExtractLayer is a vertical SaaS: it solves one problem, and the narrowness is
the chosen strategy — opinionated tools designed for this exact problem. The version to
hate having built is the general-purpose extraction or fine-tuning platform, or the black
box nobody can inspect.

## Twelve months

Stable, open-source, with real clients using it; the dev team is working on the managed
version. The number: 5 real clients, plus successful dogfooding at one cofounder's
employer.

## Riskiest assumption

Startups and mid-size companies really are doing this kind of extraction, and they do not
have enough infra to reliably observe and validate it. It is tested against reality in
two ways: real adoption at a company that makes money, and real talks with engineers and
founders of startups.

## Not building first

Metrics export in a universal format, the Slack integration, and the managed version come
after the core loop works end to end. The MVP trains a small LLM as the cheaper model;
deterministic extractors — regex, if-else, algorithmic parsers — come later.

## Build order

The core end to end — extractors, datasets, models, the metric engine, evals, the serve
path — on the background-job substrate, with training stubbed behind a real seam. Then
training (GEPA). Then the UI: list extractors; create one manually through a stepped
schema editor, or agentically from an uploaded file with an agent drafting the extractor
and a chat to refine it; an extractor screen holding datasets, schema, models and evals,
with jobs watched live through their progress. Then ingestion plugins (the
OpenAI-compatible proxy with detectors), metrics export, Slack, the managed version.
The implementation description is `docs/architecture.md`.

## Taste

Wanted: dev-ish but not complex. A modern, game-like UI that is intuitive and pleasant.
Everything reactive — no reloads in the browser, and an occasional reload never loses
information.

Avoided: the overloaded corp-style admin panel — Google Cloud, Excel, PowerPoint, partly
AWS. They look like the previous era.

## Open

- How much autonomy do the agentic workers get before a human must approve? The switch of
  an extractor to a cheaper model requires human approval; whether other adaptations do is
  undecided.
