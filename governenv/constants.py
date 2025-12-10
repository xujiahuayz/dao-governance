"""Constants."""

from governenv.settings import (
    PROJECT_ROOT,
    SNAPSHOT_API_KEY,
    INFURA_API_KEY,
)

# Directories and File Paths
DATA_DIR = PROJECT_ROOT / "data"
ABI_DIR = PROJECT_ROOT / "abi"
PROCESSED_DATA_DIR = PROJECT_ROOT / "processed_data"
FIGURE_DIR = PROJECT_ROOT / "figures"
SNAPSHOT_PATH = DATA_DIR / "snapshot.jsonl.gz"
SNAPSHOT_PATH_PROPOSALS = DATA_DIR / "snapshot_proposals.jsonl.gz"
SNAPSHOT_PATH_VOTES = DATA_DIR / "snapshot_votes.jsonl.gz"
SNAPSHOT_PATH_STATEMENTS = DATA_DIR / "snapshot_statements.jsonl.gz"
SNAPSHOT_PATH_DELEGATE = DATA_DIR / "snapshot_delegate.jsonl.gz"
SNAPSHOT_PATH_NETWORKS = DATA_DIR / "snapshot_networks.jsonl.gz"
GITHUB_PATH_IP_PULLREQUESTS = DATA_DIR / "IPs_pullRequests.jsonl.gz"
GITHUB_PATH_REFCLIENT_ISSUES = DATA_DIR / "refClient_issues.jsonl.gz"
GITHUB_PATH_REFCLIENT_PULLREQUESTS = DATA_DIR / "refClient_pullRequests.jsonl.gz"
KAIKO_PRICE_PATH = DATA_DIR / "kaiko_price.json.gz"
BITCOIN_NODES_GEO_PATH = DATA_DIR / "bitnodes_country_data.jsonl.gz"
IMPROVEMENT_PROPOSALS_DIR = DATA_DIR / "ImprovementProposals"
REFERENCE_CLIENTS_DIR = DATA_DIR / "ReferenceClients"


# DATA CUTOFF DATES
DATA_CUTOFF_DATE = "2025-09-01"

# Transfer Data Update
CURRENT_BLOCK = 23514780
DUST_THRESHOLD = 1
WHALE_THRESHOLD = 0.05

# API Endpoints
SNAPSHOT_ENDPOINT = f"https://hub.snapshot.org/graphql?apiKey={SNAPSHOT_API_KEY}"
GRAPH_SNAPSHOT_ENDPOINT = "https://gateway.thegraph.com/api/subgraphs/id/\
4YgtogVaqoM8CErHWDK8mKQ825BcVdKB8vBYmb4avAQo"
INFURA_API_BASE = "https://mainnet.infura.io/v3/"
INFURA_ENDPOINT = f"{INFURA_API_BASE}{INFURA_API_KEY}"

# Snapshot Contract Address
SNAPSHOT_DELEGATION_ADDRESS = "0x469788fE6E9E9681C6ebF3bF78e7Fd26Fc015446"
SNAPSHOT_DELEGATION_START_BLOCK = 11225329

# Event Study Parameters
EST_LOWER = -250
EST_UPPER = -20
EVENT_WINDOW = 5

# Topic List
TOPICS = [
    "user incentive increase",
    "treasury expenditure",
    "voting mechanism change",
    "protocol security",
    "tokenomics",
    "yield increase",
    "liquidity provider rewards",
]

# Discussion criteria
CRITERIA = [
    "Support",
    "Professionalism",
    "Objectiveness",
    "Unanimity",
    "Supportiveness",
    "Concensus",
    "Technical Depth",
    "Evidential Support",
    "Data Intensity",
]

# HTTP Request Headers
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )
}

# Voting Characteristics
NO = {
    "no",
    "against",
    "nah",
    "keep",
    "deny",
    "reject",
    "leave",
    "disagree",
    "disapprove",
    "don't",
    "nay",
    "decline",
    "oppose",
    "nae",
    "maintain",
    "不同意",
}
YES = {
    "yes",
    "for",
    "looks good",
    "approve",
    "in favor",
    "agree",
    "accept",
    "pass",
    "yay",
    "support",
    "cool",
    "yae",
    "confirm",
    "同意",
}
ABSTAIN = {"abstain"}

# Exclusion Keywords
EXKW = [
    # remove social media
    "discord",
    "t.me",
    "t.co",
    "telegram",
    "x.com/",
    "twitter",
    "reddit",
    "youtube",
    "youtu",
    "github",
    "bilibili",
    "gmail",
    # remove plain websites
    "baidu",
    "google",
    "coingecko",
    "blockscape",
    "helpen",
    "metamask.io",
    "opensea.io",
]

# Staking DAO Tokens Mapping
MIXED_TYPE_TOKEN = [
    # Badger DAO Staking (mixed types: drop)
    "0xca1f57ccb9e2ba18c49c873f4e51a5ef65b6e8dd",
    # Gyroscope DAO Staking (mixed types: drop)
    "0xbe9903a02b215a1fc97f8a5740acb29f78e3286e",
    # cSOS DAO Staking (mixed types: drop)
    "0x8744cd468a3d309ac8589bbb24f8ef79d2d723eb",
    "0x41cbac56ea5ec878135082f0f8d9a232a854447e",
    # Spell DAO Staking (mixed types: drop)
    "0x38a67c0f839e5f8939b12f9181a1924e4e4375ed",
    "0x958da0fc423e716554e67dff80921d171e6741b3",
    # SUSHIPOWAH (Mixed)
    "0x598eb12a541abbdb315045a4ede8d277f18b8be9",
    "0x2dbce82984595d977564888e08476053c6dbb0e3",
    "0xbeee2d4e97e05a386f0cd687c179769687e4aef6",
    "0xc7d324d52b6e14fb0f87f768ae0223362976277c",
    "0x62d11bc0652e9d9b66ac0a4c419950eeb9cfada6",
    # ZRS (mixed types: drop)
    "0x99b83672c85d8b985ea49de181da8f807a486eeb",
    # INDEXPOWAH (mixed types: drop)
    "0x44f2f64287753e0d4ee4043bb1d30077bf22414e",
    "0x78ec130ec5e470b06012f2ad0ab580d659004f7b",
    # IDEL DAO Staking (mixed types: drop)
    "0x02682c933428e7a9b7527dd9385f1e0c5d4a4f48",
    "0x826c61c3183b261e4d4a9a28adbc358061ecd207",
    "0xf241a0151841ae2e6ea750d50c5794b5edc31d99",
    "0xaac13a116ea7016689993193fce4badc8038136f",
    # DFX Snapshot Staking
    "0xb77684c5a62464c5fb0d9478efe629e94ef8d3ed",
    "0xe690e93fd96b2b8d1cdecde5f08422f3dd82e164",
    "0xbe71372995e8e920e4e72a29a51463677a302e8d",
    "0x3ac91a7a2d30fa25ada4616d337a28ea988988be",
]

STAKING_TOKEN = {
    # Airswap DAO Staking
    # Vote Escrow Contract
    "0xa4c5107184a88d4b324dd10d98a11dd8037823fe": {
        "address": "0x27054b13b1B798B345b591a4d22e6562d47eA75a".lower(),
        "decimal": 4,
        "blockNumber": 4352086,
    },
    "0x704c5818b574358dfb5225563852639151a943ec": {
        "address": "0x27054b13b1B798B345b591a4d22e6562d47eA75a".lower(),
        "decimal": 4,
        "blockNumber": 4352086,
    },
    "0x579120871266ccd8de6c85ef59e2ff6743e7cd15": {
        "address": "0x27054b13b1B798B345b591a4d22e6562d47eA75a".lower(),
        "decimal": 4,
        "blockNumber": 4352086,
    },
    "0x6d88b09805b90dad911e5c5a512eedd984d6860b": {
        "address": "0x27054b13b1B798B345b591a4d22e6562d47eA75a".lower(),
        "decimal": 4,
        "blockNumber": 4352086,
    },
    "0x9fc450f9afe2833eb44f9a1369ab3678d3929860": {
        "address": "0x27054b13b1B798B345b591a4d22e6562d47eA75a".lower(),
        "decimal": 4,
        "blockNumber": 4352086,
    },
    # Autonolas DAO Staking
    # Vote Escrow Contract
    "0x7e01a500805f8a52fad229b3015ad130a332b7b3": {
        "address": "0x0001A500A6B18995B03f44bb040A5fFc28E45CB0".lower(),
        "decimal": 18,
        "blockNumber": 15049891,
    },
    # BPT DAO Staking
    # Vote Escrow Contract
    "0x19886a88047350482990d4edd0c1b863646ab921": {
        "address": "0x0eC9F76202a7061eB9b3a7D6B59D36215A7e37da".lower(),
        "decimal": 18,
        "blockNumber": 12518864,
    },
    # CRYO DAO Staking
    # Token Staking Contract
    "0xf5bdfee7910c561606e6a19bbf0319238a6a2340": {
        "address": "0xf4308b0263723b121056938c2172868E408079D0".lower(),
        "decimal": 18,
        "blockNumber": 17137838,
    },
    # veCRV DAO Staking
    "0x5f3b5dfeb7b28cdbd7faba78963ee202a494e2a2": {
        "address": "0xD533a949740bb3306d119CC777fa900bA034cd52".lower(),
        "decimal": 18,
        "blockNumber": 10647806,
    },
    # DHT DAO Staking
    "0xee1b6b93733ee8ba77f558f8a87480349bd81f7f": {
        "address": "0xca1207647Ff814039530D7d35df0e1Dd2e91Fa84".lower(),
        "decimal": 18,
        "blockNumber": 10833180,
    },
    # MTA DAO Staking
    "0xae8bc96da4f9a9613c323478be181fdb2aa0e1bf": {
        "address": "0xa3BeD4E1c75D00fa6f4E5E6922DB7261B5E9AcD2".lower(),
        "decimal": 18,
        "blockNumber": 10450640,
    },
    # PICKLE C DAO Staking
    # LP Staking Contract + Token Staking Contract
    "0x47b7b0983bf3b1d8d5b773006809edcb208af191": {
        "address": "0xdc98556Ce24f007A5eF6dC1CE96322d65832A819".lower(),
        "decimal": 18,
        "blockNumber": 10830545,
    },
    "0xbbcf169ee191a1ba7371f30a1c344bfc498b29cf": {
        "address": "0x429881672B9AE42b8EbA0E26cD9C73711b891Ca5".lower(),
        "decimal": 18,
        "blockNumber": 10830521,
    },
    # PRISMA DAO Staking
    # Token Staking Contract
    "0xea3030b900d94ed36e5a4e8b15b1db76530acc56": {
        "address": "0xdA47862a83dac0c112BA89c6abC2159b95afd71C".lower(),
        "decimal": 18,
        "blockNumber": 18029878,
    },
    "0x3f78544364c3eccdce4d9c89a630aea26122829d": {
        "address": "0xdA47862a83dac0c112BA89c6abC2159b95afd71C".lower(),
        "decimal": 18,
        "blockNumber": 18029878,
    },
    # Silo Snapshot Staking
    "0xce3d2e0331d6776c79f329140d7ace2e94b168a4": {
        "address": "0x6f80310CA7F2C654691D1383149Fa1A57d8AB1f8".lower(),
        "decimal": 18,
        "blockNumber": 13716347,
    },
    # SDT DAO Staking
    "0x0c30476f66034e11782938df8e4384970b6c9e8a": {
        "address": "0x73968b9a57c6E53d41345FD57a6E6ae27d6CDB2F".lower(),
        "decimal": 18,
        "blockNumber": 11691867,
    },
    # SIS DAO Staking
    "0x7d4ce4c6d2e71d7bed4596f809b81fba0be42258": {
        "address": "0xd38BB40815d2B0c2d2c866e0c72c5728ffC76dd9".lower(),
        "decimal": 18,
        "blockNumber": 13641309,
    },
    # LIT DAO Voting Escrow (LP)
    "0xf17d23136b4fead139f54fb766c8795faae09660": {
        "address": "0x9232a548DD9E81BaC65500b5e0d918F8Ba93675C".lower(),
        "decimal": 18,
        "blockNumber": 16344914,
    },
    # BAL DAO Voting Escrow (LP)
    "0xc128a9954e6c874ea3d62ce62b468ba073093f25": {
        "address": "0x5c6Ee304399DBdB9C8Ef030aB642B10820DB8F56".lower(),
        "decimal": 18,
        "blockNumber": 12369384,
    },
    # BEND DAP VOTING ESCROW
    "0xd7e97172c2419566839bf80deea46d22b1b2e06e": {
        "address": "0x0d02755a5700414B26FF040e1dE35D337DF56218".lower(),
        "decimal": 18,
        "blockNumber": 14415232,
    },
    # APW DAO VOTING ESCROW
    "0xc5ca1ebf6e912e49a6a70bb0385ea065061a4f09": {
        "address": "0x4104b135DBC9609Fc1A9490E61369036497660c8".lower(),
        "decimal": 18,
        "blockNumber": 12451111,
    },
    # MOONEY DAO VOTING ESCROW
    "0xcc71c80d803381fd6ee984faff408f8501db1740": {
        "address": "0x20d4DB1946859E2Adb0e5ACC2eac58047aD41395".lower(),
        "decimal": 18,
        "blockNumber": 13826037,
    },
}

space_labal_dict = {
    # Lending
    "aavedao.eth": "aave",
    # DEX
    "vote.airswap.eth": "airswap",  # missing
    # Staking AI
    "alphakekai.eth": "AlphaKEK.AI",
    # Staking Wallet
    "ambire.eth": "ambire",
    # Staking Stablecoin
    "ampleforthorg.eth": "ampleforth",
    # AI
    "arc.market": "arc",  # equal
    # Token Offchain
    "assangedao.eth": "assangedao",
    # Token AI
    "autonolas.eth": "autonolas",
    # Token (Only)
    "aventus-gov.eth": "avt",  # equal
    # Token (Only?)
    "banklessvault.eth": "bankless dao",
    # Staking
    "blackpoolhq.eth": "blackpool",
    # Token (Only)
    "bobacatdao.eth": "BobaCat",
    # Token (Only)
    "2720.eth": "Buddha",  # equal
    # Chain
    "clvorg.eth": "clover",
    # Token AI
    "cvp.eth": "powerpool.finance",
    # Token (Only)
    "people-dao.eth": "constitutiondao",
    # Token (Only)
    "vote.cryodao.eth": "CryoDAO",
    # DEX + Lending
    "curve.eth": "curve",
}

# Discussion Forum
SHUT_DOWN = [
    "prismafinance.eth",
    "primexyz.eth",
    "poolpool.pooltogether.eth",
    "rook.eth",
    "tomoondao.eth",
    "cvp.eth",
    "phonon.eth",
    "freerossdao.eth",
    "hapione.eth",
    "yam.eth",
    "rarible.eth",
    "vote.airswap.eth",
    "banklessvault.eth",
    "synthereum.eth",
    "mstablegovernance.eth",
    "pickle.eth",
    "pooltogether.eth",
]
DISCORD = [
    "baconcoin.eth",
    "vote.cryodao.eth",
    "vote.turbocouncil.eth",
    "aviator-dao.eth",
    "researchhub.eth",
    "fyde.eth",
    "guildfiworld.eth",
    "dopdao.eth",
    "clvorg.eth",
    "ownthedoge.eth",
    "holographxyz.eth",
    "autonolas.eth",
]
TELEGRAM = ["bobacatdao.eth", "ambire.eth", "mdt.eth"]
GITHUB = ["hbot-prp.eth"]

OTHERS = ["mixin-autonomous-organization.eth", "merchminter.eth", "alphakekai.eth"]
SPECIAL = {
    "https://forum.ampleforth.org/t/deploy-unused-dao-ampl-into-rotation-vault": "815",
    "https://forum.ampleforth.org/t/geyser-refresh-for-q3-2025": "857",
    "https://forum.ampleforth.org/t/proposal-to-compensate-bill-broker-lps-for-impermanent-loss-during-fee-curve-transition/": "863",
    "https://forum.nftx.org/t/xip-32-2023-treasury-mgmt-lp-position-experiment": "558",
    "https://gov.stakedao.org/t/sdir-19-add-apw-ll-to-the-sdt-gauge": "738",
    "https://gov.perp.fi/t/proposal-for-compensation-for-flash-crash-of-18th-april/419?u=tongnk": "419",
}
