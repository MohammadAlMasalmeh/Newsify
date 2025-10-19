// Celestial Fake News Detection Frontend JavaScript

const API_BASE_URL = 'http://localhost:8001';

// Solar System Scale - matches main.py PLANETS array exactly
const PLANETS_FROM_BACKEND = [
    { name: 'Sun', description: 'Highly Trustworthy' },
    { name: 'Mercury', description: 'Very Trustworthy' },
    { name: 'Venus', description: 'Very Trustworthy' },
    { name: 'Earth', description: 'Trustworthy' },
    { name: 'Mars', description: 'Moderately Trustworthy' },
    { name: 'Jupiter', description: 'Questionable' },
    { name: 'Saturn', description: 'Questionable' },
    { name: 'Uranus', description: 'Likely Unreliable' },
    { name: 'Neptune', description: 'Unreliable' }
];

// Get celestial body based on backend's planet mapping
function getCelestialBodyFromBackend(backendResult) {
    // Extract planet name from backend result (e.g., "☀️ Sun" -> "Sun")
    const planetText = backendResult.planet || "☀️ Sun";
    const planetName = planetText.replace(/^[^\w\s]*\s*/, ''); // Remove emoji and spaces
    
    // Find matching planet in our array
    const planet = PLANETS_FROM_BACKEND.find(p => p.name === planetName) || PLANETS_FROM_BACKEND[0];
    
    return {
        name: planet.name,
        description: planet.description
    };
}

// Analyze URL function
async function analyzeURL() {
    const urlInput = document.getElementById('news-url');
    const url = urlInput.value.trim();
    
    if (!url) {
        showError('Please enter a URL to analyze.');
        return;
    }
    
    if (!isValidURL(url)) {
        showError('Please enter a valid URL (e.g., https://example.com/article).');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/predict-url`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to analyze URL');
        }
        
        const result = await response.json();
        showResult(result, true);
        
    } catch (error) {
        showError(`Analysis failed: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Show loading state
function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('result-section').style.display = 'none';
    document.getElementById('error-message').style.display = 'none';
}

// Hide loading state
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

// Show result with 3D celestial objects
function showResult(result, isURL = false) {
    const resultSection = document.getElementById('result-section');
    const resultLabel = document.getElementById('result-label');
    const bodyIcon = document.getElementById('body-icon');
    const bodyName = document.getElementById('body-name');
    const reliabilityDescription = document.getElementById('reliability-description');
    const confidenceFill = document.getElementById('confidence-fill');
    const confidenceScore = document.getElementById('confidence-score');
    const extractedText = document.getElementById('extracted-text');
    const extractedContent = document.getElementById('extracted-content');
    
    // Get celestial body from backend result
    const celestialBody = getCelestialBodyFromBackend(result);
    
    // Create 3D celestial object
    const planetName = celestialBody.name.toLowerCase();
    bodyIcon.className = `body-icon ${planetName}`;
    bodyIcon.textContent = ''; // Remove emoji, use CSS 3D object
    
    // Set planet name and description
    bodyName.textContent = celestialBody.name;
    reliabilityDescription.textContent = celestialBody.description;
    
    // Set classification result
    resultLabel.textContent = result.label;
    resultLabel.className = `result-label ${result.label.toLowerCase()}`;
    
    // Set confidence bar
    const confidencePercent = (result.score * 100).toFixed(1);
    confidenceFill.style.width = `${confidencePercent}%`;
    confidenceScore.textContent = `${confidencePercent}%`;
    
    // Color the confidence bar based on planet
    const planetColors = {
        'sun': 'linear-gradient(90deg, #ffeb3b, #ff9800)',
        'mercury': 'linear-gradient(90deg, #8d6e63, #5d4037)',
        'venus': 'linear-gradient(90deg, #ffc107, #ff8f00)',
        'earth': 'linear-gradient(90deg, #2196f3, #4caf50)',
        'mars': 'linear-gradient(90deg, #f44336, #d32f2f)',
        'jupiter': 'linear-gradient(90deg, #ff9800, #f57c00)',
        'saturn': 'linear-gradient(90deg, #ffc107, #ff8f00)',
        'uranus': 'linear-gradient(90deg, #00bcd4, #0097a7)',
        'neptune': 'linear-gradient(90deg, #3f51b5, #303f9f)'
    };
    
    confidenceFill.style.background = planetColors[planetName] || planetColors['sun'];
    
    // Show extracted text if it's a URL analysis
    if (isURL && result.extracted_text) {
        extractedContent.textContent = result.extracted_text;
        extractedText.style.display = 'block';
    } else {
        extractedText.style.display = 'none';
    }
    
    // Show result section
    resultSection.style.display = 'block';
    
    // Scroll to result
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

// Show error message
function showError(message) {
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    
    errorText.textContent = message;
    errorMessage.style.display = 'block';
    
    // Hide after 5 seconds
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
    
    // Scroll to error
    errorMessage.scrollIntoView({ behavior: 'smooth' });
}

// Validate URL
function isValidURL(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// Add enter key support for URL input
document.getElementById('news-url').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        analyzeURL();
    }
});

// Add some cosmic interactions
document.addEventListener('mousemove', function(e) {
    const stars = document.querySelector('.stars');
    const x = e.clientX / window.innerWidth;
    const y = e.clientY / window.innerHeight;
    
    stars.style.transform = `translate(${x * 10}px, ${y * 10}px)`;
});

// Add click effect to buttons
document.querySelectorAll('button').forEach(button => {
    button.addEventListener('click', function(e) {
        const ripple = document.createElement('span');
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple');
        
        this.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    });
});

// Add ripple effect CSS
const style = document.createElement('style');
style.textContent = `
    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }
    
    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);