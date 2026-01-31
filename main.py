import os
import uuid
import psycopg
from fastapi import FastAPI, UploadFile, File, HTTPException
from dotenv import load_dotenv

# LangChain & AI Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings # Used for local and fast embeddings
from langchain_postgres import PGVector, PostgresChatMessageHistory
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()

app = FastAPI(title="AI Residency RAG Chatbot")

# Database and Local Embeddings Setup
DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://myuser:mypassword@localhost:5432/mydatabase")

# Local embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="residency_docs",
    connection=DB_URL,
    use_jsonb=True,
)

# Enpoint 1 - Upload PDF
@app.post("/upload")
async def upload_document(session_id: str, file: UploadFile = File(...)):
    """Uploads a PDF and indexes it. Data is segregated by session_id."""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    temp_path = f"temp_{uuid.uuid4()}.pdf"
    try:
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        
        loader = PyPDFLoader(temp_path)
        docs = loader.load()
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        splits = text_splitter.split_documents(docs)
        
        # Tag each chunk for session segregation
        for split in splits:
            split.metadata["session_id"] = session_id
        
        # Add to pgvector 
        vector_store.add_documents(splits)
        
        return {"status": "Success", "message": f"Document '{file.filename}' indexed for session '{session_id}'."}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# -Endpoint 2 - Chat
@app.post("/chat")
async def chat_with_bot(session_id: str, query: str):
    """Chat with RAG and Conversation History stored in Postgres."""
    try:
        # 1. Establishing the connection 
        sync_conn = psycopg.connect(DB_URL.replace("+psycopg", ""))

        try:
            PostgresChatMessageHistory.create_tables(sync_conn, "chat_history")
        except Exception:
            pass 

        # UUID validation
        try:
            valid_uuid = str(uuid.UUID(session_id))
        except ValueError:
            valid_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, session_id))

        # 4. Initialize history 
        history = PostgresChatMessageHistory(
            "chat_history", 
            valid_uuid, 
            sync_connection=sync_conn
        )
        # Gemini for high-quality reasoning
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
        
        # Filter search to ONLY the current session's documents
        retriever = vector_store.as_retriever(
            search_kwargs={'filter': {'session_id': session_id}}
        )

        # Contextualization logic
        context_q_prompt = ChatPromptTemplate.from_messages([
            ("system", "Rephrase the user question to be a standalone question based on chat history."),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        history_aware_retriever = create_history_aware_retriever(llm, retriever, context_q_prompt)

        # Answer logic
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", "Answer the question using only the provided context: \n\n{context}"),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])

        qa_chain = create_stuff_documents_chain(llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, qa_chain)

        # Connect to Postgres History
        sync_conn = psycopg.connect(DB_URL.replace("+psycopg", ""))
        history = PostgresChatMessageHistory(
            "chat_history", 
            session_id, 
            sync_connection=sync_conn
        )

        # Execute Chain
        result = rag_chain.invoke({"input": query, "chat_history": history.messages})
        
        # Save History
        history.add_user_message(query)
        history.add_ai_message(result["answer"])

        return {"answer": result["answer"]}

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))
