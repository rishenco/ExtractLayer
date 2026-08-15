# Changelog

## [Unreleased]

### Added
- `research/llm-extraction-landscape.md` — survey of GitHub projects implementing
  `llm(system, raw_text) -> structured_data`, built from a 3,133-repo corpus.
- `research/llm-extraction-landscape.html` — published version of the survey.
- `research/data/corpus.csv` — the full corpus with per-repo classification, raw
  signals, and the queries that surfaced each repo.
- `research/data/shortlist.csv` — the 2,150 repos that passed the relevance filter.
- `research/data/layer-accuracy-sample.csv` — hand-labelled 30-repo sample backing the
  ~60% layer-accuracy figure.
- `research/data/landmark-profiles.csv` — call shape, enforcement mechanism, retry and
  grounding support for 24 landmark projects, each adversarially verified against primary
  sources (0 of 24 overturned).

### Fixed
- README fetcher advanced its filename loop only on HTTP 404, so timeouts and 5xx cached
  an empty README. Empty READMEs cost 15 relevance points, meaning fetch failures were
  partly driving the relevance filter. Refetched with retries: 5 recovered, 103 confirmed
  to have no README at all.
- Domain tags were scoped to README bodies, inflating every vertical by 25-50% because
  general-purpose libraries use "extract a resume" as their headline example. Now scoped
  to description and tagline.
- Tightened capability regexes that matched on unrelated words (`batch` on bare
  "pipeline", `cost` on "cost-effective", human-review on "annotate", local-inference on
  any `transformers` import).
- Corpus CSV column named `pushed` held `updated_at`, which a single new star bumps.
  Renamed to `metadata_updated` and dropped the liveness claim that rested on it.
