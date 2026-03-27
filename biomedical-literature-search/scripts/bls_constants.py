BASE_URL = "https://cada-literature.ir-cadadocs-dev.awscloud.abbvienet.com"

MAX_CONCURRENCY = 50
TIMEOUT = 600
MAX_N_SEARCH = 500
MAX_N_FILTER = 20

MODELS = {
    "filter": "claude-4.5-haiku",
    "summary": "claude-4.5-haiku",
}

ARTICLE_ATTRIBUTES = [
    'title', 'abstract', 'URL', 'pmid', 'pmc_id', 
    'journal', 'publication_date', 'authors', 
    'classification', 'publab_id'
]

FILTER_PROMPT_TEMPLATE = (
    "You are evaluating scientific articles for relevance to a research question.\n\n"
    "RESEARCH QUESTION: {query}\n\n"
    "ADDITIONAL FILTERING CRITERIA: {filter_query}\n\n"
    "Evaluate if this article is relevant based on the research question and filtering criteria."
)

REQUIRED_INPUT_KEYS = ["query", "base_dir"]
