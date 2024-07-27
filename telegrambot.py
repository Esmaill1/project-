import logging
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from rembg import remove
from PIL import Image
import os

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace 'YOUR_TOKEN_HERE' with your actual bot token
BOT_TOKEN = 'YOUR_TOKEN_HERE'

# Channel username and link
CHANNEL_USERNAME = '@xsmind'
CHANNEL_LINK = 'https://t.me/xsmind'

# Language descriptions
LANGUAGE_DESCRIPTIONS = {
    'en': {
        'start': (
            "**Welcome to the Background Removal Bot** 🎨\n\n"
            "Hello there! I'm here to help you remove backgrounds from your images effortlessly. 🌟 Just send me a picture, and I’ll take care of the rest!\n\n"
            "**Here’s how to use me:**\n\n"
            "1. **Subscribe to Our Channel:** Before using the bot, make sure you're subscribed to our channel: [Subscribe Here](https://t.me/xsmind).\n"
            "2. **Send Your Image:** After subscribing, simply send me the image you want to process.\n"
            "3. **Receive Your Image:** I'll process the image and send it back with the background removed. 📸✨"
        ),
        'subscribe': (
            f"Oops! It looks like you need to subscribe to our channel first. Please join us here: {CHANNEL_LINK} and then click the button below to verify your subscription."
        ),
        'ready': (
            "You're all set! 🎉\n\n"
            "Go ahead and send me the image you want to process. I'll remove the background and send it back to you in no time. 📸✨"
        ),
        'result': (
            "Here’s your image with the background removed! 🖼️✨\n\n"
            "I hope you love it! If you need anything else, just let me know. 😊"
        ),
        'error': (
            "Oops! Something went wrong while processing your image. 😕 Please try again or contact support if the issue persists."
        )
    },
    'ar': {
        'start': (
            "**مرحبًا بك في بوت إزالة الخلفية** 🎨\n\n"
            "مرحبًا! أنا هنا لمساعدتك في إزالة الخلفيات من صورك بسهولة. 🌟 فقط أرسل لي صورة، وسأتولى الباقي!\n\n"
            "**إليك كيفية استخدامي:**\n\n"
            "1. **اشترك في قناتنا:** قبل استخدام البوت، تأكد من أنك مشترك في قناتنا: [اشترك هنا](https://t.me/xsmind).\n"
            "2. **أرسل صورتك:** بعد الاشتراك، فقط أرسل لي الصورة التي تريد معالجتها.\n"
            "3. **استلم صورتك:** سأقوم بمعالجة الصورة وإرسالها إليك مع إزالة الخلفية. 📸✨"
        ),
        'subscribe': (
            f"عذرًا! يبدو أنك بحاجة للاشتراك في قناتنا أولاً. يرجى الانضمام إلينا هنا: {CHANNEL_LINK} ثم انقر على الزر أدناه للتحقق من اشتراكك."
        ),
        'ready': (
            "أنت جاهز الآن! 🎉\n\n"
            "الرجاء إرسال الصورة التي تريد معالجتها. سأزيل الخلفية وأرسلها إليك في أقرب وقت. 📸✨"
        ),
        'result': (
            "إليك صورتك بعد إزالة الخلفية! 🖼️✨\n\n"
            "أتمنى أن تعجبك! إذا كنت بحاجة إلى أي مساعدة أخرى، فقط أخبرني. 😊"
        ),
        'error': (
            "عذرًا! حدث خطأ أثناء معالجة صورتك. 😕 يرجى المحاولة مرة أخرى أو الاتصال بالدعم إذا استمرت المشكلة."
        )
    }
}

async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("English", callback_data='lang_en')],
        [InlineKeyboardButton("عربي", callback_data='lang_ar')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Please select your language:', reply_markup=reply_markup)

async def select_language(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    lang_code = query.data.split('_')[-1]

    if lang_code not in LANGUAGE_DESCRIPTIONS:
        lang_code = 'en'

    context.user_data['language'] = lang_code

    await query.edit_message_text(
        LANGUAGE_DESCRIPTIONS[lang_code]['start'] + '\n\n' +
        f'If you are not subscribed, please join our channel: {CHANNEL_LINK}',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Check Subscription", callback_data='check_subscription')]
        ])
    )

async def check_subscription(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    lang_code = context.user_data.get('language', 'en')

    if await is_subscribed(user_id):
        await query.edit_message_text(
            LANGUAGE_DESCRIPTIONS[lang_code]['ready']
        )
    else:
        await query.edit_message_text(
            LANGUAGE_DESCRIPTIONS[lang_code]['subscribe'],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Check Subscription", callback_data='check_subscription')]
            ])
        )

async def is_subscribed(user_id: int) -> bool:
    """Check if a user is subscribed to the channel."""
    try:
        async with Application.builder().token(BOT_TOKEN).build() as app:
            member = await app.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
            return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f'An error occurred while checking subscription: {e}')
        return False

async def handle_document(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    lang_code = context.user_data.get('language', 'en')

    if not await is_subscribed(user_id):
        await update.message.reply_text(LANGUAGE_DESCRIPTIONS[lang_code]['subscribe'])
        return

    await update.message.reply_text('Processing your image... Please wait.')

    try:
        file = await update.message.document.get_file()
        logger.info('Downloading the document...')
        file_path = 'input_image.jpg'
        await file.download(file_path)

        logger.info('Opening the image file...')
        with open(file_path, 'rb') as image_file:
            input_image = Image.open(image_file)
            logger.info('Removing the background...')
            output_image = remove(input_image)

            # Save the result as a PNG file
            output_image_file = 'output_image.png'
            output_image.save(output_image_file, format='PNG')

            logger.info('Sending the processed image...')
            with open(output_image_file, 'rb') as output_file:
                await update.message.reply_document(document=InputFile(output_file, filename='output_image.png'))

        logger.info('Image processing complete and sent successfully.')
        await update.message.reply_text(LANGUAGE_DESCRIPTIONS[lang_code]['result'])

        os.remove(file_path)
        os.remove(output_image_file)

    except Exception as e:
        logger.error(f'An error occurred: {e}')
        await update.message.reply_text(LANGUAGE_DESCRIPTIONS[lang_code]['error'])

def main() -> None:
    # Set up the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(CallbackQueryHandler(select_language, pattern='^lang_'))
    application.add_handler(CallbackQueryHandler(check_subscription))

    # Start the Bot
    logger.info('Starting the bot...')
    application.run_polling()
    logger.info('Bot is running.')

if __name__ == '__main__':
    main()
