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
                    "Você é um escritor de Blog. Escreva um esboço para uma página de Blog sobre um tópico fornecido pelo usuário. Seja abrangente e específico.",
                ),
                ("user", topic),
            ]
        )
        generate_outline_direct = direct_gen_outline_prompt | self.llm.with_structured_output(
            Outline
        )

        return generate_outline_direct
    