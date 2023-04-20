import chromadb
import openai
import os

from chromadb.config import Settings
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()


# The directory where wiki article summaries are stored.
SUMMARIES_DIR = "summaries/"
# OpenAI API-specific constants.
COMPLETIONS_MODEL = "text-davinci-003"
EMBEDDING_MODEL = "text-embedding-ada-002"


def main():
    # Set up your OpenAI API key
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Create a ChromaDB client and get/create the embeddings collection
    client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="./.chromadb",
    ))
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"), model_name="text-embedding-ada-002"
    )
    collection = client.get_or_create_collection(
        name="osrs_wiki_embeddings", embedding_function=openai_ef
    )

    # Get a list of all the wiki summary docs and store in ChromaDB
    # summary_docs = [f for f in os.listdir(SUMMARIES_DIR) if f.endswith(".txt")]
    # documents, filename_ids = [], []
    # for filename in summary_docs:
    #     filename_ids.append(filename.replace(".txt", ""))
    #     with open(SUMMARIES_DIR + filename, "r") as file:
    #         contents = file.read()
    #         documents.append(contents)

    # collection.add(
    #     documents=documents,
    #     ids=filename_ids,
    # )

    prompt = "Who was Bandos?"
    prompt = "Which god is referred to as the big high war god?"
    embedding_results = collection.query(
        query_texts=[prompt],
        n_results=4,
    )
    ids = embedding_results["ids"][0]
    filenames = []
    for id in ids:
        filenames.append(id + ".md")
    print(filenames)
    # context = ""
    # for filename in filenames:
    #     with open(SUMMARIES_DIR + filename, "r") as file:
    #         contents = file.read()
    #         context += contents + "\n\n"
    # prompt_with_context = (
    #     "Given the following sections from the OldSchool RuneScape documentation, "
    #     "answer the question using only that information. If you are unsure, say "
    #     "'Sorry, I don't know how to help with that'.\n\n"
    #     f"Context sections:\n\n{context}\n\n"
    #     f"Question: {prompt}"
    # )

    # final = openai.Completion.create(
    #     prompt=prompt_with_context,
    #     temperature=0.5,
    #     max_tokens=500,
    #     top_p=1,
    #     frequency_penalty=0,
    #     presence_penalty=0,
    #     model=COMPLETIONS_MODEL,
    # )["choices"][0]["text"].strip(" \n")

    # print(final)


if __name__ == "__main__":
    main()