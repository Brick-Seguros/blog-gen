
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from type import Perspectives

class GeneratePerspectivesUseCase:
    def __init__(self, llm):
        self.llm = llm

    def set_for_topic(self, topic: str, examples: str):
        """
            This function generates perspectives for a blog post on a given topic
        """

        gen_perspectives_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    f"""
                    Você precisa selecionar um grupo diversificado (e distinto) de editores de Blog que trabalharão juntos para criar um artigo abrangente sobre o tópico. Cada um deles representa uma perspectiva, papel ou afiliação relacionada a este tópico.
                    Você pode usar outras páginas de Blog de tópicos relacionados para se inspirar. Para cada editor, adicione uma descrição do que eles vão focar.

                    Páginas de blog para inspiração:
                    {examples}""",
                ),
                ("user", f"Tópico de interesse: {topic}"),
            ]
        )
        gen_perspectives_chain = gen_perspectives_prompt | self.llm.with_structured_output(
            Perspectives
        )
        return gen_perspectives_chain
