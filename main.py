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
from kivy.properties import StringProperty, ColorProperty
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
import webbrowser
import threading

from gemfin import StockNewsAnalyzer

# Set window size and theme
Window.size = (1200, 800)

# Dark mode colors
DARK_BG = (0.12, 0.12, 0.12, 1)
DARKER_BG = (0.08, 0.08, 0.08, 1)
TEXT_COLOR = (0.9, 0.9, 0.9, 1)
ACCENT_COLOR = (0.2, 0.6, 1, 1)
POSITIVE_COLOR = (0.2, 0.8, 0.2, 1)
NEGATIVE_COLOR = (0.8, 0.2, 0.2, 1)
NEUTRAL_COLOR = (0.7, 0.7, 0.2, 1)
ELECTRIC_BLUE = (0.0, 0.6, 1.0, 1)  # Electric blue color

class NewsTableHeader(BoxLayout):
    """Header row for the news table"""
    def __init__(self, **kwargs):
        super(NewsTableHeader, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(40)
        self.padding = [dp(5), 0]
        
        with self.canvas.before:
            Color(*DARKER_BG)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Column headers
        headers = [
            ("SENTIMENT", 0.15),
            ("TITLE", 0.5),
            ("DATE", 0.15),
            ("ACTIONS", 0.2)
        ]
        
        for text, size_x in headers:
            label = Label(
                text=text,
                size_hint_x=size_x,
                color=TEXT_COLOR,
                bold=True
            )
            self.add_widget(label)
    
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

from kivy.uix.image import AsyncImage
from kivy.uix.widget import Widget

class NewsTableRow(BoxLayout):
    """Widget to display a news item as a table row"""
    def __init__(self, article, index, **kwargs):
        super(NewsTableRow, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.padding = [dp(5), dp(5)]
        self.size_hint_y = None
        self.height = dp(80)  # Increased height to accommodate thumbnail
        
        # Store the link and article data
        self.link = article['link']
        self.article = article
        
        # Alternating row colors
        bg_color = DARK_BG if index % 2 == 0 else DARKER_BG
        with self.canvas.before:
            Color(*bg_color)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        # Set sentiment color
        sentiment = article['sentiment'].strip().upper()
        sentiment_color = POSITIVE_COLOR  # Default green for positive
        if sentiment == 'NEGATIVE':
            sentiment_color = NEGATIVE_COLOR
        elif sentiment == 'NEUTRAL':
            sentiment_color = NEUTRAL_COLOR
            
        # Add sentiment label
        sentiment_label = Label(
            text=sentiment,
            size_hint_x=0.15,
            color=sentiment_color,
            bold=True
        )
        self.add_widget(sentiment_label)
        
        # Create content box for thumbnail and title
        content_box = BoxLayout(
            orientation='horizontal',
            size_hint_x=0.5,
            spacing=dp(5)
        )
        
        # Add thumbnail if available
        thumbnail_url = article.get('thumbnail_url')
        if thumbnail_url:
            # Create a fixed-size container for the image with fixed width
            img_container = BoxLayout(size_hint_x=None, width=dp(100), padding=[0, 0, dp(15), 0])  # Add padding to the right
            
            # Add the image
            img = AsyncImage(
                source=thumbnail_url,
                allow_stretch=True,
                keep_ratio=True
            )
            img_container.add_widget(img)
            content_box.add_widget(img_container)
        else:
            # Add a placeholder with the same width to maintain layout consistency
            placeholder = BoxLayout(size_hint_x=None, width=dp(100), padding=[0, 0, dp(15), 0])  # Add padding to the right
            content_box.add_widget(placeholder)
        
        # Add title with fixed layout
        title_container = BoxLayout(size_hint_x=1)
        title_label = Label(
            text=article['title'],
            color=TEXT_COLOR,
            text_size=(None, dp(80)),
            halign='left',
            valign='middle',
            shorten=True,
            shorten_from='right',
            bold=True
        )
        # Bind the text size to the container width to ensure proper text wrapping
        title_label.bind(width=lambda *x: setattr(title_label, 'text_size', (title_label.width, dp(80))))
        title_container.add_widget(title_label)
        content_box.add_widget(title_container)
        
        self.add_widget(content_box)
        
        # Add date
        date_label = Label(
            text=article['date'],
            size_hint_x=0.15,
            color=TEXT_COLOR,
            text_size=(None, dp(80)),
            halign='left',
            valign='middle',
            shorten=True
        )
        self.add_widget(date_label)
        
        # Actions container
        actions = BoxLayout(
            orientation='horizontal',
            size_hint_x=0.2,
            spacing=dp(5),
            padding=[dp(20), 0],  # Increase horizontal padding
            pos_hint={'center_x': 0.5, 'center_y': 0.5}  # Center the box itself
        )
        
        # View details button
        details_button = Button(
            text="Details",
            size_hint=(None, None),
            size=(dp(80), dp(35)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},  # Center horizontally and vertically
            background_color=ACCENT_COLOR
        )
        details_button.bind(on_release=self.show_details)
        
        # Open link button
        link_button = Button(
            text="Link",
            size_hint=(None, None),
            size=(dp(80), dp(35)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},  # Center horizontally and vertically
            background_color=ACCENT_COLOR
        )
        link_button.bind(on_release=self.open_link)
        
        actions.add_widget(details_button)
        actions.add_widget(link_button)
        self.add_widget(actions)
    
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        
    def open_link(self, instance):
        """Open the article link in a web browser"""
        if self.link and self.link != 'No link available':
            webbrowser.open(self.link)
    
    def show_details(self, instance):
        """Show a popup with article details"""
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Title
        title_label = Label(
            text=self.article['title'],
            size_hint_y=None,
            height=dp(40),
            color=TEXT_COLOR,
            bold=True
        )
        content.add_widget(title_label)
        
        # Date and sentiment
        info_box = BoxLayout(size_hint_y=None, height=dp(30))
        
        date_label = Label(
            text=f"Published: {self.article['date']}",
            size_hint_x=0.7,
            color=TEXT_COLOR
        )
        
        sentiment = self.article['sentiment'].strip().upper()
        sentiment_color = POSITIVE_COLOR
        if sentiment == 'NEGATIVE':
            sentiment_color = NEGATIVE_COLOR
        elif sentiment == 'NEUTRAL':
            sentiment_color = NEUTRAL_COLOR
            
        sentiment_label = Label(
            text=f"Sentiment: {sentiment}",
            size_hint_x=0.3,
            color=sentiment_color,
            bold=True
        )
        
        info_box.add_widget(date_label)
        info_box.add_widget(sentiment_label)
        content.add_widget(info_box)
        
        # Add thumbnail if available
        thumbnail_url = self.article.get('thumbnail_url')
        if thumbnail_url:
            thumbnail_container = BoxLayout(
                size_hint_y=None,
                height=dp(200),
                padding=[0, dp(10)]
            )
            
            thumbnail = AsyncImage(
                source=thumbnail_url,
                allow_stretch=True,
                keep_ratio=True
            )
            thumbnail_container.add_widget(thumbnail)
            content.add_widget(thumbnail_container)
        
        # Summary in a scroll view
        scroll = ScrollView(do_scroll_x=False)
        summary_label = Label(
            text=self.article['summary'],
            size_hint_y=None,
            color=TEXT_COLOR
        )
        summary_label.bind(width=lambda *x: summary_label.setter('text_size')(summary_label, (summary_label.width, None)))
        summary_label.bind(texture_size=lambda *x: summary_label.setter('height')(summary_label, summary_label.texture_size[1]))
        scroll.add_widget(summary_label)
        content.add_widget(scroll)
        
        # Close button
        close_button = Button(
            text="Close",
            size_hint=(None, None),
            size=(dp(100), dp(40)),
            pos_hint={'center_x': 0.5},
            background_color=ACCENT_COLOR
        )
        content.add_widget(close_button)
        
        # Create popup
        popup = Popup(
            title='Article Details',
            content=content,
            size_hint=(0.8, 0.8),
            background_color=DARKER_BG,
            title_color=TEXT_COLOR
        )
        
        # Bind close button
        close_button.bind(on_release=popup.dismiss)
        
        popup.open()

class StockNewsApp(App):
    status_text = StringProperty("Ready")
    
    def build(self):
        # Set app background color
        Window.clearcolor = DARK_BG
        
        # Main layout
        self.main_layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        
        with self.main_layout.canvas.before:
            Color(*DARK_BG)
            self.rect = Rectangle(pos=self.main_layout.pos, size=self.main_layout.size)
        self.main_layout.bind(pos=self._update_rect, size=self._update_rect)
        
        # App title
        title_box = BoxLayout(size_hint_y=None, height=dp(50))
        title_label = Label(
            text="STOCK NEWS SENTIMENT ANALYZER",
            font_size=dp(24),
            bold=True,
            color=ELECTRIC_BLUE
        )
        title_box.add_widget(title_label)
        self.main_layout.add_widget(title_box)
        
        # Top controls
        controls = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(15))
        
        # Stock ticker input
        ticker_label = Label(
            text="Stock Ticker:",
            size_hint_x=0.15,
            color=TEXT_COLOR
        )
        self.ticker_input = TextInput(
            text="TSLA",
            multiline=False,
            size_hint_x=0.15,
            background_color=DARKER_BG,
            foreground_color=TEXT_COLOR,
            cursor_color=TEXT_COLOR
        )
        
        # Fetch button
        self.fetch_button = Button(
            text="FETCH NEWS",
            size_hint_x=0.15,
            background_color=ACCENT_COLOR,
            bold=True
        )
        self.fetch_button.bind(on_release=self.fetch_news)
        
        # Overall sentiment display
        self.sentiment_box = BoxLayout(
            orientation='horizontal',
            size_hint_x=0.25,
            spacing=dp(5)
        )
        
        self.sentiment_label = Label(
            text="Overall:",
            size_hint_x=0.4,
            color=TEXT_COLOR
        )
        
        self.sentiment_value = Label(
            text="N/A",
            size_hint_x=0.6,
            color=TEXT_COLOR,
            bold=True,
            font_size=dp(24)  # 1.5x bigger font
        )
        
        self.sentiment_box.add_widget(self.sentiment_label)
        self.sentiment_box.add_widget(self.sentiment_value)
        
        # Stock price info display
        self.price_info_box = BoxLayout(
            orientation='vertical',
            size_hint_x=0.3,
            spacing=dp(2)
        )
        
        # Create labels for price information
        self.ticker_label = Label(
            text="",
            color=ELECTRIC_BLUE,
            bold=True,
            font_size=dp(18)
        )
        
        self.price_info_label = Label(
            text="",
            color=TEXT_COLOR,
            font_size=dp(14)
        )
        
        self.price_info_box.add_widget(self.ticker_label)
        self.price_info_box.add_widget(self.price_info_label)
        
        # Add controls to layout
        controls.add_widget(ticker_label)
        controls.add_widget(self.ticker_input)
        controls.add_widget(self.fetch_button)
        controls.add_widget(self.sentiment_box)
        controls.add_widget(self.price_info_box)
        
        self.main_layout.add_widget(controls)
        
        # Status bar
        self.status_bar = Label(
            text=self.status_text,
            size_hint_y=None,
            height=dp(30),
            halign='left',
            valign='middle',
            color=TEXT_COLOR
        )
        self.main_layout.add_widget(self.status_bar)
        
        # Table container
        table_container = BoxLayout(orientation='vertical')
        
        # Add table header
        self.table_header = NewsTableHeader()
        table_container.add_widget(self.table_header)
        
        # Scroll view for news items
        self.scroll_view = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True
        )
        
        # Container for news items
        self.news_container = GridLayout(
            cols=1,
            spacing=1,
            size_hint_y=None
        )
        # Make sure the height is such that scrolling works
        self.news_container.bind(minimum_height=self.news_container.setter('height'))
        
        self.scroll_view.add_widget(self.news_container)
        table_container.add_widget(self.scroll_view)
        
        self.main_layout.add_widget(table_container)
        
        return self.main_layout
    
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
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
            ticker = self.ticker_input.text.strip().upper()
            
            if not ticker:
                Clock.schedule_once(lambda dt: self._show_error("Stock Ticker is required"), 0)
                return
            
            # Create analyzer and fetch news with hardcoded API key
            api_key = "AIzaSyB1YG5MNCjG5vFoa4Bo3soSsgYFsKW4lYU"
            analyzer = StockNewsAnalyzer(api_key=api_key)
            articles = analyzer.fetch_stock_news(ticker_symbol=ticker)
            
            # Get stock price information
            stock_info = analyzer.get_stock_info()
            
            # Update UI on the main thread
            Clock.schedule_once(lambda dt: self._update_news_display(articles, stock_info), 0)
            
        except Exception as e:
            error_message = str(e)
            Clock.schedule_once(lambda dt: self._show_error(f"Error: {error_message}"), 0)
        finally:
            # Re-enable button
            Clock.schedule_once(lambda dt: self._enable_fetch_button(), 0)
    
    def _update_news_display(self, articles, stock_info):
        """Update the news display with fetched articles and stock information"""
        # Clear existing news items
        self.news_container.clear_widgets()
        
        # Update stock price information
        self._update_stock_price_display(stock_info)
        
        if not articles:
            self.status_text = "No news articles found"
            # Reset sentiment display
            Clock.schedule_once(lambda dt: self._update_sentiment_display("N/A", TEXT_COLOR), 0)
        else:
            # Count sentiments
            sentiment_counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}
            for article in articles:
                sentiment = article['sentiment'].strip().upper()
                if sentiment in sentiment_counts:
                    sentiment_counts[sentiment] += 1
            
            # Determine overall sentiment (most frequent)
            overall_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])
            sentiment_name, sentiment_count = overall_sentiment
            
            # Set sentiment color
            sentiment_color = POSITIVE_COLOR
            if sentiment_name == "NEGATIVE":
                sentiment_color = NEGATIVE_COLOR
            elif sentiment_name == "NEUTRAL":
                sentiment_color = NEUTRAL_COLOR
                
            # Update sentiment display
            Clock.schedule_once(lambda dt: self._update_sentiment_display(sentiment_name, sentiment_color), 0)
            
            # Add news items to the container
            for i, article in enumerate(articles):
                news_item = NewsTableRow(article, i)
                self.news_container.add_widget(news_item)
            
            # Create a sorted list of sentiments by count (descending)
            sorted_sentiments = sorted(sentiment_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Format the sentiment counts for display with color coding
            from kivy.utils import escape_markup
            
            # Create colored text for each sentiment count
            sentiment_colors = {
                "POSITIVE": POSITIVE_COLOR,
                "NEGATIVE": NEGATIVE_COLOR,
                "NEUTRAL": NEUTRAL_COLOR
            }
            
            # Start with the overall sentiment
            sentiment_display = f"[color=#{self._color_to_hex(sentiment_colors[sentiment_name])}]{sentiment_count} {sentiment_name}[/color]"
            
            # Add the rest of the sentiments in decreasing order
            for sent_name, sent_count in sorted_sentiments:
                if sent_name != sentiment_name:  # Skip the overall sentiment (already displayed)
                    color_hex = self._color_to_hex(sentiment_colors[sent_name])
                    sentiment_display += f", [color=#{color_hex}]{sent_count} {sent_name}[/color]"
            
            # Update status text with all sentiment counts
            self.status_text = f"Found {len(articles)} news articles - {sentiment_display}"
            self.status_bar.markup = True  # Enable markup for the status bar
        
        self.status_bar.text = self.status_text
    
    def _enable_fetch_button(self):
        """Re-enable the fetch button"""
        self.fetch_button.disabled = False
    
    def _update_sentiment_display(self, sentiment_text, sentiment_color):
        """Update the sentiment display with the given text and color"""
        self.sentiment_value.text = sentiment_text
        self.sentiment_value.color = sentiment_color
    
    def _update_stock_price_display(self, stock_info):
        """Update the stock price information display"""
        if stock_info and 'ticker' in stock_info:
            ticker = stock_info['ticker']
            self.ticker_label.text = f"{ticker}"
            
            if 'price_data' in stock_info and stock_info['price_data']:
                price_data = stock_info['price_data']
                open_price = price_data['open']
                close_price = price_data['close']
                intraday_change = price_data['intraday_change']
                prev_close = price_data.get('prev_close')
                prev_close_change = price_data.get('prev_close_change')
                
                # Set color based on intraday percent change
                intraday_color = POSITIVE_COLOR if intraday_change >= 0 else NEGATIVE_COLOR
                intraday_sign = "+" if intraday_change >= 0 else ""
                
                # Create price info text
                price_info = f"Open: ${open_price} | Close: ${close_price} | Today: {intraday_sign}{intraday_change}%"
                
                # Add previous close info if available
                if prev_close is not None and prev_close_change is not None:
                    prev_sign = "+" if prev_close_change >= 0 else ""
                    prev_color = POSITIVE_COLOR if prev_close_change >= 0 else NEGATIVE_COLOR
                    
                    # Create a second label for previous close info
                    self.price_info_label.text = price_info
                    self.price_info_label.color = intraday_color
                    
                    # Update or create the previous close label
                    if not hasattr(self, 'prev_close_label'):
                        self.prev_close_label = Label(
                            text=f"Prev Close: ${prev_close} | Change: {prev_sign}{prev_close_change}%",
                            color=prev_color,
                            font_size=dp(14)
                        )
                        self.price_info_box.add_widget(self.prev_close_label)
                    else:
                        self.prev_close_label.text = f"Prev Close: ${prev_close} | Change: {prev_sign}{prev_close_change}%"
                        self.prev_close_label.color = prev_color
                else:
                    # Just show intraday change if previous close isn't available
                    self.price_info_label.text = price_info
                    self.price_info_label.color = intraday_color
                    
                    # Remove previous close label if it exists
                    if hasattr(self, 'prev_close_label') and self.prev_close_label in self.price_info_box.children:
                        self.price_info_box.remove_widget(self.prev_close_label)
            else:
                self.price_info_label.text = "Price data unavailable"
                self.price_info_label.color = TEXT_COLOR
        else:
            self.ticker_label.text = ""
            self.price_info_label.text = ""
            
            # Remove previous close label if it exists
            if hasattr(self, 'prev_close_label') and self.prev_close_label in self.price_info_box.children:
                self.price_info_box.remove_widget(self.prev_close_label)
    
    def _color_to_hex(self, color_tuple):
        """Convert a color tuple (r, g, b, a) to hex format without alpha"""
        r, g, b, a = color_tuple
        return f"{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        
    def _show_error(self, message):
        """Show an error popup"""
        self.status_text = message
        self.status_bar.text = self.status_text
        # Reset displays
        self._update_sentiment_display("N/A", TEXT_COLOR)
        self._update_stock_price_display(None)
        
        content = BoxLayout(orientation='vertical', padding=dp(10))
        
        error_label = Label(
            text=message,
            color=TEXT_COLOR
        )
        content.add_widget(error_label)
        
        close_button = Button(
            text="Close",
            size_hint=(None, None),
            size=(dp(100), dp(40)),
            pos_hint={'center_x': 0.5},
            background_color=ACCENT_COLOR
        )
        content.add_widget(close_button)
        
        popup = Popup(
            title='Error',
            content=content,
            size_hint=(None, None),
            size=(400, 200),
            background_color=DARKER_BG,
            title_color=TEXT_COLOR
        )
        
        close_button.bind(on_release=popup.dismiss)
        popup.open()
        self.fetch_button.disabled = False

if __name__ == '__main__':
    StockNewsApp().run()
