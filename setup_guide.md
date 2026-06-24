# Panduan Setup Bot Telegram Pencatat Keuangan (Multi-User)

Panduan ini menjelaskan langkah-langkah untuk menjalankan bot Telegram pencatat keuangan terintegrasi dengan Google Sheets secara multi-user.

---

## Langkah 1: Siapkan File `credentials.json` (Google Cloud Console)
Langkah ini wajib dilakukan oleh Anda sebagai pengembang/pemilik bot agar bot memiliki akses ke Google Sheets API:

1. Buka [Google Cloud Console](https://console.cloud.google.com/).
2. Buat proyek baru (klik dropdown nama proyek di kiri atas > **New Project**).
3. Cari **Google Sheets API** di kolom pencarian atas, klik hasil pencariannya, lalu klik **Enable** (Aktifkan).
4. Cari **Google Drive API** di kolom pencarian, klik, lalu klik **Enable** (Aktifkan).
5. Masuk ke menu samping (tiga garis di kiri atas) > **IAM & Admin** > **Service Accounts**.
6. Klik **Create Service Account** di bagian atas:
   - Isi *Service account name* bebas (misal: `bot-pencatat-keuangan`).
   - Klik **Create and Continue**, lalu klik **Done**.
7. Klik alamat email Service Account yang baru saja Anda buat.
8. Masuk ke tab **Keys** (di bagian atas), klik **Add Key** > **Create new key**, pilih format **JSON**, lalu klik **Create**.
9. File JSON kunci akan terunduh secara otomatis. Pindahkan/salin file JSON ini ke dalam folder proyek Anda (`d:\Projek Vibe Coding\telegram-bot\`) dan ubah namanya menjadi **`credentials.json`**.

---

## Langkah 2: Jalankan Bot di Terminal Anda
Pastikan Anda sudah mengisi `TELEGRAM_BOT_TOKEN` di file `.env`. Setelah itu, jalankan bot dengan:

1. Buka terminal atau Command Prompt di folder proyek `d:\Projek Vibe Coding\telegram-bot`.
2. Jalankan perintah:
   ```bash
   python bot.py
   ```
3. Bot Telegram Anda sekarang sudah aktif dan siap melayani pengguna.

---

## Langkah 3: Panduan Penggunaan oleh Anda & Orang Lain
Setelah bot Anda berjalan, siapa pun dapat menghubungkan Google Spreadsheet mereka dengan cara berikut:

1. Cari bot Anda di Telegram dan ketik perintah `/start`.
2. Bot akan membalas dan menyertakan **Email Service Account** Anda (misalnya `bot-pencatat-keuangan@xxxx.iam.gserviceaccount.com`).
3. Pengguna membuat Google Spreadsheet baru di akun Google mereka masing-masing.
4. Klik tombol **Share (Bagikan)** di Google Sheets tersebut, lalu tambahkan email Service Account tadi dengan akses **Editor**.
5. Salin **ID Spreadsheet** dari URL browser mereka.
   * *Contoh URL:* `https://docs.google.com/spreadsheets/d/1abc123XYZ987654321/edit#gid=0`
   * *Maka ID-nya adalah:* **`1abc123XYZ987654321`** (bagian di antara `/d/` dan `/edit`).
6. Kirimkan perintah ini ke bot Telegram Anda:
   `/set_sheet <ID_SPREADSHEET>`
   *Contoh:* `/set_sheet 1abc123XYZ987654321`
7. Selesai! Bot akan memberi tahu jika spreadsheet sudah berhasil terhubung. Anda sekarang dapat menggunakan tombol **Menu** di sebelah kolom input teks Telegram untuk memilih perintah secara langsung tanpa mengetik manual.
8. Pengguna sekarang dapat menggunakan perintah pencatatan:
   - 📥 `/masuk <jumlah> <keterangan>` (Contoh: `/masuk 50.000 Menjual buku`)
   - 💸 `/keluar <jumlah> <keterangan>` (Contoh: `/keluar 15000 Es Kopi Susu`)
   - 📊 `/laporan` untuk melihat ringkasan pemasukan, pengeluaran, dan saldo
