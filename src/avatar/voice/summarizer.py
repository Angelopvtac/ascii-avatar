"""Transform Claude's text response into a spoken status update.

Zero-dependency local summarizer. No API calls.
Extracts the most useful spoken line from a Claude response
by finding the conclusion/question/result — not the opening.
"""

from __future__ import annotations

import re


def strip_markdown(text: str) -> str:
    """Remove markdown formatting, code blocks, file paths."""
    # Remove code blocks
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Remove inline code
    text = re.sub(r"`[^`]+`", "", text)
    # Remove headers
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove bold/italic
    text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
    # Remove links — keep label
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Remove bullet points
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    # Remove numbered lists
    text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
    # Remove file paths
    text = re.sub(r"/?(?:home|tmp|usr|etc|var|src|tests)/\S+", "", text)
    # Remove table formatting
    text = re.sub(r"\|[^\n]+\|", "", text)
    text = re.sub(r"^[-|:\s]+$", "", text, flags=re.MULTILINE)
    # Collapse whitespace
    text = re.sub(r"\n{2,}", ". ", text)
    text = " ".join(text.split())
    return text.strip()


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    # Split on sentence-ending punctuation followed by space or end
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in parts if s.strip() and len(s.strip()) > 5]


def _is_question(sentence: str) -> bool:
    return sentence.rstrip().endswith("?")


def _is_result(sentence: str) -> bool:
    """Check if sentence announces a result/completion."""
    patterns = [
        r"\b(done|complete|finished|ready|pass|success|fail|error|fixed|created|updated)\b",
        r"\b(all \d+ tests)\b",
        r"\b(committed|deployed|installed|running)\b",
        r"\b(here'?s|looks like|that'?s)\b",
    ]
    lower = sentence.lower()
    return any(re.search(p, lower) for p in patterns)


def _is_action_request(sentence: str) -> bool:
    """Check if sentence asks the user to do something."""
    patterns = [
        r"\b(want me to|should I|shall I|let me know|what do you)\b",
        r"\b(want to|would you|ready to|need your)\b",
    ]
    lower = sentence.lower()
    return any(re.search(p, lower) for p in patterns)


def summarize_for_voice(text: str) -> str:
    """Extract the most useful spoken line from a Claude response.

    Strategy:
    1. If response ends with a question → speak the question
    2. If response has a result/completion sentence → speak that
    3. If response has an action request → speak that
    4. Otherwise → speak the last meaningful sentence
    """
    if not text:
        return ""

    clean = strip_markdown(text)
    if not clean:
        return ""

    # Very short responses — just speak them
    if len(clean) < 100:
        return clean

    sentences = _split_sentences(clean)
    if not sentences:
        return clean[:150]

    # Priority 1: trailing question (Claude asking the user something)
    for s in reversed(sentences[-3:]):
        if _is_question(s):
            return _cap(s)

    # Priority 2: result/completion sentence
    for s in reversed(sentences):
        if _is_result(s):
            return _cap(s)

    # Priority 3: action request
    for s in reversed(sentences[-3:]):
        if _is_action_request(s):
            return _cap(s)

    # Priority 4: last sentence
    return _cap(sentences[-1])


def _cap(text: str, max_words: int = 35) -> str:
    """Cap at max_words, end cleanly."""
    words = text.split()
    if len(words) <= max_words:
        return text
    capped = " ".join(words[:max_words])
    # End at last sentence boundary if possible
    for i in range(len(capped) - 1, max(0, len(capped) - 20), -1):
        if capped[i] in ".!?,":
            return capped[: i + 1]
    return capped + "."
