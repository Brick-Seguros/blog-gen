from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

from typing import Annotated, Sequence, List, Optional
from type import Editor, handle_editor_name
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableLambda, chain as as_runnable
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
import json
from type import InterviewState, Queries, AnswerWithCitations
from langchain_core.prompts import ChatPromptTemplate

def tag_with_name(ai_message: AIMessage, name: str):
    """
        Tag an AIMessage with a name
    """

    ai_message.name = handle_editor_name(name)
    return ai_message


def swap_roles(state: InterviewState, name: str):
    """
        Swap the roles of the editor and the subject matter expert
    """

    converted = []
    for message in state["messages"]:
        if isinstance(message, AIMessage) and message.name !=handle_editor_name(name):
            message = HumanMessage(**message.dict(exclude={"type"}))
        converted.append(message)
    return {"messages": converted}


gen_question_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            Você é um escritor experiente de Blog e deseja editar uma página específica. \
            Além de sua identidade como escritor de Blog, você tem um foco específico ao pesquisar o tópico. \
Agora, você está conversando com um especialista para obter informações. Faça boas perguntas para obter informações mais úteis.

Quando você não tiver mais perguntas a fazer, diga "Muito obrigado pela sua ajuda!" para encerrar a conversa.\
Por favor, faça apenas uma pergunta de cada vez e não pergunte o que você já perguntou antes.\
Suas perguntas devem estar relacionadas ao tópico que você deseja escrever.
Seja abrangente e curioso, obtendo o máximo de informações exclusivas do especialista possível.\

Mantenha-se fiel à sua perspectiva específica:

{persona}""",
        ),
        MessagesPlaceholder(variable_name="messages", optional=True),
    ]
)

gen_queries_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Você é um assistente de pesquisa muito útil. Consulte o mecanismo de pesquisa para responder às perguntas do usuário.",
        ),
        MessagesPlaceholder(variable_name="messages", optional=True),
    ]
)

gen_answer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
                Você é um especialista que pode usar informações efetivamente. 
                Você está conversando com um escritor de Blog que deseja escrever uma página de Blog sobre o tópico que você conhece. 
                Você reuniu as informações relacionadas e agora usará as informações para formar uma resposta.

                Garanta que sua resposta seja informativa e que cada frase seja apoiada pelas informações coletadas.
                Cada resposta deve ser apoiada por uma citação de uma fonte confiável, formatada como uma nota de rodapé, reproduzindo as URLS após sua resposta.
            """,
        ),
        MessagesPlaceholder(variable_name="messages", optional=True),
    ]
)

class InterviewManager:
    def __init__(
            self, 
            llm, 
            search_engine,
            max_num_turns
        ):
        self.llm = llm
        self.search_engine = search_engine
        self.max_num_turns = max_num_turns

        self.build_graph()
    
    def generate_question(self, state: InterviewState):
        """
            Generate a question for the subject matter expert
        """

        print("Generating question")

        editor = state["editor"]

        gn_chain = (
            RunnableLambda(swap_roles).bind(name=handle_editor_name(editor.name))
            | gen_question_prompt.partial(persona=editor.persona)
            | self.llm
            | RunnableLambda(tag_with_name).bind(name=handle_editor_name(editor.name))
        )
        result = gn_chain.invoke(state)
        return result

    def generate_queries(self, swapped_state):
        """
            Generate queries for the search engine
        """

        gen_queries_chain = gen_queries_prompt | self.llm.with_structured_output(Queries, include_raw=True).with_config(run_name="GenerateQueries")
        result = gen_queries_chain.invoke(swapped_state)
        return result
    
    def generate_answer(self, state: InterviewState,
            config: Optional[RunnableConfig] = None,
            name: str = "Subject_Matter_Expert",
            max_str_len: int = 15000,
    ):
        """
            Generate an answer for the editor
        """
        
        swapped_state = swap_roles(state, name)  # Convert all other AI messages
        
        queries = self.generate_queries(swapped_state)

        query_results = self.search_engine.batch(
            queries["parsed"].queries, config, return_exceptions=True
        )

        successful_results = [
            res for res in query_results if not isinstance(res, Exception)
        ]

        all_query_results = {
            res["url"]: res["content"] for results in successful_results for res in results
        }

        # We could be more precise about handling max token length if we wanted to here
        dumped = json.dumps(all_query_results)[:max_str_len]

        ai_message: AIMessage = queries["raw"]

        tool_call = queries["raw"].additional_kwargs["tool_calls"][0]

        tool_id = tool_call["id"]

        tool_message = ToolMessage(tool_call_id=tool_id, content=dumped)

        swapped_state["messages"].extend([ai_message, tool_message])
        
        # Only update the shared state with the final answer to avoid
        # polluting the dialogue history with intermediate messages
        gen_answer_chain = gen_answer_prompt | self.llm.with_structured_output(
            AnswerWithCitations, include_raw=True
        ).with_config(run_name="GenerateAnswer")

        generated = gen_answer_chain.invoke(swapped_state)
        
        cited_urls = set(generated["parsed"].cited_urls)

        # Save the retrieved information to a the shared state for future reference
        cited_references = {k: v for k, v in all_query_results.items() if k in cited_urls}

        formatted_message = AIMessage(name=name, content=generated["parsed"].as_str)

        return [formatted_message, cited_references]

    def build_graph(self):
        """
            Build the graph for the interview manager
        """

        def route_messages(state: InterviewState, name: str = "Subject Matter Expert"):
            messages = state["messages"]
            num_responses = len(
                [m for m in messages if isinstance(m, AIMessage) and handle_editor_name(m.name) == handle_editor_name(name)]
            )
            if num_responses >= self.max_num_turns:
                return END
            last_question = messages[-1]
            if last_question.content.endswith("Muito obrigado pela sua ajuda!"):
                return END
            return "ask_question"


        def generate_question(state: InterviewState):
            res = self.generate_question(state)
            messages = state["messages"]
            messages.append(res)
            return {
                "messages": messages,
                "editor": state["editor"],
                "references": state["references"],
            }
        
        def gen_answer(state: InterviewState):
            res = self.generate_answer(state)
            print("Answer generated!")

            messages = state["messages"]
            references = state["references"]

            messages.append(res[0])

            if not references:
                references = {}

            references.update(res[1])

            return {
                "messages":  messages,
                "references": references,
                "editor": state["editor"],
            }
        
        builder = StateGraph(InterviewState)

        builder.add_node("ask_question", generate_question)
        builder.add_node("answer_question", gen_answer)
        builder.add_conditional_edges("answer_question", route_messages)
        builder.add_edge("ask_question", "answer_question")

        builder.set_entry_point("ask_question")
        interview_graph = builder.compile().with_config(run_name="Conduct Interviews", recursion_limit=40)

        self.interview_graph = interview_graph
        print("Interview Graph built")
        
    def run(self, initial_states: List[InterviewState]):
        """
            Run the interview manager
        """

        print("Starting interviews")
        return self.interview_graph.batch(initial_states)