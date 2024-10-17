from openai import OpenAI
import gzip
import json
import pickle
from governenv.settings import OPENAI_API_KEY
from governenv.constants import DATA_DIR

# unpickle data_unique
with open(DATA_DIR / "discussion_links.pkl", "rb") as f:
    data_unique = pickle.load(f)


client = OpenAI(api_key=OPENAI_API_KEY)

# check if jsonl.gz file "sentiment.jsonl.gz" exists in DATA_DIR
# if not, create it
# if it exists, load the data
# if the data is empty, process the first proposal
# if the data is not empty, process the next proposal

if not (DATA_DIR / "sentiment.jsonl.gz").exists():
    with gzip.open(DATA_DIR / "sentiment.jsonl.gz", "wt") as f:
        # create an empty list
        json.dump([], f)
else:
    # load the data
    with gzip.open(DATA_DIR / "sentiment.jsonl.gz", "rt") as f:
        sentiment = [json.loads(line) for line in f]

# # get ids not in sentiment
# ids = set([list(i.keys())[0] for i in sentiment])
# ids = [i for i in data_unique if list(i.keys())[0] not in ids]
with gzip.open(DATA_DIR / "sentiment.jsonl.gz", "at") as f:
    for key, value in data_unique.items():

        discussion = data_unique[key]
        # Define the prompt
        prompt = f"""
        Please determine the content of the following page:
        {discussion}

        Please return just "NA"  if you cannot access the URL or if the content is obviously not a forum discussion.

        Otherwise, please return only the JSON object with 5 entries containing evaluation of the discussion based on four criteria:

        1. Level of support (Very Low = most disapproving, Very High = most supportive)
        2. Professionalism (Very Low = least professional, Very High = most professional)
        3. Objectiveness (Very Low = purely subjective, Very High = purely objective)
        4. Unanimity (Very Low = completely polarized opinions and there is no "majority", Very High = unanimous)

        the first 4 of the entries being "support", "professionalism", "objectiveness", "unanimity", 
        each with a evaluation result of "Very Low", "Low", "Medium", "High", or "Very High".
        the last one being "explanation", with concise text explaining the reasoning behind the evaluation.
        No additional information should be returned.
        """

        # Make the request to the OpenAI API
        response = client.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=200,
            temperature=0.1,  # We want a deterministic response (no creativity)
            # stop=["}"],  # Stop after the JSON object is complete
        )

        # Extract the JSON string from the response
        json_output = response.choices[0].text.strip()

        # write key: eval(json_output) in sentiment.jsonl.gz
        result = {key: {"scores": json_output, "discussion": discussion}}

        print(result)

        f.write(json.dumps(result) + "\n")
