import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from mediacloud.api import SearchApi
from main import get_truthfulness_score

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define planets in order of truth value (lowest to highest)
PLANETS = [
    "☀️ Sun",
    "☿️ Mercury", 
    "♀️ Venus",
    "🌍 Earth",
    "♂️ Mars",
    "♃ Jupiter",
    "♄ Saturn",
    "♅ Uranus",
    "☆ Neptune"
]

# Cache for MediaCloud results
_mediacloud_cache = {}
CACHE_TTL_SECONDS = 3600


class MediaCloudCollector:
    """Handles MediaCloud API interactions for finding similar articles."""
    
    def __init__(self, api_key: str):
        """Initialize MediaCloud API client with authentication."""
        if not api_key:
            raise ValueError("MediaCloud API key is required")
        
        self.api_key = api_key
        self.mc = SearchApi(api_key)
        logger.info("MediaCloud API client initialized")
    
    def search_articles(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search for articles using MediaCloud API.
        
        Args:
            query: Search query string (article title or keywords)
            limit: Maximum number of articles to return
            
        Returns:
            List of article dictionaries with metadata
        """
        try:
            # Check cache first
            cache_key = f"{query}_{limit}"
            cached_result = self._check_cache(cache_key)
            if cached_result:
                logger.info(f"Returning cached results for query: {query}")
                return cached_result
            
            # Search MediaCloud for articles
            logger.info(f"Searching MediaCloud for: {query}")
            
            # Use story_list to search for articles
            # MediaCloud expects specific date ranges, so we'll search recent articles
            end_date = datetime.now().date()
            start_date = (datetime.now() - timedelta(days=30)).date()  # Last 30 days
            
            stories_list, pagination_token = self.mc.story_list(
                query=query,
                start_date=start_date,
                end_date=end_date,
                page_size=limit
            )
            
            articles = []
            if stories_list:
                # Enhanced relevance scoring for better keyword matching
                scored_articles = []
                
                for story in stories_list:
                    article_data = self.get_article_metadata(story)
                    if article_data:
                        relevance_score = self._calculate_relevance_score(article_data, query)
                        scored_articles.append((article_data, relevance_score))
                
                # Sort by relevance score (highest first) and extract articles
                # Don't filter - just prioritize relevant articles at the top
                scored_articles.sort(key=lambda x: x[1], reverse=True)
                articles = [article for article, score in scored_articles]
            
            # Cache the results
            self._store_cache(cache_key, articles)
            
            logger.info(f"Found {len(articles)} articles for query: {query}")
            return articles
            
        except Exception as e:
            logger.error(f"Error searching MediaCloud: {e}")
            return []
    
    def get_article_metadata(self, article_data: Dict) -> Optional[Dict]:
        """
        Extract relevant metadata from MediaCloud article data.
        
        Args:
            article_data: Raw article data from MediaCloud API
            
        Returns:
            Dictionary with standardized article metadata
        """
        try:
            # Extract key fields from MediaCloud story data
            metadata = {
                'title': article_data.get('title', ''),
                'url': article_data.get('url', ''),
                'domain': article_data.get('media_name', ''),
                'publish_date': article_data.get('publish_date', ''),
                'id': article_data.get('id', ''),
                'indexed_date': article_data.get('indexed_date', ''),
                'language': article_data.get('language', ''),
                'media_url': article_data.get('media_url', ''),
                'raw_mediacloud_data': article_data
            }
            
            # Validate required fields
            if not metadata['title'] or not metadata['url']:
                logger.warning(f"Skipping article with missing title or URL: {metadata}")
                return None
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting article metadata: {e}")
            return None
    
    def _check_cache(self, cache_key: str) -> Optional[List[Dict]]:
        """Check if MediaCloud results exist in cache and are not expired."""
        if cache_key in _mediacloud_cache:
            result, timestamp = _mediacloud_cache[cache_key]
            
            if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL_SECONDS):
                return result
            else:
                del _mediacloud_cache[cache_key]
        
        return None
    
    def _store_cache(self, cache_key: str, result: List[Dict]):
        """Store MediaCloud results in cache with timestamp."""
        _mediacloud_cache[cache_key] = (result, datetime.now())
    
    def _calculate_relevance_score(self, article_data: Dict, query: str) -> float:
        """
        Calculate relevance score based on keyword matching.
        Balanced approach - not too strict but prioritizes relevant articles.
        """
        title = article_data.get('title', '').lower()
        query_words = [word.lower().strip() for word in query.split() if len(word.strip()) > 2]
        
        if not query_words:
            return 1.0  # Default score if no meaningful query words
        
        score = 1.0  # Base score for all articles
        
        # Check for keyword matches in title
        title_matches = 0
        for word in query_words:
            if word in title:
                title_matches += 1
                score += 3.0  # Good bonus for each keyword match
        
        # Extra bonus for exact phrase matches
        if len(query_words) > 1 and query.lower() in title:
            score += 8.0  # Strong bonus for exact phrase
        
        # Bonus for multiple word matches (indicates topical relevance)
        if title_matches > 1:
            score += title_matches * 1.5
        
        # Check for related terms to expand relevance
        related_terms = self._get_related_terms(query.lower())
        for term in related_terms:
            if term in title:
                score += 1.0  # Small bonus for related terms
        
        # Small penalty for very long titles (usually less focused)
        title_word_count = len(title.split())
        if title_word_count > 20:
            score -= 0.5
        
        # Small bonus for focused titles with matches
        if 5 <= title_word_count <= 15 and title_matches > 0:
            score += 1.0
        
        return score
    
    def _get_related_terms(self, query: str) -> List[str]:
        """Get semantically related terms for better matching."""
        # Simple related terms mapping for common topics
        related_map = {
            'climate change': ['global warming', 'greenhouse', 'carbon', 'emissions', 'temperature', 'weather', 'environment'],
            'artificial intelligence': ['ai', 'machine learning', 'neural', 'algorithm', 'automation', 'robot'],
            'covid': ['coronavirus', 'pandemic', 'vaccine', 'virus', 'outbreak', 'health'],
            'election': ['voting', 'ballot', 'candidate', 'campaign', 'poll', 'democracy'],
            'economy': ['economic', 'financial', 'market', 'gdp', 'inflation', 'recession', 'business'],
            'technology': ['tech', 'digital', 'software', 'innovation', 'startup', 'computer'],
            'health': ['medical', 'healthcare', 'disease', 'treatment', 'hospital', 'medicine'],
            'energy': ['power', 'electricity', 'renewable', 'solar', 'wind', 'oil', 'gas', 'fuel']
        }
        
        related_terms = []
        for key, terms in related_map.items():
            if key in query:
                related_terms.extend(terms)
        
        return related_terms
    
    def _calculate_relevance_score(self, article_data: Dict, query: str) -> float:
        """
        Calculate relevance score based on keyword matching in title and content.
        Higher score = more relevant to the search query.
        """
        title = article_data.get('title', '').lower()
        query_words = [word.lower().strip() for word in query.split() if len(word.strip()) > 2]
        
        if not query_words:
            return 0.0
        
        score = 0.0
        
        # Title matching (weighted heavily)
        title_matches = 0
        for word in query_words:
            if word in title:
                title_matches += 1
                # Bonus for exact phrase matches
                if len(query_words) > 1 and query.lower() in title:
                    score += 10.0
        
        # Score based on percentage of query words found in title
        title_coverage = title_matches / len(query_words)
        score += title_coverage * 20.0  # Up to 20 points for full title coverage
        
        # Bonus for multiple word matches
        if title_matches > 1:
            score += title_matches * 2.0
        
        # Penalty for very long titles (likely less focused)
        title_word_count = len(title.split())
        if title_word_count > 15:
            score -= 2.0
        
        # Bonus for shorter, more focused titles
        if title_word_count <= 10 and title_matches > 0:
            score += 3.0
        
        return score


def analyze_articles_by_planet(query: str, articles_per_planet: int = 1) -> Dict[str, Any]:
    """
    Search MediaCloud for articles, score them with credibility analyzer,
    and group results by planet-based credibility ratings.
    
    Args:
        query: Search query string (article title or keywords)
        articles_per_planet: Maximum number of articles to show per planet
        
    Returns:
        Dictionary with articles grouped by planet and metadata
    """
    try:
        # Get MediaCloud API key from environment
        api_key = os.getenv('MEDIACLOUD_API_KEY')
        if not api_key:
            logger.error("MEDIACLOUD_API_KEY environment variable not set")
            return {
                'error': 'MediaCloud API key not configured',
                'query': query,
                'results_by_planet': {},
                'total_articles': 0,
                'cache_hit': False
            }
        
        # Initialize MediaCloud collector
        collector = MediaCloudCollector(api_key)
        
        # Search for articles (reduced limit for faster processing)
        articles = collector.search_articles(query, limit=20)
        
        if not articles:
            return {
                'query': query,
                'results_by_planet': {},
                'total_articles': 0,
                'cache_hit': False,
                'message': 'No articles found for the given query'
            }
        
        # Score articles and group by planet
        results_by_planet = {planet: [] for planet in PLANETS}
        total_processed = 0
        
        # Process articles until we have enough for each planet or run out
        for i, article in enumerate(articles):
            try:
                # Skip if we already have enough articles
                if total_processed >= articles_per_planet * len(PLANETS):
                    break
                    
                # Get credibility score for the article
                url = article['url']
                logger.info(f"Analyzing article {i+1}/{len(articles)}: {article['title'][:50]}...")
                credibility_result = get_truthfulness_score(url)
                
                if 'error' in credibility_result:
                    logger.warning(f"Failed to analyze article {url}: {credibility_result['error']}")
                    continue
                
                # Combine article metadata with credibility scores
                article_result = {
                    'title': article['title'],
                    'url': article['url'],
                    'domain': article['domain'],
                    'publish_date': article['publish_date'],
                    'credibility_score': credibility_result['score'],
                    'fake_news_score': credibility_result['fake_news_score'],
                    'sarcasm_score': credibility_result['sarcasm_score'],
                    'planet': credibility_result['planet'],
                    'analysis_timestamp': datetime.now().isoformat(),
                    'raw_data': article['raw_mediacloud_data']
                }
                
                # Add to appropriate planet group if there's space
                planet = credibility_result['planet']
                if len(results_by_planet[planet]) < articles_per_planet:
                    results_by_planet[planet].append(article_result)
                    total_processed += 1
                
            except Exception as e:
                logger.error(f"Error processing article {article.get('url', 'unknown')}: {e}")
                continue
        
        # Remove empty planet groups
        results_by_planet = {
            planet: articles for planet, articles in results_by_planet.items() 
            if articles
        }
        
        return {
            'query': query,
            'results_by_planet': results_by_planet,
            'total_articles': total_processed,
            'articles_per_planet_limit': articles_per_planet,
            'search_timestamp': datetime.now().isoformat(),
            'cache_hit': False  # This would be set to True if we implement query-level caching
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_articles_by_planet: {e}")
        return {
            'error': str(e),
            'query': query,
            'results_by_planet': {},
            'total_articles': 0,
            'cache_hit': False
        }