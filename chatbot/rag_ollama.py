#!/usr/bin/env python3
"""
RAG (Retrieval Augmented Generation) with Ollama and Gemma2
Processes documents and enables context-aware conversations
"""

import os
import requests
import json
import PyPDF2
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import argparse

class RAGWithOllama:
    def __init__(self, model_name="gemma2", ollama_url="http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        dirname = os.path.dirname(__file__)
        self.chroma_client = chromadb.PersistentClient(path=os.path.join(dirname, 'database'))
        self.collection = self.chroma_client.get_or_create_collection(name="documents")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to end at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                boundary = max(last_period, last_newline)
                if boundary > start + chunk_size // 2:
                    chunk = text[start:start + boundary + 1]
                    end = start + boundary + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
            
        return [chunk for chunk in chunks if len(chunk.strip()) > 50]
    
    def add_document(self, file_path: str, doc_name: str = None):
        """Add a document to the vector database"""
        if doc_name is None:
            doc_name = os.path.basename(file_path)
        
        print(f"Processing document: {doc_name}")
        
        # Extract text
        if file_path.lower().endswith('.pdf'):
            text = self.extract_text_from_pdf(file_path)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        
        # Create chunks
        chunks = self.chunk_text(text)
        print(f"Created {len(chunks)} chunks")
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks)
        
        # Add to ChromaDB
        chunk_ids = [f"{doc_name}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": doc_name, "chunk_id": i} for i in range(len(chunks))]
        
        self.collection.add(
            documents=chunks,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            ids=chunk_ids
        )
        print(f"Added {len(chunks)} chunks to vector database")
    
    def retrieve_relevant_chunks(self, query: str, n_results: int = 3) -> List[str]:
        """Retrieve relevant document chunks for a query"""
        query_embedding = self.embedding_model.encode([query])
        
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results
        )
        
        return results['documents'][0] if results['documents'] else []
    
    def call_ollama(self, prompt: str, stream: bool = True) -> str:
        """Call Ollama API with the prompt"""
        # First check if Ollama is running
        try:
            health_response = requests.get(f"{self.ollama_url}")
            if health_response.status_code != 200:
                return "Error: Ollama is not running. Please start it with 'ollama serve'"
        except requests.exceptions.ConnectionError:
            return "Error: Cannot connect to Ollama. Please start it with 'ollama serve'"
        
        print(f"calling ollama with prompt length: {len(prompt)}")
        
        url = f"{self.ollama_url}/api/generate"
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": stream,
            "keepalive": -1
        }
        
        try:
            response = requests.post(url, json=data, stream=True)
            response.raise_for_status()
            
            if not stream:
                return response.json()['response']
            
            # Handle streaming response
            full_response = ""
            for line in response.iter_lines():
                if line:
                    json_response = json.loads(line)
                    chunk = json_response.get('response', '')
                    print(chunk, end='', flush=True)
                    full_response += chunk
                    if json_response.get('done', False):
                        break
            print()  # New line after response is complete
            return full_response
            
        except requests.exceptions.RequestException as e:
            if "404" in str(e):
                return f"Error: Model '{self.model_name}' not found. Available models: {self.get_available_models()}"
            return f"Error calling Ollama: {e}"
    
    def list_documents(self):
        """List all documents in the knowledge base"""
        try:
            # Get all documents
            results = self.collection.get()
            
            if not results['metadatas']:
                print("No documents in knowledge base")
                return
            
            # Group by source document
            docs = {}
            for metadata in results['metadatas']:
                source = metadata.get('source', 'Unknown')
                if source not in docs:
                    docs[source] = 0
                docs[source] += 1
            
            print("\nDocuments in knowledge base:")
            print("-" * 40)
            for doc_name, chunk_count in docs.items():
                print(f"📄 {doc_name}: {chunk_count} chunks")
            print(f"\nTotal: {len(docs)} documents, {sum(docs.values())} chunks")
            
        except Exception as e:
            print(f"Error listing documents: {e}")
    
    def search_documents(self, query: str, n_results: int = 5):
        """Search through documents and show results"""
        try:
            relevant_chunks = self.retrieve_relevant_chunks(query, n_results)
            
            if not relevant_chunks:
                print("No relevant documents found")
                return
            
            print(f"\nFound {len(relevant_chunks)} relevant chunks:")
            print("=" * 50)
            
            for i, chunk in enumerate(relevant_chunks, 1):
                # Show first 200 characters of each chunk
                preview = chunk[:200] + "..." if len(chunk) > 200 else chunk
                print(f"\n{i}. {preview}")
                print("-" * 30)
                
        except Exception as e:
            print(f"Error searching documents: {e}")
    
    def delete_document(self, doc_name: str):
        """Delete a specific document from the knowledge base"""
        try:
            # Get all items
            results = self.collection.get()
            
            # Find IDs for this document
            ids_to_delete = []
            for i, metadata in enumerate(results['metadatas']):
                if metadata.get('source') == doc_name:
                    ids_to_delete.append(results['ids'][i])
            
            if not ids_to_delete:
                print(f"Document '{doc_name}' not found")
                return
            
            # Delete the chunks
            self.collection.delete(ids=ids_to_delete)
            print(f"Deleted {len(ids_to_delete)} chunks from '{doc_name}'")
            
        except Exception as e:
            print(f"Error deleting document: {e}")
    
    def clear_all_documents(self):
        """Clear all documents from the knowledge base"""
        try:
            # Delete the collection and recreate it
            self.chroma_client.delete_collection("documents")
            self.collection = self.chroma_client.create_collection("documents")
            print("All documents cleared from knowledge base")
        except Exception as e:
            print(f"Error clearing documents: {e}")
        """Get list of available Ollama models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except:
            return []
    
    def ask_question(self, question: str, use_context: bool = True) -> str:
        """Ask a question with optional document context"""
        if use_context:
            # Retrieve relevant chunks
            relevant_chunks = self.retrieve_relevant_chunks(question, n_results=3)
            
            if relevant_chunks:
                context = "\n\n".join(relevant_chunks)
                prompt = f"""Context from documents:
{context}

Question: {question} 

This is very important:
Please answer the question based on the provided context. 
If the context doesn't contain enough information, please say so. 
If the question has nothing to do with the context, dont answer the question, just say you dont have any information about the subject
At the end of your answer, provide up to three relevant follow up questions the user might ask about the provided context."""
            else:
                prompt = f"No relevant context found. Question: {question}"
        else:
            prompt = question
        
        return self.call_ollama(prompt)
    
    def interactive_chat(self):
        """Start an interactive chat session"""
        print("RAG Chat with Gemma2 (type 'quit' to exit, 'no-context' to disable RAG)")
        print("Available commands:")
        print("  /add <file_path> - Add a document to the knowledge base")
        print("  /list - List all documents in the knowledge base")
        print("  /search <query> - Search through documents")
        print("  /delete <doc_name> - Delete a specific document")
        print("  /clear - Clear all documents")
        print("  /toggle-context - Toggle context usage on/off")
        print("  /status - Show system status")
        
        use_context = True
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.startswith('/add '):
                    file_path = user_input[5:].strip()
                    if os.path.exists(file_path):
                        self.add_document(file_path)
                        print("Document added successfully!")
                    else:
                        print("File not found!")
                elif user_input == '/toggle-context':
                    use_context = not use_context
                    print(f"Context usage: {'enabled' if use_context else 'disabled'}")
                elif user_input == '/status':
                    count = self.collection.count()
                    print(f"Documents in knowledge base: {count} chunks")
                    print(f"Context usage: {'enabled' if use_context else 'disabled'}")
                    print(f"Model: {self.model_name}")
                elif user_input == '/list':
                    self.list_documents()
                elif user_input.startswith('/search '):
                    query = user_input[8:].strip()
                    if query:
                        self.search_documents(query)
                    else:
                        print("Please provide a search query")
                elif user_input.startswith('/delete '):
                    doc_name = user_input[8:].strip()
                    if doc_name:
                        confirm = input(f"Are you sure you want to delete '{doc_name}'? (y/N): ")
                        if confirm.lower() == 'y':
                            self.delete_document(doc_name)
                    else:
                        print("Please provide a document name")
                elif user_input == '/clear':
                    confirm = input("Are you sure you want to clear ALL documents? (y/N): ")
                    if confirm.lower() == 'y':
                        self.clear_all_documents()
                elif user_input:
                    print("Thinking...")
                    response = self.ask_question(user_input, use_context)
                    print(f"\nGemma2: {response}")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="RAG with Ollama and Gemma2")
    parser.add_argument("--model", default="gemma2:2b", help="Ollama model name")
    parser.add_argument("--add-doc", help="Add a document to the knowledge base")
    parser.add_argument("--list-docs", action='store_true', help="Lists all documents of the knowldge base")
    parser.add_argument("--question", help="Ask a single question")
    parser.add_argument("--interactive", action="store_true", help="Start interactive mode")
    
    args = parser.parse_args()
    
    if args.add_doc:
        rag = RAGWithOllama(model_name=args.model)
        rag.add_document(args.add_doc)
        print("Document added successfully!")

    elif args.list_docs:
        rag = RAGWithOllama(model_name=args.model)
        rag.list_documents()
    
    elif args.question:
        rag = RAGWithOllama(model_name=args.model)
        response = rag.ask_question(args.question)
        print(f"Answer: {response}")

    elif args.interactive:
        rag = RAGWithOllama(model_name=args.model)
        rag.interactive_chat()

    else:
        parser.print_help()

if __name__ == "__main__":
    main()