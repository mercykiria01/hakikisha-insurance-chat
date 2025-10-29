from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from google.colab import userdata # Import userdata

# --- Global Variables for RAG components ---
retriever = None
llm = None

def initialize_rag():
    """Initializes the RAG system by loading, splitting, and embedding the website content."""
    global retriever, llm

    # NOTE: Ensure the OPENAI_API_KEY environment variable is set before running.
    # Set the OpenAI API key from Colab user data secrets
    os.environ["OPENAI_API_KEY"] = userdata.get('OPENAI_API_KEY')


    if not os.environ.get('OPENAI_API_KEY'):
        print("CRITICAL ERROR: OPENAI_API_KEY environment variable is not set.")
        # Attempt to proceed with initialization, but API calls will fail without a key
    else:
        print("OPENAI_API_KEY found. Initializing RAG system...")

    # Load and process website content
    url = "https://hakikisha-insurance-chat.onrender.com"
    print(f"Loading content from: {url}")
    loader = WebBaseLoader(url)
    documents = loader.load()

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = text_splitter.split_documents(documents)
    print(f"Content loaded and split into {len(docs)} chunks.")

    # Create vector store
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    # Store the retriever globally
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # Create LLM (Stored globally)
    llm = ChatOpenAI(model_name="gpt-4")
    print("RAG System successfully initialized!")

def get_rag_answer(question):
    """Executes the RAG logic to find and summarize an answer."""
    if not retriever or not llm:
        return "RAG system not initialized. Check server logs."

    # Get relevant documents
    relevant_docs = retriever.invoke(question)

    # Build context
    context = "\n\n".join([doc.page_content for doc in relevant_docs])

    # Improved prompt for final answer generation
    prompt = f"""You are a helpful insurance assistant for Hakikisha Insurance.
Answer the question based ONLY on the context provided. If the context contains relevant information,
use it to give a detailed, helpful answer. If the context does not contain the answer, state that you cannot find the information in the provided context.

The website URL is: https://hakikisha-insurance-chat.onrender.com

Context:
{context}

Question: {question}

Provide a comprehensive answer about the insurance topic, using information from the context.
Answer:"""

    # Get answer
    response = llm.invoke(prompt)
    return response.content

# --- Flask Application Setup ---
app = Flask(__name__)
# Enable CORS for cross-origin requests from your Node.js/React frontend
CORS(app)

@app.route('/ask-faq', methods=['POST'])
def ask_faq_endpoint():
    """
    API endpoint to receive a question and return a RAG-generated answer.
    Expected JSON body: {"question": "What is motor insurance?"}
    """
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({"error": "Missing 'question' in request body"}), 400

        query = data['question']
        print(f"Received FAQ query: {query}")

        answer = get_rag_answer(query)

        return jsonify({
            "question": query,
            "answer": answer
        })

    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({"error": "An internal server error occurred during processing."}), 500

if __name__ == '__main__':
    # Initialize RAG components once when the server starts
    initialize_rag()
    # Run the Flask app on a specified port (e.g., 5000)
    # NOTE: You will need to start this server and expose it publicly (e.g., using Heroku, Vercel, or a VM)
    # for your Dialogflow Webhook to reach it.
    app.run(host='0.0.0.0', port=5000, debug=True)