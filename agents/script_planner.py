import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.chat_models.base import BaseChatModel
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from tenacity import retry
from utils.retry import after_func

narrative_script_prompt_template = \
"""
You are a world-class creative writing and screenplay development expert with extensive experience in story structure, character development, and narrative pacing.

**Task**
Your task is to transform a basic story idea into a comprehensive, engaging script with rich narrative detail, compelling character arcs, and cinematic storytelling elements.

**Input**
You will receive a basic story idea or concept enclosed within <basic_idea> and </basic_idea>.

**Output**
{format_instructions}

**Guidelines**
No metaphors allowed!!!

1. **Story Structure**: Develop a clear three-act structure with proper setup, confrontation, and resolution.
2. **Character Development**: Create well-rounded characters with clear motivations, flaws, and character arcs.
3. **Visual Storytelling**: Write with cinematic language that emphasizes visual elements.
4. **Emotional Depth**: Incorporate emotional beats and character relationships.
5. **Pacing and Tension**: Build suspense and maintain engagement through proper scene transitions.
6. **Genre Consistency**: Maintain appropriate tone and style for the story's genre.
7. **Dialogue Quality**: When writing dialogue, use :" " symbols. Create natural, character-specific dialogue.
8. **Thematic Elements**: Weave in meaningful themes and subtext.
9. **Conflict and Stakes**: Establish clear external and internal conflicts.
10. **Satisfying Resolution**: Ensure all major plot threads are resolved.
11. **Each dialogue should not too short or too long.**

**Warnings**
- Don't write any camera movement in the script (e.g., cut to).
- No metaphors allowed.
"""

motion_script_prompt_template = \
"""
You are a top-tier action and motion-sequence script designer with deep visual expertise in conveying speed, force, choreography, and technical precision.

**Task**
Transform a basic idea into a motion-driven script that emphasizes precise action description, clear spatial orientation, and unambiguous, technically accurate details.

**Input**
You will receive a basic idea enclosed within <basic_idea> and </basic_idea>.

**Output**
{format_instructions}

**Global Rules**
No metaphors allowed. Less conversation.

**Motion Style Guidelines**
1. Technical Explicitness: Prefer precise nouns and qualifiers over poetic language.
2. Kinetic Clarity: Make trajectories, vectors, speed/acceleration sensations explicit.
3. Spatial Cohesion: Maintain a consistent mental map of positions.
4. Sequenced Action Beats: Write step-by-step beats that can be storyboarded.
5. Dialogue Minimalism: Use dialogue sparingly. Use :"dialogue" quotes for spoken lines.
6. Keep the script length appropriate.
7. If the user does not specify, only one character can appear at most.
8. Less character's actions close-ups, more exterior shots.
9. Don't describe the character's physical state.

**Warnings**
- Do not use metaphors.
"""

montage_script_prompt_template = \
"""
You are a top-tier montage script designer with deep expertise in compressing time, juxtaposing images, and shaping emotional arcs through shot selection and rhythm.

Task
Transform a basic idea into an emotion-driven montage script.

Input
You will receive a basic idea enclosed within <basic_idea> and </basic_idea>.

Output
{format_instructions}

**Global Rules**
No metaphors allowed. Keep dialogue minimal. Use pure paragraph.

**Montage Style Guidelines**
- For each scene, write multiple shots to enhance montage effect.
- Total no less than 500 words, each paragraph no more than 50 words.
- Escalation or Resolution: Build an emotional arc across beats.
- Sound Design Minimalism: Use sparse, precise notes.
- Dialogue Minimalism: Include dialogue only if it marks a clear emotional shift. Use :"dialogue" quotes.
- Visual Clarity Over Action: Focus on expressive visuals, reactions, and transitions.
- No extraneous physical traits.

**Warnings**
Do not use metaphors. Avoid poetic language.
"""

human_prompt_template_script_planner = \
"""
<basic_idea>
{basic_idea}
</basic_idea>
"""

class IntentRouterResponse(BaseModel):
    intent: Literal["narrative", "motion", "montage"] = Field(
        ..., description="Routing decision: 'narrative', 'motion', or 'montage'"
    )
    rationale: Optional[str] = Field(
        default=None, description="Brief reason for the classification"
    )

class PlannedScriptResponse(BaseModel):
    planned_script: str = Field(
        ...,
        description="The full planned script with rich narrative detail."
    )

class ScriptPlanner:
    def __init__(
        self,
        chat_model: BaseChatModel,
    ):
        self.chat_model = chat_model

    @retry(stop_after_attempt(3), after=after_func)
    async def plan_script(
        self,
        basic_idea: str,
    ) -> PlannedScriptResponse:
        # 1) Route intent to select the appropriate template
        router_parser = PydanticOutputParser(pydantic_object=IntentRouterResponse)
        router_prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    'system',
                    """
                    You are an intent router for script planning. Classify the user's basic idea:
                    - narrative: Character, plot, themes, dialogue focus.
                    - motion: Action, speed, vehicles, combat, sports focus.
                    - montage: Emotional arc through imagery and pacing.
                    {format_instructions}
                    """
                ),
                ('human', human_prompt_template_script_planner),
            ]
        )
        router_chain = router_prompt_template | self.chat_model | router_parser

        routing = await router_chain.ainvoke(
            {
                "format_instructions": router_parser.get_format_instructions(),
                "basic_idea": basic_idea,
            }
        )
        chosen_intent = routing.intent if isinstance(routing, IntentRouterResponse) else "narrative"
        logging.info(f"[ScriptPlanner] Intent routed to: {chosen_intent}")

        # 2) Build the planning chain with the selected template
        planning_parser = PydanticOutputParser(pydantic_object=PlannedScriptResponse)

        def get_system_template(intent: str) -> str:
            if intent == "narrative":
                return narrative_script_prompt_template
            if intent == "motion":
                return motion_script_prompt_template
            if intent == "montage":
                return montage_script_prompt_template
            return narrative_script_prompt_template

        system_template = get_system_template(chosen_intent)

        planning_prompt_template = ChatPromptTemplate.from_messages(
            [
                ('system', system_template),
                ('human', human_prompt_template_script_planner),
            ]
        )
        planning_chain = planning_prompt_template | self.chat_model | planning_parser

        try:
            logging.info(f"Planning script from basic idea: {basic_idea[:100]}...")
            response = await planning_chain.ainvoke(
                {
                    "format_instructions": planning_parser.get_format_instructions(),
                    "basic_idea": basic_idea,
                }
            )
            logging.info("Script planning completed.")
            return response
        except Exception as e:
            logging.error(f"Error planning script: \n{e}")
            raise e
