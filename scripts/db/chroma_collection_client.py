import chromadb

from chromadb.config import Settings
from chromadb.utils import embedding_functions
from gpt_index.indices import GPTListIndex
from gpt_index.readers.schema.base import Document
from typing import List, Tuple


EMBEDDING_MODEL = "text-embedding-ada-002"


class ChromaCollectionClient:
    def __init__(
        self,
        api_type: str,
        host: str,
        port: int,
        openai_api_key: str,
        collection_name: str,
    ) -> None:
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

    def delete(self) -> None:
        self._client.delete_collection(name=self._collection_name)
        del self

    def load_summaries(self, summaries: List[Tuple[str, str]]) -> None:
        filename_ids, documents_content = [], []
        for filename, content in summaries:
            filename_ids.append(filename)
            documents_content.append(content)
        self._collection.add(
            documents=documents_content,
            ids=filename_ids,
        )

    def query(self, prompt: str, n_results: int = 3) -> str:
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
