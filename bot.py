import os
import io
from flask import Flask
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio

app = Flask(__name__)
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

@app.route('/')
def home():
    return "Image to PDF Bot is Running!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me any image and I'll convert it to PDF!")

async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo = await update.message.photo[-1].get_file()
        img_data = await photo.download_as_bytearray()
        image = Image.open(io.BytesIO(img_data))
        
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        w, h = letter
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        img_w, img_h = image.size
        ratio = min(w / img_w, h / img_h)
        nw = img_w * ratio
        nh = img_h * ratio
        x = (w - nw) / 2
        y = (h - nh) / 2
        
        temp = io.BytesIO()
        image.save(temp, format='PNG')
        temp.seek(0)
        
        c.drawImage(temp, x, y, nw, nh)
        c.save()
        
        pdf_buffer.seek(0)
        await update.message.reply_document(pdf_buffer, filename="image.pdf")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

if __name__ == "__main__":
    # Setup bot
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(MessageHandler(filters.PHOTO, convert))
    
    # Run bot in background
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(bot_app.run_polling())
    
    # Run Flask web server
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
