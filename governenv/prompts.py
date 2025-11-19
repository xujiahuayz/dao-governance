"""
Prompts, instructions, and json schemas
"""

# Prompts
TOPIC_PROMPT = """Given the following DAO governance proposal, determine whether \
it is directly relevant to {topic}.\

Proposal:
{proposal}
(End of Proposal)
"""

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
TOPIC_INSTRUCT = """You are an expert in decentralized autonomous organizations (DAOs). \
Your response should follow this format: '{"result": <true/false>}'."""

IDF_INSTRUCT = """You are an expert in decentralized autonomous organizations (DAOs). \
Your output should follow this format: '{"result": <true/false>}'."""

EVAL_INSTRUCT = """You are an expert in decentralized autonomous organizations (DAOs). \
Your output format should be as follows:

Support: {Yes/No}
Professionalism: {Yes/No}
Objectiveness: {Yes/No}
Unanimity: {Yes/No}."""

# JSON Schemas

JSON_SCHEMA = {
    "name": "dao",
    "schema": {
        "type": "object",
        "properties": {
            "result": {
                "type": "boolean",
            },
        },
        "required": ["result"],
        "additionalProperties": False,
    },
    "strict": True,
}

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
