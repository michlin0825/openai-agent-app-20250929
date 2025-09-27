#!/usr/bin/env python3
"""
Document Ingestion Script for ChromaDB
Usage: python ingest_documents.py <pdf_path>
"""
import sys
import os
from pdf_processor import load_pdf_to_chroma

def main():
    if len(sys.argv) != 2:
        print("Usage: python ingest_documents.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} not found")
        sys.exit(1)
    
    print(f"Ingesting document: {pdf_path}")
    chunks = load_pdf_to_chroma(pdf_path)
    print(f"Successfully ingested {len(chunks)} chunks into ChromaDB")

if __name__ == "__main__":
    main()
