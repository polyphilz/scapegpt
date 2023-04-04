import chromadb
import openai
import os
import re

from dotenv import load_dotenv

load_dotenv()


COMPLETIONS_MODEL = "text-davinci-003"
EMBEDDING_MODEL = "text-embedding-ada-002"


def create_embeddings(markdown_document):
    # Convert Markdown document to plain text
    plain_text = re.sub("#+ ", "", markdown_document)

    return openai.Embedding.create(input=plain_text, model=EMBEDDING_MODEL)


def main():
    # Set up your OpenAI API key
    openai.api_key = os.getenv("OPENAI_API_KEY")

    client = chromadb.Client()
    collection = client.create_collection("sample_collection")

    # Set the path to the directory containing the Markdown files
    directory_path = "summaries/"

    # Get a list of all the Markdown files in the directory
    markdown_files = [f for f in os.listdir(directory_path) if f.endswith(".md")]

    # Loop through each Markdown file
    embeddings = []
    documents = []
    for filename in markdown_files:
        documents.append(filename.replace(".md", ""))
        with open(directory_path + filename, "r") as file:
            contents = file.read()
            embedding = create_embeddings(contents)
            embeddings.append(embedding.data[0].embedding)
    collection.add(
        embeddings=embeddings,
        documents=documents,
        ids=documents,
    )

    # prompt = "Where can I find a barrel of rainwater (NOT the one from Misthalin Mystery)?"
    # prompt = "Where can I find a bunk bed?"
    # prompt = "How do I build an altar space?"
    prompt = "What is an altar space?"
    query1_embedding = create_embeddings(prompt)
    embedding_results = collection.query(
        query_embeddings=query1_embedding.data[0].embedding, n_results=4
    )
    document_results = embedding_results["documents"][0]
    filenames = []
    for document in document_results:
        filename = document + ".md"
        filenames.append(filename)
    print(filenames)
    context = ""
    for filename in filenames:
        with open(directory_path + filename, "r") as file:
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
        temperature=0,
        max_tokens=300,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        model=COMPLETIONS_MODEL,
    )["choices"][0]["text"].strip(" \n")

    print(final)


if __name__ == "__main__":
    main()
