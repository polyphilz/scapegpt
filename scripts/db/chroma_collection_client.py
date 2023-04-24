import chromadb
import tiktoken

from chromadb.config import Settings
from chromadb.utils import embedding_functions
from gpt_index.indices.service_context import ServiceContext
from gpt_index.indices.tree.base import GPTTreeIndex
from gpt_index.langchain_helpers.chain_wrapper import LLMPredictor
from gpt_index.readers.schema.base import Document
from langchain.chat_models import ChatOpenAI
from typing import List, Tuple


# OpenAI constants
CHAT_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "text-embedding-ada-002"
MAX_TOKENS_FOR_PROMPT = 1024


class ChromaCollectionClient:
    def __init__(
        self,
        api_type: str,
        host: str,
        port: int,
        openai_api_key: str,
        collection_name: str,
    ) -> None:
        """
        Args:
            api_type (str): The type of API to use when connecting to ChromaDB
                (e.g. 'rest').
            host (str): The hostname of the database server to connect to
                (usually an IP address).
            port (int): The port number to connect to.
            openai_api_key (str): The OpenAI API key to use.
            collection_name (str): The name of the ChromaDB collection to use. If
                unavailable, a new collection will be created with this name.
        """
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
        """
        Deletes the specified collection and removes the reference to this
        instance.
        """
        self._client.delete_collection(name=self._collection_name)
        del self

    def load(self, summaries: List[Tuple[str, str]]) -> None:
        """Loads content into the ChromaDB collection.

        Args:
            summaries (List[Tuple[str, str]]): A list of tuples containing
                                            filename and content pairs for each
                                            document summary.
        """
        filename_ids, documents_content = [], []
        for filename, content in summaries:
            filename_ids.append(filename)
            documents_content.append(content)
        self._collection.add(
            documents=documents_content,
            ids=filename_ids,
        )

    def query(self, prompt: str, n_results: int = 3) -> str:
        """Constructs an answer to a provided prompt based on DB content.

        How it works:
            1. Tokenize the prompt to ensure it's not too long. If it is, this
               should be indicated to the user
            2. Queries ChromaDB to return the 3 most similar documents to the
               prompt
            3. LlamaIndex is used to construct a list index out of the 3
               documents
            4. This index is queried with the prompt, and the documents' content
               injected as context
            5. LlamaIndex uses OpenAI's chat model under the hood to generate
               a response to the prompt using the documents' content

        Args:
            prompt (str): The search prompt to query the collection for.
            n_results (int): The number of results to return. Defaults to 3.

        Returns:
            str: The query result as a string.
        """

        def num_tokens_from_string(string: str, encoding_name: str) -> int:
            """Returns the number of tokens in a text string."""
            encoding = tiktoken.get_encoding(encoding_name)
            num_tokens = len(encoding.encode(string))
            return num_tokens

        num_tokens = num_tokens_from_string(prompt, "cl100k_base")
        if num_tokens > MAX_TOKENS_FOR_PROMPT:
            raise ValueError(f"Prompt too long: {prompt} has {num_tokens} tokens.")

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

        num_outputs = 256
        llm_predictor = LLMPredictor(
            llm=ChatOpenAI(
                temperature=0.6, model_name=CHAT_MODEL, max_tokens=num_outputs
            )
        )
        service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)
        index = GPTTreeIndex.from_documents(
            documents,
            service_context=service_context,
        )

        return index.query(prompt, mode="retrieve")
