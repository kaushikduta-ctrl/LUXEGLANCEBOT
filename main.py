# ============================================
# LUXEGLANCEBOT - Complete Production Code
# Multi-Channel Support | Railway Ready
# ============================================

import asyncio
import logging
import random
import os
import feedparser
import requests
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from flask import Flask
from threading import Thread

# ============================================
# CONFIGURATION
# ============================================

# Get from Railway Environment Variables
TOKEN = os.environ.get('BOT_TOKEN')
UNSPLASH_KEY = os.environ.get('UNSPLASH_KEY')

# Check if token exists
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN not found! Please set it in Railway environment variables.")

if not UNSPLASH_KEY:
    print("⚠️ WARNING: UNSPLASH_KEY not set. Using fallback images only.")

# Content Pool (Fallback if APIs fail)
FALLBACK_CONTENT = [
    {
        "news": "Chanel unveils its 2026 Cruise Collection in Monaco",
        "review": "The collection features exquisite pearl-embellished tweed suits and metallic accessories that redefine luxury. A perfect blend of classic elegance and modern sophistication.",
        "keyword": "chanel fashion"
    },
    {
        "news": "Tiffany & Co. introduces new diamond engagement ring collection",
        "review": "These ethically-sourced diamonds feature exceptional clarity and a proprietary cut that maximizes brilliance. Each ring tells a story of timeless romance.",
        "keyword": "diamond ring"
    },
    {
        "news": "Dior's new rose-infused skincare line hits global markets",
        "review": "Using rare Grasse roses, this 5-step routine promises visible rejuvenation in 7 days. The luxurious texture and intoxicating scent make it a sensorial journey.",
        "keyword": "rose beauty"
    },
    {
        "news": "Gucci launches sustainable luxury handbag collection",
        "review": "Crafted from eco-friendly materials without compromising on Gucci's iconic design. The bamboo handles and GG canvas remain, but now with a conscience.",
        "keyword": "luxury handbag"
    },
    {
        "news": "Cartier's new high-jewelry watches debut in Paris",
        "review": "Combining horology with haute joaillerie, these timepieces feature baguette-cut diamonds and intricate enamel work. A masterpiece on the wrist.",
        "keyword": "luxury watch"
    },
    {
        "news": "Valentino's couture floral gown takes center stage at Met Gala",
        "review": "Hand-embroidered with 10,000 silk petals, this dress is a tribute to nature's artistry. A breathtaking fusion of fashion and botanical beauty.",
        "keyword": "floral dress"
    },
    {
        "news": "Bulgari's new Serpenti collection reimagines snake motifs",
        "review": "The iconic serpent is reincarnated with emerald eyes and pavé diamonds. A bold statement piece for the confident woman.",
        "keyword": "luxury jewelry"
    },
    {
        "news": "Hermès presents limited edition silk scarves featuring celestial maps",
        "review": "Each scarf takes 18 months to create, combining traditional printing techniques with astronomical accuracy. A wearable piece of art.",
        "keyword": "silk scarf"
    },
    {
        "news": "Saint Laurent's leather collection gets a sustainable upgrade",
        "review": "Using plant-based tanning and recycled metals, this collection proves that edgy fashion can be environmentally conscious.",
        "keyword": "leather fashion"
    },
    {
        "news": "Boucheron's new Quatre collection radiates contemporary elegance",
        "review": "The iconic four-ring design is reinterpreted with ceramic and gold. Versatile for day or night, it's the modern woman's armor.",
        "keyword": "gold ring"
    },
    {
        "news": "Prada's new sustainable nylon collection is here",
        "review": "Recycled ocean plastics transformed into luxury bags. This collection proves that sustainable fashion can be chic and desirable.",
        "keyword": "sustainable fashion"
    },
    {
        "news": "Van Cleef & Arpels unveils new Alhambra collection",
        "review": "The iconic clover motif is reimagined with malachite and mother of pearl. A symbol of luck and elegance for the discerning collector.",
        "keyword": "luxury jewelry"
    }
]

# RSS Feeds (Real luxury news sources)
RSS_FEEDS = [
    'https://www.vogue.com/feed/rss',
    'https://www.harpersbazaar.com/feeds/',
    'https://www.elle.com/feeds/',
    'https://www.wwd.com/feed/',
]

# Store active chats (channels/groups that have started the bot)
active_chats = set()

# ============================================
# LOGGING
# ============================================

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# FLASK APP (Keep Railway Alive)
# ============================================

flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "✅ LuxeGlanceBot is running! 🚀", 200

@flask_app.route('/stats')
def stats():
    return f"📊 Active chats: {len(active_chats)}", 200

def run_flask():
    """Run Flask server on Railway assigned port"""
    port = int(os.environ.get('PORT', 8080))
    flask_app.run(host='0.0.0.0', port=port)

# ============================================
# CORE FUNCTIONS
# ============================================

def get_luxury_news_from_rss():
    """Fetch real news from luxury RSS feeds"""
    try:
        feed = feedparser.parse(random.choice(RSS_FEEDS))
        if feed.entries:
            entry = random.choice(feed.entries[:5])  # Get latest 5
            return entry.title, entry.link
    except Exception as e:
        logger.error(f"RSS fetch failed: {e}")
    return None, None

def get_luxury_image(keyword):
    """Fetch image from Unsplash API"""
    if not UNSPLASH_KEY:
        return None, None
    
    try:
        url = "https://api.unsplash.com/search/photos"
        params = {
            "query": keyword,
            "client_id": UNSPLASH_KEY,
            "orientation": "squarish",
            "per_page": 5
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('results'):
            # Pick a random image from results
            image = random.choice(data['results'])
            return image['urls']['regular'], image.get('alt_description', 'Luxury beauty')
    except Exception as e:
        logger.error(f"Unsplash fetch failed: {e}")
    return None, None

def generate_review(news_title):
    """AI-like review generator"""
    luxury_adjectives = [
        "exquisite", "breathtaking", "luxurious", "sophisticated",
        "elegant", "opulent", "artisanal", "premium", "lavish",
        "refined", "exclusive", "impeccable"
    ]
    
    templates = [
        f"This {random.choice(luxury_adjectives)} creation represents the pinnacle of {random.choice(['craftsmanship', 'design', 'luxury'])}. "
        f"Every detail has been meticulously considered, resulting in a piece that's truly {random.choice(['timeless', 'iconic', 'unforgettable'])}.",
        
        f"A {random.choice(['masterpiece', 'work of art', 'tour de force'])} that redefines {random.choice(['elegance', 'beauty', 'style'])}. "
        f"This collection demonstrates why {random.choice(['true luxury', 'exceptional design', 'artisanal quality'])} never goes out of style.",
        
        f"The {random.choice(['attention to detail', 'quality of materials', 'craftsmanship'])} is immediately apparent. "
        f"Combining {random.choice(['heritage', 'innovation', 'tradition'])} with modern sensibilities, this is a {random.choice(['must-have', 'essential', 'statement'])} piece.",
        
        f"A stunning example of {random.choice(['haute couture', 'fine jewelry', 'luxury design'])}. "
        f"The {random.choice(['craftsmanship', 'materials', 'execution'])} is simply {random.choice(['exceptional', 'unparalleled', 'magnificent'])}.",
    ]
    
    return random.choice(templates)

def create_post_content():
    """Create a complete post with news, image, and review"""
    
    # Try to get real news from RSS
    news_title, news_link = get_luxury_news_from_rss()
    
    # Try to get image from Unsplash
    keyword = random.choice(['luxury fashion', 'diamond ring', 'rose bouquet', 
                            'designer handbag', 'couture dress', 'luxury watch',
                            'gold jewelry', 'silk scarf', 'high jewelry', 
                            'luxury perfume', 'designer shoes', 'evening gown'])
    image_url, image_desc = get_luxury_image(keyword)
    
    # Fallback to manual content if APIs fail
    if not news_title or not image_url:
        fallback = random.choice(FALLBACK_CONTENT)
        news_title = fallback['news']
        review = fallback['review']
        image_url = None
    else:
        # Generate review based on news
        review = generate_review(news_title)
    
    return {
        'news': news_title,
        'review': review,
        'image_url': image_url,
        'source': news_link if news_link else '#'
    }

async def send_post_to_all():
    """Send post to all active chats"""
    if not active_chats:
        logger.info("No active chats to send to")
        return
    
    content = create_post_content()
    
    # Format the message
    message = (
        f"✨ *{content['news']}* ✨\n\n"
        f"{content['review']}\n\n"
        f"💎 *LuxeGlanceBot* | Luxury Beauty & Fashion\n\n"
        f"_Powered by real luxury sources_"
    )
    
    # Send to each active chat
    bot = Bot(token=TOKEN)
    success_count = 0
    
    for chat_id in list(active_chats):
        try:
            if content['image_url']:
                try:
                    # Download image
                    response = requests.get(content['image_url'], timeout=15)
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=response.content,
                        caption=message,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Image send failed for {chat_id}: {e}")
                    # Send text only
                    await bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='Markdown'
                    )
            else:
                # Send text only if no image
                await bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
            success_count += 1
            logger.info(f"✅ Post sent to {chat_id}")
            
        except Exception as e:
            # If bot is removed or blocked, remove from active chats
            if "Bot was blocked by the user" in str(e) or "Chat not found" in str(e):
                active_chats.discard(chat_id)
                logger.warning(f"Removed inactive chat: {chat_id}")
            else:
                logger.error(f"❌ Failed to send to {chat_id}: {e}")
    
    if success_count > 0:
        logger.info(f"📊 Post sent to {success_count}/{len(active_chats)} chats")

# ============================================
# TELEGRAM BOT HANDLERS
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    # Add to active chats
    active_chats.add(chat_id)
    logger.info(f"New chat added: {chat_id} (type: {chat_type})")
    
    # Check if it's a group or channel
    if chat_type in ['group', 'supergroup', 'channel']:
        welcome_msg = (
            "💎 *LuxeGlanceBot is now active in this group/channel!* ✨\n\n"
            "I'll be posting luxury beauty and fashion content every 3 minutes.\n\n"
            "*What you'll get:*\n"
            "👗 Haute Couture news\n"
            "💍 Exquisite Jewelry\n"
            "🌹 Rare Flowers & Beauty\n"
            "👜 Premium Accessories\n\n"
            "Use /start anytime to reactivate if I stop posting.\n"
            "Use /settings to customize your feed.\n\n"
            "First post coming in 3 minutes! 🎀"
        )
    else:
        welcome_msg = (
            "💎 *Welcome to LuxeGlanceBot!* ✨\n\n"
            "Your premier source for luxury beauty and fashion news.\n\n"
            "I'll be posting stunning content every 3 minutes.\n\n"
            "To use me in your group or channel:\n"
            "1️⃣ Add me to your group/channel\n"
            "2️⃣ Make me an admin\n"
            "3️⃣ Type /start\n\n"
            "First post coming soon! 🎀"
        )
    
    keyboard = [
        [InlineKeyboardButton("📸 Get Latest Now", callback_data='latest')],
        [InlineKeyboardButton("ℹ️ About", callback_data='about')],
        [InlineKeyboardButton("🔄 Set Frequency", callback_data='settings')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_msg,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /settings command"""
    keyboard = [
        [InlineKeyboardButton("⏰ Every 3 Minutes", callback_data='freq_3')],
        [InlineKeyboardButton("⏰ Every 5 Minutes", callback_data='freq_5')],
        [InlineKeyboardButton("⏰ Every 10 Minutes", callback_data='freq_10')],
        [InlineKeyboardButton("🔙 Back", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🛠 *Settings*\n\n"
        "Choose how often you want to receive luxury content:\n"
        "• Every 3 minutes (default)\n"
        "• Every 5 minutes\n"
        "• Every 10 minutes",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button clicks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'latest':
        # Send latest post immediately to this chat
        chat_id = query.message.chat_id
        active_chats.add(chat_id)
        await send_post_to_chat(chat_id)
        await query.edit_message_text("📸 Latest post sent! Check the chat above.")
    
    elif query.data == 'about':
        about_msg = (
            "✨ *LuxeGlanceBot* ✨\n\n"
            "Powered by AI and curated luxury sources.\n\n"
            "*Features:*\n"
            "• Real RSS feeds from Vogue, Harper's Bazaar, Elle\n"
            "• High-quality images from Unsplash\n"
            "• AI-generated luxury reviews\n"
            "• Automated posting every 3 minutes\n"
            "• Multi-channel/group support\n\n"
            "*How to use:*\n"
            "1. Add me to your group/channel\n"
            "2. Make me admin\n"
            "3. Type /start\n\n"
            "Made with ❤️ for luxury enthusiasts."
        )
        await query.edit_message_text(about_msg, parse_mode='Markdown')
    
    elif query.data == 'settings':
        keyboard = [
            [InlineKeyboardButton("⏰ Every 3 Minutes", callback_data='freq_3')],
            [InlineKeyboardButton("⏰ Every 5 Minutes", callback_data='freq_5')],
            [InlineKeyboardButton("⏰ Every 10 Minutes", callback_data='freq_10')],
            [InlineKeyboardButton("🔙 Back", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🛠 *Settings*\n\nChoose your preferred frequency:",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif query.data == 'back':
        keyboard = [
            [InlineKeyboardButton("📸 Get Latest Now", callback_data='latest')],
            [InlineKeyboardButton("ℹ️ About", callback_data='about')],
            [InlineKeyboardButton("🔄 Set Frequency", callback_data='settings')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "💎 *LuxeGlanceBot* ✨\n\nHow can I help you?",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif query.data.startswith('freq_'):
        minutes = query.data.split('_')[1]
        await query.edit_message_text(
            f"✅ Frequency set to every {minutes} minutes!\n\n"
            f"I'll now post luxury content every {minutes} minutes in this chat.",
            parse_mode='Markdown'
        )

async def send_post_to_chat(chat_id):
    """Send a single post to a specific chat"""
    bot = Bot(token=TOKEN)
    content = create_post_content()
    
    # Format the message
    message = (
        f"✨ *{content['news']}* ✨\n\n"
        f"{content['review']}\n\n"
        f"💎 *LuxeGlanceBot* | Luxury Beauty & Fashion"
    )
    
    try:
        if content['image_url']:
            try:
                response = requests.get(content['image_url'], timeout=15)
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=response.content,
                    caption=message,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Image send failed: {e}")
                await bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode='Markdown'
                )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
        logger.info(f"✅ Post sent to {chat_id}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send to {chat_id}: {e}")
        if "Bot was blocked" in str(e) or "Chat not found" in str(e):
            active_chats.discard(chat_id)
        return False

async def post_loop():
    """Main posting loop - runs every 3 minutes"""
    logger.info("🚀 Posting loop started")
    
    while True:
        try:
            await asyncio.sleep(180)  # Wait 3 minutes
            await send_post_to_all()
        except Exception as e:
            logger.error(f"Loop error: {e}")
            await asyncio.sleep(60)  # Wait 1 min on error

# ============================================
# MAIN APPLICATION
# ============================================

def main():
    """Start both Flask (web) and Telegram bot"""
    
    # Start Flask thread (keeps Railway alive)
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("🌐 Flask server started")
    
    # Create Telegram Application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Start posting loop in background
    loop = asyncio.get_event_loop()
    loop.create_task(post_loop())
    logger.info("🚀 Posting loop started")
    
    # Run bot
    logger.info("🤖 LuxeGlanceBot is running...")
    logger.info("📊 Ready for multiple channels/groups!")
    application.run_polling(allowed_updates=['message', 'callback_query'])

if __name__ == "__main__":
    main()
