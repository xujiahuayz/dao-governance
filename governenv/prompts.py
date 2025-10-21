"""
Prompts, instructions, and json schemas
"""

# Prompts
IDF_PROMPT = """Given the following contents extracted from the website HTML or TXT, determine \
whether it satisfies the following criteria.

Criteria:
1. The content of the website is a forum discussion.
2. The forum discussion has at least one response.
(End of Criteria)

Contents:
{content}
(End of Contents)
"""

EVAL_PROMPT = """Given the following contents extracted from the webpage \
(HTML or plain text), evaluate the *discussion portion* (i.e., replies, \
comments, and exchanges between participants, not the proposal text itself):

Criteria:
1. Support
2. Professionalism
3. Objectiveness
4. Unanimity
(End of Criteria)

Respond only with "Yes" or "No" for each criterion.

Contents:
{content}
(End of Contents)
"""

# Instructions
IDF_INSTRUCT = """You are a decentralized autonomous organizations (DAO) expert \
who is proficient in evaluating forum discussions. Your output should follow this\
format: '{"is_forum_discussion": <true/false>}'"""

EVAL_INSTRUCT = """You are a decentralized autonomous organizations (DAO) expert \
who is proficient in evaluating forum discussions. Your output format should be as follows:
Support: {Yes/No}
Professionalism: {Yes/No}
Objectiveness: {Yes/No}
Unanimity: {Yes/No}"""

# JSON Schemas
IDF_JSON_SCHEMA = {
    "name": "dao",
    "schema": {
        "type": "object",
        "properties": {
            "is_forum_discussion": {
                "type": "boolean",
            },
        },
        "required": ["is_forum_discussion"],
        "additionalProperties": False,
    },
    "strict": True,
}
