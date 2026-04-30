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

STANCE_PROMPT = """You are a governance analyst and political economy researcher studying \
decentralized autonomous organizations (DAOs). You are given a DAO governance proposal \
("Post") and its associated discussion thread ("Discussion").Your task is to objectively \
classify governance discussion threads based strictly on their expressed content. Maintain \
neutrality and analytical rigor. Do not infer unstated motives. Do not hallucinate facts. \
Base your classification only on the text provided. The Post and Discussion entries are \
numbered. If a discussion entry is a reply to another entry, this is indicated in parentheses \
(e.g., "reply to 5"). User roles such as [moderator], [admin], or [staff] may appear in square \
brackets. Focus your evaluation strictly on the Discussion, not on the Post itself. \

Post:
{post}
(End of Post)

Discussion:
{discussion}
(End of Discussion)

Classification Tasks
Part 1 — Primary Stakeholder Stance (Single-Label)
Select the ONE category that best represents the dominant advocacy position in the thread:
1 = Pro-management (core contributors/foundation/developers)
Advocates expanding discretion, authority, compensation, treasury access, or operational flexibility for core contributors, foundations, multisig signers, or developers. Includes reducing governance constraints or token-holder oversight.
2 = Pro-DAO token holders (governance/financial interest)
Advocates strengthening token-holder voting rights, increasing transparency and accountability, limiting treasury spending, improving governance checks, or prioritizing token value and financial returns.
3 = Pro-users (protocol participants/end users)
Advocates lower fees, improved usability, enhanced decentralization, increased accessibility, improved security, or protections for non-governance users.
4 = Neutral or unclear
Does not clearly advocate for any stakeholder group, presents mixed arguments without a dominant stance, or is purely informational/technical.
 
Part 2 — Multi-Label Stakeholder Support (Binary Coding)
Indicate whether the thread meaningfully supports each group below.
Use 1 = Yes, 0 = No.
A = Pro-management
B = Pro-token holders
C = Pro-users
D = Neutral/informational only
Rules:
- Multiple of A, B, and C may equal 1 if clearly supported.
- If D = 1, then A = B = C = 0.
- Coding must reflect explicit advocacy.

Part 3 — Voting Power Alignment (Political Economy Layer)
Classify the thread's implicit or explicit alignment regarding governance power concentration:
1 = Whale-aligned
Supports maintaining or strengthening vote-weighted influence proportional to token ownership, resisting anti-concentration reforms (e.g., delegation caps, quadratic voting), or preserving capital-based control.
2 = Small-holder-aligned
Advocates reducing concentration of voting power, supporting delegation limits, quadratic voting, participation reforms, or governance mechanisms that limit dominance by large token holders.
3 = Neutral or unclear
Only code whale/small-holder alignment if there is meaningful indication related to voting power or governance concentration.
 
Part 4 — Confidence Score
Provide an integer from 0 to 100 representing your confidence in the overall classification.
Confidence should reflect:
- Clarity of stakeholder advocacy
- Strength of expressed position
- Lack of ambiguity"""

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


JSON_SCHEMA_STANCE = {
    "name": "dao_stance",
    "schema": {
        "type": "object",
        "properties": {
            "Primary": {"type": "integer", "enum": [1, 2, 3, 4]},
            "A": {"type": "integer", "enum": [0, 1]},
            "B": {"type": "integer", "enum": [0, 1]},
            "C": {"type": "integer", "enum": [0, 1]},
            "D": {"type": "integer", "enum": [0, 1]},
            "PowerAlignment": {"type": "integer", "enum": [1, 2, 3]},
            "Confidence": {"type": "integer", "minimum": 0, "maximum": 100},
        },
        "required": ["Primary", "A", "B", "C", "D", "PowerAlignment", "Confidence"],
        "additionalProperties": False,
    },
    "strict": True,
}
