import logging
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from rembg import remove
from PIL import Image
from io import BytesIO

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace 'YOUR_TOKEN_HERE' with your actual bot token
BOT_TOKEN = '1114907949:AAFiJ-iWmImrGbaCGhUcRHDWjvgclWWDyfI'


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Hi there! 🎉 Send me an image file, and I will remove its background for you.')


async def handle_document(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Processing your image... Please wait.')

    try:
        file = await update.message.document.get_file()
        logger.info('Downloading the document...')
        await file.download_to_drive('input_image.jpg')

        logger.info('Opening the image file...')
        with open('input_image.jpg', 'rb') as image_file:
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

    except Exception as e:
        logger.error(f'An error occurred: {e}')
        await update.message.reply_text('your image is ready ❤️')


def main() -> None:
    # Set up the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Start the Bot
    logger.info('Starting the bot...')
    application.run_polling()
    logger.info('Bot is running.')


if __name__ == '__main__':
    main()
