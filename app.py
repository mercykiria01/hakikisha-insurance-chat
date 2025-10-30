from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
# from langchain.vectorstores import Chroma
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import openai
# --- Global Variables for RAG components ---
retriever = None
llm = None
RAG_READY = False  # <-- added readiness flag


def initialize_rag():
    """Initializes the RAG system by loading, splitting, and embedding the website content."""
    global retriever, llm, RAG_READY

    load_dotenv()

    # Get the OpenAI API key from environment variables (Render uses this)
    openai_api_key = os.getenv("OPENAI_API_KEY")

    print(openai_api_key)

    if not openai_api_key:
        print("❌ CRITICAL ERROR: OPENAI_API_KEY environment variable is not set.")
        RAG_READY = False
        return
    else:
        os.environ["OPENAI_API_KEY"] = openai_api_key
        print("✅ OPENAI_API_KEY found. Initializing RAG system...")

    try:
        # Load and process website content
        url = "https://hakikisha-insurance-chat.onrender.com"
        print(f"🌐 Loading content from: {url}")
        loader = WebBaseLoader(url)
        documents = loader.load()

        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        docs = text_splitter.split_documents(documents)
        print(f"📄 Content loaded and split into {len(docs)} chunks.")
     

        # Create vector store
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(docs, embeddings)

        # Store the retriever globally
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

        # Create LLM (Stored globally)
        llm = ChatOpenAI(model_name="gpt-4")
        RAG_READY = True  # <-- set ready only after full init
        print("✅ RAG System successfully initialized!")

    except Exception as e:
        RAG_READY = False
        print(f"⚠️ Error initializing RAG system: {e}")


def get_rag_answer(question):
    """Executes the RAG logic to find and summarize an answer."""
    if not RAG_READY:
        return "RAG system is still initializing. Please try again in a moment."

    if not retriever or not llm:
        return "RAG system not initialized. Please try again later."

    try:
        # Get relevant documents (use appropriate retriever method)
        relevant_docs = retriever.invoke(question)

        print(relevant_docs)

        # Build context
        context = "\n\n".join([doc.page_content for doc in relevant_docs])

        print('tuko hapa')

        print(context)

    #     messages = [{"role": "system", "content": get_patient_prompt()}]
    # for m in messages_data:
    #     messages.append({"role": m["role"], "content": m["content"]})

    # # GPT response
    # response = client.chat.completions.create(
    #     model="gpt-4",
    #     messages=messages
    # )

    #     prompt = f"""You are a helpful insurance assistant for Hakikisha Insurance.
    # Answer the question based ONLY on the context provided...
    # Context:
    # {context}

    # Question: {question}
    # Answer:"""

        # Use llm.generate and extract text (adjust if your LangChain version differs)
        # response = llm.generate([prompt])

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are a helpful insurance assistant for Hakikisha Insurance. Answer the question based ONLY on the context provided..."}, {"role": "user", "content": context}]
        )

        print(response)
        answer_text = response.choices[0].message.content
        return answer_text or "No answer generated."

    except Exception as e:
        print(f"⚠️ Error during RAG answer generation: {e}")
        return (
            "An error occurred while processing your question. Please try again later."
        )


# --- Flask Application Setup ---
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access


# serve frontend pages
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("index.html")


@app.route("/ask-faq", methods=["POST"])
def ask_faq_endpoint():
    """API endpoint to receive a question and return a RAG-generated answer."""
    try:
        data = request.get_json()
        if not data or "question" not in data:
            return jsonify({"error": "Missing 'question' in request body"}), 400

        query = data["question"]
        print(f"🗨️ Received FAQ query: {query}")

        answer = get_rag_answer(query)

        return jsonify({"question": query, "answer": answer})

    except Exception as e:
        print(f"🔥 API Error: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


if __name__ == "__main__":
    print("🚀 Starting Flask server...")
    # initialize_rag()  # avoid blocking; start in background
    from threading import Thread

    Thread(target=initialize_rag, daemon=True).start()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
