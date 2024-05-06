from langchain_core.runnables import RunnableLambda, chain as as_runnable

class SurveySubjectsUseCase:
    def __init__(self, related_topics_chain, knowledge_base, gen_perspectives_chain):
        self.related_topics_chain = related_topics_chain
        self.knowledge_base = knowledge_base
        self.gen_perspectives_chain = gen_perspectives_chain

    def format_doc(self, doc):
        text = ''
        for d in doc:
            if isinstance(d[1], str):
                text += d[1]
        return text

    def format_docs(self, docs):
        return "\n\n".join(self.format_doc(doc) for doc in docs)

    def survey_subjects(self, topic: str):
        """
            This function surveys the subjects for a given topic
        """
        
        related_topics_chain = self.related_topics_chain.set_for_topic()

        related_subjects = related_topics_chain.invoke({"topic": topic})

        retrieved_docs = self.knowledge_base.batch(
            related_subjects.topics, return_exceptions=True
        )
        
        all_docs = []
        for docs in retrieved_docs:
            if isinstance(docs, BaseException):
                continue
            all_docs.extend(docs)
        formatted = self.format_docs(all_docs)
        gen_perspectives_chain = self.gen_perspectives_chain.set_for_topic(topic, formatted[:3])
        
        return gen_perspectives_chain.invoke({"examples": formatted, "topic": topic})