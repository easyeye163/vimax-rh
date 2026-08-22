import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.chat_models.base import BaseChatModel
from pydantic import BaseModel, Field
from typing import List
from tenacity import retry, stop_after_attempt
from interfaces import CharacterInScene
from langchain_core.messages import HumanMessage, SystemMessage

from utils.retry import after_func

system_prompt_template_extract_characters = \
"""
[Role]
You are a top-tier movie script analysis expert.

[Task]
Your task is to analyze the provided script and extract all relevant character information.

[Input]
You will receive a script enclosed within <script> and </script> tags.

[Output]
{format_instructions}

[Guidelines]
- Ensure that the language of all output values(not include keys) matches that used in the script.
- Group all names referring to the same entity under one character. Select the most appropriate name as the character's identifier.
- If the character's name is not mentioned, you can use reasonable pronouns to refer to them.
- For background characters in the script, you do not need to consider them as individual characters.
- If a character's traits are not described or only partially outlined in the script, you need to design plausible features based on the context.
- In static features, describe the character's physical appearance, physique, and other relatively unchanging features. In dynamic features, describe the character's attire, accessories, key items they carry.
- Don't include any information about the character's personality, role, or relationships with others in either static or dynamic features.
- When designing character features, different character appearances should be made more distinct from each other.
- The description of characters should be detailed, avoiding the use of abstract terms. Instead, employ descriptions that can be visualized.
"""

human_prompt_template_extract_characters = \
"""
<script>
{script}
</script>
"""

class ExtractCharactersResponse(BaseModel):
    characters: List[CharacterInScene] = Field(
        ..., description="A list of characters extracted from the script."
    )

class CharacterExtractor:
    def __init__(
        self,
        chat_model: BaseChatModel,
    ):
        self.chat_model = chat_model

    @retry(
        stop=stop_after_attempt(3),
        after=after_func,
    )
    async def extract_characters(self, script: str) -> List[CharacterInScene]:
        parser = PydanticOutputParser(pydantic_object=ExtractCharactersResponse)

        messages = [
            SystemMessage(content=system_prompt_template_extract_characters.format(format_instructions=parser.get_format_instructions())),
            HumanMessage(content=human_prompt_template_extract_characters.format(script=script)),
        ]

        chain = self.chat_model | parser
        response: ExtractCharactersResponse = await chain.ainvoke(messages)
        return response.characters
