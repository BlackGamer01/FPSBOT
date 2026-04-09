import os
import shutil
import zipfile
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from r import TencentPakFile, repack_gamepatch

BOT_TOKEN = "8553167317:AAGRD1DLmiPBLUbKd_9DHlrYVX6bnoGgdgQ"

# 🔥 FIXED: Use Windows path based on script location
fps_folder = str(Path(__file__).parent.resolve())
main_folder = os.path.join(fps_folder, "MAIN")
mod_folder = os.path.join(fps_folder, "MOD")

dat_file = os.path.join(fps_folder, "Client120FPSMapping.uexp")
pak_file = os.path.join(fps_folder, "game_patch_4.3.0.20980.pak")

processing_queue = asyncio.Queue()


# 🔹 Modify + Repack
def modify_file(model_number: str):
    dat_file_main = os.path.join(main_folder, "Client120FPSMapping.uexp")
    pak_file_main = os.path.join(main_folder, "game_patch_4.3.0.20980.pak")

    if not os.path.exists(dat_file):
        return "Error: DAT file missing!"
    if not os.path.exists(pak_file):
        return "Error: PAK file missing!"

    os.makedirs(main_folder, exist_ok=True)
    os.makedirs(mod_folder, exist_ok=True)

    # Copy files
    shutil.copy(dat_file, dat_file_main)
    shutil.copy(pak_file, pak_file_main)

    # 🔥 Replace model string
    old_text = b"SM-S921U1|SM-S921W|SM-S921N"
    new_text = model_number.encode().ljust(len(old_text), b'|')

    with open(dat_file_main, "rb") as f:
        content = f.read()

    content = content.replace(old_text, new_text)

    with open(dat_file_main, "wb") as f:
        f.write(content)

    # 🔥 Proper r.py repack
    try:
        pak_path = Path(pak_file_main)
        output_path = pak_path.with_suffix(".repacked")

        pak = TencentPakFile(pak_path)

        repack_gamepatch(
            pak,
            Path(main_folder),
            output_path
        )

        if not output_path.exists():
            return "Error: Repack failed - no output file!"

        # Replace original pak
        os.remove(pak_file_main)
        os.rename(output_path, pak_file_main)

    except Exception as e:
        return f"Error: Repack exception - {str(e)}"

    # Move to MOD
    final_pak = os.path.join(mod_folder, "game_patch_4.3.0.20980.pak")
    shutil.copy(pak_file_main, final_pak)

    # ZIP
    zip_path = os.path.join(mod_folder, f"BlackGamerOG{model_number}.zip")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        zipf.write(final_pak, "game_patch_4.3.0.20980.pak")

    # Delete PAK from MOD folder (keep only ZIP)
    os.remove(final_pak)

    # Clean MAIN
    for f in os.listdir(main_folder):
        p = os.path.join(main_folder, f)
        if os.path.isfile(p):
            os.remove(p)

    return zip_path


# 🔹 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 @BlackGamerOG FPS BOT READY 🔥\nUse: /modify <MODEL>"
    )


# 🔹 /modify
async def modify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from telegram.error import TimedOut, NetworkError
    import asyncio
    
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /modify <model>")
        return

    model = context.args[0]

    zip_path = os.path.join(mod_folder, f"BlackGamerOG {model}.zip")

    if os.path.exists(zip_path):
        try:
            with open(zip_path, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=os.path.basename(zip_path),
                    caption="🔥 Already Cached File"
                )
            return
        except (TimedOut, NetworkError) as e:
            await update.message.reply_text(f"⚠️ Network error: {str(e)}\nTry again!")
            return

    msg = await update.message.reply_text(f"Processing {model}...")

    await processing_queue.put(model)

    result = modify_file(model)

    if result.startswith("Error") or "failed" in result.lower():
        await update.message.reply_text(result)
        await processing_queue.get()
        return

    if not os.path.exists(result):
        await update.message.reply_text("Error: Output file not found!")
        await processing_queue.get()
        return

    # Check file size (Telegram limit: 50MB)
    file_size_mb = os.path.getsize(result) / (1024 * 1024)
    await update.message.reply_text(f"📦 File size: {file_size_mb:.2f} MB")
    
    if file_size_mb > 50:
        await update.message.reply_text(
            f"⚠️ File too large for Telegram ({file_size_mb:.2f} MB)\n"
            f"Max limit: 50 MB\n\n"
            f"📁 File location:\n`{result}`",
            parse_mode='Markdown'
        )
        await processing_queue.get()
        return

    # 🔥 Retry logic for upload (3 attempts)
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            await update.message.reply_text(f"📤 Uploading... (Attempt {attempt + 1}/{max_attempts})")
            with open(result, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=os.path.basename(result),
                    caption="🔥 Done Successfully",
                    read_timeout=120,  # Increased to 120 seconds for large files
                    write_timeout=120,
                    connect_timeout=30,
                    pool_timeout=30
                )
            await msg.delete()
            await update.message.reply_text("✅ Upload successful!")
            break  # Success - exit loop
        except (TimedOut, NetworkError) as e:
            if attempt == max_attempts - 1:
                # Last attempt failed
                await update.message.reply_text(
                    f"⚠️ Upload failed after {max_attempts} attempts: {str(e)}\n\n"
                    f"📁 File is ready at:\n`{result}`\n\n"
                    f"💡 Tip: Send this file manually from your device!",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"⏳ Attempt {attempt + 1} failed. Retrying in 5 seconds...")
                await asyncio.sleep(5)  # Wait before retry
        finally:
            await processing_queue.get()


# 🔹 Main
def main():
    app = Application.builder() \
        .token(BOT_TOKEN) \
        .read_timeout(120) \
        .write_timeout(120) \
        .connect_timeout(30) \
        .pool_timeout(30) \
        .build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("modify", modify))

    print("Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
