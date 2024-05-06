from langchain_core.prompts import ChatPromptTemplate
from type import RelatedSubjects
class GenerateRelatedTopicsUseCase:
    def __init__(self, llm):
        self.llm = llm

    def set_for_topic(self):
        """
            This function generates related topics for a blog post on a given topic
        """

        gen_related_topics_prompt = ChatPromptTemplate.from_template(
            """
            Estou escrevendo uma página de Blog para o assunto abaixo. 
            Por favor identifique e recomende algumas Páginas de Blog sobre assuntos relacionados.
            Estou procurando exemplos que forneçam insights sobre aspectos interessantes comumente associados a este tópico, ou exemplos que me ajudem a entender o conteúdo e a estrutura típicos incluídos nas páginas de Blog para tópicos semelhantes. 
            Por favor liste o máximo de assuntos e urls que você puder.

            Tópico de interesse: {topic}
            """
        )
        chain = gen_related_topics_prompt | self.llm.with_structured_output(
            RelatedSubjects
        )
        return chain