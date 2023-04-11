import openai
import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# The directory where wiki article summaries are stored.
SUMMARIES_DIR = "summaries/"
# OpenAI API-specific constants.
EMBEDDING_MODEL = "text-embedding-ada-002"


def main():
    # Set up your OpenAI API key
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Set up Supabase URL/key and client
    sb_url = os.getenv("SUPABASE_URL")
    sb_key = os.getenv("SUPABASE_KEY")
    supabase = create_client(sb_url, sb_key)

    # Store summary documents in Supabase
    summary_docs = [f for f in os.listdir(SUMMARIES_DIR) if f.endswith(".txt")]
    documents = []
    for filename in summary_docs:
        document = {"filename": filename.replace(".txt", "")}
        with open(SUMMARIES_DIR + filename, "r") as file:
            content = file.read()
            # content = content.replace("\n", " ")
            document["content"] = content
            embedding = openai.Embedding.create(input=content, model="text-embedding-ada-002")
            document["embedding"] = embedding.data[0].embedding
        documents.append(document)

    for document in documents:
        data = supabase.table("documents").insert(document).execute()
        assert len(data.data) > 0


if __name__ == "__main__":
    main()
