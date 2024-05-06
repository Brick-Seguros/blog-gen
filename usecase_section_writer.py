
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from type import BlogSection


class SectionWriterUseCase:
    """
        Use case for writing a section of a blog post.
        Use long context LLMs to write a section of a blog post.
    """

    def __init__(self, llm):
        self.llm = llm

   
    def setup(self, retriever) -> BlogSection:
        """
            This function writes a section of a blog post
        """

        section_writer_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Você é um ótimo escritor de Blog. Complete o texto do seu Blog a partir do seguinte esboço:\n\n{outline}\n\nCite suas fontes, usando as seguintes referências:\n\n<Documentos>\n{docs}\n<Documentos>",
                ),
                ("user", "Escreva o texto completo para a seção {section}."),
            ]
        )

        def retrieve(inputs: dict):
            docs = retriever.invoke(inputs["topic"] + ": " + inputs["section"])

            formatted = "\n".join(
                [
                    f'<Document"/>\n{doc.page_content}\n</Document>'
                    for doc in docs
                ]
            )
            return {"docs": formatted, **inputs}

        section_writer = (
            retrieve
            | section_writer_prompt
            | self.llm.with_structured_output(BlogSection)
        )

        return section_writer
