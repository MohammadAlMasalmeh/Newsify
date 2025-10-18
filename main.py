import torch
import requests
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from urllib.parse import urlparse
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define planets in order of truth value (lowest to highest)
# 0.0 (real) = Sun, 1.0 (fake) = Neptune
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

# Global variables for model and tokenizer (singleton pattern)
_tokenizer = None
_model = None
_satire_tokenizer = None
_satire_model = None
_device = None

# Cache with TTL
_cache = {}
CACHE_TTL_SECONDS = 3600

# Removed SATIRE_PUBLISHERS - relying purely on AI model classification


def initialize_model():
    """
    Lazy load and initialize the models once using singleton pattern.
    """
    global _tokenizer, _model, _satire_tokenizer, _satire_model, _device
    
    if _model is None:
        logger.info("Initializing fake news detection model...")
        
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {_device}")
        
        _tokenizer = AutoTokenizer.from_pretrained("mrm8488/bert-tiny-finetuned-fake-news-detection")
        _model = AutoModelForSequenceClassification.from_pretrained("mrm8488/bert-tiny-finetuned-fake-news-detection")
        _model.to(_device)
        logger.info("Fake news model loaded successfully")
    
    if _satire_model is None:
        logger.info("Initializing sarcasm detection model...")
        
        try:
            _satire_tokenizer = AutoTokenizer.from_pretrained("helinivan/english-sarcasm-detector")
            _satire_model = AutoModelForSequenceClassification.from_pretrained("helinivan/english-sarcasm-detector")
            _satire_model.to(_device)
            logger.info("Sarcasm model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load sarcasm model: {str(e)}")
            _satire_model = None
            _satire_tokenizer = None


def extract_article_text(url: str) -> Optional[str]:
    """
    Extracts article text from a URL.
    """
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")
        
        logger.info(f"Fetching article from: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        article_text = ""
        for tag in soup.find_all(['article', 'main']):
            article_text = tag.get_text()
            break
        
        if not article_text:
            for tag in soup.find_all('div'):
                if tag.get('class') and any(
                    cls in str(tag.get('class')).lower() 
                    for cls in ['content', 'article', 'post', 'body', 'story']
                ):
                    article_text = tag.get_text()
                    break
        
        if not article_text:
            paragraphs = soup.find_all('p')
            article_text = '\n'.join([p.get_text() for p in paragraphs])
        
        article_text = ' '.join(article_text.split())
        
        if not article_text:
            logger.warning(f"No article text extracted from {url}")
            return None
        
        logger.info(f"Successfully extracted {len(article_text)} characters from article")
        return article_text
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error fetching {url}: {str(e)}")
        return None
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error fetching {url}: {str(e)}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching {url}: {str(e)}")
        return None
    except ValueError as e:
        logger.error(f"Invalid URL: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error extracting article from {url}: {str(e)}")
        return None


def chunk_text(text: str, max_tokens: int = 512) -> list:
    """
    Chunks text into smaller segments for processing.
    """
    chars_per_chunk = max_tokens * 4
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0
    
    for word in words:
        current_length += len(word) + 1
        current_chunk.append(word)
        
        if current_length > chars_per_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_length = 0
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


def get_cache_key(text: str) -> str:
    """Generate cache key from text hash."""
    import hashlib
    return hashlib.md5(text.encode()).hexdigest()


def check_cache(cache_key: str) -> Optional[Dict]:
    """Check if result exists in cache and is not expired."""
    if cache_key in _cache:
        result, timestamp = _cache[cache_key]
        
        if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL_SECONDS):
            logger.info("Cache hit")
            return result
        else:
            del _cache[cache_key]
    
    return None


def store_cache(cache_key: str, result: Dict):
    """Store result in cache with timestamp."""
    _cache[cache_key] = (result, datetime.now())


# Removed satire publisher checking - relying purely on AI model


def get_satire_score(text: str) -> float:
    """
    Detects sarcasm/satire in text.
    """
    if _satire_model is None or _satire_tokenizer is None:
        return 0.0
    
    inputs = _satire_tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True
    )
    
    inputs = {k: v.to(_device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = _satire_model(**inputs)
    
    probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
    sarcasm_score = probabilities[0][1].item()
    
    return sarcasm_score


def get_truthfulness_score(article_input: str) -> Dict[str, Any]:
    """
    Analyzes an article and returns a truthfulness score (0.0-1.0) 
    and corresponding planet rating.
    
    Scoring scale:
    - 0.0 = Real article (maps to Sun)
    - 1.0 = Fake article (maps to Neptune)
    """
    initialize_model()
    
    # Check if input is a URL or direct text
    if article_input.startswith('http://') or article_input.startswith('https://'):
        article_text = extract_article_text(article_input)
        source = "URL"
        
        if article_text is None:
            logger.error(f"Failed to extract article from {article_input}")
            return {
                'error': "Failed to fetch or extract article from URL",
                'score': None,
                'planet': None,
                'label': None,
                'confidence': None,
                'source': "URL"
            }
    else:
        article_text = article_input
        source = "Text"
    
    # Check cache
    cache_key = get_cache_key(article_text)
    cached_result = check_cache(cache_key)
    if cached_result:
        return cached_result
    
    satire_chunks = chunk_text(article_text, max_tokens=512)
    
    # Process full article through fake news model (no chunking)
    inputs = _tokenizer(
        article_text, 
        return_tensors="pt", 
        truncation=True, 
        max_length=512, 
        padding=True
    )
    
    inputs = {k: v.to(_device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = _model(**inputs)
    
    probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
    
    real_probability = probabilities[0][0].item()
    final_fake_score = 1.0 - real_probability
    
    # Check for sarcasm/satire
    logger.info(f"Analyzing article for sarcasm/satire ({len(satire_chunks)} chunk(s))...")
    
    satire_scores = []
    for i, chunk in enumerate(satire_chunks):
        logger.info(f"Processing satire chunk {i+1}/{len(satire_chunks)}")
        sarcasm_chunk_score = get_satire_score(chunk)
        satire_scores.append(sarcasm_chunk_score)
    
    sarcasm_score = max(satire_scores) if satire_scores else 0.0
    
    # Combine scores
    final_score = max(final_fake_score, sarcasm_score)
    
    # Map score to planet
    planet_index = min(int(final_score * len(PLANETS)), len(PLANETS) - 1)
    planet = PLANETS[planet_index]
    
    # Determine label
    predicted_label = "Fake" if final_score > 0.5 else "Real"
    
    # Build result
    result = {
        'score': round(final_score, 4),
        'planet': planet,
        'label': predicted_label,
        'confidence': round(final_score, 4),
        'fake_news_score': round(final_fake_score, 4),
        'sarcasm_score': round(sarcasm_score, 4),
        'source': source,
        'chunks_processed': len(satire_chunks)
    }
    
    # Store in cache
    store_cache(cache_key, result)
    
    return result