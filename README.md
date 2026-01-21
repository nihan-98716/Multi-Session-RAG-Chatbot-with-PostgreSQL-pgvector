# Multi-Session RAG Chatbot with PostgreSQL & pgvector

A production-ready Retrieval-Augmented Generation (RAG) API built with **FastAPI**, **LangChain**, and **PostgreSQL**. This system allows users to upload PDF documents, index them into a vector database, and engage in context-aware conversations where the AI "remembers" both the uploaded document details and the chat history.

## 🚀 Key Technical Features

### 1. Hybrid Embedding Architecture

To ensure 100% reliability and bypass common cloud rate limits (like OpenAI/Gemini 429 errors), this project utilizes a **Hybrid AI approach**:

* **Local Embeddings**: Document indexing is performed using `sentence-transformers/all-MiniLM-L6-v2` locally. This ensures document processing is instant, free, and works without an internet-dependent quota.
* **Cloud LLM**: Generative responses are powered by **Google Gemini 2.5 Flash**, providing high-speed, state-of-the-art reasoning for chat.

### 2. Multi-Session Data Segregation

Architected specifically for multi-user environments, the system implements **Metadata Filtering**. Even though all data resides in one PostgreSQL table, documents and chat histories are strictly segregated by `session_id`. Users cannot "leak" information into another user's session.

### 3. Persistent Conversation Memory

Unlike basic RAG setups, this chatbot maintains a **Persistent Chat History** in PostgreSQL.

* **History-Aware Retrieval**: The system re-phrases user queries based on previous context before searching the vector store (e.g., if a user asks "Who is the author?" and follows with "Where is he from?", the system understands "he" refers to the author).
* **Postgres Storage**: All messages are stored in a `chat_history` table, allowing sessions to be resumed even after a server restart.

### 4. Vectorized Knowledge Base

Utilizes **PostgreSQL with the `pgvector` extension** as the primary vector store. This allows for high-performance similarity searches directly alongside relational data.

---

## 🛠️ Tech Stack

* **Backend**: FastAPI (Python 3.12+)
* **Orchestration**: LangChain (Modular v1.0 / `langchain-classic`)
* **Database**: PostgreSQL + `pgvector`
* **LLM**: Google Gemini 2.5 Flash
* **Embeddings**: HuggingFace (Local)

---

## 📖 Detailed Setup Guide

Follow these steps exactly to run the application on your local machine.

### Prerequisites

* **Python 3.12** installed.
* **Docker Desktop** (to run the database).
* **Google Gemini API Key** (Get one for free at [Google AI Studio](https://aistudio.google.com/)).

### Step 1: Clone and Environment Setup

1. Navigate to your project folder:
```bash
cd my-chatbot

```


2. Create a Virtual Environment:
```bash
python -m venv chatbot_env

```


3. Activate the Environment:
* **Windows**: `chatbot_env\Scripts\activate`
* **Mac/Linux**: `source chatbot_env/bin/activate`



### Step 2: Install Dependencies

Run the following command to install all required libraries:

```bash
pip install fastapi uvicorn langchain langchain-classic langchain-community langchain-google-genai langchain-postgres psycopg[binary] pypdf sentence-transformers python-dotenv

```

### Step 3: Start the Database

Ensure Docker is running, then start the pre-configured PostgreSQL container:

```bash
docker-compose up -d

```

*Verification*: Open Docker Desktop; you should see a container named `pgvector` running on port `5432`.

### Step 4: Configure Environment Variables

Create a file named `.env` in the root directory and add your keys:

```text
GOOGLE_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql+psycopg://myuser:mypassword@localhost:5432/mydatabase

```

### Step 5: Run the Application

Launch the FastAPI server with auto-reload:

```bash
python -m uvicorn main:app --reload

```

---

## 🧪 How to Use

1. **Access the Interface**: Open your browser to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
2. **Upload a Document**:
* Open `POST /upload`.
* Set `session_id` to a unique ID (e.g., `f47ac10b-58cc-4372-a567-0e02b2c3d479`).
* Choose a PDF and click **Execute**.


3. **Chat with the PDF**:
* Open `POST /chat`.
* Use the **same** `session_id` (`f47ac10b-58cc-4372-a567-0e02b2c3d479`).
* Ask a question like "What are the main points of this document?".


4. **Test Memory**:
* Ask a follow-up: "Can you summarize that in 3 bullet points?". The bot will remember the previous answer.



--

**Would you like me to generate a `requirements.txt` file content to match this README perfectly?**
