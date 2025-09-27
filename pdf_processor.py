import PyPDF2
import chromadb
import os

def extract_pdf_text(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

def setup_chromadb():
    # Ensure directory exists
    db_path = "./chroma_db"
    os.makedirs(db_path, exist_ok=True)
    
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_or_create_collection("documents")
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

def query_chroma(query, n_results=3):
    """Query ChromaDB for relevant documents"""
    try:
        collection = setup_chromadb()
        results = collection.query(query_texts=[query], n_results=n_results)
        return results['documents'][0] if results['documents'] else []
    except Exception as e:
        print(f"ChromaDB query error: {e}")
        return []

# Legacy function for backward compatibility
def insert_pdf_to_chroma(pdf_path):
    return len(load_pdf_to_chroma(pdf_path))
