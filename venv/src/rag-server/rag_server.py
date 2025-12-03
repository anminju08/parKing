import os  # 파일 경로 구성, 디렉토리 탐색 등 운영체제 관련 기능을 사용할 수 있는 표준 모듈
from dotenv import load_dotenv  # .env 파일에서 환경 변수를 로드하는 모듈

# 상위 폴더의 .env 파일 로드
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import logging  # 프로그램 실행 중의 정보, 경고, 오류 등을 콘솔 또는 로그 파일에 출력하기 위한 모듈
from mcp.server.fastmcp import FastMCP  # MCP 프로토콜 서버를 간편하게 생성하고 도구를 등록할 수 있는 클래스

from langchain_community.vectorstores import Chroma  # 문서 임베딩을 저장하고, 벡터 기반으로 검색할 수 있는 Chroma 벡터 저장소 모듈
from langchain_community.document_loaders import PyPDFLoader  # PDF 파일을 LangChain의 문서 객체로 로딩하는 데 사용하는 도구
from langchain_text_splitters import RecursiveCharacterTextSplitter  # 긴 문서를 일정 길이로 나누는 데 사용하는 텍스트 분할 도구
from langchain_classic.chains import RetrievalQA  # 검색 기반 질문응답 시스템(RAG)을 구성하기 위한 LangChain 체인 구성 클래스
from langchain_google_genai import ChatGoogleGenerativeAI  # Google Gemini 언어 모델을 LangChain에서 사용할 수 있게 해주는 래퍼
from langchain_huggingface import HuggingFaceEmbeddings  # HuggingFace 임베딩 모델 (무료, 로컬 실행)

# 로그 출력 수준 설정 (INFO 이상의 로그만 출력됨)
logging.basicConfig(level=logging.INFO)

# MCP 서버 인스턴스 생성 (이름은 "PDF-RAG"으로 설정되며, 로깅 또는 디버깅에 사용됨)
mcp = FastMCP("PDF-RAG")

# 분석할 PDF 파일의 경로를 지정 (이 파일의 내용을 Gemini가 이해할 수 있도록 처리함)
PDF_PATH = os.path.join(os.path.dirname(__file__), "스마트팜.pdf")  # 현재 스크립트와 같은 디렉토리에 있는 PDF 파일을 사용

# PDF 파일을 로드하고, 페이지 단위로 문서 객체(pages)로 변환
loader = PyPDFLoader(PDF_PATH)
pages = loader.load()  # 각 페이지는 LangChain의 Document 객체로 구성됨

# 페이지 단위 문서를 500자 단위로 잘라서 RAG에 더 적합하게 구성
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)  # 50자씩 겹치게 분할하여 문맥 보존
docs = splitter.split_documents(pages)  # 분할된 문서 리스트 생성

# HuggingFace 임베딩 모델을 초기화 (문서 텍스트를 벡터로 변환하는 데 사용됨, 무료 로컬 실행)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Google Gemini 언어 모델을 초기화 (최종 응답을 생성하는 데 사용됨)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro", google_api_key=os.getenv("GEMINI_API_KEY"))

# 분할된 문서를 벡터로 임베딩하여 Chroma 벡터 저장소에 저장 (기본적으로 메모리 내 저장)
vectorstore = Chroma.from_documents(docs, embeddings)

# 검색 기반 질문응답 체인(RAG)을 생성tlf


qa_chain = RetrievalQA.from_chain_type(
    llm=llm,  # Gemini 2.5 Pro 모델을 사용하여 답변 생성
    retriever=vectorstore.as_retriever()  # Chroma 저장소에서 관련 문서를 검색하는 리트리버 사용
)

# ask_pdf 함수를 MCP 도구로 등록하여 외부 클라이언트(예: Cursor, Claude)가 호출 가능하게 만듦
@mcp.tool()
def ask_pdf(query: str) -> str:
    """PDF 내용을 기반으로 질문에 답변합니다."""
    logging.info(f"Received query: {query}")  # 사용자가 입력한 질문을 로그로 출력
    return qa_chain.run(query)  # RAG 체인을 실행하여 질문에 대한 답변을 생성하고 반환

# MCP 서버 실행 (표준 입출력 방식으로 실행되며, 다른 프로그램에서 subprocess로 연결할 수 있음)
if __name__ == "__main__":
    mcp.run(transport="stdio")