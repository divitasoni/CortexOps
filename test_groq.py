import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
model = os.getenv("GROQ_MODEL")

print("API key loaded:", bool(api_key))
print("Model:", model)

if not api_key:
    print("ERROR: GROQ_API_KEY is missing")
    exit()

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

try:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly: GROQ WORKS"
            }
        ],
        temperature=0.2
    )

    print("\nSUCCESS!")
    print(response.choices[0].message.content)

except Exception as e:
    print("\nREAL ERROR:")
    print(type(e).__name__)
    print(str(e))