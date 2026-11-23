from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

POSITIVE = {"excited", "congratulations", "great", "achievement", "success", "growth", "innovative",
            "partner", "opportunity", "value", "impressive", "thrilled", "benefit", "improve", "welcome"}
NEGATIVE = {"unfortunately", "problem", "issue", "fail", "worry", "risk", "cheap", "urgent", "must",
            "behind", "lose", "threat", "regret"}


class SentimentInput(BaseModel):
    text: str = Field(..., description="Outreach text to analyse")


class SentimentAnalysisTool(BaseTool):
    name: str = "Sentiment Analysis Tool"
    description: str = ("Analyses the sentiment of outreach content and returns a score from -1 to 1 "
                        "with a suggestion. Aim for a positive, professional score above 0.3.")
    args_schema: Type[BaseModel] = SentimentInput

    def _run(self, text: str) -> str:
        words = [w.strip(".,!?;:()\"'").lower() for w in text.split()]
        pos = sum(w in POSITIVE for w in words)
        neg = sum(w in NEGATIVE for w in words)
        score = round((pos - neg) / max(pos + neg, 1), 2)
        label = "positive" if score > 0.3 else "neutral" if score >= 0 else "negative"
        tip = "Tone is good." if score > 0.3 else "Add warmer, achievement-focused language and remove pressure words."
        return f"Sentiment: {label} (score {score}; {pos} positive / {neg} negative cues). {tip}"
