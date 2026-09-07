# LangGraph adapter

This boundary owns graph definitions, checkpointing choices, and translation between Testflight
contracts and LangGraph state. `LangGraphWorkflowEngine` executes portable Testflight step
semantics through a compiled state graph while the shared runtime opts into the upstream package.
Other packages can still use the adapter without installing the optional orchestration dependency.

Install it with `uv sync --all-packages --extra langgraph`.
