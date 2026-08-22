import logging
from typing import List
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain.chat_models.base import BaseChatModel
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt
from interfaces import Event
from utils.retry import after_func

system_prompt_template_extract_events = \
"""
You are a highly skilled Literary Analyst AI.

**TASK**
Extract the next event from the provided novel.

**INPUT**
1. The full text of the novel, enclosed within <novel_text> and </novel_text>.
2. Already-extracted events, enclosed within <extracted_events> and </extracted_events>.

**OUTPUT**
{format_instructions}

**GUIDELINES**
1. Focus on events critical to the plot.
2. Ensure the event is logically distinct from previous events.
3. If the event spans multiple scenes, unify them under a single dramatic goal.
4. Maintain objectivity.
5. For the process field, provide a detailed step-by-step account.
6. Every detail must be directly supported by the input novel.
7. The language of outputs should be same as the input text.
"""

human_prompt_template_extract_next_event = \
"""
<novel_text>
{novel_text}
</novel_text>

<extracted_events>
{extracted_events}
</extracted_events>
"""

class EventExtractor:
    def __init__(
        self,
        chat_model: BaseChatModel,
    ):
        self.chat_model = chat_model
        self.parser = PydanticOutputParser(pydantic_object=Event)

    async def __call__(
        self,
        novel_text: str,
    ) -> List[Event]:
        logging.info("Extracting events from novel...")
        events: List[Event] = []
        while True:
            event = await self.extract_next_event(novel_text, events)
            events.append(event)
            logging.info(f"Extracted event {event.index}")
            if event.is_last:
                break
        return events

    @retry(
        stop=stop_after_attempt(3),
        after=after_func,
    )
    async def extract_next_event(
        self,
        novel_text: str,
        extracted_events: List[Event],
    ) -> Event:
        extracted_events_str = "\n\n".join([str(e) for e in extracted_events])

        messages = [
            SystemMessage(
                content=system_prompt_template_extract_events.format(
                    format_instructions=self.parser.get_format_instructions(),
                ),
            ),
            HumanMessage(
                content=human_prompt_template_extract_next_event.format(
                    novel_text=novel_text,
                    extracted_events=extracted_events_str,
                )
            )
        ]

        chain = self.chat_model | self.parser
        event: Event = await chain.ainvoke(messages)

        assert event.index == len(extracted_events), \
            f"Extracted event index {event.index} != expected {len(extracted_events)}"

        return event
