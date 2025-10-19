// Content script that runs on all pages
// This script can be used for additional functionality like highlighting suspicious content

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractContent') {
    const content = extractPageContent();
    sendResponse({ content: content });
  }
});

function extractPageContent() {
  // Create a clone to avoid modifying the actual page
  const clone = document.cloneNode(true);
  
  // Remove unwanted elements from clone
  const unwanted = clone.querySelectorAll('script, style, nav, header, footer, aside, .ad, .advertisement, .sidebar');
  unwanted.forEach(el => el.remove());

  // Try to find main content
  let content = '';
  
  // Look for article content
  const article = clone.querySelector('article');
  if (article) {
    content = article.innerText || article.textContent;
  } else {
    // Look for main content areas
    const main = clone.querySelector('main, [role="main"], .content, .article, .post, .story');
    if (main) {
      content = main.innerText || main.textContent;
    } else {
      // Fallback to all paragraphs
      const paragraphs = clone.querySelectorAll('p');
      content = Array.from(paragraphs)
        .map(p => p.innerText || p.textContent)
        .filter(text => text.length > 20) // Filter out short paragraphs
        .join(' ');
    }
  }

  // Get title and meta description
  const title = document.title || '';
  const metaDesc = document.querySelector('meta[name="description"]');
  const description = metaDesc ? metaDesc.getAttribute('content') : '';
  
  // Combine title, description, and content
  const fullContent = [title, description, content]
    .filter(text => text && text.length > 0)
    .join(' ');
  
  // Clean up whitespace and return
  return fullContent.replace(/\s+/g, ' ').trim();
}

// Optional: Add visual indicators to the page
function addTruthIndicator(score, label) {
  // Create a floating indicator
  const indicator = document.createElement('div');
  indicator.id = 'newsify-indicator';
  indicator.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10000;
    padding: 10px 15px;
    border-radius: 20px;
    color: white;
    font-family: Arial, sans-serif;
    font-size: 14px;
    font-weight: bold;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    cursor: pointer;
    transition: all 0.3s ease;
    background: ${label === 'REAL' ? 'linear-gradient(45deg, #2ecc71, #27ae60)' : 'linear-gradient(45deg, #e74c3c, #c0392b)'};
  `;
  
  indicator.innerHTML = `
    <div style="display: flex; align-items: center; gap: 8px;">
      <span>${label === 'REAL' ? '✅' : '❌'}</span>
      <span>${label} (${Math.round(score * 100)}%)</span>
    </div>
  `;
  
  // Add click handler to remove
  indicator.addEventListener('click', () => {
    indicator.remove();
  });
  
  // Remove any existing indicator
  const existing = document.getElementById('newsify-indicator');
  if (existing) existing.remove();
  
  // Add to page
  document.body.appendChild(indicator);
  
  // Auto-remove after 10 seconds
  setTimeout(() => {
    if (indicator.parentNode) {
      indicator.remove();
    }
  }, 10000);
}