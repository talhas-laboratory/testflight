# Initial upstream evaluation

Research captured on 2026-08-18.

## Cognee

Cognee is Apache-2.0, supports Python 3.10 through 3.14, and exposes a pipeline-oriented memory
system with replaceable LLM, graph, vector, and relational infrastructure. Its released Python
package is the right first integration boundary; copying its large repository would add no value.

Sources: [repository](https://github.com/topoteretes/cognee),
[package metadata](https://github.com/topoteretes/cognee/blob/main/pyproject.toml), and
[architecture notes](https://github.com/topoteretes/cognee/blob/main/CLAUDE.md).

## DeepSeek Harness

DeepSeek Harness is MIT-licensed and built around Cordis plugins, profiles, bundles, reversible
effects, typed events, and replaceable services. The project explicitly labels itself a developer
preview with compatibility-breaking changes. Testflight should therefore use an out-of-tree
plugin/profile overlay and retain an exact commit alongside its pre-release CLI pin.

Sources: [repository](https://github.com/deepseek-ai/deepseek-harness),
[architecture](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md),
and [development guide](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/development.md).

## LangGraph

LangGraph is an MIT-licensed, stable Python orchestration library with durable execution concepts.
The library can be used independently of the commercial deployment control plane. Standalone
Agent Servers can also be containerized later, but introducing that server now would prematurely
select persistence and operational components.

Sources: [repository](https://github.com/langchain-ai/langgraph),
[library metadata](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/pyproject.toml),
and [standalone server documentation](https://docs.langchain.com/langsmith/deploy-standalone-server).

## Deployment direction

Cloudflare Containers can be evaluated later for stateless or externally persisted services.
Provider choice should follow an actual workload because agent execution, graph/vector storage,
checkpointing, accelerators, and long-running process requirements may demand different hosts.

Source: [Cloudflare Containers documentation](https://developers.cloudflare.com/containers/).
