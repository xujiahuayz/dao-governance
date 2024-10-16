from openai import OpenAI
from governenv.settings import OPENAI_API_KEY

from governenv.constants import SNAPSHOT_PATH_PROPOSALS, DATA_DIR
import gzip

import json


# load the data
with gzip.open(SNAPSHOT_PATH_PROPOSALS, "rt") as f:
    # load data and skip duplicates
    data = [json.loads(line) for line in f]

# remove duplicates and filter out proposals with not discussion link
data_unique = {
    w["id"]: w["discussion"]
    for line in set([json.dumps(row, sort_keys=True) for row in data])
    if len((w := json.loads(line))["discussion"]) > 5
}


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
        Evaluate the following forum discussion based on four criteria:

        1. Level of support (0 = most disapproving, 1 = most supportive)
        2. Professionalism (0 = least professional, 1 = most professional)
        3. Objectiveness (0 = purely subjective, 1 = purely objective)
        4. Unanimity (0 = completely polarized opinions and there is no "majority", 1 = unanimous)

        Return the result as a JSON dictionary with these criteria as keys and their corresponding numeric values as floating-point numbers between 0 and 1.

        The URL to the discussion is:
        {discussion}

        Return only the JSON object with 5 entries; 
        the first 4 being "support", "professionalism", "objectiveness", "unanimity", with floating-point numbers being the value of each entry; 
        the last one being "explanation", with concise text explaining the reasoning behind the evaluation.
        If you cannot access the URL or if the content is obviously not a forum discussion, return NAN for the first 4 entries and "Invalid URL" for the last entry.
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
        result = {key: {"scores": eval(json_output), "discussion": discussion}}

        print(result)

        f.write(json.dumps(result) + "\n")
