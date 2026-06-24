# Panduan Deploy Telegram Bot ke Railway

Dokumen ini menjelaskan langkah-langkah untuk mendeploy bot Telegram pencatatan uang ke platform **Railway** dengan aman dan menjaga data database agar tidak hilang saat restart.

## Prasyarat
- Akun GitHub yang terhubung dengan repositori bot ini.
- Akun [Railway](https://railway.app).

---

## Langkah 1: Hubungkan Repositori ke Railway
1. Masuk ke [Railway.app](https://railway.app) dan login menggunakan akun GitHub Anda.
2. Klik tombol **New Project** di pojok kanan atas.
3. Pilih **Deploy from GitHub repo**.
4. Pilih repositori **`bot-tele-pencatatan-uang`**.
5. Klik **Deploy Now** (Abaikan jika deployment pertama kali gagal/eror, ini wajar karena variabel lingkungan belum dikonfigurasi).

---

## Langkah 2: Konfigurasi Environment Variables (Variabel Lingkungan)
Agar bot dapat berjalan, Anda perlu menambahkan konfigurasi token dan kredensial.
1. Di Dashboard Railway, klik pada service bot Anda.
2. Buka tab **Variables**.
3. Tambahkan variabel-variabel berikut:

| Key | Value / Contoh | Keterangan |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | `8775263587:AAH98qq6vf...` | Token bot Telegram Anda dari `@BotFather`. |
| `SHEET_NAME` | `Sheet1` | Nama sheet/tab default Google Sheets Anda. |
| `GOOGLE_CREDENTIALS` | *Isi seluruh teks dari file credentials.json* | Buka file lokal `credentials.json`, salin seluruh isi JSON tersebut, dan paste di kolom ini. |
| `DATABASE_PATH` | `/data/users.db` | Path database SQLite di dalam volume persisten (lihat Langkah 3). |

---

## Langkah 3: Setup Volume Persisten (PENTING untuk SQLite)
Railway menggunakan sistem file kontainer yang bersifat sementara (*ephemeral*). Tanpa Volume, file database `users.db` akan terhapus dan bot akan lupa spreadsheet milik pengguna setiap kali ada pembaruan kode atau bot di-restart.

Untuk mengatasinya, pasang volume penyimpanan persisten:
1. Di dashboard proyek Railway Anda, klik tombol **+ New** di pojok kanan atas.
2. Pilih **Volume**.
3. Atur nama volume (misal: `data`) dan ukuran minimal (1 GB).
4. Klik pada Volume yang baru dibuat, lalu hubungkan (**Mount**) ke service bot Anda.
5. Set **Mount Path** ke `/data`.
6. Pastikan variabel lingkungan `DATABASE_PATH` sudah diset ke `/data/users.db` di menu **Variables** pada Langkah 2.

---

## Langkah 4: Proses Start Up
Dalam repositori ini sudah ditambahkan file `Procfile` berisi:
```procfile
worker: python bot.py
```
Railway akan otomatis mendeteksi file ini dan menjalankan bot sebagai background worker (polling service) tanpa memerlukan port web terbuka.

Setelah semua konfigurasi di atas selesai, Railway akan otomatis melakukan re-build dan men-deploy bot Anda secara sukses. Anda dapat memantau log jalannya bot melalui tab **Deployments**.
