import chromadb
import os

from chromadb.config import Settings
from chromadb.utils import embedding_functions
from gpt_index.indices import GPTListIndex
from gpt_index.readers.schema.base import Document

# The directory where content summaries are stored.
SUMMARIES_DIR = "summaries/"
# OpenAI API-specific constants.
EMBEDDING_MODEL = "text-embedding-ada-002"


class ChromaCollectionClient:
    def __init__(self, api_type, host, port, openai_api_key, collection_name):
        self._client = chromadb.Client(
            Settings(
                chroma_api_impl=api_type,
                chroma_server_host=host,
                chroma_server_http_port=port,
            )
        )
        self._openai_api_key = openai_api_key
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=self._openai_api_key, model_name=EMBEDDING_MODEL
        )
        self._collection_name = collection_name
        self._collection = self._client.get_or_create_collection(
            name=collection_name, embedding_function=openai_ef
        )

    def delete(self):
        self._client.delete_collection(name=self._collection_name)
        del self

    def load_summaries(self):
        # Get a list of all content summary docs and store in the collection.
        summary_docs = [f for f in os.listdir(SUMMARIES_DIR) if f.endswith(".txt")]
        documents, filename_ids = [], []
        for filename in summary_docs:
            filename_ids.append(filename.replace(".txt", ""))
            with open(SUMMARIES_DIR + filename, "r") as file:
                contents = file.read()
                documents.append(contents)

        self._collection.add(
            documents=documents,
            ids=filename_ids,
        )

    def query(self, prompt, n_results=3):
        results = self._collection.query(
            query_texts=[prompt],
            n_results=n_results,
        )

        documents = []
        for result in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
        ):
            document = Document(
                doc_id=result[0],
                text=result[1],
                extra_info=result[2],
            )
            documents.append(document)

        index = GPTListIndex.from_documents(documents)
        return index.query(prompt)
