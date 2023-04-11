import asyncio
import openai
import os
import sys

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


# The directory where wiki article summaries are stored.
SUMMARIES_DIR = "summaries/"
# OpenAI API-specific constants.
COMPLETIONS_MODEL = "text-davinci-003"
EMBEDDING_MODEL = "text-embedding-ada-002"
# Supabase constants.
SIMILARITY_THRESHOLD = 0.50
MATCH_COUNT = 20


async def main():
    args = sys.argv[1:]
    if len(args) == 0:
        raise Exception("No prompt provided.")
    prompt = args[0]

    # Set up your OpenAI API key
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Set up Supabase URL/key and client
    sb_url = os.getenv("SUPABASE_URL")
    sb_key = os.getenv("SUPABASE_KEY")
    supabase = create_client(sb_url, sb_key)
    func = supabase.functions()

    # Convert prompt to an embedding
    embedding = openai.Embedding.create(input=prompt, model="text-embedding-ada-002")
    embedding_vector = embedding.data[0].embedding

    # Query embeddings in Supabase with prompt embedding
    result = supabase.rpc("match_documents", {
        "query_embedding": embedding_vector,
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "match_count": MATCH_COUNT,
    })
    data = result.execute().data
    for x in data:
        print(x.keys())
        print(x["filename"])


    # embedding_results = collection.query(
    #     query_texts=[prompt],
    #     n_results=4,
    # )
    # ids = embedding_results["ids"][0]
    # filenames = []
    # for id in ids:
    #     filenames.append(id + ".md")
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
    asyncio.run(main())
