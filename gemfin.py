import yfinance as yf
from google import genai
from datetime import datetime
import pandas as pd
import pytz

class StockNewsAnalyzer:
    def __init__(self, api_key):
        # Initialize Google API client
        self.client = genai.Client(api_key=api_key)
        self.articles = []
        
    def fetch_stock_news(self, ticker_symbol="TSLA", count=15):
        """Fetch news for a given stock ticker and analyze sentiment"""
        # Fetch the stock information
        stock = yf.Ticker(ticker_symbol)
        
        # Get stock price information
        self.stock_info = {
            'ticker': ticker_symbol,
            'price_data': None
        }
        
        try:
            # Get 2 days of data to calculate change from previous close
            hist = stock.history(period="2d")
            if not hist.empty and len(hist) >= 1:
                today_close = round(hist['Close'].iloc[-1], 2)
                today_open = round(hist['Open'].iloc[-1], 2)
                
                # Calculate intraday percent change
                intraday_change = round(((today_close - today_open) / today_open) * 100, 2)
                
                # Calculate previous close percent change if we have at least 2 days of data
                prev_close_change = None
                if len(hist) >= 2:
                    prev_close = round(hist['Close'].iloc[-2], 2)
                    prev_close_change = round(((today_close - prev_close) / prev_close) * 100, 2)
                
                self.stock_info['price_data'] = {
                    'open': today_open,
                    'close': today_close,
                    'intraday_change': intraday_change,
                    'prev_close': prev_close if len(hist) >= 2 else None,
                    'prev_close_change': prev_close_change
                }
        except Exception as e:
            print(f"Error fetching stock price data: {e}")
        
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
                    dt = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)
                    dateandtime = dt.astimezone(pytz.timezone('US/Mountain')).strftime("%Y-%m-%d %I:%M:%S %p")
                except ValueError:
                    dateandtime = 'Date format error'
            else:
                dateandtime = 'No date available'
            
            # Only process articles with contentType 'STORY'
            if content_type == 'STORY':
                # Call the Google API for sentiment analysis with both title and summary
                sentiment = self.client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=f"Analyze the sentiment of the following news article and classify it as POSITIVE, NEGATIVE, or NEUTRAL. No explanation needed only one word output either POSITIVE, NEGATIVE, or NEUTRAL! Title: {title} Summary: {summary}"
                )
                
                # Extract thumbnail URL if available
                thumbnail_url = None
                thumbnail_data = article_content.get('thumbnail', {})
                if thumbnail_data:
                    # Try to get the original URL first
                    thumbnail_url = thumbnail_data.get('originalUrl')
                    
                    # If not available, try to get from resolutions
                    if not thumbnail_url and 'resolutions' in thumbnail_data:
                        resolutions = thumbnail_data['resolutions']
                        if resolutions and isinstance(resolutions, list) and len(resolutions) > 0:
                            # Get the first resolution URL
                            thumbnail_url = resolutions[0].get('url')
                
                # Append the article with title, date, sentiment, etc.
                self.articles.append({
                    "sentiment": sentiment.text,
                    "date": dateandtime,
                    "title": title,
                    "link": link,
                    "content_type": content_type,
                    "summary": summary,
                    "thumbnail_url": thumbnail_url
                })
        
        return self.articles
    
    def get_dataframe(self):
        """Convert articles to a pandas DataFrame"""
        if not self.articles:
            return pd.DataFrame()
            
        df = pd.DataFrame(self.articles)
        return df
    
    def get_stock_info(self):
        """Return the stock price information"""
        return self.stock_info
