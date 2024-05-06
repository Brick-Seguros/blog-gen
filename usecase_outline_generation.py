from type import Outline, Section, Subsection
from langchain_core.prompts import ChatPromptTemplate

class GenerateOutlineUseCase:
    def __init__(self, llm):
        self.llm = llm

    def set_for_topic(self, topic: str):
        """
            This function generates an outline for a blog post on a given topic
        """

        direct_gen_outline_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a Blog Post writer. Write an outline for a Blog Post page about a user-provided topic. Be comprehensive and specific.",
                ),
                ("user", topic),
            ]
        )
        generate_outline_direct = direct_gen_outline_prompt | self.llm.with_structured_output(
            Outline
        )

        return generate_outline_direct
    