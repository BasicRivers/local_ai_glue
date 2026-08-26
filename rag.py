import os
import uuid

import numpy as np
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from ollama import show
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct

from settings import RAG_PATHS, LLM, RAGS

PATHS = RAG_PATHS

class RagsManager:
    def __init__(self, paths=PATHS, nearest_K=2, score_threshold=0.85):
        self.SOURCE_DATA_PATH = paths["SOURCE_DATA"]
        self.EMBEDDED_PATH = paths["VECTOR_DB_PATH"]
        self.PDF_DB = paths["PDF_COLLECTION"]
        
        self.CHUNK_SIZE = 500
        self.CHUNK_OVERLAP=100

        self.RAGS_MODEL=SentenceTransformer(RAGS)
        self.LLM_INFO = show(LLM)["modelinfo"]
        self.CONTEXT_LENGTH = next(value for key, value in self.LLM_INFO.items() if key.lower().endswith(".context_length")) # look through the parameters (metadata info) of the llm to figure out how much context length it can benefit from as a maximum.
        self.EMBEDDING_DIMENSIONS = self.RAGS_MODEL.get_embedding_dimension()
        self._init_DB_client()
        self.nearest_K = nearest_K
        self.score_threshold = score_threshold

    def load_documents(self):
        loader = DirectoryLoader(self.SOURCE_DATA_PATH, glob="*.pdf", loader_cls=PyPDFLoader)
        documents = loader.load()
        return documents
    
    def generate_chunks(self, documents):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=self.CHUNK_SIZE, chunk_overlap=self.CHUNK_OVERLAP, length_function=len, separators=["\n\n", "\n", "."])
        documents_split = text_splitter.split_documents(documents)
        texts = [doc.page_content for doc in documents_split]
        return texts
    
    def generate_embeddings(self, sentences):
        embeddings = self.RAGS_MODEL.encode(sentences)
        return embeddings
    
    def _init_DB_client(self):
        self.client = QdrantClient(path=self.EMBEDDED_PATH)
        
    def kill_DB_client(self):
        self.client.close()
        
    def create_collection_database(self):
        # This will delete the existing collection and recreate a new one
        if self.client.collection_exists(collection_name=self.PDF_DB):
            self.client.delete_collection(collection_name=self.PDF_DB)
        self.client.create_collection(collection_name=self.PDF_DB, vectors_config=VectorParams(size=self.EMBEDDING_DIMENSIONS, distance=Distance.EUCLID))

    def add_all_documents(self, texts:list, embeddings:list):
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            doc_id = uuid.uuid4()
            self.client.upsert(collection_name=self.PDF_DB, wait=True, points=[PointStruct(id=doc_id, vector=embedding, payload={"page_content":text})])

    def user_query(self, input_text):
        user_question = self.generate_embeddings(input_text)
        query_results = [x.payload["page_content"] for x in self.client.query_points(collection_name=self.PDF_DB, query=user_question, with_payload=True, limit=self.nearest_K, score_threshold=self.score_threshold).points]
        return query_results
    
if __name__ == "__main__":
    rags_manager = RagsManager()
    documents = rags_manager.load_documents()
    texts = rags_manager.generate_chunks(documents)
    embeddings = rags_manager.generate_embeddings(texts)
    rags_manager.create_collection_database()
    rags_manager.add_all_documents(texts, embeddings)
    
    test_query = "How do I copy files in linux?"
    results = rags_manager.user_query(test_query)
    print(results)
    rags_manager.kill_DB_client()
