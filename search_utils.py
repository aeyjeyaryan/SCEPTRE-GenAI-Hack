import os
import re
import logging
import asyncio
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from cachetools import TTLCache
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk

# Configure logging
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('stopwords', quiet=True)
except Exception as e:
    logger.error(f"Error downloading NLTK data: {e}")

# Environment variables
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
if not all([GOOGLE_API_KEY, GOOGLE_CSE_ID]):
    raise ValueError("Missing required environment variables: GOOGLE_API_KEY or GOOGLE_CSE_ID")

# Cache for search results (TTL: 1 hour)
search_cache = TTLCache(maxsize=100, ttl=3600)

# Data models
class Document(BaseModel):
    title: str
    snippet: str
    url: str
    content: str
    relevance_score: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("url")
    def validate_url(cls, v):
        if not re.match(r'^https?://', v):
            raise ValueError("Invalid URL format")
        return v

class SearchQuery(BaseModel):
    query: str = Field(..., description="Search query to find documents", min_length=1, max_length=500)

class SearchResults(BaseModel):
    status: str
    query: str
    results: list[Document]

def preprocess_query(query: str) -> str:
    """Preprocess the query by removing stopwords and normalizing."""
    try:
        query = query.lower().strip()
        query = re.sub(r'[^\w\s]', '', query)
        tokens = word_tokenize(query)
        stop_words = set(stopwords.words('english'))
        tokens = [token for token in tokens if token not in stop_words]
        return ' '.join(tokens)
    except Exception as e:
        logger.error(f"Error preprocessing query: {e}")
        return query

def filter_trusted_sources(results: list[dict]) -> list[dict]:
    """Filter and score search results based on domain trustworthiness."""
    trusted_domains = {'.edu', '.gov', '.org', '.news'}
    for result in results:
        url = result.get('url', '')
        score = 0.5
        if any(domain in url for domain in trusted_domains):
            score += 0.3
        if 'wikipedia.org' in url or 'reddit.com' in url:
            score -= 0.2
        result['relevance_score'] = min(max(score, 0.0), 1.0)
    return sorted(results, key=lambda x: x['relevance_score'], reverse=True)

async def google_custom_search(query: str, num_results: int = 10) -> list[dict]:
    """Query Google Custom Search API with caching."""
    cache_key = f"search:{query}:{num_results}"
    if cache_key in search_cache:
        return search_cache[cache_key]
    
    try:
        processed_query = preprocess_query(query)
        url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CSE_ID}&q={processed_query}&num={num_results}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            results = response.json().get('items', [])
            processed_results = [
                {
                    'title': item.get('title'),
                    'snippet': item.get('snippet'),
                    'url': item.get('link')
                } for item in results
            ]
            filtered_results = filter_trusted_sources(processed_results)
            search_cache[cache_key] = filtered_results
            return filtered_results
    except Exception as e:
        logger.error(f"Error querying Google Custom Search API: {e}")
        return []

async def fetch_document_content(url: str) -> str:
    """Fetch full content from a URL asynchronously, following redirects."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        async with httpx.AsyncClient(follow_redirects=True) as client:  # Enable redirect following
            response = await client.get(url, headers=headers, timeout=5)
            response.raise_for_status()  # Raise an exception for bad status codes after following redirects
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            content = ' '.join([para.get_text().strip() for para in paragraphs])
            return content
    except httpx.HTTPStatusError as e:
        logger.error(f"Error fetching content from {url}: {e.response.status_code} {e.response.reason_phrase} for url '{e.request.url}'")
        if e.response.status_code in (301, 302):
            logger.error(f"Redirect location: '{e.response.headers.get('Location', 'Unknown')}'")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error fetching content from {url}: {str(e)}")
        return ""

async def search_documents(query: str) -> SearchResults:
    """Search for documents using Google Custom Search API."""
    try:
        search_results = await google_custom_search(query, num_results=5)
        documents = []
        
        async def fetch_content(result):
            content = await fetch_document_content(result['url'])
            if content:
                return Document(
                    title=result['title'],
                    snippet=result['snippet'],
                    url=result['url'],
                    content=content,
                    relevance_score=result.get('relevance_score', 0.5)
                )
            return None
        
        tasks = [fetch_content(result) for result in search_results]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        documents = [doc for doc in results if doc and not isinstance(doc, Exception)]
        
        return SearchResults(
            status="success" if documents else "no_results",
            query=query,
            results=documents
        )
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return SearchResults(status="error", query=query, results=[])