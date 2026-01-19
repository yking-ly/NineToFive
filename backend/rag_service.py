import sys
import os
from pathlib import Path

# Add project root to sys.path to allow importing services
# Assumes backend/ is at /NineToFive/backend
# and project_root is /NineToFive
backend_dir = Path(__file__).parent.resolve()
project_root = backend_dir.parent.resolve()
sys.path.insert(0, str(project_root))

from services.retrieval_engine.src.vector_store.chroma_client import ChromaDBClient

class RAGService:
    def __init__(self):
        self.chroma = ChromaDBClient()
        print("[RAG Service] ChromaDB Client Initialized")

    def query_statutes(self, query_text: str, n_results: int = 3):
        """
        Query IPC, BNS, and Mapping collections in parallel logic
        """
        results = {
            "ipc": [],
            "bns": [],
            "mapping": []
        }
        
        # 1. Search IPC
        try:
            ipc_res = self.chroma.query("ipc", query_text, n_results)
            if ipc_res['ids']:
                for i, doc_id in enumerate(ipc_res['ids']):
                    results["ipc"].append({
                        "id": doc_id,
                        "text": ipc_res['documents'][i],
                        "metadata": ipc_res['metadatas'][i],
                        "score": ipc_res['distances'][i] if ipc_res['distances'] else 0
                    })
        except Exception as e:
            print(f"[RAG Error] IPC Query failed: {e}")

        # 2. Search BNS
        try:
            bns_res = self.chroma.query("bns", query_text, n_results)
            if bns_res['ids']:
                for i, doc_id in enumerate(bns_res['ids']):
                    results["bns"].append({
                        "id": doc_id,
                        "text": bns_res['documents'][i],
                        "metadata": bns_res['metadatas'][i],
                        "score": bns_res['distances'][i] if bns_res['distances'] else 0
                    })
        except Exception as e:
            print(f"[RAG Error] BNS Query failed: {e}")

        # 3. Search Mapping
        try:
            map_res = self.chroma.query("mapping", query_text, n_results)
            if map_res['ids']:
                for i, doc_id in enumerate(map_res['ids']):
                    results["mapping"].append({
                        "id": doc_id,
                        "text": map_res['documents'][i],
                        "metadata": map_res['metadatas'][i],
                        "score": map_res['distances'][i] if map_res['distances'] else 0
                    })
        except Exception as e:
            print(f"[RAG Error] Mapping Query failed: {e}")

        return results

    def generate_answer(self, query: str, context: dict) -> str:
        """
        Simulate LLM generation based on retrieved context.
        In future, replace this with calls to Claude/Gemini.
        """
        response_parts = []
        
        response_parts.append(f"### Analysis for: *{query}*\n")
        
        # Mapping Logic: If mapping found, highlight the transition
        if context["mapping"]:
            top_map = context["mapping"][0]
            bns_sec = top_map["metadata"]["bns_section"]
            ipc_sec = top_map["metadata"]["ipc_section"]
            subject = top_map["metadata"]["subject"]
            
            response_parts.append(f"**Legal Transition:**")
            response_parts.append(f"The relevant law has transitioned from **IPC Section {ipc_sec}** to **BNS Section {bns_sec}**.")
            response_parts.append(f"**Subject:** {subject}")
            response_parts.append(f"**Changes:** {top_map['metadata']['summary']}\n")

        # BNS Logic
        if context["bns"]:
            top_bns = context["bns"][0]
            response_parts.append(f"**New Law (BNS):**")
            response_parts.append(f"Section {top_bns['metadata']['section_number']}: {top_bns['metadata']['section_title']}")
            response_parts.append(f"> {top_bns['text'][:300]}...\n") # Preview

        # IPC Logic
        if context["ipc"]:
            top_ipc = context["ipc"][0]
            response_parts.append(f"**Old Law (IPC):**")
            response_parts.append(f"Section {top_ipc['metadata']['section_number']}: {top_ipc['metadata']['section_title']}")
            pass
            
        if not any(context.values()):
            return "I could not find any specific legal sections matching your query in the BNS or IPC databases."
            
        return "\n".join(response_parts)

