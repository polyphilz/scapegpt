import openai
import os
import re

from dotenv import load_dotenv

load_dotenv()


def create_embeddings(markdown_document):
    # Convert Markdown document to plain text
    plain_text = re.sub("#+ ", "", markdown_document)

    return openai.Embedding.create(input=plain_text, model="text-embedding-ada-002")


def main():
    # Set up your OpenAI API key
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Example usage
    markdown_document = """
  # Heading 1

  This is some text.

  ## Heading 2

  This is more text.
  """

    embeddings = create_embeddings(markdown_document)
    print(embeddings)


if __name__ == "__main__":
    main()
