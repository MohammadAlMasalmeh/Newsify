// Celestial Fake News Detection Frontend JavaScript

const API_BASE_URL = 'http://localhost:8001';

// Tab Management
function switchTab(tabName) {
    // Remove active class from all tabs and content
    document.querySelectorAll('.tab-button').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Add active class to selected tab and content
    document.getElementById(`${tabName}-tab`).classList.add('active');
    document.getElementById(`${tabName}-content`).classList.add('active');
    
    // Clear any existing results when switching tabs
    if (tabName === 'analyze') {
        document.getElementById('result-section').style.display = 'none';
    } else if (tabName === 'similar') {
        document.getElementById('similar-results-section').style.display = 'none';
    }
    
    // Hide loading and error states
    document.getElementById('loading').style.display = 'none';
    document.getElementById('error-message').style.display = 'none';
}

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
    const loading = document.getElementById('loading');
    loading.style.display = 'block';
    document.getElementById('result-section').style.display = 'none';
    document.getElementById('similar-results-section').style.display = 'none';
    document.getElementById('error-message').style.display = 'none';
}

// Show loading with custom message
function showLoadingWithMessage(message) {
    const loading = document.getElementById('loading');
    const loadingText = loading.querySelector('p');
    if (loadingText) {
        loadingText.textContent = message;
    }
    loading.style.display = 'block';
    document.getElementById('result-section').style.display = 'none';
    document.getElementById('similar-results-section').style.display = 'none';
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
    
    // Show model breakdown if scores are available
    if (result.fake_news_score !== undefined && result.sarcasm_score !== undefined) {
        showModelBreakdown(result.fake_news_score, result.sarcasm_score);
    }
    

    
    // Show result section
    resultSection.style.display = 'block';
    
    // Scroll to result
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

// Show model breakdown with animated bars
function showModelBreakdown(fakeNewsScore, sarcasmScore) {
    const modelBreakdown = document.getElementById('model-breakdown');
    const fakeNewsFill = document.getElementById('fake-news-fill');
    const fakeNewsValue = document.getElementById('fake-news-value');
    const sarcasmFill = document.getElementById('sarcasm-fill');
    const sarcasmValue = document.getElementById('sarcasm-value');
    
    // Convert scores to percentages
    const fakeNewsPercent = Math.round(fakeNewsScore * 100);
    const sarcasmPercent = Math.round(sarcasmScore * 100);
    
    // Show the breakdown section
    modelBreakdown.style.display = 'block';
    
    // Animate the bars with a slight delay for visual effect
    setTimeout(() => {
        fakeNewsFill.style.width = `${fakeNewsPercent}%`;
        fakeNewsValue.textContent = `${fakeNewsPercent}%`;
        
        sarcasmFill.style.width = `${sarcasmPercent}%`;
        sarcasmValue.textContent = `${sarcasmPercent}%`;
    }, 300);
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

// Similar Articles Search Function
async function searchSimilarArticles() {
    const queryInput = document.getElementById('article-query');
    
    const query = queryInput.value.trim();
    const articlesPerPlanet = 1; // Fixed to 1 article per credibility level
    
    if (!query) {
        showError('Please enter a search query to find similar articles.');
        return;
    }
    
    showLoadingWithMessage('🌌 Searching MediaCloud for similar articles...');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/similar-articles`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                query: query,
                articles_per_planet: articlesPerPlanet
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to search similar articles');
        }
        
        const result = await response.json();
        displayArticlesByPlanet(result);
        
    } catch (error) {
        showError(`Search failed: ${error.message}`);
    } finally {
        hideLoading();
    }
}

// Display Articles Grouped by Planet
function displayArticlesByPlanet(result) {
    const resultsSection = document.getElementById('similar-results-section');
    const searchInfo = document.getElementById('search-info');
    const planetsContainer = document.getElementById('planets-container');
    
    // Update search info
    searchInfo.innerHTML = `
        <div>Query: "<strong>${result.query}</strong>"</div>
        <div>Found ${result.total_articles} articles across ${Object.keys(result.results_by_planet).length} credibility levels</div>
    `;
    
    // Clear previous results
    planetsContainer.innerHTML = '';
    
    if (result.total_articles === 0) {
        planetsContainer.innerHTML = `
            <div class="no-results">
                <div class="no-results-icon">🌌</div>
                <h3>No Articles Found</h3>
                <p>${result.message || 'Try a different search query or check your MediaCloud API configuration.'}</p>
            </div>
        `;
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
        return;
    }
    
    // Create planet groups
    const planetOrder = [
        '☀️ Sun', '☿️ Mercury', '♀️ Venus', '🌍 Earth', 
        '♂️ Mars', '♃ Jupiter', '♄ Saturn', '♅ Uranus', '☆ Neptune'
    ];
    
    planetOrder.forEach(planetKey => {
        const articles = result.results_by_planet[planetKey];
        if (!articles || articles.length === 0) return;
        
        const planetGroup = createPlanetGroup(planetKey, articles);
        planetsContainer.appendChild(planetGroup);
    });
    
    // Show results section
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Create Planet Group Element
function createPlanetGroup(planetKey, articles) {
    const planetGroup = document.createElement('div');
    planetGroup.className = 'planet-group';
    
    // Extract planet name and get credibility info
    const planetName = planetKey.replace(/^[^\w\s]*\s*/, '');
    const celestialBody = getCelestialBodyFromBackend({ planet: planetKey });
    
    planetGroup.innerHTML = `
        <div class="planet-header">
            <div class="planet-icon ${planetName.toLowerCase()}"></div>
            <div class="planet-info">
                <h3>${planetName}</h3>
                <div class="credibility-level">${celestialBody.description}</div>
            </div>
        </div>
        <div class="articles-grid">
            ${articles.map(article => createArticleCard(article)).join('')}
        </div>
    `;
    
    return planetGroup;
}

// Create Article Card Element
function createArticleCard(article) {
    const publishDate = article.publish_date ? new Date(article.publish_date).toLocaleDateString() : 'Unknown date';
    
    return `
        <div class="article-card">
            <div class="article-title">${escapeHtml(article.title)}</div>
            <div class="article-meta">
                <div class="article-domain">${escapeHtml(article.domain)}</div>
                <div class="article-date">${publishDate}</div>
            </div>
            <div class="article-scores">
                <div class="score-item">
                    <div class="score-label">Credibility</div>
                    <div class="score-value">${((1 - article.credibility_score) * 100).toFixed(1)}%</div>
                </div>
                <div class="score-item">
                    <div class="score-label">Fake News Risk</div>
                    <div class="score-value">${(article.fake_news_score * 100).toFixed(1)}%</div>
                </div>
                <div class="score-item">
                    <div class="score-label">Sarcasm Risk</div>
                    <div class="score-value">${(article.sarcasm_score * 100).toFixed(1)}%</div>
                </div>
            </div>
            <div class="article-actions">
                <button class="compare-btn" onclick="showCredibilityComparison('${escapeHtml(article.url)}')">
                    Compare Credibility
                </button>
                <a href="${escapeHtml(article.url)}" target="_blank" class="visit-btn" title="Visit Article">
                    🔗
                </a>
            </div>
        </div>
    `;
}

// Credibility Comparison Modal Functions
async function showCredibilityComparison(url) {
    const modal = document.getElementById('credibility-modal');
    const modalBody = document.getElementById('modal-body');
    
    // Show modal with loading state
    modal.style.display = 'flex';
    modalBody.innerHTML = `
        <div class="modal-loading">
            <div class="loading-spinner"></div>
            <p>Analyzing article credibility...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/analyze-article`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to analyze article');
        }
        
        const result = await response.json();
        displayCredibilityAnalysis(result);
        
    } catch (error) {
        modalBody.innerHTML = `
            <div class="modal-error">
                <div class="error-icon">⚠️</div>
                <h3>Analysis Failed</h3>
                <p>${error.message}</p>
                <button class="retry-btn" onclick="showCredibilityComparison('${escapeHtml(url)}')">
                    Try Again
                </button>
            </div>
        `;
    }
}

function displayCredibilityAnalysis(result) {
    const modalBody = document.getElementById('modal-body');
    const celestialBody = getCelestialBodyFromBackend(result);
    const planetName = celestialBody.name.toLowerCase();
    
    // Get credibility description based on score (lower score = more credible)
    function getCredibilityDescription(score) {
        if (score < 0.2) return "Highly credible content with minimal risk indicators";
        if (score < 0.4) return "Generally credible with some minor concerns";
        if (score < 0.6) return "Mixed credibility signals detected";
        if (score < 0.8) return "Significant credibility concerns identified";
        return "High risk of misinformation or unreliable content";
    }
    
    modalBody.innerHTML = `
        <div class="credibility-analysis">
            <div class="analysis-header">
                <div class="analysis-url">${escapeHtml(result.url)}</div>
                <div class="analysis-planet">
                    <div class="analysis-planet-icon ${planetName}"></div>
                    <div class="analysis-planet-info">
                        <h3>${celestialBody.name}</h3>
                        <div class="credibility-description">${celestialBody.description}</div>
                    </div>
                </div>
            </div>
            
            <div class="detailed-scores">
                <div class="score-detail">
                    <h4><span class="score-icon">🎯</span>Overall Credibility</h4>
                    <div class="score-number">${((1 - result.credibility_score) * 100).toFixed(1)}%</div>
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${(1 - result.credibility_score) * 100}%; background: linear-gradient(90deg, #26de81 0%, #ffc107 50%, #ff6b6b 100%);"></div>
                    </div>
                    <div class="score-description">Combined reliability assessment</div>
                </div>
                
                <div class="score-detail">
                    <h4><span class="score-icon">🧠</span>Fake News Risk</h4>
                    <div class="score-number">${(result.fake_news_score * 100).toFixed(1)}%</div>
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${result.fake_news_score * 100}%; background: linear-gradient(90deg, #26de81 0%, #ffc107 50%, #ff6b6b 100%);"></div>
                    </div>
                    <div class="score-description">Likelihood of false information</div>
                </div>
                
                <div class="score-detail">
                    <h4><span class="score-icon">😏</span>Sarcasm/Satire</h4>
                    <div class="score-number">${(result.sarcasm_score * 100).toFixed(1)}%</div>
                    <div class="score-bar">
                        <div class="score-fill" style="width: ${result.sarcasm_score * 100}%; background: linear-gradient(90deg, #4fc3f7 0%, #a855f7 50%, #ec4899 100%);"></div>
                    </div>
                    <div class="score-description">Satirical or sarcastic content</div>
                </div>
                

            </div>
            
            <div class="analysis-summary">
                <h4>📋 Analysis Summary</h4>
                <p>${getCredibilityDescription(result.credibility_score)}</p>
                <p style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.8;">
                    Analysis processed ${result.chunks_processed || 1} text segments • 
                    Classification: <strong>${result.label}</strong>
                </p>
                <p style="margin-top: 0.5rem; font-size: 0.8rem; opacity: 0.6;">
                    💡 Credibility % = trustworthiness level • Risk % = likelihood of issues
                </p>
            </div>
        </div>
    `;
}

function closeCredibilityModal() {
    const modal = document.getElementById('credibility-modal');
    modal.style.display = 'none';
}

// Close modal when clicking outside
document.getElementById('credibility-modal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeCredibilityModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeCredibilityModal();
    }
});

// Utility function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add enter key support for inputs
document.getElementById('news-url').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        analyzeURL();
    }
});

document.getElementById('article-query').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        searchSimilarArticles();
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