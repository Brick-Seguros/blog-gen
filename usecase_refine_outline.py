
from type import Outline
from langchain_core.prompts import ChatPromptTemplate


class RefineOutlineUseCase:
    """
        Use case for refining the outline of a blog post.
        Use long context LLMs to refine the outline of a blog post.
    """

    def __init__(self, llm):
        self.llm = llm

    def setup(self, topic: str, old_outline, conversations: str):
        """
            This function refines the outline of a blog post on a given topic
        """
        
        refine_outline_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    Você é um escritor de Blog. Você reuniu informações de especialistas e mecanismos de busca. Agora, você está refinando a estrutura da página do Blog. \
                    Você precisa garantir que o esboço seja  específico. \
                    Tópico que você está escrevendo: {topic}
                    Aqui está o esboço inicial que você escreveu:

                    {old_outline}
                """,
                ),
                (
                    "user",
                    "Refine a estrutura com base em suas conversas com especialistas no assunto:\n\nConversas:\n\n{conversations}\n\nEscreva o esboço refinado da página de Blog:",
                ),
            ]
        )

        # Using turbo preview since the context can get quite long
        refine_outline_chain = refine_outline_prompt | self.llm.with_structured_output(
            Outline
        )

        return refine_outline_chain