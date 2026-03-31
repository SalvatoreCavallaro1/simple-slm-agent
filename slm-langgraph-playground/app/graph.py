from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any, Iterator, TypedDict

from langfuse import Langfuse
from langgraph.graph import END, START, StateGraph

from .config import Settings, load_settings
from .evaluator import evaluate_response
from .model_registry import get_model
from .ollama_client import OllamaClient
from .prompts import build_messages

logger = logging.getLogger(__name__)


class GraphState(TypedDict, total=False):
    input: str
    model: str
    messages: list[dict[str, str]]
    response: str
    started_at: float
    result: dict[str, Any]


class _NullObservation:
    def update(self, **_: Any) -> None:
        return None


@contextmanager
def _observation(
    client: Langfuse | None,
    *,
    name: str,
    as_type: str = "span",
    input: Any | None = None,
    output: Any | None = None,
    metadata: Any | None = None,
) -> Iterator[Any]:
    if client is None:
        yield _NullObservation()
        return

    with client.start_as_current_observation(
        name=name,
        as_type=as_type,
        input=input,
        output=output,
        metadata=metadata,
    ) as observation:
        yield observation


def build_graph(
    ollama_client: OllamaClient,
    langfuse_client: Langfuse | None = None,
) -> Any:
    workflow = StateGraph(GraphState)

    def input_node(state: GraphState) -> GraphState:
        logger.info(
            "Prepared prompt messages",
            extra={"graph_node": "input_node", "model": state["model"]},
        )
        return {"messages": build_messages(state["input"])}

    def model_node(state: GraphState) -> GraphState:
        with _observation(
            langfuse_client,
            name="model_call",
            input={"model": state["model"], "messages": state["messages"]},
            metadata={"model": state["model"], "temperature": 0},
        ) as observation:
            response = ollama_client.chat(
                model=state["model"],
                messages=state["messages"],
                temperature=0,
            )
            observation.update(output={"response": response})

        logger.info(
            "Model response generated",
            extra={"graph_node": "model_node", "model": state["model"]},
        )
        return {"response": response}

    def evaluator_node(state: GraphState) -> GraphState:
        latency_ms = (time.perf_counter() - state["started_at"]) * 1000
        result = evaluate_response(
            input_text=state["input"],
            model=state["model"],
            response=state["response"],
            latency_ms=latency_ms,
        )

        with _observation(
            langfuse_client,
            name="evaluation",
            input={"model": state["model"], "response": state["response"]},
            output=result,
            metadata={"model": state["model"], "latency_ms": result["metrics"]["latency_ms"]},
        ):
            logger.info(
                "Evaluation completed",
                extra={
                    "graph_node": "evaluator_node",
                    "model": state["model"],
                    "latency_ms": result["metrics"]["latency_ms"],
                },
            )

        return {"result": result}

    workflow.add_node("input_node", input_node)
    workflow.add_node("model_node", model_node)
    workflow.add_node("evaluator_node", evaluator_node)

    workflow.add_edge(START, "input_node")
    workflow.add_edge("input_node", "model_node")
    workflow.add_edge("model_node", "evaluator_node")
    workflow.add_edge("evaluator_node", END)

    return workflow.compile()


def run_graph(
    prompt: str,
    model: str | None = None,
    *,
    settings: Settings | None = None,
    ollama_client: OllamaClient | None = None,
    langfuse_client: Langfuse | None = None,
) -> dict[str, Any]:
    runtime_settings = settings or load_settings()
    selected_model = get_model(model, runtime_settings)
    client = ollama_client or OllamaClient.from_settings(runtime_settings)
    graph = build_graph(client, langfuse_client=langfuse_client)

    with _observation(
        langfuse_client,
        name="graph_execution",
        as_type="chain",
        input={"prompt": prompt, "model": selected_model},
        metadata={"available_models": list(runtime_settings.available_models)},
    ) as observation:
        final_state = graph.invoke(
            {
                "input": prompt,
                "model": selected_model,
                "started_at": time.perf_counter(),
            }
        )
        result = final_state["result"]
        observation.update(output=result)

    return result
