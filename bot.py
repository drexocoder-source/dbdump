import os
import subprocess
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# 🌿 Load environment variables
load_dotenv()

# 🔑 CONFIG
BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DB_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ⚙️ SETTINGS
USE_GZIP = True  # compress backup
BACKUP_DIR = "backups"

# 🪵 Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# 📁 Ensure backup folder exists
os.makedirs(BACKUP_DIR, exist_ok=True)


# 🔐 Access control
def is_authorized(user_id: int) -> bool:
    return ADMIN_ID == 0 or user_id == ADMIN_ID


# 🚀 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("🚫 Unauthorized access.")
        return

    await update.message.reply_text(
        "🤖 Neon Backup Bot Online\n\n"
        "Use /backup to create and download your database backup."
    )


# 💾 /backup
async def backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_authorized(user_id):
        await update.message.reply_text("🚫 Unauthorized access.")
        return

    msg = await update.message.reply_text("🗄️ Preparing backup...")

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if USE_GZIP:
            filename = f"{BACKUP_DIR}/backup_{timestamp}.sql.gz"
            command = f'pg_dump "{DB_URL}" | gzip > "{filename}"'
        else:
            filename = f"{BACKUP_DIR}/backup_{timestamp}.sql"
            command = f'pg_dump "{DB_URL}" > "{filename}"'

        # ⚡ Run command
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )

        # ❌ If failed
        if result.returncode != 0:
            error_msg = result.stderr.strip()

            if "compute time quota" in error_msg.lower():
                await msg.edit_text("❌ Neon quota exceeded. Cannot access DB right now.")
            else:
                await msg.edit_text(f"❌ Backup failed:\n{error_msg[:1000]}")
            return

        # 📤 Send file
        await msg.edit_text("📤 Uploading backup...")

        with open(filename, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=os.path.basename(filename)
            )

        await msg.edit_text("✅ Backup completed successfully!")

        # 🧹 Cleanup (optional)
        os.remove(filename)

    except Exception as e:
        await msg.edit_text(f"⚠️ Error: {str(e)[:1000]}")


# 🧩 Main
def main():
    if not BOT_TOKEN or not DB_URL:
        print("❌ Missing BOT_TOKEN or DB_URL in environment variables.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("backup", backup))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
