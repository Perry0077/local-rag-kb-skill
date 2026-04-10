from __future__ import annotations

from dataclasses import asdict
import json
import re
from typing import List, Sequence

from openai import OpenAI

from .config import RuntimeConfig
from .models import ContextCandidate, HostAnswerBundle, QueryHit
from .utils import strip_markdown_formatting


def build_context_prompt(contexts: Sequence[ContextCandidate]) -> str:
    parts: List[str] = []
    for index, context in enumerate(contexts, start=1):
        parts.append(
            "\n".join(
                [
                    f"[{index}] Title: {context.title}",
                    f"[{index}] Source: {context.source_rel_path}",
                    f"[{index}] Mode: {context.mode}",
                    f"[{index}] Hit count: {context.hit_count}",
                    f"[{index}] Content: {context.text}",
                ]
            )
        )
    return "\n\n".join(parts)


def build_host_answer_instructions() -> str:
    return (
        "Answer only from the provided contexts. "
        "Do not invent facts. "
        "Keep the answer concise and readable. "
        "Use bracket citations like [1]. "
        "Do not use Markdown bold. "
        "After the answer, show a References section using the provided references only."
    )


def extract_cited_reference_indices(answer: str) -> List[int]:
    indices = sorted({int(match) for match in re.findall(r"\[(\d+)\]", answer)})
    return [index for index in indices if index >= 1]


def sanitize_answer_output(text: str) -> str:
    text = strip_markdown_formatting(text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def build_chat_answer(config: RuntimeConfig, question: str, contexts: Sequence[ContextCandidate]) -> str:
    client = OpenAI(api_key=config.chat_api_key, base_url=config.chat_base_url)
    system_prompt = (
        "You answer only from the provided knowledge-base contexts. "
        "Do not invent facts. Keep the answer concise. "
        "Use bracket citations like [1]. Do not use Markdown bold."
    )
    user_prompt = "\n\n".join(
        [
            f"Question: {question}",
            "Contexts:",
            build_context_prompt(contexts),
        ]
    )
    try:
        response = client.responses.create(
            model=config.chat_model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        output_text = getattr(response, "output_text", "")
        if output_text:
            return output_text.strip()
    except Exception:
        pass

    response = client.chat.completions.create(
        model=config.chat_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return (response.choices[0].message.content or "").strip()


def generate_answer(config: RuntimeConfig, question: str, contexts: Sequence[ContextCandidate]) -> str:
    if not contexts:
        return "I could not find relevant documents for this question."
    if config.chat_backend == "openai-compatible":
        if not config.chat_api_key:
            raise SystemExit("CHAT_BACKEND is openai-compatible but CHAT_API_KEY is missing.")
        return sanitize_answer_output(build_chat_answer(config, question, contexts))
    raise SystemExit(
        "CHAT_BACKEND=host is handled by the host orchestration layer. "
        "Use --emit-host-bundle for host-model answering, or switch CHAT_BACKEND to openai-compatible."
    )


def format_references(contexts: Sequence[ContextCandidate], cited_indices: Sequence[int]) -> str:
    lines = ["References:"]
    selected_indices = list(cited_indices) if cited_indices else list(range(1, len(contexts) + 1))
    for index in selected_indices:
        if index < 1 or index > len(contexts):
            continue
        context = contexts[index - 1]
        lines.append(f"[{index}] {context.title} | {context.source_rel_path}")
    return "\n".join(lines)


def build_host_answer_bundle(
    question: str,
    kb_name: str,
    contexts: Sequence[ContextCandidate],
    hits: Sequence[QueryHit],
    *,
    include_hits: bool = False,
) -> HostAnswerBundle:
    reference_rows = [
        {
            "index": index,
            "title": context.title,
            "source_rel_path": context.source_rel_path,
        }
        for index, context in enumerate(contexts, start=1)
    ]
    context_rows = [
        {
            "index": index,
            "title": context.title,
            "source_rel_path": context.source_rel_path,
            "mode": context.mode,
            "hit_count": context.hit_count,
            "text": context.text,
        }
        for index, context in enumerate(contexts, start=1)
    ]
    hit_rows = [
        {
            "chunk_id": hit.chunk_id,
            "doc_id": hit.doc_id,
            "title": hit.metadata.get("title", ""),
            "source_rel_path": hit.metadata.get("source_rel_path", ""),
            "chunk_index": hit.metadata.get("chunk_index", ""),
            "score": hit.score,
            "text": hit.text,
        }
        for hit in hits
    ] if include_hits else []
    return HostAnswerBundle(
        question=question,
        kb_name=kb_name,
        instructions=build_host_answer_instructions(),
        contexts=context_rows,
        references=reference_rows,
        hits=hit_rows,
    )


def format_host_answer_bundle_json(bundle: HostAnswerBundle) -> str:
    return json.dumps(asdict(bundle), ensure_ascii=False, indent=2)
