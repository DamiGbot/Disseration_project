import os
import time
import openai
from openai.embeddings_utils import get_embedding
from openai.error import OpenAIError, RateLimitError
import tiktoken

# Configuration
openai.api_key = os.getenv('OPENAI_API_KEY')  # Set your API key here
encoding = tiktoken.get_encoding("cl100k_base")
embedding_model = "text-embedding-ada-002"
max_tokens = 8000  # Set to your chosen maximum token count

def get_embeddings(text_series):
    embeddings = []
    backoff_time = 1  # Start with a 1 second wait, will increase on each retry

    for text in text_series:
        while True:
            try:
                # Ensure the text is within the token limit using tiktoken
                encoded_text = encoding.encode(text)
                if len(encoded_text) > max_tokens:
                    print(f"Text is too long ({len(encoded_text)} tokens), truncating.")
                    text = encoding.decode(encoded_text[:max_tokens])
                
                # Get the embedding using OpenAI API
                embedding = get_embedding(text, engine=embedding_model, max_tokens=max_tokens)
                embeddings.append(embedding)
                # Reset backoff time if successful
                backoff_time = 1
                break  # Break out of the retry loop if successful
            except RateLimitError as e:
                print("Hit rate limit, backing off...")
                time.sleep(backoff_time)
                backoff_time *= 2  # Exponential back-off
            except OpenAIError as e:
                # Handle other possible exceptions from the OpenAI API
                print(f"An error occurred: {e}")
                break  # Break out of the loop if there's an unknown error
    return embeddings

