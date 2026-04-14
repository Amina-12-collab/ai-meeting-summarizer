"""
Module 3 + 5: Text Preprocessing & AI Summarisation Engine
Cleans raw transcript text, chunks it if too long, then calls the
OpenAI Chat API (GPT-4o-mini by default) to produce structured output.
"""
 
import os
import re
import json
from dotenv import load_dotenv
 
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
 
 
# ── Constants ─────────────────────────────────────────────────────────────────
# Approx tokens per chunk (GPT-4o-mini context = 128k, but smaller chunks
# give better, more focused summaries for each segment).
CHUNK_CHAR_LIMIT = 12_000   # ~3,000 tokens
OVERLAP_CHARS    = 500       # overlap between chunks to preserve context
 
 
# ── Public API ────────────────────────────────────────────────────────────────
def summarise_text(text: str) -> dict:
    """
    Clean, chunk (if needed), and summarise text.
 
    Returns a dict with keys:
        summary      : str
        key_points   : list[str]
        action_items : list[{"task": str, "assignee": str, "due": str}]
        decisions    : list[str]
    """
    cleaned = _preprocess(text)
    chunks  = _chunk(cleaned)
 
    if len(chunks) == 1:
        return _call_llm(chunks[0])
 
    # Multiple chunks — summarise each then merge
    partial_summaries = [_call_llm(c) for c in chunks]
    return _merge(partial_summaries)
 
 
# ── Preprocessing (Module 3) ──────────────────────────────────────────────────
def _preprocess(text: str) -> str:
    """Remove filler words, fix spacing, strip transcription artifacts."""
    # Remove common filler words
    fillers = r"\b(um+|uh+|hmm+|ah+|er+|like\s+I\s+said|you\s+know)\b"
    text = re.sub(fillers, "", text, flags=re.IGNORECASE)
 
    # Collapse multiple spaces / newlines
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
 
    # Strip repeated punctuation artifacts (e.g. "... ... ...")
    text = re.sub(r"(\.\s*){3,}", "... ", text)
 
    return text.strip()
 
 
# ── Chunking (Module 4) ───────────────────────────────────────────────────────
def _chunk(text: str) -> list[str]:
    """Split text into overlapping chunks if it exceeds CHUNK_CHAR_LIMIT."""
    if len(text) <= CHUNK_CHAR_LIMIT:
        return [text]
 
    chunks = []
    start  = 0
    while start < len(text):
        end = start + CHUNK_CHAR_LIMIT
        # Break at a sentence boundary if possible
        if end < len(text):
            boundary = text.rfind(". ", start, end)
            if boundary != -1:
                end = boundary + 1
        chunks.append(text[start:end].strip())
        start = end - OVERLAP_CHARS  # overlap for context continuity
    return chunks
 
 
# ── LLM Call (Module 5) ───────────────────────────────────────────────────────
def _call_llm(text: str) -> dict:
    """Send text to LLM and return structured result dict."""
    use_local = os.getenv("USE_LOCAL_LLM", "true").lower() == "true"
    
    if use_local:
        api_key = "ollama"
        base_url = "http://localhost:11434/v1"
        model = os.getenv("OPENAI_MODEL", "llama3")
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = None
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable not set.\n"
                "Add it to your .env file:  OPENAI_API_KEY=sk-..."
            )

    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError(
            "OpenAI SDK not installed. Run:  pip install openai"
        )

    if base_url:
        client = OpenAI(api_key=api_key, base_url=base_url)
    else:
        client = OpenAI(api_key=api_key)

    system_prompt = """You are an expert meeting analyst. 
Given a meeting transcript or notes, extract and return ONLY a valid JSON object 
with exactly these four keys:
 
{
  "summary": "<2-4 sentence overview of the meeting>",
  "key_points": ["<point 1>", "<point 2>", ...],
  "action_items": [
    {"task": "<what>", "assignee": "<who, or Unknown>", "due": "<date or TBD>"},
    ...
  ],
  "decisions": ["<decision 1>", "<decision 2>", ...]
}
 
Rules:
- Return ONLY the JSON. No markdown, no extra text, no code fences.
- key_points: 3-7 concise bullet points.
- action_items: list every concrete task mentioned. If no assignee is clear, use "Unknown".
- decisions: only final agreed outcomes, not discussions.
- If a field has nothing relevant, return an empty list [].
"""

    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": f"Meeting transcript:\n\n{text}"}
        ]
    )
 
    raw = response.choices[0].message.content.strip()
 
    # Strip accidental markdown fences if model adds them
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
 
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM returned invalid JSON: {e}\nRaw output:\n{raw}")
 
 
# ── Merge partial summaries (for chunked docs) ────────────────────────────────
def _merge(partials: list[dict]) -> dict:
    """Combine multiple chunk summaries into one final result."""
    combined_text = "\n\n".join(
        f"[Section {i+1}]\n"
        f"Summary: {p.get('summary','')}\n"
        f"Key Points: {'; '.join(p.get('key_points',[]))}\n"
        f"Action Items: {json.dumps(p.get('action_items',[]))}\n"
        f"Decisions: {'; '.join(p.get('decisions',[]))}"
        for i, p in enumerate(partials)
    )
    # Re-run LLM on the combined partial summaries for a coherent final output
    return _call_llm(combined_text)
 