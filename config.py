"""
config.py
=========
Pusat konfigurasi Bot Info Scammer.

Semua nilai yang perlu diubah oleh pengguna (token bot, ID admin, API key,
dsb) ada di file ini. Modul lain (bot.py, database.py, tampilan.py) hanya
membaca nilai dari sini dan tidak boleh menyimpan konfigurasi sendiri.
"""

from pathlib import Path

# ======================================================================
# IDENTITAS BOT
# ======================================================================

# Token didapat dari @BotFather di Telegram (perintah /newbot).
# JANGAN bagikan token ini ke siapa pun.
TOKEN_BOT: str = "8919894894:AAHHousJT8c-SRgwxJu4XuKoc5Wqfh3HoJk"

# Username bot tanpa tanda @, hanya dipakai untuk tampilan panel CLI.
USERNAME_BOT: str = "InfoScammerShellBot"

NAMA_BOT: str = "Info Scammer"
VERSI_BOT: str = "1.0.0"

# ======================================================================
# ADMIN
# ======================================================================

# Daftar Telegram ID yang boleh membuka menu /admin.
# Cara mengetahui Telegram ID sendiri: chat bot @userinfobot di Telegram.
# Contoh: DAFTAR_ID_ADMIN = [1390927569, 222222222]
DAFTAR_ID_ADMIN: list[int] = [
   1390927569,
]

# ======================================================================
# IMGBB — UPLOAD GAMBAR OTOMATIS
# ======================================================================

# API key gratis, didapat di https://api.imgbb.com/ setelah membuat akun.
KUNCI_API_IMGBB: str = "7a518b0a1874508d5d7f79e20f685833"
URL_API_IMGBB: str = "https://api.imgbb.com/1/upload"

# Batas waktu (detik) menunggu proses upload ke imgbb sebelum dianggap gagal.
BATAS_WAKTU_UPLOAD_DETIK: int = 30

# Foto bukti yang sisi terpanjangnya melebihi nilai ini akan dikompres
# otomatis (memakai Pillow) sebelum diunggah, agar hemat kuota & waktu
# terutama saat bot dijalankan lewat jaringan seluler di Termux.
UKURAN_MAKSIMAL_SISI_GAMBAR: int = 1600
KUALITAS_KOMPRESI_JPEG: int = 85

# ======================================================================
# LOKASI FILE (relatif terhadap folder project, bukan hardcode /sdcard/...
# supaya project tetap berjalan walau dipindah lokasi)
# ======================================================================

DIREKTORI_DASAR: Path = Path(__file__).resolve().parent
PATH_DATABASE: Path = DIREKTORI_DASAR / "database.db"
PATH_FOTO_SAMBUTAN: Path = DIREKTORI_DASAR / "assets" / "welcome.jpg"

# ======================================================================
# DAFTAR BANK & E-WALLET YANG DIKENALI BOT
# ======================================================================
# Dipakai untuk mendeteksi otomatis jenis data saat pencarian & pelaporan.
# Tambah/kurangi daftar ini sesuai kebutuhan tanpa perlu mengubah kode lain.

DAFTAR_EWALLET: list[str] = ["DANA", "OVO", "GOPAY", "SHOPEEPAY", "LINKAJA"]

DAFTAR_BANK: list[str] = [
    "BCA", "BRI", "MANDIRI", "BNI", "BSI",
    "SEABANK", "CIMB", "PERMATA", "DANAMON", "BTN", "SUPERBANK", "BANKJAGO", "NEOBANK", "ALLOBANK", "PANIN", "USDT", "USDC", "BTC", "ETH", "SOL",
]

# ======================================================================
# PENGATURAN UMUM
# ======================================================================

BAHASA_DEFAULT: str = "id"            # "id" atau "en", dipakai sebelum user memilih bahasa
BATAS_BARIS_DAFTAR_ADMIN: int = 15    # maksimal baris yang ditampilkan pada daftar laporan admin
BATAS_WAKTU_SESI_DETIK: int = 600     # sesi pelaporan/admin otomatis berakhir jika idle sekian detik
PANJANG_MAKSIMAL_KRONOLOGI_TAMPIL: int = 3500  # potong kronologi saat ditampilkan agar tidak melebihi batas pesan Telegram
