# -*- coding: utf-8 -*-
"""
Created on Fri Jun 27 09:46:34 2025

@author: vchundru
"""

from flask import Flask, jsonify, render_template_string
import requests
import os

# Initialize the Flask application
app = Flask(__name__)

# --- Configuration ---
# IMPORTANT: Replace 'YOUR_API_KEY' with your actual NewsAPI key.
# You can get a free API key from https://newsapi.org/register
API_KEY = os.environ.get('NEWS_API_KEY', 'b4aadf8e29764046ae31352ba1639cf3')
NEWS_API_URL = 'https://newsapi.org/v2/top-headlines'
COUNTRY = 'us' # Fetch news from the United States

# --- HTML & JavaScript Template ---
# This is the frontend of our application. It's a single HTML file
# with embedded CSS (Tailwind) and JavaScript.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real-Time News Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Inter', sans-serif;
            /* Added a blue to pink gradient background */
            background: linear-gradient(to right, #60a5fa, #ec4899);
        }
        .article-card {
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }
        .article-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        }
    </style>
</head>
<body class="bg-gray-100 text-gray-800">

    <div class="container mx-auto px-4 py-8">
        <header class="text-center mb-8">
            <h1 class="text-4xl font-bold text-white">Real-Time News Dashboard</h1>
            <p class="text-lg text-gray-200 mt-2">Top Headlines from the US</p>
        </header>

        <!-- Loading Spinner -->
        <div id="loading" class="text-center">
            <svg class="animate-spin h-8 w-8 text-white mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p class="mt-2 text-gray-200">Fetching latest news...</p>
        </div>
        
        <!-- Error Message Display -->
        <div id="error-message" class="hidden bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg relative mb-6" role="alert">
            <strong class="font-bold">Error:</strong>
            <span class="block sm:inline" id="error-text"></span>
        </div>


        <!-- News Articles Grid -->
        <div id="news-grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <!-- News articles will be injected here by JavaScript -->
        </div>

    </div>

    <footer class="text-center py-4 mt-8">
        <p class="text-gray-200">Powered by <a href="https://newsapi.org/" target="_blank" class="text-white hover:underline">NewsAPI.org</a></p>
    </footer>

    <script>
        const newsGrid = document.getElementById('news-grid');
        const loadingIndicator = document.getElementById('loading');
        const errorMessage = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');

        // Function to create a single news article card
        function createArticleCard(article) {
            const card = document.createElement('div');
            card.className = 'bg-white rounded-lg shadow-md overflow-hidden article-card';

            const imageUrl = article.urlToImage || 'https://placehold.co/600x400/e2e8f0/4a5568?text=No+Image';

            card.innerHTML = `
                <a href="${article.url}" target="_blank" rel="noopener noreferrer">
                    <img src="${imageUrl}" alt="${article.title}" class="w-full h-48 object-cover" onerror="this.onerror=null;this.src='https://placehold.co/600x400/e2e8f0/4a5568?text=Image+Error';">
                    <div class="p-6">
                        <h2 class="text-xl font-bold mb-2">${article.title}</h2>
                        <p class="text-gray-600 text-sm mb-4">By ${article.author || 'Unknown'} | ${new Date(article.publishedAt).toLocaleDateString()}</p>
                        <p class="text-gray-700">${article.description || 'No description available.'}</p>
                        <p class="text-blue-600 hover:underline mt-4 inline-block">Read more &rarr;</p>
                    </div>
                </a>
            `;
            return card;
        }

        // Function to fetch news from our Flask backend
        async function fetchNews() {
            loadingIndicator.style.display = 'block';
            errorMessage.classList.add('hidden');
            newsGrid.innerHTML = '';

            try {
                const response = await fetch('/get_news');
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
                }
                const data = await response.json();

                if (data.articles && data.articles.length > 0) {
                    data.articles.forEach(article => {
                        const card = createArticleCard(article);
                        newsGrid.appendChild(card);
                    });
                } else {
                   errorText.textContent = 'No articles found. The API might be configured incorrectly or there is no news.';
                   errorMessage.classList.remove('hidden');
                }

            } catch (error) {
                console.error('Error fetching news:', error);
                errorText.textContent = error.message;
                errorMessage.classList.remove('hidden');
            } finally {
                loadingIndicator.style.display = 'none';
            }
        }

        // Fetch news on initial page load
        fetchNews();

        // Refresh news every 5 minutes (300000 milliseconds)
        setInterval(fetchNews, 300000);
    </script>
</body>
</html>
"""

# --- Backend Routes ---

@app.route('/')
def index():
    """
    Renders the main HTML page.
    """
    return render_template_string(HTML_TEMPLATE)

@app.route('/get_news')
def get_news():
    """
    This is our API endpoint. It fetches news from NewsAPI.org
    and returns it as JSON.
    """
    if API_KEY == 'YOUR_API_KEY':
        return jsonify({
            "error": "Invalid API Key. Please replace 'YOUR_API_KEY' in the Python script with your actual key from NewsAPI.org."
        }), 500
        
    params = {
        'country': COUNTRY,
        'apiKey': API_KEY,
        'pageSize': 30 # Fetch 30 articles
    }
    try:
        response = requests.get(NEWS_API_URL, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        return jsonify(data)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch news from NewsAPI: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500

# --- Main Execution ---

if __name__ == '__main__':
    # To run this application:
    # 1. Make sure you have Python installed.
    # 2. Install Flask and Requests: pip install Flask requests
    # 3. Save this code as a Python file (e.g., news_app.py).
    # 4. Replace 'YOUR_API_KEY' with your key from newsapi.org.
    # 5. Run from your terminal: python news_app.py
    # 6. Open your web browser and go to http://127.0.0.1:5000
    #
    # Note: `use_reloader=False` is added to prevent issues in some IDEs
    # like Spyder that can cause the application to exit unexpectedly.
    app.run(debug=True, use_reloader=False)
