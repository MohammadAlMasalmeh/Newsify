# Newsify Chrome Extension

A Chrome extension that analyzes any webpage for fake news using your Newsify backend.

## Features

- 🔍 **One-click analysis** - Analyze any webpage with a single click
- 🌌 **Cosmic interface** - Beautiful space-themed popup matching your website
- 📊 **Smart extraction** - Intelligently extracts and analyzes page content
- ⚡ **Fast results** - Get instant fake news detection scores
- 🎯 **Optimized processing** - Uses your intelligent text optimization system

## Installation

### Development Installation

1. **Start your Newsify server**:
   ```bash
   python3 server.py
   ```
   Make sure it's running on `http://localhost:8001`

2. **Load the extension in Chrome**:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top right)
   - Click "Load unpacked"
   - Select the `extension` folder from your Newsify project

3. **Add icons** (optional but recommended):
   - Add `icon16.png`, `icon48.png`, and `icon128.png` to the `extension/icons/` folder
   - Icons should be space/cosmic themed to match your brand

## Usage

1. **Navigate to any news article** or webpage you want to analyze
2. **Click the Newsify extension icon** in your Chrome toolbar
3. **Click "Analyze This Page"** in the popup
4. **View results** with cosmic truth ratings and optimization stats

## How It Works

The extension:
1. **Extracts content** from the current webpage using intelligent content detection
2. **Sends content** to your local Newsify server for analysis
3. **Displays results** with the same cosmic planet rating system as your website
4. **Shows optimization stats** including compression ratios and token usage

## Fallback Behavior

- If content extraction fails, it falls back to URL-based analysis
- If the server is unavailable, it shows helpful error messages
- Works with most news websites and article formats

## Development Notes

- The extension requires your Newsify server to be running locally
- Content extraction works on most websites but may vary by site structure
- The popup maintains the same cosmic theme as your main website
- All the intelligent text optimization features are preserved

## Publishing to Chrome Web Store

To publish this extension:
1. Add proper icons to the `icons` folder
2. Test thoroughly on various websites
3. Create a Chrome Web Store developer account
4. Package and upload the extension
5. Update the `host_permissions` to include your production server URL

## Security Notes

- The extension only requests `activeTab` permission (minimal access)
- Content is processed locally through your own server
- No data is sent to third-party services
- Users maintain full control over what gets analyzed