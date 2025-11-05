"""Query templates for GraphQL."""

SPACES = """
    id
    name
    private
    about
    avatar
    terms
    location
    website
    twitter
    github
    coingecko
    email
    network
    symbol
    skin
    domain
    strategies {
      name
      network
      params
    }
    admins
    members
    moderators
    filters {
      minScore
      onlyMembers
    }
    plugins
    voting {
      delay
      period
      type
      quorum
      blind
      hideAbstain
      privacy
      aliased
    }
    categories
    validation {
      name
      params
    }
    voteValidation {
      name
      params
    }
    delegationPortal {
      delegationType
      delegationContract
      delegationApi
    }
    treasuries {
      name
      address
      network
    }
    activeProposals
    proposalsCount
    proposalsCount7d
    votesCount
    votesCount7d
    parent {
      id
    }
    children {
      id
    }
    guidelines
    template
    verified
    flagged
    hibernated
    turbo
    rank
    created
"""

PROPOSALS = """
    id
    ipfs
    author
    created
    updated
    space {id}
    network
    symbol
    type
    strategies {
      name
      network
      params
    }
    validation {
      name
      params
    }
    plugins
    title
    body
    discussion
    choices
    start
    end
    quorum
    quorumType
    privacy
    snapshot
    state
    link
    app
    scores
    scores_by_strategy
    scores_state
    scores_updated
    votes
    flagged
"""

STATEMENTS = """
    id
    about
    statement
    space
    delegate
    updated
    created
"""

VOTES = """
    id
    ipfs
    voter
    created
    proposal {id}
    choice
    metadata
    reason
    app
    vp
    vp_by_strategy
    vp_state
"""

DELEGATIONS = """
    id
    delegator
    space
    delegate
    timestamp
"""

NETWORKS = """
    id
    name
    premium
    spacesCount
"""
