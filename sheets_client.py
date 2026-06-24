import gspread
import os
import json
from google.oauth2.service_account import Credentials
from datetime import datetime

class SheetsClient:
    def __init__(self, credentials_file):
        self.credentials_file = credentials_file
        self.client = None
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

    def connect(self):
        """Menghubungkan ke Google Sheets API jika belum terhubung."""
        if self.client:
            return True
        try:
            google_creds_env = os.getenv("GOOGLE_CREDENTIALS") or os.getenv("GOOGLE_CREDENTIAL")
            if google_creds_env:
                creds_info = json.loads(google_creds_env)
                creds = Credentials.from_service_account_info(creds_info, scopes=self.scopes)
            else:
                creds = Credentials.from_service_account_file(self.credentials_file, scopes=self.scopes)
            self.client = gspread.authorize(creds)
            return True
        except Exception as e:
            print(f"Error koneksi ke Google Sheets API: {e}")
            raise e

    def _get_worksheet(self, spreadsheet_id, sheet_name="Sheet1"):
        """Membuka spreadsheet berdasarkan ID dan mendapatkan worksheet."""
        self.connect()
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
        except gspread.exceptions.SpreadsheetNotFound:
            raise ValueError("Spreadsheet tidak ditemukan. Periksa kembali ID Spreadsheet Anda.")
        except gspread.exceptions.APIError as e:
            if "PERMISSION_DENIED" in str(e):
                raise PermissionError("Akses ditolak. Pastikan Anda telah membagikan spreadsheet ke email Service Account.")
            raise e

        # Dapatkan atau buat worksheet jika belum ada
        try:
            sheet = spreadsheet.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="4")
            
        # Inisialisasi header jika kosong
        try:
            first_row = sheet.row_values(1)
        except Exception:
            first_row = []
            
        if not first_row:
            headers = ["Waktu", "Tipe", "Jumlah", "Keterangan"]
            sheet.append_row(headers)
            
        return sheet

    def add_record(self, spreadsheet_id, sheet_name, record_type, amount, description):
        """Menambahkan catatan baru ke spreadsheet tertentu."""
        sheet = self._get_worksheet(spreadsheet_id, sheet_name)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [timestamp, record_type, amount, description]
        sheet.append_row(row)

    def get_summary(self, spreadsheet_id, sheet_name):
        """Menghitung ringkasan total pemasukan, pengeluaran, dan saldo dari spreadsheet tertentu."""
        sheet = self._get_worksheet(spreadsheet_id, sheet_name)
        records = sheet.get_all_records()
        total_pemasukan = 0
        total_pengeluaran = 0
        
        for record in records:
            tipe = record.get("Tipe")
            try:
                jumlah = float(str(record.get("Jumlah", 0)).replace(",", ""))
            except (ValueError, TypeError):
                jumlah = 0
                
            if tipe == "Pemasukan":
                total_pemasukan += jumlah
            elif tipe == "Pengeluaran":
                total_pengeluaran += jumlah
                
        saldo = total_pemasukan - total_pengeluaran
        return {
            "pemasukan": total_pemasukan,
            "pengeluaran": total_pengeluaran,
            "saldo": saldo
        }
