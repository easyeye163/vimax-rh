from pydantic import BaseModel, Field
from typing import List, Optional


class Event(BaseModel):
    index: int = Field(
        description="The index of the event in the sequence, starting from 0.",
        examples=[0, 1, 2],
    )
    is_last: bool = Field(
        description="Indicates if this is the last event.",
        examples=[False, True],
    )
    description: str = Field(
        description="A clear, concise summary of the event.",
    )
    timeframe: Optional[str] = Field(
        default=None,
        description="The timeframe in which the event occurs.",
    )
    characters: Optional[List[str]] = Field(
        default=None,
        description="List of character names involved in the event.",
    )
    cause: Optional[str] = Field(
        default=None,
        description="The cause or trigger of the event.",
    )
    process_chain: List[str] = Field(
        description="A step-by-step account of the event's progression.",
    )
    outcome: Optional[str] = Field(
        default=None,
        description="The outcome or result of the event.",
    )

    def __str__(self):
        s = f"Event {self.index}:"
        s += f"\nDescription: {self.description}"
        if self.timeframe:
            s += f"\nTimeframe: {self.timeframe}"
        if self.characters:
            s += f"\nCharacters: {', '.join(self.characters)}"
        if self.cause:
            s += f"\nCause: {self.cause}"
        s += "\nProcess Chain:"
        for i, process in enumerate(self.process_chain):
            s += f"\n  {i + 1}. {process}"
        if self.outcome:
            s += f"\nOutcome: {self.outcome}"
        return s
