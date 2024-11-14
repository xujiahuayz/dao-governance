"""
Prompts and instructions
"""

IDF_PROMPT = """Given the following HTTP website response, determine \
whether it satisfies the following criteria. If it satisfies all three criteria, \
return "Yes". Otherwise, return "No".

Criteria:
1. The website is accessible.
2. The content of the website is a forum discussion.
3. The forum discussion has at least one response.
(End of Criteria)

HTTP Response:
{http_response}
(End of HTTP Response)
"""

EVAL_PROMPT = """Given the following website HTTP response, evaluate the \
content based on the following 3 criteria with either "Yes" or "No". You also \
need to provide concise text explaining the reasoning behind the evaluation.

Criteria:
1. Support
2. Professionalism
3. Objectiveness
(End of Criteria)

HTTP Response:
{http_response}
(End of HTTP Response)
"""


IDF_INSTRUCT = """You are a decentralized autonomous organizations (DAO) expert \
who is proficient in evaluating forum discussions. Your output should always be \
either Yes or No."""

EVAL_INSTRUCT = """You are a decentralized autonomous organizations (DAO) expert \
who is proficient in evaluating forum discussions. Your output format should be as follows:
Support: {Yes/No}
Professionalism: {Yes/No}
Objectiveness: {Yes/No}
Explanation: {Your explanation here}"""
