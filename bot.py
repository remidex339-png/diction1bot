import os
import io
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# Get bot token from Railway environment variables
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_URL = os.environ.get("RAILWAY_PUBLIC_DOMAIN") or os.environ.get("WEBHOOK_URL")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me an image, and I'll convert it to PDF!\n"
        "Supported formats: PNG, JPEG, JPG"
    )

async def convert_to_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Get the image from user
        photo = await update.message.photo[-1].get_file()
        image_bytes = await photo.download_as_bytearray()
        
        # Open image with PIL
        image = Image.open(io.BytesIO(image_bytes))
        
        # Create PDF in memory
        pdf_buffer = io.BytesIO()
        
        # Create PDF
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        width, height = letter
        
        # Convert PIL image to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Calculate image dimensions to fit on page
        img_width, img_height = image.size
        ratio = min(width / img_width, height / img_height)
        new_width = img_width * ratio
        new_height = img_height * ratio
        
        # Center image on page
        x = (width - new_width) / 2
        y = (height - new_height) / 2
        
        # Save image temporarily
        temp_img = io.BytesIO()
        image.save(temp_img, format='PNG')
        temp_img.seek(0)
        
        # Draw image on PDF
        c.drawImage(temp_img, x, y, new_width, new_height)
        c.save()
        
        # Send PDF back to user
        pdf_buffer.seek(0)
        await update.message.reply_document(
            document=pdf_buffer,
            filename="converted_image.pdf",
            caption="✅ Here's your PDF!"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot is alive!")

def main():
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    
    # Create bot application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("health", health_check))
    application.add_handler(MessageHandler(filters.PHOTO, convert_to_pdf))
    
    # Set webhook or polling
    if WEBHOOK_URL:
        # Use webhook (production on Railway)
        webhook_path = f"/webhook/{TOKEN}"
        full_webhook_url = f"{WEBHOOK_URL}{webhook_path}"
        
        print(f"🚀 Setting webhook: {full_webhook_url}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=webhook_path,
            webhook_url=full_webhook_url
        )
    else:
        # Fallback to polling (for local development)
        print("🤖 Running in polling mode...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
