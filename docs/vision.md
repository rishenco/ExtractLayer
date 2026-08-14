# Vision

## What it is

ExtractLayer is where LLM-based extractors live. You define an extractor here, we run it, and every run is recorded — input, output, prompt version, latency, cost, failure. Versioning and auto-improvement are built on that record.

We are a runtime, not a wrapper. Users do not keep their own inference loop and call us to watch it; they hand us the extractor.

## Who it is for

Platform and AI teams at mid-size companies — the people who own extractors other teams depend on, and who are on the hook when one silently degrades. They inherited the prompt; they did not write it yesterday. They care about regression safety, cost attribution, and separate environments.

Not the first user: solo developers wanting a ten-minute self-serve tool, and non-technical operators reviewing extractions by hand. Either may come later. Neither shapes decisions now.

## What has to be excellent

Observability. "I finally know what my extractors are doing" is why someone signs up. Versioning and auto-improvement are why they stay, and both consume the same run record — but if observability is mediocre, nothing downstream matters.

Ranked: observability > versioning and regression safety > auto-improvement.

## Open tension

The wedge is observability, which sells on immediate time-to-value. Being a full platform means migrating an extractor before seeing anything at all. Unresolved: what a user can see in their first ten minutes without moving their pipeline.
