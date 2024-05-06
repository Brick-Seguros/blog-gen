from type import ResearchState, Outline
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END


class ArticleWriterUseCase: 
    def __init__(
        self, 
        fast_llm, 
        long_context_llm,
        survey_use_case,
        outline_generator,
        interview_manager,
        outline_refiner,
        indexing_service,
        section_writer,
        verbose
    ):
        self.fast_llm = fast_llm
        self.long_context_llm = long_context_llm

        self.outline_generator = outline_generator
        self.interview_manager = interview_manager
        self.outline_refiner = outline_refiner
        self.indexing_service = indexing_service
        self.section_writer = section_writer
        self.survey_use_case = survey_use_case

        self.verbose = verbose

        self.build_graph()

    def writer(self, topic, draft):
        """
            This function writes the final article using the long context model and the draft provided
        """

        writer_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Você é um ótimo autor de Blog. Escreva um texto completo de Blog sobre {topic} usando os seguinte rascunho de seções:\n\n{draft}\n\nSiga estritamente as diretrizes de formato: Image - Data - Conteúdo - Referências.",
                ),
                (
                    "user",
                    "Escreva um artigo completo usando o formato markdown. Organize as citações usando notas de rodapé como '[1]'.",
                ),
            ]
        )

        writer = writer_prompt | self.long_context_llm | StrOutputParser()

        return writer.invoke({"topic": topic, "draft": draft})

    def build_graph(self):
        """
            This function builds the graph for the article writer use case
        """

        def initialize_research(state: ResearchState):
            topic = state["topic"]

            # if self.verbose:
            print(f"Initializing research for {topic}")
            
            generate_outline_direct = self.outline_generator.set_for_topic(topic)

            outline = generate_outline_direct.invoke({"topic": topic}),
            print("Outline generated")
            perspectives =  self.survey_use_case.survey_subjects(topic),
            print("Perspectives generated")

            return {
                **state,
                "outline": outline[0],
                "editors": perspectives[0].editors,
            }
        
        def conduct_interviews(state: ResearchState):
            topic = state["topic"]  
            initial_states = []
            for editor in state["editors"]:
                initial_states.append({
                    "editor": editor,
                    "messages": [
                        AIMessage(
                            content=f"Você disse que estava escrevendo um texto de Blog sobre {topic}?",
                            name="subject_matter_rxpert",
                        )
                    ],
                })

            # if self.verbose:
            print(f"Conducting interviews for {topic}")
            # We call in to the sub-graph here to parallelize the interviews
            interview_results = self.interview_manager.run(initial_states)
            print(f"Finished the interviews")

            return {
                **state,
                "interview_results": interview_results,
            }
                

        def format_conversation(interview_state):
            messages = interview_state["messages"]
            convo = "\n".join(f"{m.name}: {m.content}" for m in messages)
            return f'Conversa com {interview_state["editor"].name}\n\n' + convo


        def refine_outline(state: ResearchState):
            convos = "\n\n".join(
                [
                    format_conversation(interview_state)
                    for interview_state in state["interview_results"]
                ]
            )

            # if self.verbose:
            print(f"Refining outline for {state['topic']}")

            refine_outline_chain = self.outline_refiner.setup(
                state["topic"], state["outline"], convos
            )

            updated_outline = refine_outline_chain.invoke(
                {
                    "topic": state["topic"],
                    "old_outline": state["outline"].as_str,
                    "conversations": convos,
                }
            )
            
            return {**state, "outline": updated_outline}


        def write_sections(state: ResearchState):
            outline = state["outline"]

            # if self.verbose:
            print(f"Indexing sections for {state['topic']}")

            retriver = self.indexing_service.execute(state["interview_results"])

            # if self.verbose:
            print(f"Writing sections for {state['topic']}")
            
            section_writer = self.section_writer.setup(retriver)

            sections = section_writer.batch(
                [
                    {
                        "outline": outline.as_str,
                        "section": section.section_title,
                        "topic": state["topic"],
                    }
                    for section in outline.sections
                ]
            )
            return {
                **state,
                "sections": sections,
            }
        

        def write_article(state: ResearchState):
            topic = state["topic"]
            sections = state["sections"]
            draft = "\n\n".join([section.as_str for section in sections])

            # if self.verbose:
            print(f"Writing article for {topic}")

            article = self.writer(topic, draft)
            return {
                **state,
                "article": article,
            }


        graph = StateGraph(ResearchState)

        nodes = [
            ("init_research", initialize_research),
            ("conduct_interviews", conduct_interviews),
            ("refine_outline", refine_outline),
            ("write_sections", write_sections),
            ("write_article", write_article),
        ]
        for i in range(len(nodes)):
            name, node = nodes[i]
            graph.add_node(name, node)
            if i > 0:
                graph.add_edge(nodes[i - 1][0], name)

        graph.set_entry_point("init_research")
        graph.set_finish_point(nodes[-1][0])
        runnable = graph.compile()

        self.runnable = runnable

        print("Writer Graph built")
        return 

    def run(self, topic) -> ResearchState:
        """
            This function runs the article writer use case for a given topic
        """

        print(f"Running writer for {topic}")
        try:
            res = self.runnable.invoke(
                {
                    "topic": topic,
                    "outline": Outline(page_title="", sections=[]),
                    "editors": [],
                    "interview_results": [],
                    "sections": [],
                    "article": "",
                }
            )
            print(f"Finished writer for {topic}")
            return res
        except Exception as e:
            print(e)
            raise e









