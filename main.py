import torch
import requests
from bs4 import BeautifulSoup
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from urllib.parse import urlparse

# Load model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("Pulk17/Fake-News-Detection")
model = AutoModelForSequenceClassification.from_pretrained("Pulk17/Fake-News-Detection")

# Define planets in order of truth value (highest to lowest)
PLANETS = [
    "☆ Neptune",
    "♅ Uranus",
    "♄ Saturn",
    "♃ Jupiter",
    "♂️ Mars",
    "🌍 Earth",
    "♀️ Venus",
    "☿️ Mercury",
    "☀️ Sun"
]

def extract_article_text(url: str) -> str:
    """
    Extracts article text from a URL.
    
    Args:
        url: The URL of the news article
        
    Returns:
        str: The extracted article text
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Extract text from common article elements
    article_text = ""
    for tag in soup.find_all(['article', 'main', 'div']):
        if tag.get('class') and any(cls in str(tag.get('class')).lower() for cls in ['content', 'article', 'post', 'body']):
            article_text = tag.get_text()
            break
    
    # Fallback to all paragraph text if no article container found
    if not article_text:
        paragraphs = soup.find_all('p')
        article_text = '\n'.join([p.get_text() for p in paragraphs])
    
    # Clean up whitespace
    article_text = ' '.join(article_text.split())
    
    return article_text

def get_truthfulness_score(article_input: str) -> dict:
    """
    Analyzes an article and returns a truthfulness score (0.0-1.0) 
    and corresponding planet rating.
    
    Args:
        article_input: Either the article content or a URL to an article
        
    Returns:
        dict with keys: 'score', 'planet', 'label', 'source'
    """
    # Check if input is a URL
    if article_input.startswith('http://') or article_input.startswith('https://'):
        try:
            article_text = extract_article_text(article_input)
            source = "URL"
        except Exception as e:
            return {
                'error': f"Failed to fetch article from URL: {str(e)}",
                'score': None,
                'planet': None,
                'label': None
            }
    else:
        article_text = article_input
        source = "Text"
    # Tokenize the input
    inputs = tokenizer(article_text, return_tensors="pt", truncation=True, 
                      max_length=512, padding=True)
    
    # Get model predictions
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Apply softmax to get probabilities
    probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
    
    # The model outputs [fake, real] probabilities
    # We'll use the "real" probability (index 1) as our truth score
    truth_score = probabilities[0][1].item()
    
    # Map score to planet (0.0-1.0 maps to index 0-8)
    planet_index = min(int(truth_score * len(PLANETS)), len(PLANETS) - 1)
    planet = PLANETS[planet_index]
    
    # Get the label (fake or real)
    predicted_label = "Real" if truth_score > 0.5 else "Fake"
    
    return {
        'score': round(truth_score, 4),
        'planet': planet,
        'label': predicted_label,
        'confidence': round(max(probabilities[0].tolist()), 4)
    }

# Example usage
if __name__ == "__main__":
    # Test article
    test_article = """
    Scientists have discovered a new species of deep-sea fish in the Mariana Trench.
    The fish, which was found at a depth of 10,000 meters, exhibits bioluminescent 
    properties and has been named after the research vessel that discovered it.
    """
    
    result = get_truthfulness_score(test_article)
    
    print(f"Article Truth Score: {result['score']}")
    print(f"Planet Rating: {result['planet']}")
    print(f"Label: {result['label']}")
    print(f"Confidence: {result['confidence']}")
    
    # You can also analyze multiple articles
    print("\n" + "="*50 + "\n")
    
    articles = [
        "The earth is flat and NASA is lying to us.",
        "Water boils at 100 degrees Celsius at sea level.",
        "Drinking bleach cures all diseases."
    ]
    
    for i, article in enumerate(articles, 1):
        result = get_truthfulness_score(article)
        print(f"Article {i}:")
        print(f"  Score: {result['score']} - {result['planet']}")
        print(f"  Label: {result['label']}")
        print()