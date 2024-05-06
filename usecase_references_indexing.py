from langchain_core.documents import Document

class ReferencesIndexingUseCase:
    def __init__(self, chroma):
        self.vs = chroma
        return 
    
    def execute(self, data):
        """
            This function indexes the references for a given article
        """

        all_docs = []
        for interview_state in data:
            reference_docs = []
            for k, v in interview_state["references"].items():
                reference_docs.append(Document(page_content=v, metadata={"source": k}))
            all_docs.extend(reference_docs)
        self.vs.add_documents(all_docs)

        return self.vs.as_retriever(k=10)