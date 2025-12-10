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

DISCUSSION_PROMPT = """You are given a DAO governance proposal ("Post") and its \
associated discussion thread ("Discussion"). Your task is to evaluate the \
**Discussion** according to the following criterion: **{criterion}**.

Instructions:
- The Post and Discussion entries are numbered.
- If a discussion entry is a reply to another entry, this is indicated in parentheses (e.g., "reply to 5").
- User roles such as [moderator], [admin], or [staff] may appear in square brackets.
- Focus your evaluation strictly on the Discussion, not on the Post itself.

Post:
{post}
(End of Post)

Discussion:
{discussion}
(End of Discussion)
"""


# Instructions
TOPIC_INSTRUCT = """You are an expert in decentralized autonomous organizations (DAOs). \
Your response should follow this format: '{"result": <true/false>}'."""

DISCUSSION_INSTRUCT = """You are an expert in decentralized autonomous organizations (DAOs). \
Your response should follow this format: '{"result": <true/false>}'."""


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
