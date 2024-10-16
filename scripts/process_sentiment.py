from openai import OpenAI
from governenv.settings import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)

# Set your API key

# Define the prompt
prompt = "Explain how blockchain works in simple terms."

# Make a request to the OpenAI API
response = client.completions.create(
    prompt=prompt,
    model="gpt-3.5-turbo-instruct",
    max_tokens=100,
)

# Print the response
print(response.choices[0].text.strip())
