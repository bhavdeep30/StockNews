import yfinance as yf
from google import genai
from datetime import datetime
import pandas as pd

class StockNewsAnalyzer:
    def __init__(self, api_key):
        # Initialize Google API client
        self.client = genai.Client(api_key=api_key)
        self.articles = []
        
    def fetch_stock_news(self, ticker_symbol="TSLA", count=10):
        """Fetch news for a given stock ticker and analyze sentiment"""
        # Fetch the stock information
        stock = yf.Ticker(ticker_symbol)
        
        # Fetch the latest news articles
        news = stock.get_news(count=count, tab='news', proxy=None)
        news = stock.news
        
        # Clear previous articles
        self.articles = []
        
        # Iterate over all articles in the news list
        for article in news:
            # Extract the content of each article
            article_content = article.get('content', {})
            
            # Parse the title, contentType, and summary
            title = article_content.get('title', 'No title available')
            content_type = article_content.get('contentType', 'No content type available')
            summary = article_content.get('summary', 'No summary available')
            
            # Get the URL, handling nested dictionaries
            link_data = article_content.get('canonicalUrl', {})
            if isinstance(link_data, dict):
                link = link_data.get('url', 'No link available')
            else:
                link = 'No link available'
            
            # Get and format the date
            date = article_content.get('pubDate', None)
            if date:
                try:
                    dt = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
                    # Convert to 12-hour format with AM/PM
                    dateandtime = dt.strftime("%Y-%m-%d %I:%M:%S %p")
                except ValueError:
                    dateandtime = 'Date format error'
            else:
                dateandtime = 'No date available'
            
            # Only process articles with contentType 'STORY'
            if content_type == 'STORY':
                # Call the Google API for sentiment analysis
                sentiment = self.client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=f"Analyze the sentiment of the following summary and classify it as POSITIVE, NEGATIVE, or NEUTRAL. No explanation needed only one word output either POSITIVE, NEGATIVE, or NEUTRAL! Summary: {summary}"
                )
                
                # Append the article with title, date, sentiment, etc.
                self.articles.append({
                    "sentiment": sentiment.text,
                    "date": dateandtime,
                    "title": title,
                    "link": link,
                    "content_type": content_type,
                    "summary": summary
                })
        
        return self.articles
    
    def get_dataframe(self):
        """Convert articles to a pandas DataFrame"""
        if not self.articles:
            return pd.DataFrame()
            
        df = pd.DataFrame(self.articles)
        return df
