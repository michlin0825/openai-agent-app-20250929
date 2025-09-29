import PyPDF2
import chromadb
import os
from dotenv import load_dotenv

load_dotenv()

def extract_pdf_text(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def setup_chromadb():
    # Ensure directory exists
    db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    os.makedirs(db_path, exist_ok=True)
    
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection(os.getenv("CHROMA_COLLECTION_NAME", "documents"))
    return collection

def load_pdf_to_chroma(pdf_path):
    """Load PDF content into ChromaDB - only call when adding new documents"""
    text = extract_pdf_text(pdf_path)
    collection = setup_chromadb()
    
    # Split text into chunks
    chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
    
    collection.add(
        documents=chunks,
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        metadatas=[{"source": pdf_path} for _ in chunks]
    )
    return chunks

def query_chroma(query, n_results=None):
    """Query ChromaDB for relevant documents"""
    if n_results is None:
        n_results = int(os.getenv("MAX_SEARCH_RESULTS", "3"))
    try:
        collection = setup_chromadb()
        results = collection.query(query_texts=[query], n_results=n_results)
        return results['documents'][0] if results['documents'] else []
    except Exception as e:
        print(f"ChromaDB query error: {e}")
        return []
