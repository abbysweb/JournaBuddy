"""
JournaBuddy Semantic Chunker Service
Splits raw PDF text into logical sections (Abstract, Introduction, etc.)
using heading pattern detection. Each chunk is returned with its section name
and index for downstream embedding and LLM agent processing.
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class TextChunk:
    """Represents a single semantic chunk extracted from a PDF."""
    index: int
    section_name: str
    text: str


# Known academic section headings to detect (case-insensitive)
KNOWN_SECTIONS = [
    "abstract",
    "introduction",
    "background",
    "related work",
    "literature review",
    "methodology",
    "methods",
    "materials and methods",
    "experimental setup",
    "results",
    "discussion",
    "conclusion",
    "conclusions",
    "future work",
    "acknowledgements",
    "acknowledgments",
    "references",
    "bibliography",
    "appendix",
]

# Regex to detect section headings (standalone line, possibly numbered)
_HEADING_PATTERN = re.compile(
    r"^\s*(?:\d+[\.\d]*\s+)?(" + "|".join(re.escape(s) for s in KNOWN_SECTIONS) + r")\s*$",
    re.IGNORECASE | re.MULTILINE,
)


class SemanticChunker:
    """
    Splits PDF text into named section-based chunks.

    Algorithm:
    1. Scan the raw text for known academic section headings.
    2. Split the text at each detected heading boundary.
    3. Return each section as a TextChunk with its section label.
    4. If no headings are found, falls back to fixed-size paragraph splitting.
    """

    def __init__(self, max_chars_per_chunk: int = 3000):
        """
        Args:
            max_chars_per_chunk: Maximum characters per chunk before splitting.
                                  Used for the fallback paragraph mode.
        """
        self.max_chars_per_chunk = max_chars_per_chunk

    def chunk(self, text: str) -> list[TextChunk]:
        """
        Split the provided text into semantic chunks.

        Args:
            text: Full extracted text from the PDF.

        Returns:
            List of TextChunk objects sorted by chunk index.
        """
        chunks: list[TextChunk] = []
        matches = list(_HEADING_PATTERN.finditer(text))

        if not matches:
            # Fallback: split by paragraph boundaries if no headings found
            return self._paragraph_split(text)

        # Build chunks between detected heading positions
        for i, match in enumerate(matches):
            section_name = match.group(1).title()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section_text = text[start:end].strip()

            if not section_text:
                continue

            # If a single section is very long, sub-split it
            if len(section_text) > self.max_chars_per_chunk:
                sub_chunks = self._split_by_size(section_text, section_name)
                for sub in sub_chunks:
                    sub.index = len(chunks)
                    chunks.append(sub)
            else:
                chunks.append(TextChunk(
                    index=len(chunks),
                    section_name=section_name,
                    text=section_text,
                ))

        return chunks

    def _paragraph_split(self, text: str) -> list[TextChunk]:
        """
        Fallback chunking: splits text into paragraphs by double newlines.
        Labels each chunk as 'Body' with a sequential index.
        """
        paragraphs = re.split(r"\n{2,}", text.strip())
        chunks = []
        buffer = ""
        for para in paragraphs:
            if len(buffer) + len(para) < self.max_chars_per_chunk:
                buffer += para + "\n\n"
            else:
                if buffer.strip():
                    chunks.append(TextChunk(
                        index=len(chunks),
                        section_name="Body",
                        text=buffer.strip(),
                    ))
                buffer = para + "\n\n"
        if buffer.strip():
            chunks.append(TextChunk(
                index=len(chunks),
                section_name="Body",
                text=buffer.strip(),
            ))
        return chunks

    def _split_by_size(self, text: str, section_name: str) -> list[TextChunk]:
        """Split an oversized section into fixed-size sub-chunks."""
        parts = []
        while text:
            parts.append(TextChunk(
                index=0,  # Will be reassigned by caller
                section_name=section_name,
                text=text[:self.max_chars_per_chunk].strip(),
            ))
            text = text[self.max_chars_per_chunk:]
        return parts
