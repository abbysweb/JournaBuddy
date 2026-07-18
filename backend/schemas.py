from pydantic import BaseModel, Field
from typing import List, Optional

class CitationReference(BaseModel):
    doi: str = Field(..., description="The DOI of the cited paper")
    title: str = Field(..., description="The title of the paper")
    year: str = Field(..., description="The year of publication")

class CitationSchema(BaseModel):
    dois: List[CitationReference] = Field(default_factory=list, description="List of extracted references")
    coverage_percent: float = Field(..., description="Percentage of claims backed by citations")

class ProofreadIssue(BaseModel):
    type: str = Field(..., description="Type of issue (e.g. grammar, spelling, style)")
    description: str = Field(..., description="Description of the issue")
    suggestion: str = Field(..., description="Suggested fix")

class ProofreadSchema(BaseModel):
    structure_score: int = Field(..., description="Score from 0-100 evaluating the structure")
    issues: List[ProofreadIssue] = Field(default_factory=list, description="List of grammatical or stylistic issues")

class TruthCheckSchema(BaseModel):
    hallucination_score: float = Field(..., description="Score from 0.0 to 1.0 indicating hallucination likelihood")
    consistency_score: float = Field(..., description="Score from 0.0 to 1.0 indicating logical consistency")
    flagged_claims: List[str] = Field(default_factory=list, description="List of specific claims that are highly suspicious")

class QualityGateSchema(BaseModel):
    overall_grade: str = Field(..., description="Letter grade like A, B, C, D, or F")
    confidence: float = Field(..., description="Confidence score from 0.0 to 1.0")
    bias_score: float = Field(..., description="Score from 0.0 to 1.0 indicating detected bias")
    verdict: str = Field(..., description="A short one-sentence final verdict")
    strengths: List[str] = Field(default_factory=list, description="Key strengths of the paper")
    weaknesses: List[str] = Field(default_factory=list, description="Key weaknesses of the paper")
    suggestions: List[str] = Field(default_factory=list, description="Actionable improvement suggestions")
