# Cognee adapter

This boundary will translate Testflight memory operations into Cognee's ingestion, cognify,
search, and memory APIs. The upstream dependency is optional and loaded lazily so unrelated
experiments do not pay its installation or startup cost.

Install it with `uv sync --all-packages --extra cognee`.
