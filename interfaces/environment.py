from pydantic import BaseModel, Field
from typing import Optional


class EnvironmentInScene(BaseModel):
    slugline: str = Field(
        description="The scene heading/slugline (e.g., 'INT. APARTMENT - DAY')",
        examples=["INT. APARTMENT - DAY", "EXT. BEACH - SUNSET"],
    )
    description: str = Field(
        description="A detailed description of the environment, including location, time, lighting, weather, and atmosphere.",
    )

    def __str__(self):
        return f"{self.slugline}: {self.description}"
