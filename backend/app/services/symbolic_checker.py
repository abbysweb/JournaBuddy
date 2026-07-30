"""
JournaBuddy Symbolic Checker Service
Implements three deterministic rule-based analysis modules:

1. Acronym Resolution Checker — detects acronyms not defined on first use.
2. Section Completeness Auditor — verifies all mandatory sections are present.
3. Grammar & Passive Voice Density Analyzer — estimates passive voice percentage.

These checks are fast, offline, and fully deterministic (no LLM required).
All results are returned in a structured dict ready for provenance logging.
"""
import re
import logging
from dataclasses import dataclass, field
from typing import Optional

import textstat
import math
from collections import Counter

logger = logging.getLogger(__name__)

# Mandatory sections every scientific paper should contain
REQUIRED_SECTIONS = {
    "abstract",
    "introduction",
    "methodology",
    "results",
    "conclusion",
}

# Common abbreviations that do NOT need to be defined (always acceptable)
COMMON_ABBREVIATIONS = {
    "AI", "ML", "NLP", "API", "URL", "HTTP", "HTTPS", "SQL", "PDF", "DOI",
    "HTML", "CSS", "GPU", "CPU", "RAM", "e.g.", "i.e.", "etc.", "Fig", "Tab",
    "USA", "EU", "PhD", "MSc", "BSc", "IEEE", "ACM",
}

# Regex to detect acronym definitions: e.g., "Natural Language Processing (NLP)"
_DEFINITION_PATTERN = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+\(([A-Z]{2,})\)")

# Regex to detect standalone uppercase acronyms (2-6 letters)
_ACRONYM_USAGE_PATTERN = re.compile(r"\b([A-Z]{2,6})\b")

# Passive voice detection: "is/was/were/are/been + past participle"
_PASSIVE_PATTERN = re.compile(
    r"\b(is|was|were|are|been|be|being)\s+\w+ed\b",
    re.IGNORECASE
)


@dataclass
class SymbolicCheckResult:
    """
    Container for all symbolic rule-check results.

    Attributes:
        undefined_acronyms: List of acronyms found used before definition.
        defined_acronyms: Dict mapping acronym → full form.
        missing_sections: Set of required sections not found in the document.
        found_sections: Set of section headings detected.
        passive_voice_percent: Estimated percentage of passive voice sentences.
        simpson_diversity_index: Mathematical measure of vocabulary repetition.
        mattr: Moving-Average Type-Token Ratio for length-agnostic vocabulary richness.
        coleman_liau_index: PDF-safe grade level metric based on characters.
        smog_index: SMOG readability index.
        gunning_fog: Gunning Fog readability index.
        flesch_reading_ease: Flesch Reading Ease score.
        jaccard_similarity: Redundancy overlap between start and end of paper.
        total_words: Total word count of the document.
        issues: Human-readable list of all detected problems.
    """
    undefined_acronyms: list[str] = field(default_factory=list)
    defined_acronyms: dict[str, str] = field(default_factory=dict)
    missing_sections: set[str] = field(default_factory=set)
    found_sections: set[str] = field(default_factory=set)
    passive_voice_percent: float = 0.0
    lexical_density: float = 0.0
    shannon_entropy: float = 0.0
    simpson_diversity_index: float = 0.0
    mattr: float = 0.0
    coleman_liau_index: float = 0.0
    smog_index: float = 0.0
    gunning_fog: float = 0.0
    flesch_reading_ease: float = 0.0
    jaccard_similarity: float = 0.0
    top_keywords: list[str] = field(default_factory=list)
    total_words: int = 0
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialise result to a JSON-compatible dictionary."""
        return {
            "undefined_acronyms": self.undefined_acronyms,
            "defined_acronyms": self.defined_acronyms,
            "missing_sections": list(self.missing_sections),
            "found_sections": list(self.found_sections),
            "passive_voice_percent": round(self.passive_voice_percent, 2),
            "lexical_density": round(self.lexical_density, 2),
            "shannon_entropy": round(self.shannon_entropy, 2),
            "simpson_diversity_index": round(self.simpson_diversity_index, 4),
            "mattr": round(self.mattr, 2),
            "coleman_liau_index": round(self.coleman_liau_index, 2),
            "smog_index": round(self.smog_index, 2),
            "gunning_fog": round(self.gunning_fog, 2),
            "flesch_reading_ease": round(self.flesch_reading_ease, 2),
            "jaccard_similarity": round(self.jaccard_similarity, 2),
            "top_keywords": self.top_keywords,
            "total_words": self.total_words,
            "issues": self.issues,
        }


class SymbolicChecker:
    """
    Runs three deterministic rule-based checks on extracted PDF text:
    1. Acronym resolution completeness
    2. Mandatory section presence
    3. Passive voice / readability metrics

    Usage:
        checker = SymbolicChecker()
        result = checker.check(full_text)
    """

    def check(self, text: str) -> SymbolicCheckResult:
        """
        Execute all symbolic checks on the given text.

        Args:
            text: Full extracted text from the PDF document.

        Returns:
            SymbolicCheckResult containing all findings.
        """
        result = SymbolicCheckResult()

        self._check_acronyms(text, result)
        self._check_sections(text, result)
        self._check_readability(text, result)

        logger.info(
            f"Symbolic check complete — "
            f"undefined acronyms: {len(result.undefined_acronyms)}, "
            f"missing sections: {len(result.missing_sections)}, "
            f"passive voice: {result.passive_voice_percent:.1f}%"
        )
        return result

    def _check_acronyms(self, text: str, result: SymbolicCheckResult) -> None:
        """
        Detect acronyms used before or without a definition.
        Scans for the pattern "Full Name (ACRONYM)" to build the definition set.
        """
        # Step 1: find all acronyms that are properly defined
        definitions = _DEFINITION_PATTERN.findall(text)
        defined = {acronym: full_form for full_form, acronym in definitions}
        result.defined_acronyms = defined

        # Step 2: find all standalone uppercase acronym usages
        used_acronyms = set(_ACRONYM_USAGE_PATTERN.findall(text))

        # Step 3: report acronyms used but never defined
        for acronym in sorted(used_acronyms):
            if (
                acronym not in defined
                and acronym not in COMMON_ABBREVIATIONS
                and len(acronym) >= 2
            ):
                result.undefined_acronyms.append(acronym)

        if result.undefined_acronyms:
            result.issues.append(
                f"Undefined acronyms detected: {', '.join(result.undefined_acronyms[:10])}"
                + (" (and more)" if len(result.undefined_acronyms) > 10 else "")
            )

    def _check_sections(self, text: str, result: SymbolicCheckResult) -> None:
        """
        Verify that all required academic sections are present in the document.
        Uses case-insensitive scanning against REQUIRED_SECTIONS.
        """
        text_lower = text.lower()

        for section in REQUIRED_SECTIONS:
            # Allow flexible matching (e.g., "methodology" also matches "methods")
            if section in text_lower or section.rstrip("y") + "ies" in text_lower:
                result.found_sections.add(section)
            elif section == "methodology" and "methods" in text_lower:
                result.found_sections.add(section)
            elif section == "conclusion" and "conclusions" in text_lower:
                result.found_sections.add(section)

        result.missing_sections = REQUIRED_SECTIONS - result.found_sections

        if result.missing_sections:
            result.issues.append(
                f"Missing required sections: {', '.join(sorted(result.missing_sections))}"
            )

    def _check_readability(self, text: str, result: SymbolicCheckResult) -> None:
        """
        Calculate passive voice density and rigorous statistical NLP metrics.
        """
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        total_sentences = max(len(sentences), 1)

        passive_count = sum(
            1 for s in sentences if _PASSIVE_PATTERN.search(s)
        )
        result.passive_voice_percent = (passive_count / total_sentences) * 100

        # Mathematical NLP Metrics (immune to PDF punctuation artifacts)
        # 1. Clean and tokenize into lowercase words
        words = re.findall(r"\b[a-z]{2,}\b", text.lower())
        result.total_words = len(words)
        
        if result.total_words > 0:
            word_counts = Counter(words)
            unique_words = len(word_counts)
            
            # Lexical Density (Type-Token Ratio)
            result.lexical_density = (unique_words / result.total_words) * 100
            
            # Shannon Entropy & Simpson's Diversity Index
            entropy = 0.0
            simpson_sum = 0.0
            for count in word_counts.values():
                p = count / result.total_words
                entropy -= p * math.log2(p)
                simpson_sum += (count / result.total_words) ** 2
                
            result.shannon_entropy = entropy
            result.simpson_diversity_index = 1.0 - simpson_sum
            
            # MATTR (Moving-Average Type-Token Ratio)
            window_size = 50
            if result.total_words >= window_size:
                ttr_sum = 0.0
                num_windows = result.total_words - window_size + 1
                for i in range(num_windows):
                    window = words[i:i + window_size]
                    ttr_sum += len(set(window)) / window_size
                result.mattr = (ttr_sum / num_windows) * 100
            else:
                result.mattr = result.lexical_density
            
            # Term Frequency (Keyword Extraction)
            stop_words = {"the", "and", "of", "to", "in", "a", "is", "that", "for", "it", "with", "as", "on", "was", "are", "by", "this", "an", "be", "from", "at", "which", "or", "have", "not", "but"}
            valid_words = [(w, c) for w, c in word_counts.items() if w not in stop_words and len(w) > 3]
            valid_words.sort(key=lambda x: x[1], reverse=True)
            result.top_keywords = [w[0] for w in valid_words[:7]]
            
        else:
            result.lexical_density = 0.0
            result.shannon_entropy = 0.0
            result.simpson_diversity_index = 0.0
            result.mattr = 0.0
            
        # Readability Indices using textstat and character counting
        letters = sum(c.isalpha() for c in text)
        if result.total_words > 0:
            L = (letters / result.total_words) * 100
            S = (total_sentences / result.total_words) * 100
            result.coleman_liau_index = 0.0588 * L - 0.296 * S - 15.8
        
        try:
            result.smog_index = textstat.smog_index(text)
            result.gunning_fog = textstat.gunning_fog(text)
            result.flesch_reading_ease = textstat.flesch_reading_ease(text)
        except Exception:
            pass
            
        # Jaccard Similarity (Self-Plagiarism / Redundancy Check)
        if len(words) > 600:
            start_words = set(words[:300])
            end_words = set(words[-300:])
            intersection = len(start_words.intersection(end_words))
            union = len(start_words.union(end_words))
            result.jaccard_similarity = (intersection / union) * 100 if union > 0 else 0.0
        else:
            result.jaccard_similarity = 0.0

        # Flag high passive voice usage (> 20% is academically discouraged)
        if result.passive_voice_percent > 20:
            result.issues.append(
                f"High passive voice density: {result.passive_voice_percent:.1f}% "
                f"(recommended < 20%)"
            )

        # Flag extremely low lexical density or entropy (suggests repetitive/filler text)
        if result.lexical_density > 0 and result.lexical_density < 10:
            result.issues.append(
                f"Extremely low vocabulary richness (Lexical Density: {result.lexical_density:.1f}%). Text may be highly repetitive."
            )
        if result.shannon_entropy > 0 and result.shannon_entropy < 5.0:
            result.issues.append(
                f"Low information density (Shannon Entropy: {result.shannon_entropy:.2f} bits). Text lacks complex vocabulary distribution."
            )
