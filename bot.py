
import os
import json
import logging
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from sheets_client import SheetsClient
from database import init_db, get_user_sheet, set_user_sheet

# Load environment variables dari file .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SHEET_NAME = os.getenv("SHEET_NAME", "Sheet1")
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE", "credentials.json")

# Inisialisasi database SQLite
init_db()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ambil email Service Account secara dinamis (dari env variable atau file credentials.json)
SERVICE_ACCOUNT_EMAIL = "email_service_account_belum_diatur"
google_creds_env = os.getenv("GOOGLE_CREDENTIALS")

if google_creds_env:
    try:
        creds_data = json.loads(google_creds_env)
        SERVICE_ACCOUNT_EMAIL = creds_data.get("client_email", SERVICE_ACCOUNT_EMAIL)
    except Exception as e:
        logger.error(f"Gagal memproses GOOGLE_CREDENTIALS dari env variable: {e}")
elif os.path.exists(CREDENTIALS_FILE):
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            creds_data = json.load(f)
            SERVICE_ACCOUNT_EMAIL = creds_data.get("client_email", SERVICE_ACCOUNT_EMAIL)
    except Exception as e:
        logger.error(f"Gagal membaca email Service Account dari {CREDENTIALS_FILE}: {e}")

# Inisialisasi client Google Sheets (tanpa SPREADSHEET_ID statis)
sheets_client = SheetsClient(credentials_file=CREDENTIALS_FILE)

# Coba koneksi awal saat startup untuk memverifikasi credentials.json atau GOOGLE_CREDENTIALS env
try:
    if os.getenv("GOOGLE_CREDENTIALS") or os.path.exists(CREDENTIALS_FILE):
        sheets_client.connect()
        logger.info("Berhasil mengautentikasi ke Google API Service Account.")
    else:
        logger.warning("Kredensial Google Sheets belum dikonfigurasi penuh (credentials.json atau GOOGLE_CREDENTIALS env belum siap).")
except Exception as e:
    logger.error(f"Gagal otentikasi awal ke Google API: {e}")

def format_rupiah(value):
    """Format angka menjadi format mata uang Rupiah."""
    return f"Rp {value:,.0f}".replace(",", ".")

def parse_amount(text):
    """Membersihkan format input angka seperti 50.000 atau 50,000 menjadi 50000."""
    cleaned = text.replace(".", "").replace(",", "")
    return float(cleaned)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk perintah /start."""
    welcome_message = (
        "👋 **Halo! Saya adalah Bot Pencatat Keuangan Multi-User.**\n\n"
        "Saya dapat membantu mencatat pemasukan dan pengeluaran Anda ke Google Sheets pribadi Anda.\n\n"
        "🛠 **Cara Konfigurasi Awal:**\n"
        "1. Buat Google Sheets baru di akun Google Anda.\n"
        "2. Tekan tombol **Share (Bagikan)** di kanan atas spreadsheet Anda.\n"
        "3. Berikan akses **Editor** ke email Service Account bot ini:\n"
        f"   `{SERVICE_ACCOUNT_EMAIL}`\n"
        "4. Hubungkan spreadsheet dengan menyalin **ID Spreadsheet** Anda, lalu kirim ke bot:\n"
        "   `/set_sheet <ID_SPREADSHEET>`\n\n"
        "🔍 **Cara Menemukan ID Spreadsheet:**\n"
        "ID spreadsheet adalah deretan karakter unik di tengah URL spreadsheet Anda.\n"
        "Jika URL sheet Anda:\n"
        "👉 `https://docs.google.com/spreadsheets/d/`**`1a2b3c4d5e...`**`/edit#gid=0`\n"
        "Maka ID-nya adalah: `1a2b3c4d5e...`\n\n"
        "📌 **Cara Penggunaan (setelah dihubungkan):**\n"
        "📥 *Pemasukan:* `/masuk <jumlah> <keterangan>`\n"
        "   Contoh: `/masuk 1500000 Gaji Bulanan`\n"
        "💸 *Pengeluaran:* `/keluar <jumlah> <keterangan>`\n"
        "   Contoh: `/keluar 25000 Makan Siang`\n"
        "📊 *Laporan:* `/laporan` untuk melihat saldo Anda.\n\n"
        "💡 *Tips:* Jika Anda mengklik menu `/masuk` atau `/keluar` langsung, bot akan membimbing Anda secara bertahap!"
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

async def set_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mendaftarkan spreadsheet_id milik pengguna."""
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text(
            "❌ Format salah!\n"
            "Gunakan format: `/set_sheet <ID_SPREADSHEET>`\n"
            "Contoh: `/set_sheet 1a2b3c4d5e...`"
        )
        return

    spreadsheet_id = context.args[0].strip()
    loading_msg = await update.message.reply_text("⏳ Memverifikasi akses ke spreadsheet Anda...")

    try:
        # Lakukan verifikasi akses dengan mencoba membuka worksheet
        sheets_client.connect()
        sheets_client._get_worksheet(spreadsheet_id, SHEET_NAME)

        # Jika berhasil terbuka, simpan relasi user_id -> spreadsheet_id ke SQLite DB
        set_user_sheet(user_id, spreadsheet_id)

        success_msg = (
            "✅ *Spreadsheet Berhasil Dihubungkan!*\n\n"
            "Kini Anda bisa mulai mencatat transaksi keuangan Anda:\n"
            "📥 `/masuk <jumlah> <keterangan>`\n"
            "💸 `/keluar <jumlah> <keterangan>`\n"
            "📊 `/laporan` untuk melihat total keuangan"
        )
        await loading_msg.edit_text(success_msg, parse_mode="Markdown")
    except ValueError:
        await loading_msg.edit_text(
            "❌ *ID Spreadsheet Tidak Valid!*\n\n"
            "Periksa kembali ID yang Anda masukkan. Pastikan ID disalin dari URL browser spreadsheet Anda.",
            parse_mode="Markdown"
        )
    except PermissionError:
        await loading_msg.edit_text(
            "❌ *Akses Ditolak!*\n\n"
            "Bot belum diberi akses ke spreadsheet Anda. Pastikan Anda telah:\n"
            "1. Membuka Google Sheet Anda.\n"
            "2. Menekan tombol **Share (Bagikan)**.\n"
            "3. Membagikan akses **Editor** ke email berikut:\n"
            f"`{SERVICE_ACCOUNT_EMAIL}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error memverifikasi spreadsheet: {e}")
        await loading_msg.edit_text(
            f"❌ Terjadi kesalahan saat mencoba menghubungkan spreadsheet.\n\n"
            f"**Detail Error:** `{str(e)}`"
        )

async def masuk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk perintah /masuk (Pemasukan)."""
    user_id = update.effective_user.id
    spreadsheet_id = get_user_sheet(user_id)

    if not spreadsheet_id:
        await update.message.reply_text(
            "❌ Anda belum menghubungkan spreadsheet!\n\n"
            "Silakan bagikan spreadsheet Anda ke email berikut sebagai **Editor**:\n"
            f"`{SERVICE_ACCOUNT_EMAIL}`\n\n"
            "Lalu ketik perintah:\n"
            "`/set_sheet <ID_SPREADSHEET>`",
            parse_mode="Markdown"
        )
        return

    # Periksa argumen perintah
    if not context.args:
        # Masuk ke mode step-by-step jika tidak ada parameter
        context.user_data['temp_transaction'] = {
            'type': 'Pemasukan',
            'step': 'amount'
        }
        await update.message.reply_text(
            "📥 *Pencatatan Pemasukan*\n\n"
            "Masukkan jumlah pemasukan Anda (angka saja):\n"
            "_(Ketik /cancel untuk membatalkan)_",
            parse_mode="Markdown"
        )
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Format salah!\n"
            "Gunakan format: `/masuk <jumlah> <keterangan>`\n"
            "Contoh: `/masuk 100000 Hadiah Ulang Tahun`"
        )
        return

    amount_str = context.args[0]
    description = " ".join(context.args[1:])

    try:
        amount = parse_amount(amount_str)
        if amount <= 0:
            raise ValueError("Jumlah harus lebih besar dari 0.")
    except ValueError:
        await update.message.reply_text("❌ Jumlah yang dimasukkan tidak valid. Harap masukkan angka saja.")
        return

    loading_msg = await update.message.reply_text("⏳ Sedang menyimpan data ke Google Sheets...")

    try:
        # Tambah record ke Google Sheet milik user tersebut
        sheets_client.add_record(spreadsheet_id, SHEET_NAME, "Pemasukan", amount, description)
        formatted_amount = format_rupiah(amount)
        await loading_msg.edit_text(
            f"✅ *Pemasukan Berhasil Dicatat!*\n\n"
            f"💰 Jumlah: *{formatted_amount}*\n"
            f"📝 Keterangan: {description}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error mencatat pemasukan: {e}")
        await loading_msg.edit_text(
            "❌ Terjadi kesalahan saat menyimpan data. "
            "Pastikan spreadsheet Anda masih terhubung dengan email Service Account bot."
        )

async def keluar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk perintah /keluar (Pengeluaran)."""
    user_id = update.effective_user.id
    spreadsheet_id = get_user_sheet(user_id)

    if not spreadsheet_id:
        await update.message.reply_text(
            "❌ Anda belum menghubungkan spreadsheet!\n\n"
            "Silakan bagikan spreadsheet Anda ke email berikut sebagai **Editor**:\n"
            f"`{SERVICE_ACCOUNT_EMAIL}`\n\n"
            "Lalu ketik perintah:\n"
            "`/set_sheet <ID_SPREADSHEET>`",
            parse_mode="Markdown"
        )
        return

    # Periksa argumen perintah
    if not context.args:
        # Masuk ke mode step-by-step jika tidak ada parameter
        context.user_data['temp_transaction'] = {
            'type': 'Pengeluaran',
            'step': 'amount'
        }
        await update.message.reply_text(
            "💸 *Pencatatan Pengeluaran*\n\n"
            "Masukkan jumlah pengeluaran Anda (angka saja):\n"
            "_(Ketik /cancel untuk membatalkan)_",
            parse_mode="Markdown"
        )
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Format salah!\n"
            "Gunakan format: `/keluar <jumlah> <keterangan>`\n"
            "Contoh: `/keluar 15000 Makan Siang`"
        )
        return

    amount_str = context.args[0]
    description = " ".join(context.args[1:])

    try:
        amount = parse_amount(amount_str)
        if amount <= 0:
            raise ValueError("Jumlah harus lebih besar dari 0.")
    except ValueError:
        await update.message.reply_text("❌ Jumlah yang dimasukkan tidak valid. Harap masukkan angka saja.")
        return

    loading_msg = await update.message.reply_text("⏳ Sedang menyimpan data ke Google Sheets...")

    try:
        # Tambah record ke Google Sheet milik user tersebut
        sheets_client.add_record(spreadsheet_id, SHEET_NAME, "Pengeluaran", amount, description)
        formatted_amount = format_rupiah(amount)
        await loading_msg.edit_text(
            f"✅ *Pengeluaran Berhasil Dicatat!*\n\n"
            f"💸 Jumlah: *{formatted_amount}*\n"
            f"📝 Keterangan: {description}",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error mencatat pengeluaran: {e}")
        await loading_msg.edit_text(
            "❌ Terjadi kesalahan saat menyimpan data. "
            "Pastikan spreadsheet Anda masih terhubung dengan email Service Account bot."
        )

async def laporan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk perintah /laporan."""
    user_id = update.effective_user.id
    spreadsheet_id = get_user_sheet(user_id)

    if not spreadsheet_id:
        await update.message.reply_text(
            "❌ Anda belum menghubungkan spreadsheet!\n\n"
            "Silakan bagikan spreadsheet Anda ke email berikut sebagai **Editor**:\n"
            f"`{SERVICE_ACCOUNT_EMAIL}`\n\n"
            "Lalu ketik perintah:\n"
            "`/set_sheet <ID_SPREADSHEET>`",
            parse_mode="Markdown"
        )
        return

    loading_msg = await update.message.reply_text("⏳ Sedang menghitung laporan...")

    try:
        summary = sheets_client.get_summary(spreadsheet_id, SHEET_NAME)
        msg = (
            "📊 *LAPORAN KEUANGAN SAAT INI*\n\n"
            f"📥 Total Pemasukan: *{format_rupiah(summary['pemasukan'])}*\n"
            f"💸 Total Pengeluaran: *{format_rupiah(summary['pengeluaran'])}*\n"
            "----------------------------\n"
            f"💰 Saldo Akhir: *{format_rupiah(summary['saldo'])}*"
        )
        await loading_msg.edit_text(msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error mendapatkan laporan: {e}")
        await loading_msg.edit_text("❌ Terjadi kesalahan saat memproses laporan dari Google Sheets.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Membatalkan proses input transaksi saat ini."""
    if 'temp_transaction' in context.user_data:
        context.user_data.pop('temp_transaction')
        await update.message.reply_text("❌ Transaksi dibatalkan.")
    else:
        await update.message.reply_text("Tidak ada transaksi aktif yang sedang berjalan.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani input pesan teks dari pengguna untuk alur step-by-step."""
    user_id = update.effective_user.id
    temp = context.user_data.get('temp_transaction')

    if not temp:
        # Jika tidak dalam proses transaksi, abaikan saja
        return

    step = temp.get('step')
    trans_type = temp.get('type')

    if step == 'amount':
        # Proses input jumlah uang
        amount_str = update.message.text.strip()
        try:
            amount = parse_amount(amount_str)
            if amount <= 0:
                raise ValueError()
            
            # Simpan jumlah dan ubah step ke keterangan
            temp['amount'] = amount
            temp['step'] = 'description'
            
            await update.message.reply_text(
                f"💰 *Jumlah dicatat:* {format_rupiah(amount)}\n\n"
                f"Sekarang, masukkan keterangan/deskripsi untuk {trans_type.lower()} ini:\n"
                "_(Ketik /cancel untuk membatalkan)_",
                parse_mode="Markdown"
            )
        except ValueError:
            await update.message.reply_text("❌ Jumlah tidak valid. Harap masukkan angka saja (Contoh: 50000 atau 50.000):")

    elif step == 'description':
        # Proses input deskripsi dan simpan ke sheets
        description = update.message.text.strip()
        amount = temp['amount']
        
        spreadsheet_id = get_user_sheet(user_id)
        if not spreadsheet_id:
            context.user_data.pop('temp_transaction')
            await update.message.reply_text("❌ Spreadsheet Anda terputus. Harap hubungkan kembali dengan `/set_sheet`.")
            return

        loading_msg = await update.message.reply_text("⏳ Sedang menyimpan data ke Google Sheets...")
        
        try:
            sheets_client.add_record(spreadsheet_id, SHEET_NAME, trans_type, amount, description)
            formatted_amount = format_rupiah(amount)
            
            # Hapus transaksi sementara karena sudah sukses
            context.user_data.pop('temp_transaction')
            
            await loading_msg.edit_text(
                f"✅ *{trans_type} Berhasil Dicatat!*\n\n"
                f"💰 Jumlah: *{formatted_amount}*\n"
                f"📝 Keterangan: {description}",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error mencatat transaksi step-by-step: {e}")
            await loading_msg.edit_text(
                "❌ Terjadi kesalahan saat menyimpan data ke Google Sheets. "
                "Pastikan spreadsheet Anda masih terhubung dengan email Service Account bot."
            )

async def post_init(application):
    """Dijalankan setelah bot terhubung untuk mengeset menu perintah di aplikasi Telegram."""
    await application.bot.set_my_commands([
        BotCommand("start", "Melihat panduan awal & cara konfigurasi"),
        BotCommand("set_sheet", "Menghubungkan Google Sheet pribadi Anda"),
        BotCommand("masuk", "Mencatat pemasukan (Uang Masuk)"),
        BotCommand("keluar", "Mencatat pengeluaran (Uang Keluar)"),
        BotCommand("laporan", "Melihat saldo dan total pemasukan/pengeluaran"),
        BotCommand("cancel", "Membatalkan proses input saat ini")
    ])

def main():
    """Menjalankan bot."""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        print("\n[ERROR] TELEGRAM_BOT_TOKEN belum diset di file .env!")
        print("Silakan buka file .env dan isi TELEGRAM_BOT_TOKEN dengan token bot Anda.")
        return

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    # Daftarkan handler perintah
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_sheet", set_sheet))
    app.add_handler(CommandHandler("masuk", masuk))
    app.add_handler(CommandHandler("keluar", keluar))
    app.add_handler(CommandHandler("laporan", laporan))
    app.add_handler(CommandHandler("cancel", cancel))
    
    # Message handler untuk menangani teks biasa saat alur input bertahap
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("\n=======================================================")
    print("Bot Telegram Multi-User sedang berjalan...")
    print("Tekan Ctrl+C untuk menghentikan.")
    print("=======================================================\n")
    
    app.run_polling()

if __name__ == '__main__':
    main()
