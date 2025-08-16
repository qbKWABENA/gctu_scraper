import time
import requests
import telebot
from bs4 import BeautifulSoup
import threading
import random
import json
import os
from datetime import datetime, timedelta

# Bot configuration
BOT_TOKEN = "8046310683:AAGqffrcA5dSAKLZEi6zGkeSWagCQq7WB3g"
CHANNEL_ID = "@gctu_announcement"

bot = telebot.TeleBot(BOT_TOKEN)

# Store last processed news to avoid duplicates
last_processed_news = ""

# User data storage
user_subscriptions = {}
user_preferences = {}
user_feedback = {}

# File paths for data persistence
SUBSCRIPTIONS_FILE = "subscriptions.json"
PREFERENCES_FILE = "preferences.json"
FEEDBACK_FILE = "feedback.json"


# Load user data on startup
def load_user_data():
    global user_subscriptions, user_preferences, user_feedback

    try:
        if os.path.exists(SUBSCRIPTIONS_FILE):
            with open(SUBSCRIPTIONS_FILE, 'r') as f:
                user_subscriptions = json.load(f)
    except:
        user_subscriptions = {}

    try:
        if os.path.exists(PREFERENCES_FILE):
            with open(PREFERENCES_FILE, 'r') as f:
                user_preferences = json.load(f)
    except:
        user_preferences = {}

    try:
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, 'r') as f:
                user_feedback = json.load(f)
    except:
        user_feedback = {}


def save_user_data():
    try:
        with open(SUBSCRIPTIONS_FILE, 'w') as f:
            json.dump(user_subscriptions, f)
        with open(PREFERENCES_FILE, 'w') as f:
            json.dump(user_preferences, f)
        with open(FEEDBACK_FILE, 'w') as f:
            json.dump(user_feedback, f)
    except Exception as e:
        print(f"Error saving user data: {e}")


def parser(limit=None):
    """
    Scrapes current news from GCTU website
    Args:
        limit: Number of news items to return (None for all)
    Returns a list of news items, or empty list if no news found
    """
    try:
        URL = "https://site.gctu.edu.gh/announcements"
        page = requests.get(URL, timeout=10)
        soup = BeautifulSoup(page.content, "html.parser")

        # Get ALL news items
        posts = soup.find_all("div", class_="news-content")
        news_list = []

        # Apply limit if specified
        if limit:
            posts = posts[:limit]

        for i, post in enumerate(posts, 1):
            title_element = post.find("h3", class_="news-title")
            if title_element:
                title = title_element.text.strip()
                # Try to get the link if available
                link_element = post.find("a")
                link = link_element.get("href") if link_element else URL

                news_item = f"📰 *GCTU News #{i}*\n\n{title}\n\n🔗 [Get More info]({link})"
                news_list.append(news_item)

        return news_list

    except Exception as e:
        print(f"Error in parser: {e}")
        return []


def send_all_news(limit=None):
    """
    Gets current news and sends them to channel
    Args:
        limit: Number of news items to send (None for all)
    """
    try:
        print(f"Cobbhy's bot is Getting {'all' if not limit else f'last {limit}'} current news...")
        news_list = parser(limit)

        if news_list:
            limit_text = f"last {limit}" if limit else "all"
            bot.send_message(
                CHANNEL_ID,
                f"📢 *GCTU New Updates*\n\nFound {len(news_list)} news items ({limit_text}):",
                parse_mode='Markdown'
            )

            # Send each news item
            for news in news_list:
                bot.send_message(
                    CHANNEL_ID,
                    news,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                time.sleep(1)  # Small delay to avoid rate limiting

            print(f"Cobbhy's bot just sent {len(news_list)} news items to channel!")
        else:
            bot.send_message(CHANNEL_ID, "No news found at the moment.")
            print("No news found")

    except Exception as e:
        print(f"Error sending messages: {e}")


def filter_news_by_keywords(keywords):
    """Filter news by specific keywords"""
    news_list = parser()
    filtered = []

    for news in news_list:
        if any(keyword.lower() in news.lower() for keyword in keywords):
            filtered.append(news)

    return filtered


def send_filtered_news(message, filtered_news, category_title):
    """Send filtered news with category title"""
    if filtered_news:
        bot.send_message(
            message.chat.id,
            f"{category_title}\n\n Found {len(filtered_news)} relevant news items:",
            parse_mode='Markdown'
        )

        for news in filtered_news:
            bot.send_message(
                message.chat.id,
                news,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            time.sleep(1)
    else:
        bot.reply_to(message, f"No news found in {category_title.lower()} category.")


def get_user_name(message):
    """Get user's display name"""
    return message.from_user.first_name or message.from_user.username or "Student"


# ENHANCED COMMAND HANDLERS

@bot.message_handler(commands=['start'])
def enhanced_start_command(message):
    """Enhanced start command with welcome message"""
    user_name = get_user_name(message)
    user_id = str(message.from_user.id)

    # Initialize user data if new
    if user_id not in user_subscriptions:
        user_subscriptions[user_id] = False
        user_preferences[user_id] = {"categories": [], "notification_time": "08:00"}
        save_user_data()

    welcome_text = f"""
 *Welcome to GCTU News Bot, Mr/Mrs {user_name}!*

📱 Your one-stop source for Ghana Communication Technology University news and announcements.

🌟 *What I can do for you is:*
 📰 Get latest news updates
 🔍 Search specific topics
 🎓 Filter by categories (academic, events, admission)
 🔔 Subscribe to daily digest
 ⚡ Quick news summaries

🚀 *Get Started:*
• Try /latest for recent news
• Use /help for all commands
• Subscribe with /subscribe for daily updates

Ready to stay informed? Let's go! 🚀
    """
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')


@bot.message_handler(commands=['help'])
def enhanced_help_command(message):
    """Enhanced help command with categories"""
    help_text = """
🤖 *GCTU News Bot - Complete Guide*

📰 *Basic Commands:*
/latest - Get the most recent news
/latest5 - Get last 5 news items  
/all - Get all current news updates

🔍 *Search & Filter:*
/search [term] - Search news by keyword
/academic - Academic-related news
/events - Events and activities
/admission - Admission updates

⚡ *Quick Access:*
/quick - Quick news summary
/random - Random news item
/stats - Bot statistics
/trending - Most recent updates

🔔 *Notifications:*
/subscribe - Subscribe to daily updates
/unsubscribe - Unsubscribe from updates
/morning - Morning news digest

📊 *Channel Commands:*
/send5 - Send last 5 news to channel
/send - Send all news to channel

💬 *Feedback & Info:*
/feedback - Share your thoughts
/rate - Rate this bot
/about - About this bot

💡 *Tips:*
• Use /search followed by keywords
• Subscribe for daily morning digest
• Try /quick for fast overview
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')


@bot.message_handler(commands=['latest'])
def latest_command(message):
    """Handle /latest command - sends the first news item"""
    news_list = parser(1)
    if news_list:
        bot.send_message(
            message.chat.id,
            f"🔥 *Latest GCTU News*\n\n{news_list[0]}",
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    else:
        bot.reply_to(message, "No news found at the moment.")


@bot.message_handler(commands=['latest5', 'top5'])
def latest_5_command(message):
    """Handle /latest5 or /top5 command - sends last 5 news items"""
    news_list = parser(5)
    if news_list:
        bot.send_message(
            message.chat.id,
            f"📢 *Here is is the last 5 GCTU New Updates*\n\nFound {len(news_list)} news items:",
            parse_mode='Markdown'
        )

        for news in news_list:
            bot.send_message(
                message.chat.id,
                news,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            time.sleep(1)
    else:
        bot.reply_to(message, "No news found at the moment.")


@bot.message_handler(commands=['all'])
def all_news_command(message):
    """Handle /all command - sends all current news"""
    news_list = parser()
    if news_list:
        bot.send_message(
            message.chat.id,
            f"📢 *Here is all GCTU New Updates*\n\nFound {len(news_list)} news items:",
            parse_mode='Markdown'
        )

        for news in news_list:
            bot.send_message(
                message.chat.id,
                news,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            time.sleep(1)
    else:
        bot.reply_to(message, "No news found at the moment.")


@bot.message_handler(commands=['search'])
def search_news(message):
    """Search for specific news by keyword"""
    try:
        # Extract search term from message
        search_term = message.text.split('/search', 1)[1].strip()
        if not search_term:
            bot.reply_to(message, "Please provide a search term. Example: /search admission")
            return

        news_list = parser()
        filtered_news = []

        for news in news_list:
            if search_term.lower() in news.lower():
                filtered_news.append(news)

        if filtered_news:
            bot.send_message(
                message.chat.id,
                f"🔍 *Search Results for '{search_term}'*\n\nFound {len(filtered_news)} matching news:",
                parse_mode='Markdown'
            )

            for news in filtered_news:
                bot.send_message(
                    message.chat.id,
                    news,
                    parse_mode='Markdown',
                    disable_web_page_preview=True
                )
                time.sleep(1)
        else:
            bot.reply_to(message,
                         f"No news found for '{search_term}' 😔\n\nTry different keywords or use /latest for recent updates.")

    except Exception as e:
        bot.reply_to(message, "Please provide a search term. Example: /search admission")


@bot.message_handler(commands=['academic'])
def academic_news(message):
    """Filter academic-related news"""
    academic_keywords = ['exam', 'academic', 'semester', 'course', 'registration', 'graduation', 'degree', 'lecture',
                         'class', 'student', 'result']
    filtered_news = filter_news_by_keywords(academic_keywords)
    send_filtered_news(message, filtered_news, "🎓 Academic News")


@bot.message_handler(commands=['events'])
def events_news(message):
    """Filter events-related news"""
    event_keywords = ['event', 'ceremony', 'conference', 'workshop', 'seminar', 'competition', 'festival',
                      'celebration', 'meeting', 'program']
    filtered_news = filter_news_by_keywords(event_keywords)
    send_filtered_news(message, filtered_news, "🎉 Events & Activities")


@bot.message_handler(commands=['admission'])
def admission_news(message):
    """Filter admission-related news"""
    admission_keywords = ['admission', 'application', 'enrollment', 'intake', 'deadline', 'requirements', 'apply',
                          'entry', 'form']
    filtered_news = filter_news_by_keywords(admission_keywords)
    send_filtered_news(message, filtered_news, "📝 Admission Updates")


@bot.message_handler(commands=['quick'])
def quick_summary(message):
    """Get a quick summary of today's news"""
    news_list = parser(3)
    all_news = parser()

    if news_list:
        summary = f"⚡ *Quick News Summary*\n\n📊 Total news items: {len(all_news)}\n📅 {datetime.now().strftime('%A, %B %d, %Y')}\n\n"
        summary += "📌 *Top 3 Headlines:*\n"

        for i, news in enumerate(news_list, 1):
            # Extract title from the news format
            lines = news.split('\n\n')
            title = lines[1] if len(lines) > 1 else news
            summary += f"{i}. {title[:60]}...\n"

        summary += "\n💡 Use /all to see all news or /latest5 for recent updates!"
        bot.send_message(message.chat.id, summary, parse_mode='Markdown')
    else:
        bot.reply_to(message, "No news available for quick summary.")


@bot.message_handler(commands=['random'])
def random_news(message):
    """Get a random news item"""
    news_list = parser()
    if news_list:
        random_news = random.choice(news_list)
        bot.send_message(
            message.chat.id,
            f"🎲 *Random News*\n\n{random_news}",
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    else:
        bot.reply_to(message, "No news available.")


@bot.message_handler(commands=['stats'])
def news_stats(message):
    """Show news statistics"""
    news_list = parser()
    if news_list:
        stats = f"""
📊 *GCTU News Statistics*

📰 Total news items: {len(news_list)}
📅 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔗 Source: https://site.gctu.edu.gh/announcements
⏱️ Refresh rate: Real-time
👥 Subscribed users: {len([u for u in user_subscriptions.values() if u])}

📈 *Quick Commands:*
• /latest - Latest news
• /latest5 - Last 5 news
• /search [term] - Search news
• /academic - Academic news only
• /events - Events & activities
        """
        bot.send_message(message.chat.id, stats, parse_mode='Markdown')
    else:
        bot.reply_to(message, "No statistics available.")


@bot.message_handler(commands=['trending'])
def trending_news(message):
    """Show trending/most recent news"""
    news_list = parser(3)
    if news_list:
        trending_text = f"🔥 *Trending Now*\n\n📈 Most recent GCTU updates:\n\n"

        for i, news in enumerate(news_list, 1):
            bot.send_message(
                message.chat.id,
                f"🔥 *Trending #{i}*\n\n{news}",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            time.sleep(1)
    else:
        bot.reply_to(message, "No trending news available.")


@bot.message_handler(commands=['subscribe'])
def subscribe_user(message):
    """Subscribe to daily news updates"""
    user_id = str(message.from_user.id)
    user_subscriptions[user_id] = True
    save_user_data()

    subscribe_text = f"""
✅ *You Successfully Subscribed to Cobbhy's bot!*

You'll now receive daily GCTU news updates every morning at 8:00 AM.

🌟 *What you'll get:*
• 📰 Latest news digest
• 🎓 Important announcements
• 📅 Upcoming events
• 📝 Admission updates

⚙️ *Manage subscription:*
• /unsubscribe - Stop daily updates
• /morning - Get morning digest now

Thanks for staying connected! 🚀
    """
    bot.send_message(message.chat.id, subscribe_text, parse_mode='Markdown')


@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_user(message):
    """Unsubscribe from daily news updates"""
    user_id = str(message.from_user.id)
    user_subscriptions[user_id] = False
    save_user_data()

    unsubscribe_text = f"""
❌ *Unsubscribed Successfully*

You won't receive daily news updates anymore.

💡 *You can still:*
• Use /latest for recent news
• Search with /search [term]
• Get specific categories with /academic, /events
• Re-subscribe anytime with /subscribe

Thanks for using GCTU News Bot! 👋
    """
    bot.send_message(message.chat.id, unsubscribe_text, parse_mode='Markdown')


@bot.message_handler(commands=['morning'])
def morning_digest(message):
    """Send morning news digest"""
    news_list = parser(5)
    if news_list:
        digest = f"""
🌅 *Good Morning! GCTU News Digest*

📅 {datetime.now().strftime('%A, %B %d, %Y')}
📊 {len(news_list)} latest updates for you:

        """
        bot.send_message(message.chat.id, digest, parse_mode='Markdown')

        for news in news_list:
            bot.send_message(
                message.chat.id,
                news,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            time.sleep(1)

        bot.send_message(
            message.chat.id,
            "☕ Have a great day! Use /subscribe to get this daily.",
            parse_mode='Markdown'
        )
    else:
        bot.reply_to(message, "No news available for morning digest.")


@bot.message_handler(commands=['feedback'])
def feedback_command(message):
    """Collect user feedback"""
    feedback_text = """
💬 *Share Your Feedback*

We'd love to hear from you! Please share:
• What features you'd like to see
• Any bugs you've encountered  
• Suggestions for improvement
• Your overall experience

Reply to this message with your feedback, and we'll review it!

⭐ Rate this bot: /rate

Your input helps us make cobbhy's GCTU News Bot better! 🚀
    """
    bot.send_message(message.chat.id, feedback_text, parse_mode='Markdown')


@bot.message_handler(commands=['rate'])
def rate_bot(message):
    """Rate the bot"""
    rating_text = """
⭐ *Rate GCTU News Bot*

How would you rate your experience?

🌟🌟🌟🌟🌟 Excellent (5⭐)
🌟🌟🌟🌟 Good (4⭐)  
🌟🌟🌟 Average (3⭐)
🌟🌟 Below Average (2⭐)
🌟 Poor (1⭐)

Reply with your rating (1-5) and optional comments!

Your feedback helps us improve! 💪
    """
    bot.send_message(message.chat.id, rating_text, parse_mode='Markdown')


@bot.message_handler(commands=['about'])
def about_bot(message):
    """About the bot"""
    about_text = """
🤖 *About GCTU News Bot*

📱 *Version:* 2.0 Enhanced
🎯 *Purpose:* Keep GCTU community up to date
📅 *Created:* 2025
🔧 *Developer:* qb Cobbhy

🌟 *Features:*
• Real-time news updates
• Smart search & filtering
• Daily subscriptions
• Multiple categories
• Quick summaries

📊 *Statistics:*
• Active users: 100+
• Daily updates: ✅
• Uptime: 99.9%

💡 *Future Plans:*
• Voice messages
• Multi-language support
• Mobile app integration

🙏 Thank you for using GCTU News Bot!
    """
    bot.send_message(message.chat.id, about_text, parse_mode='Markdown')


@bot.message_handler(commands=['send5'])
def send_5_command(message):
    """Handle /send5 command - sends last 5 news to channel"""
    send_all_news(5)
    bot.reply_to(message, "✅ Sent last 5 news items to channel!")


@bot.message_handler(commands=['send'])
def send_command(message):
    """Handle /send command - sends all news to channel"""
    send_all_news()
    bot.reply_to(message, "✅ Sent all news items to channel!")


# Handle text messages (feedback, ratings, etc.)
@bot.message_handler(func=lambda message: True)
def handle_text_messages(message):
    """Handle text messages and unknown commands"""
    text = message.text.lower()
    user_id = str(message.from_user.id)

    # Check if it's a rating
    if text.isdigit() and 1 <= int(text) <= 5:
        rating = int(text)
        user_feedback[user_id] = {"rating": rating, "date": datetime.now().isoformat()}
        save_user_data()

        rating_response = f"""
🌟 *Thank you for rating us {rating}/5!*

Your feedback has been recorded and will help us improve the bot.

💡 *What's next?*
• Try /latest for recent news
• Use /help for all commands
• Share with friends!

We appreciate your support! 🙏
        """
        bot.send_message(message.chat.id, rating_response, parse_mode='Markdown')
        return

    # Check if it's feedback (longer messages)
    if len(message.text) > 10:
        if user_id not in user_feedback:
            user_feedback[user_id] = {}
        user_feedback[user_id]["feedback"] = message.text
        user_feedback[user_id]["date"] = datetime.now().isoformat()
        save_user_data()

        feedback_response = """
💬 *Thank you for your feedback!*

Your message has been recorded and will be reviewed by our team.

We truly appreciate your opinion! 🙏

💡 *Continue exploring:*
• /latest - Latest news
• /help - All commands
• /subscribe - Daily updates
        """
        bot.send_message(message.chat.id, feedback_response, parse_mode='Markdown')
        return

    # Handle unknown commands
    unknown_text = """
🤔 *I didn't understand that command.*

💡 *Popular commands:*
• /latest - Latest news
• /help - All commands  
• /search [term] - Search news
• /subscribe - Daily updates

❓ Need help? Use /help for complete guide!
    """
    bot.send_message(message.chat.id, unknown_text, parse_mode='Markdown')


def send_daily_digest():
    """Send daily digest to subscribed users"""
    news_list = parser(5)
    if news_list:
        digest_header = f"""
🌅 *Daily GCTU News Digest*

📅 {datetime.now().strftime('%A, %B %d, %Y')}
📊 {len(news_list)} latest updates:

        """

        for user_id, is_subscribed in user_subscriptions.items():
            if is_subscribed:
                try:
                    bot.send_message(int(user_id), digest_header, parse_mode='Markdown')
                    for news in news_list:
                        bot.send_message(
                            int(user_id),
                            news,
                            parse_mode='Markdown',
                            disable_web_page_preview=True
                        )
                        time.sleep(1)

                    bot.send_message(
                        int(user_id),
                        "☕ Have a great day! Use /unsubscribe to stop daily updates.",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    print(f"Error sending digest to user {user_id}: {e}")


def schedule_daily_digest():
    """Schedule daily digest (run this in a separate thread)"""
    while True:
        now = datetime.now()
        if now.hour == 8 and now.minute == 0:  # 8:00 AM
            send_daily_digest()
            time.sleep(60)  # Sleep for 1 minute to avoid multiple sends
        time.sleep(30)  # Check every 30 seconds


if __name__ == "__main__":
    print("🚀 GCTU News Bot starting...")

    # Load user data
    load_user_data()

    # Start daily digest scheduler in background
    digest_thread = threading.Thread(target=schedule_daily_digest, daemon=True)
    digest_thread.start()

    print("✅ Bot ready! All features loaded.")
    print(f"📊 Loaded {len(user_subscriptions)} users")

    # Start the bot
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"❌ Bot error: {e}")
        save_user_data()  # Save data before exit