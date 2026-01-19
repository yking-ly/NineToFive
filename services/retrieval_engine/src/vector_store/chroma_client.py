"""
ChromaDB client for vector storage and retrieval.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..config import settings


class ChromaDBClient:
    """Client for interacting with ChromaDB collections."""
    
    def __init__(self, persist_directory: Optional[Path] = None):
        self.persist_dir = persist_directory or settings.CHROMA_PERSIST_DIR
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model
        self._embedding_model = None
        
        # Collection references
        self._collections = {}
    
    @property
    def embedding_model(self) -> SentenceTransformer:
        """Lazy load embedding model."""
        if self._embedding_model is None:
            print(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self._embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return self._embedding_model
    
    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        """Get or create a ChromaDB collection."""
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
        return self._collections[name]
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def add_documents(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> int:
        """
        Add documents to a collection.
        
        Args:
            collection_name: Name of the collection
            documents: List of dicts with 'id', 'document', 'metadata'
            batch_size: Number of documents to process at once
            
        Returns:
            Number of documents added
        """
        collection = self.get_or_create_collection(collection_name)
        total_added = 0
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            ids = [doc["id"] for doc in batch]
            texts = [doc["document"] for doc in batch]
            metadatas = [doc["metadata"] for doc in batch]
            
            # Generate embeddings
            embeddings = self.embed_texts(texts)
            
            # Add to collection
            collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            total_added += len(batch)
            print(f"Added {total_added}/{len(documents)} documents to '{collection_name}'")
        
        return total_added
    
    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = None,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Query a collection for similar documents.
        
        Args:
            collection_name: Name of the collection to query
            query_text: The query text
            n_results: Number of results to return
            where: Metadata filter
            where_document: Document content filter
            
        Returns:
            Query results with documents, metadatas, and distances
        """
        collection = self.get_or_create_collection(collection_name)
        n_results = n_results or settings.TOP_K
        
        # Generate query embedding
        query_embedding = self.embed_texts([query_text])[0]
        
        # Execute query
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=["documents", "metadatas", "distances"]
        )
        
        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else []
        }
    
    def query_multiple_collections(
        self,
        collection_names: List[str],
        query_text: str,
        n_results: int = None,
        where: Optional[Dict] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Query multiple collections in parallel.
        
        Returns:
            Dict mapping collection names to their results
        """
        results = {}
        for name in collection_names:
            try:
                results[name] = self.query(
                    collection_name=name,
                    query_text=query_text,
                    n_results=n_results,
                    where=where
                )
            except Exception as e:
                print(f"Error querying collection '{name}': {e}")
                results[name] = {"ids": [], "documents": [], "metadatas": [], "distances": []}
        
        return results
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection."""
        collection = self.get_or_create_collection(collection_name)
        return {
            "name": collection_name,
            "count": collection.count()
        }
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name)
            if collection_name in self._collections:
                del self._collections[collection_name]
            return True
        except Exception as e:
            print(f"Error deleting collection '{collection_name}': {e}")
            return False
