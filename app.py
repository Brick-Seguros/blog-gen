import os
import uuid
from dotenv import load_dotenv

from flask import Flask, jsonify, request

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.tools import tool

from middleware import auth_middleware
from usecase_article_writer import ArticleWriterUseCase
from usecase_interview import InterviewManager
from usecase_outline_generation import GenerateOutlineUseCase
from usecase_section_writer import SectionWriterUseCase
from usecase_perspectives_generation import GeneratePerspectivesUseCase
from usecase_references_indexing import ReferencesIndexingUseCase
from usecase_refine_outline import RefineOutlineUseCase
from usecase_related_topics_generation import GenerateRelatedTopicsUseCase
from usecase_survey_subjects import SurveySubjectsUseCase

from blog_publisher import BlogPublisher
# from repository import QuestionRepository, ChatRepository


# Loading environment variables -----------------------------------
load_dotenv()

app = Flask(__name__)

api_key = os.environ.get('API_KEY')
openai_key = os.environ.get('OPENAI_API_KEY')

aws_access_key_id = os.environ.get('S3_ACCESS_KEY')
aws_secret_access_key = os.environ.get('S3_SECRET_KEY')
aws_region = os.environ.get('S3_REGION')
bucket = os.environ.get('S3_BUCKET')
# ------------------------------------------------------------------


# Setting up the Knowledge Base ------------------------------------
print("Loading File ./assets/blog_texts.txt")
blog_texts = ""
with open("./assets/blog_texts.txt") as f:
    for line in f:
        blog_texts += line

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300, 
    chunk_overlap=50, 
    separators=["##########"],
)

print("Creating documents")
documents = text_splitter.create_documents([blog_texts])

embeddings = OpenAIEmbeddings(
    api_key=openai_key,
)

print("Embedding documents")
db = Chroma.from_documents(documents, embeddings)

knowledge_base = db.as_retriever(k=2)
# ------------------------------------------------------------------


# Setting up the Third Party Providers -----------------------------
print("Connecting to Chroma")
chroma = Chroma('references-indexing-store', embeddings)

print("Connecting to FAST LLM")
fast_llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0,
    verbose=True,
    api_key=openai_key
  )

print("Connecting to Long Content LLM")
long_context_llm =  ChatOpenAI(
    model="gpt-4-turbo-2024-04-09",
    temperature=0,
    verbose=True,
    api_key=openai_key
  )

print("Creating the search engine")
search_engine = DuckDuckGoSearchAPIWrapper()

@tool
def search_engine(query: str):
    """Search engine to the internet."""
    results = DuckDuckGoSearchAPIWrapper()._ddgs_text(query)
    return [{"content": r["body"], "url": r["href"]} for r in results]
# ------------------------------------------------------------------


# print("Building repositories")
# question_repository = QuestionRepository()
# chat_repository = ChatRepository()


# Initialize internal implementations ------------------------------
print("Building Blog Publisher")
blog_publisher = BlogPublisher(
    bucket=bucket,
    key=aws_access_key_id,
    secret=aws_secret_access_key,
    region=aws_region
)

print("Building Outline Generator")
outline_generator = GenerateOutlineUseCase(fast_llm)
print("Building Related Topics Generator")
related_topics = GenerateRelatedTopicsUseCase(fast_llm)
print("Building Perspectives Generator")
generate_perspectives = GeneratePerspectivesUseCase(fast_llm)

print("Building Survey Use Case")
survey_use_case = SurveySubjectsUseCase(related_topics, knowledge_base, generate_perspectives)

print("Building Interview Manager")
interview_manager = InterviewManager(fast_llm, search_engine, 2)

print("Building Outline Refiner")
outline_refiner = RefineOutlineUseCase(long_context_llm)

print("Building Indexing Service")
indexing_service = ReferencesIndexingUseCase(chroma)

print("Building Section Writer")
section_writer = SectionWriterUseCase(long_context_llm)
 
print("Building Article Writer")
article_writer = ArticleWriterUseCase(
    fast_llm,
    long_context_llm,
    survey_use_case,
    outline_generator,
    interview_manager,
    outline_refiner,
    indexing_service,
    section_writer,
    verbose=True
)
# ------------------------------------------------------------------


print("Building Routes")

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Welcome to the API'}), 200

@app.route('/article', methods=['POST'])
def generate_article():
    # Authenticate the request
    auth_result = auth_middleware(request)
    if not auth_result['shoudl_continue']:
        return jsonify({'error': auth_result['message']}), auth_result['status']

    # Get article topic and draft from request body
    data = request.get_json()
    prompt = data.get('prompt')

    # Ensure prompt and draft are provided
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    max_tries = 3
    should_continue = True

    while should_continue:
        try:
            # Generate article
            result = article_writer.run(prompt)
            should_continue = False
        except Exception as e:
            max_tries -= 1
            if max_tries == 0:
                should_continue = False
                return jsonify({'error': str(e)}), 500
     
    print("Article generated")
    
    article = result.get('article')

    uuid_key = str(uuid.uuid4())

    random_title = "article-" + uuid_key+".md"
    
    url = blog_publisher.publish(random_title, article)
    
    return {'article': article, 'url': url }


if __name__ == '__main__':
    app.run(debug=True, port=4300)