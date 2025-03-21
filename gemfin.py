import yfinance as yf
from google import genai
from datetime import datetime
import pandas as pd
from IPython.core.display import display, HTML

# Initialize Google API client
client = genai.Client(api_key="AIzaSyB1YG5MNCjG5vFoa4Bo3soSsgYFsKW4lYU")

# Fetch the stock information
stock = yf.Ticker("TSLA")

# Fetch the latest 20 news articles using the get_news method
news = stock.get_news(count=10, tab='news', proxy=None)
news = stock.news

# Initialize an empty list to store articles with 'STORY' contentType
articles = []

# Iterate over all articles in the news list
for article in news:
    # Extract the content of each article
    article_content = article.get('content', {})
 

    # Parse the title, contentType, and summary
    title = article_content.get('title', 'No title available')
    content_type = article_content.get('contentType', 'No content type available')
    summary = article_content.get('summary', 'No summary available')
    link = article_content.get('canonicalUrl', 'No link available').get('url', 'No link available')

    date = article_content.get('pubDate', 'No link available')
    dt = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    # Convert to 12-hour format with AM/PM
    dateandtime = dt.strftime("%Y-%m-%d %I:%M:%S %p")

    # Only append articles with contentType 'STORY'
    if content_type == 'STORY':
        # Call the Google API for sentiment analysis
        sentiment = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=f"Analyze the sentiment of the following summary and classify it as POSITIVE, NEGATIVE, or NEUTRAL. No explanation needed only one word output either POSITIVE, NEGATIVE, or NEUTRAL! Summary: {summary}"
        )

        # Append the article with title, contentType, summary, and sentiment
        articles.append([sentiment.text, dateandtime, title, f'<a href="{link}" target="_blank">Link</a>', content_type, summary])

# Create a pandas DataFrame
df = pd.DataFrame(articles, columns=["Sentiment", "Date & Time", "Title", "Link", "Summary"])

# Display the DataFrame with HTML links properly rendered
display(HTML(df.to_html(escape=False)))  # Renders HTML in Colab
