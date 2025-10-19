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


def initialize_model():
    """Lazy load and initialize the models once using singleton pattern."""
    global _tokenizer, _model, _satire_tokenizer, _satire_model, _device
    
    if _model is None:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        
        _tokenizer = AutoTokenizer.from_pretrained("mrm8488/bert-tiny-finetuned-fake-news-detection")
        _model = AutoModelForSequenceClassification.from_pretrained("mrm8488/bert-tiny-finetuned-fake-news-detection")
        _model.to(_device)
    
    if _satire_model is None:
        try:
            _satire_tokenizer = AutoTokenizer.from_pretrained("helinivan/english-sarcasm-detector")
            _satire_model = AutoModelForSequenceClassification.from_pretrained("helinivan/english-sarcasm-detector")
            _satire_model.to(_device)
        except Exception:
            _satire_model = None
            _satire_tokenizer = None


def clean_extracted_text(text: str) -> str:
    """
    Clean up extracted text by removing common noise.
    
    This function filters out UI elements, navigation, and spam content
    while preserving the actual article text.
    """
    import re
    
    # Split into sentences for granular filtering
    sentences = re.split(r'[.!?]+', text)
    cleaned_sentences = []
    
    # Spam keywords to check for (but don't auto-remove entire sentences)
    spam_keywords = ['subscribe', 'newsletter', 'click here', 'sign up', 
                     'follow us', 'copyright', 'all rights reserved']
    
    for sentence in sentences:
        sentence = sentence.strip()
        
        # Skip very short sentences (likely UI fragments like "Home" or "Menu")
        if len(sentence) < 20:
            continue
            
        # Skip sentences that are mostly spam
        sentence_lower = sentence.lower()
        spam_word_count = sum(1 for keyword in spam_keywords if keyword in sentence_lower)
        word_count = len(sentence.split())
        
        # Only skip if >30% of sentence is spam keywords (preserves sentences with occasional spam words)
        if word_count > 0 and (spam_word_count / word_count) < 0.3:
            cleaned_sentences.append(sentence)
    
    return '. '.join(cleaned_sentences)


def extract_article_text(url: str) -> Optional[str]:
    """Extracts article text from a URL with improved cleaning."""
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer", 
                            "aside", "iframe", "noscript", "form", "button"]):
            element.decompose()
        
        # Remove common ad/tracking containers
        for div in soup.find_all(['div', 'section', 'span']):
            try:
                div_class = str(div.get('class', '')).lower() if div else ''
                div_id = str(div.get('id', '')).lower() if div else ''
                if any(keyword in div_class or keyword in div_id 
                       for keyword in ['ad', 'advertisement', 'social', 'share', 
                                      'comment', 'related', 'sidebar', 'menu',
                                      'promo', 'newsletter', 'subscription', 'popup',
                                      'trending', 'recommended', 'widget', 'banner']):
                    div.decompose()
            except (AttributeError, TypeError):
                continue
        
        article_text = ""
        
        # Try to find main article content
        for tag in soup.find_all(['article', 'main']):
            article_text = tag.get_text()
            if article_text:
                break
        
        if not article_text:
            for tag in soup.find_all('div'):
                if tag.get('class') and any(
                    cls in str(tag.get('class')).lower() 
                    for cls in ['content', 'article', 'post', 'body', 'story']
                ):
                    article_text = tag.get_text()
                    if article_text:
                        break
        
        if not article_text:
            paragraphs = soup.find_all('p')
            article_text = '\n'.join([p.get_text() for p in paragraphs])
        
        # Clean and normalize whitespace
        article_text = ' '.join(article_text.split())
        
        # Additional cleaning to remove UI noise
        article_text = clean_extracted_text(article_text)
        
        if not article_text or len(article_text) < 100:
            return None
        
        return article_text
        
    except Exception as e:
        logger.error(f"Error extracting article: {e}")
        return None


def chunk_text(text: str, max_tokens: int = 512) -> list:
    """Chunks text into smaller segments for processing."""
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


def get_middle_chunk(chunks: list) -> str:
    """Get the middle chunk from a list of chunks."""
    if not chunks:
        return ""
    
    middle_index = len(chunks) // 2
    return chunks[middle_index]


def get_cache_key(text: str) -> str:
    """Generate cache key from text hash."""
    import hashlib
    return hashlib.md5(text.encode()).hexdigest()


def check_cache(cache_key: str) -> Optional[Dict]:
    """Check if result exists in cache and is not expired."""
    if cache_key in _cache:
        result, timestamp = _cache[cache_key]
        
        if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL_SECONDS):
            return result
        else:
            del _cache[cache_key]
    
    return None


def store_cache(cache_key: str, result: Dict):
    """Store result in cache with timestamp."""
    _cache[cache_key] = (result, datetime.now())


def get_satire_score(text: str) -> float:
    """Detects sarcasm/satire in text."""
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
    
    KEY FIX: Processes ALL chunks and averages scores to analyze entire article,
    not just first 512 tokens. This ensures consistent results regardless of
    website structure and HTML noise.
    """
    initialize_model()
    
    # Check if input is a URL or direct text
    if article_input.startswith('http://') or article_input.startswith('https://'):
        article_text = extract_article_text(article_input)
        source = "URL"
        
        if article_text is None:
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
    
    # FIXED: Chunk the text and process ALL chunks through fake news detection
    fake_news_chunks = chunk_text(article_text, max_tokens=450)  # Leave room for special tokens
    
    # Process ALL chunks through fake news model and collect scores
    fake_news_scores = []
    for chunk in fake_news_chunks:
        inputs = _tokenizer(
            chunk, 
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
        fake_news_scores.append(1.0 - real_probability)
    
    # Average all chunk scores to get overall fake news score
    final_fake_score = sum(fake_news_scores) / len(fake_news_scores) if fake_news_scores else 0.0
    
    # Check for sarcasm/satire across all chunks
    satire_chunks = chunk_text(article_text, max_tokens=512)
    satire_scores = []
    for chunk in satire_chunks:
        sarcasm_chunk_score = get_satire_score(chunk)
        satire_scores.append(sarcasm_chunk_score)
    
    # Use maximum satire score (if any part is satirical, flag it)
    sarcasm_score = max(satire_scores) if satire_scores else 0.0
    
    # Combine scores: take the maximum of fake news and satire scores
    final_score = max(final_fake_score, sarcasm_score)
    
    # Map score to planet (0.0 = Sun, 1.0 = Neptune)
    planet_index = min(int(final_score * len(PLANETS)), len(PLANETS) - 1)
    planet = PLANETS[planet_index]
    
    # Determine label based on threshold
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
        'chunks_processed': len(fake_news_chunks)
    }
    
    # Store in cache
    store_cache(cache_key, result)
    
    return result