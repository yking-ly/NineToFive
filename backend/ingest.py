import os
import shutil
from typing import List, Optional
import docx
from langchain_community.document_loaders import PyPDFLoader, TextLoader
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

# Updated imports for modern LangChain
try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.docstore.document import Document

import core

def load_docx(file_path):
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return [Document(page_content="\n".join(full_text), metadata={"source": file_path})]

def ingest_document(file_path: str, original_filename: str) -> List[str]:
    """
    Ingests a document into ChromaDB.
    """
    try:
        ext = os.path.splitext(file_path)[1].lower()
        documents = []

        if ext == '.pdf':
            loader = PyPDFLoader(file_path)
            documents = loader.load()
        elif ext == '.docx':
            documents = load_docx(file_path)
        elif ext == '.txt':
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
        else:
            return []

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
        chunks = text_splitter.split_documents(documents)
        
        for i, chunk in enumerate(chunks):
            chunk.metadata['filename'] = original_filename
            chunk.metadata['chunk_index'] = i
            chunk.metadata['source'] = original_filename

        if not chunks:
            return []

        # Use persistent DB
        # Distribute chunks across shards
        dbs = core.get_dbs()
        shard_chunks = [[] for _ in range(core.NUM_SHARDS)]
        
        for i, chunk in enumerate(chunks):
            shard_idx = i % core.NUM_SHARDS
            shard_chunks[shard_idx].append(chunk)
            
        all_ids = []
        all_ids = []
        BATCH_SIZE = 32

        for i, db_chunks in enumerate(shard_chunks):
            if db_chunks:
                total_chunks = len(db_chunks)
                print(f"Ingesting {total_chunks} chunks to shard {i}...")
                
                for j in range(0, total_chunks, BATCH_SIZE):
                    batch = db_chunks[j : j + BATCH_SIZE]
                    try:
                        ids = dbs[i].add_documents(batch)
                        all_ids.extend(ids)
                        print(f"  Processed batch {j//BATCH_SIZE + 1} ({len(batch)} chunks)")
                    except Exception as batch_error:
                        print(f"  Error processing batch {j//BATCH_SIZE + 1}: {batch_error}")
        
        print(f"Ingested total {len(all_ids)} chunks for {original_filename}")
        
        # Invalidate cache on new ingest
        core.clear_cache()
        
        return all_ids

    except Exception as e:
        print(f"Error during ingestion: {e}")
        return []

def generate_summary(file_path: str) -> str:
    try:
        ext = os.path.splitext(file_path)[1].lower()
        text = ""
        
        if ext == '.pdf':
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            text = "\n".join([d.page_content for d in docs])
        elif ext == '.docx':
            docs = load_docx(file_path)
            text = docs[0].page_content
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        
        if not text:
            return "Could not extract text."

        context = text[:4000]
        # ChatML Format for Summary
        prompt = f"""<|im_start|>system
You are a helpful assistant. Summarize the following document concisely.<|im_end|>
<|im_start|>user
Content:
{context}

Summary:<|im_end|>
<|im_start|>assistant
"""
        
        summary = core.safe_llm_invoke(prompt, stop=["<|im_end|>"])
        return summary

    except Exception as e:
        print(f"Error generating summary: {e}")
        return "Summary generation failed."
