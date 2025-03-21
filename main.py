from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.clock import Clock
import webbrowser
import threading

from gemfin import StockNewsAnalyzer

# Set window size
Window.size = (1000, 700)

class NewsItem(BoxLayout):
    """Widget to display a single news item"""
    def __init__(self, article, **kwargs):
        super(NewsItem, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(5)
        self.size_hint_y = None
        self.height = dp(200)
        
        # Store the link
        self.link = article['link']
        
        # Create header with title and sentiment
        header = BoxLayout(size_hint_y=None, height=dp(30))
        
        # Set sentiment color
        sentiment = article['sentiment'].strip().upper()
        sentiment_color = (0.2, 0.8, 0.2, 1)  # Default green for positive
        if sentiment == 'NEGATIVE':
            sentiment_color = (0.8, 0.2, 0.2, 1)  # Red
        elif sentiment == 'NEUTRAL':
            sentiment_color = (0.7, 0.7, 0.2, 1)  # Yellow
            
        # Add sentiment label
        sentiment_label = Label(
            text=sentiment,
            size_hint_x=0.2,
            color=sentiment_color,
            bold=True
        )
        header.add_widget(sentiment_label)
        
        # Add title
        title_label = Label(
            text=article['title'],
            size_hint_x=0.8,
            text_size=(None, dp(30)),
            halign='left',
            valign='middle',
            shorten=True,
            bold=True
        )
        header.add_widget(title_label)
        self.add_widget(header)
        
        # Add date
        date_label = Label(
            text=f"Published: {article['date']}",
            size_hint_y=None,
            height=dp(20),
            halign='left',
            text_size=(self.width, None)
        )
        self.add_widget(date_label)
        
        # Add summary
        summary_label = Label(
            text=article['summary'],
            size_hint_y=None,
            height=dp(100),
            text_size=(self.width, dp(100)),
            halign='left',
            valign='top'
        )
        self.add_widget(summary_label)
        
        # Add "Open Link" button
        link_button = Button(
            text="Open Article",
            size_hint=(None, None),
            size=(dp(120), dp(40)),
            pos_hint={'right': 1}
        )
        link_button.bind(on_release=self.open_link)
        self.add_widget(link_button)
        
    def open_link(self, instance):
        """Open the article link in a web browser"""
        if self.link and self.link != 'No link available':
            webbrowser.open(self.link)

class StockNewsApp(App):
    status_text = StringProperty("Ready")
    
    def build(self):
        # Main layout
        self.main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Top controls
        controls = BoxLayout(size_hint_y=None, height=dp(50), spacing=10)
        
        # API Key input
        api_key_label = Label(text="API Key:", size_hint_x=0.15)
        self.api_key_input = TextInput(
            text="AIzaSyB1YG5MNCjG5vFoa4Bo3soSsgYFsKW4lYU",
            multiline=False,
            size_hint_x=0.35,
            password=True
        )
        
        # Stock ticker input
        ticker_label = Label(text="Stock Ticker:", size_hint_x=0.15)
        self.ticker_input = TextInput(
            text="TSLA",
            multiline=False,
            size_hint_x=0.15
        )
        
        # Fetch button
        self.fetch_button = Button(
            text="Fetch News",
            size_hint_x=0.2
        )
        self.fetch_button.bind(on_release=self.fetch_news)
        
        # Add controls to layout
        controls.add_widget(api_key_label)
        controls.add_widget(self.api_key_input)
        controls.add_widget(ticker_label)
        controls.add_widget(self.ticker_input)
        controls.add_widget(self.fetch_button)
        
        self.main_layout.add_widget(controls)
        
        # Status bar
        self.status_bar = Label(
            text=self.status_text,
            size_hint_y=None,
            height=dp(30),
            halign='left',
            valign='middle'
        )
        self.main_layout.add_widget(self.status_bar)
        
        # Scroll view for news items
        self.scroll_view = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True
        )
        
        # Container for news items
        self.news_container = GridLayout(
            cols=1,
            spacing=10,
            padding=10,
            size_hint_y=None
        )
        # Make sure the height is such that scrolling works
        self.news_container.bind(minimum_height=self.news_container.setter('height'))
        
        self.scroll_view.add_widget(self.news_container)
        self.main_layout.add_widget(self.scroll_view)
        
        return self.main_layout
    
    def fetch_news(self, instance):
        """Fetch news for the specified stock ticker"""
        # Disable button during fetch
        self.fetch_button.disabled = True
        self.status_text = "Fetching news..."
        self.status_bar.text = self.status_text
        
        # Start fetch in a separate thread to keep UI responsive
        threading.Thread(target=self._fetch_news_thread).start()
    
    def _fetch_news_thread(self):
        """Background thread for fetching news"""
        try:
            api_key = self.api_key_input.text.strip()
            ticker = self.ticker_input.text.strip().upper()
            
            if not api_key or not ticker:
                Clock.schedule_once(lambda dt: self._show_error("API Key and Ticker are required"), 0)
                return
            
            # Create analyzer and fetch news
            analyzer = StockNewsAnalyzer(api_key=api_key)
            articles = analyzer.fetch_stock_news(ticker_symbol=ticker)
            
            # Update UI on the main thread
            Clock.schedule_once(lambda dt: self._update_news_display(articles), 0)
            
        except Exception as e:
            error_message = str(e)
            Clock.schedule_once(lambda dt: self._show_error(f"Error: {error_message}"), 0)
        finally:
            # Re-enable button
            Clock.schedule_once(lambda dt: self._enable_fetch_button(), 0)
    
    def _update_news_display(self, articles):
        """Update the news display with fetched articles"""
        # Clear existing news items
        self.news_container.clear_widgets()
        
        if not articles:
            self.status_text = "No news articles found"
        else:
            # Add news items to the container
            for article in articles:
                news_item = NewsItem(article)
                self.news_container.add_widget(news_item)
            
            self.status_text = f"Found {len(articles)} news articles"
        
        self.status_bar.text = self.status_text
    
    def _enable_fetch_button(self):
        """Re-enable the fetch button"""
        self.fetch_button.disabled = False
    
    def _show_error(self, message):
        """Show an error popup"""
        self.status_text = message
        self.status_bar.text = self.status_text
        
        popup = Popup(
            title='Error',
            content=Label(text=message),
            size_hint=(None, None),
            size=(400, 200)
        )
        popup.open()
        self.fetch_button.disabled = False

if __name__ == '__main__':
    StockNewsApp().run()
