import chromadb
import openai
import os
import re

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
    client = chromadb.Client(
        Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./.chromadb",
        )
    )
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"), model_name="text-embedding-ada-002"
    )
    collection = client.get_or_create_collection(
        name="osrs_wiki_embeddings", embedding_function=openai_ef
    )

    # # Get a list of all the wiki summary docs and store in ChromaDB
    # summary_docs = [f for f in os.listdir(SUMMARIES_DIR) if f.endswith(".md")]
    # documents, filename_ids = [], []
    # for filename in summary_docs:
    #     filename_ids.append(filename.replace(".md", ""))
    #     with open(SUMMARIES_DIR + filename, "r") as file:
    #         contents = file.read()
    #         # Convert Markdown to plain text to reduce noise
    #         plain_text_contents = re.sub("#+ ", "", contents)
    #         documents.append(plain_text_contents)
    #         # embedding = create_embeddings(contents)
    #         # embeddings.append(embedding.data[0].embedding)
    # # collection.add(
    # #     embeddings=embeddings,
    # #     documents=documents,
    # #     ids=documents,
    # # )
    # collection.add(
    #     documents=documents,
    #     ids=filename_ids,
    # )

    # prompt = "Where can I find a barrel of rainwater (NOT the one from Misthalin Mystery)?"
    # prompt = "Where can I find a barrel of rainwater?"
    # prompt = "Which locations can I find a barrel of rainwater, and of those locations, which are accessible only by members?"
    # prompt = "Where can I find a bunk bed?"
    # prompt = "How do I build an altar space?"
    # prompt = "What is an altar space?"
    # prompt = "Tell me more about bank chests."
    # prompt = "Tell me some trivia about bank chests."
    # prompt = "How many bank chests are accessible by members?"
    # prompt = "How many bank chests are there in the game?"
    prompt = "When was the bank chest-wreck released?"
    prompt = "What is the examine text of the bank chest-wreck?"
    prompt = "Tell me the changes the bank chest-wreck has undergone, and their dates."
    prompt = "What construction level do I need to make an accomplishment scroll space?"
    prompt = "How do I make an accomplishment scroll space?"
    prompt = "What are the different types of altars I can create?"
    prompt = "How do I make a dark altar?"
    prompt = "Tell me about dark altars."
    prompt = "How much will it cost to make a dark altar?"
    embedding_results = collection.query(
        query_texts=[prompt],
        n_results=4,
    )
    ids = embedding_results["ids"][0]
    filenames = []
    for id in ids:
        filenames.append(id + ".md")
    context = ""
    for filename in filenames:
        with open(SUMMARIES_DIR + filename, "r") as file:
            contents = file.read()
            context += contents + "\n\n"
    prompt_with_context = (
        "Given the following sections from the OldSchool RuneScape documentation, "
        "answer the question using only that information. If you are unsure, say "
        "'Sorry, I don't know how to help with that'.\n\n"
        f"Context sections:\n\n{context}\n\n"
        f"Question: {prompt}"
    )

    final = openai.Completion.create(
        prompt=prompt_with_context,
        temperature=0.5,
        max_tokens=500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        model=COMPLETIONS_MODEL,
    )["choices"][0]["text"].strip(" \n")

    print(final)


if __name__ == "__main__":
    main()
