// Popup script for the Chrome extension
document.addEventListener('DOMContentLoaded', async () => {
  const analyzeBtn = document.getElementById('analyzeBtn');
  const loading = document.getElementById('loading');
  const result = document.getElementById('result');
  const error = document.getElementById('error');
  const currentUrlDiv = document.getElementById('currentUrl');

  // Get current tab URL
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const url = tab.url;
    
    // Display current URL (truncated)
    const displayUrl = url.length > 50 ? url.substring(0, 47) + '...' : url;
    currentUrlDiv.textContent = displayUrl;
    
    // Check if it's a valid URL for analysis
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      showError('This page cannot be analyzed. Please navigate to a news website.');
      analyzeBtn.disabled = true;
      return;
    }

    analyzeBtn.addEventListener('click', () => analyzePage(url));
  } catch (err) {
    showError('Unable to access current page. Please refresh and try again.');
    analyzeBtn.disabled = true;
  }
});

async function analyzePage(url) {
  const analyzeBtn = document.getElementById('analyzeBtn');
  const loading = document.getElementById('loading');
  const result = document.getElementById('result');
  const error = document.getElementById('error');

  // Show loading state
  analyzeBtn.style.display = 'none';
  loading.style.display = 'block';
  result.style.display = 'none';
  error.style.display = 'none';

  try {
    // Always try URL analysis first for consistency with the main website
    await analyzeByUrl(url);
  } catch (urlErr) {
    console.error('URL analysis failed:', urlErr);
    
    // Fallback to content extraction if URL analysis fails
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      // Inject content script to extract page content
      const results = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        function: extractPageContent
      });

      const pageContent = results[0].result;
      
      if (!pageContent || pageContent.length < 100) {
        throw new Error('Unable to extract sufficient content from page');
      }

      // Analyze the extracted content
      const response = await fetch('http://localhost:8001/predict-url', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: pageContent }) // Send content as "url" for text analysis
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      showResult(data, 'content');

    } catch (contentErr) {
      showError(`Analysis failed: ${contentErr.message}. Make sure the Newsify server is running on localhost:8001.`);
    }
  }
}

async function analyzeByUrl(url) {
  try {
    const response = await fetch('http://localhost:8001/predict-url', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url: url })
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const data = await response.json();
    showResult(data, 'url');

  } catch (err) {
    throw new Error(`URL analysis failed: ${err.message}`);
  }
}

// Function to be injected into the page to extract content
function extractPageContent() {
  // Remove scripts and styles
  const scripts = document.querySelectorAll('script, style, nav, header, footer, aside');
  scripts.forEach(el => el.remove());

  // Try to find main content
  let content = '';
  
  // Look for article content
  const article = document.querySelector('article');
  if (article) {
    content = article.innerText;
  } else {
    // Look for main content areas
    const main = document.querySelector('main, [role="main"], .content, .article, .post');
    if (main) {
      content = main.innerText;
    } else {
      // Fallback to all paragraphs
      const paragraphs = document.querySelectorAll('p');
      content = Array.from(paragraphs).map(p => p.innerText).join(' ');
    }
  }

  // Get title
  const title = document.title || '';
  
  // Combine title and content
  const fullContent = title + ' ' + content;
  
  // Clean up whitespace
  return fullContent.replace(/\s+/g, ' ').trim();
}

// Planet data matching the website
const PLANETS_DATA = {
  'Sun': { name: 'Sun', description: 'Highly Trustworthy' },
  'Mercury': { name: 'Mercury', description: 'Very Trustworthy' },
  'Venus': { name: 'Venus', description: 'Very Trustworthy' },
  'Earth': { name: 'Earth', description: 'Trustworthy' },
  'Mars': { name: 'Mars', description: 'Moderately Trustworthy' },
  'Jupiter': { name: 'Jupiter', description: 'Questionable' },
  'Saturn': { name: 'Saturn', description: 'Questionable' },
  'Uranus': { name: 'Uranus', description: 'Likely Unreliable' },
  'Neptune': { name: 'Neptune', description: 'Unreliable' }
};

function showResult(data, method) {
  const loading = document.getElementById('loading');
  const result = document.getElementById('result');
  const bodyIcon = document.getElementById('body-icon');
  const bodyName = document.getElementById('body-name');
  const reliabilityDescription = document.getElementById('reliability-description');
  const score = document.getElementById('score');
  const label = document.getElementById('label');
  const stats = document.getElementById('stats');

  loading.style.display = 'none';
  result.style.display = 'block';

  // Set result class for styling
  result.className = `result ${data.label.toLowerCase()}`;
  
  // Set label class for styling
  label.className = `label ${data.label.toLowerCase()}`;

  // Extract planet name from backend result (e.g., "☀️ Sun" -> "Sun")
  const planetText = data.planet || "☀️ Sun";
  const planetName = planetText.replace(/^[^\w\s]*\s*/, ''); // Remove emoji and spaces
  
  // Get planet data
  const planetData = PLANETS_DATA[planetName] || PLANETS_DATA['Sun'];
  
  // Create 3D celestial object (only the icon spins, not the text)
  const planetClass = planetData.name.toLowerCase();
  bodyIcon.className = `body-icon ${planetClass}`;
  bodyIcon.textContent = ''; // Remove emoji, use CSS 3D object
  
  // Set planet name and description (these don't spin)
  bodyName.textContent = planetData.name;
  reliabilityDescription.textContent = planetData.description;
  
  // Use the score directly from the server (no conversion needed)
  const displayScore = Math.round(data.score * 100);
  score.textContent = `${displayScore}%`;
  label.textContent = data.label;

  // Show optimization stats if available
  let statsText = `Analyzed via ${method === 'content' ? 'page content' : 'URL'}`;
  if (data.optimization_stats) {
    const stats_data = data.optimization_stats;
    statsText += `\n${stats_data.original_length} → ${stats_data.optimized_length} chars`;
    statsText += `\n${Math.round(stats_data.compression_ratio * 100)}% compression`;
    statsText += `\n~${stats_data.token_estimate} tokens processed`;
  }
  
  stats.textContent = statsText;
}

function showError(message) {
  const analyzeBtn = document.getElementById('analyzeBtn');
  const loading = document.getElementById('loading');
  const result = document.getElementById('result');
  const error = document.getElementById('error');
  const errorMessage = document.getElementById('errorMessage');

  analyzeBtn.style.display = 'block';
  loading.style.display = 'none';
  result.style.display = 'none';
  error.style.display = 'block';
  errorMessage.textContent = message;
}