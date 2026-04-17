from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import date


class SourceLink(BaseModel):
    platform: str = Field(description="Platform name e.g. Lowyat, Reddit, RinggitPlus")
    url: Optional[str] = Field(default=None, description="Full URL as found in the report, null if not provided")


class Quote(BaseModel):
    text: str = Field(description="The representative quote or paraphrase")
    source: str = Field(description="Source platform e.g. Lowyat, Reddit, RinggitPlus")


class Topic(BaseModel):
    id: int = Field(description="Topic number / rank")
    theme: str = Field(description="Short theme label, 2-5 words")
    title: str = Field(description="Full topic title as scraped")

    hotness: int = Field(
        ge=1, le=10,
        description="Engagement level 1-10 based on post volume, recency, reply depth"
    )
    hotness_rationale: str = Field(
        description="One sentence explaining the hotness score"
    )

    sentiment: Literal["positive", "negative", "neutral", "mixed"] = Field(
        description="Overall sentiment of the discussion"
    )
    sentiment_score: float = Field(
        ge=-1.0, le=1.0,
        description="Numeric sentiment from -1.0 (very negative) to +1.0 (very positive)"
    )

    summary: str = Field(
        description="2-3 sentence neutral summary of what people are saying"
    )

    key_complaints: list[str] = Field(
        default=[],
        description="Bullet-point complaints raised by users"
    )
    key_praises: list[str] = Field(
        default=[],
        description="Bullet-point praises raised by users"
    )

    representative_quotes: list[Quote] = Field(
        default=[],
        max_length=2,
        description="Up to 2 representative quotes or close paraphrases with source"
    )

    sources: list[SourceLink] = Field(
        description="Sources where this topic was observed, each with platform name and URL if available"
    )
    tags: list[str] = Field(
        description="Keyword tags for filtering e.g. ['fees', 'annual-fee', 'waiver']"
    )


class BuzzingTopicsReport(BaseModel):
    brand: str = Field(description="Brand or entity being monitored")
    generated_at: str = Field(description="ISO timestamp of report generation")
    period_start: date
    period_end: date
    sources_monitored: list[str] = Field(
        description="Platforms scanned e.g. ['Lowyat', 'Reddit r/MalaysianPF', 'RinggitPlus']"
    )
    total_topics: int
    topics: list[Topic]
    analyst_notes: str = Field(
        default="",
        description="Any caveats or notes about data coverage"
    )