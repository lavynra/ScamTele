"""
bahasa.py
=========
Modul teks dwibahasa (Indonesia & English) untuk Bot Info Scammer.

Seluruh kalimat yang dikirim ke pengguna disimpan di kamus TEKS supaya
mudah diedit tanpa menyentuh logika bot. Gunakan fungsi t(kunci, bahasa)
untuk mengambil teks sesuai bahasa pilihan pengguna.
"""

TEKS: dict[str, dict[str, str]] = {

    # ------------------------------------------------------------
    # PEMILIHAN BAHASA
    # ------------------------------------------------------------
    "pilih_bahasa": {
        "id": "Silakan pilih bahasa yang ingin digunakan.",
        "en": "Please choose your preferred language.",
    },
    "tombol_bahasa_id": {"id": "Indonesia", "en": "Indonesia"},
    "tombol_bahasa_en": {"id": "English", "en": "English"},

    # ------------------------------------------------------------
    # SAMBUTAN / WELCOME
    # ------------------------------------------------------------
    "sambutan_caption": {
        "id": (
            "Halo {nama}\n\n"
            "Selamat datang di Info Scammer.\n\n"
            "Bot ini membantu pengguna melakukan pengecekan awal terhadap "
            "informasi yang pernah dilaporkan sebagai dugaan penipuan.\n\n"
            "Seluruh data telah melalui proses verifikasi admin sebelum ditampilkan.\n\n"
            "JoinGroup: @webshellmarketindonesian \n"
            "Email for Business: webshellmarketindonesian@gmil.com \n\n"
            "Tetap berhati-hati ketika melakukan transaksi."
        ),
        "en": (
            "Hello {nama}\n\n"
            "Welcome to Info Scammer.\n\n"
            "This bot helps the users do an initial check on information that "
            "has been reported as suspected fraud.\n\n"
            "All data has gone through an admin verification process before being shown.\n\n"
            "JoinGroup: @webshellmarketindonesian \n"
            "Email for Business: webshellmarketindonesian@gmil.com \n\n"
            "Always stay careful when making a transaction."
        ),
    },

    # ------------------------------------------------------------
    # MENU UTAMA
    # ------------------------------------------------------------
    "menu_utama_prompt": {
        "id": "Silakan pilih menu di bawah ini:",
        "en": "Please choose a menu below:",
    },
    "tombol_cari_scammer": {"id": "Cari Scammer", "en": "Search Scammer"},
    "tombol_lapor_scammer": {"id": "Lapor Scammer", "en": "Report Scammer"},

    # ------------------------------------------------------------
    # PENCARIAN
    # ------------------------------------------------------------
    "cari_prompt": {
        "id": (
            "Kirimkan salah satu data berikut untuk melakukan pencarian:\n\n"
            "• Username Telegram (contoh: @namaakun)\n"
            "• Nomor HP (contoh: 0812xxxxxxx)\n"
            "• Nomor Rekening Bank (contoh: BCA 1234567890)\n"
            "• Nomor E-Wallet (contoh: DANA 0812xxxxxxx)\n"
            "• Alamat Wallet (contoh: BTC ag6jwr#65a)\n\n"
            "Ketik /batal untuk membatalkan."
        ),
        "en": (
            "Send one of the following to search:\n\n"
            "• Telegram username (e.g. @account)\n"
            "• Phone number (e.g. 0812xxxxxxx)\n"
            "• Bank account number (e.g. BCA 1234567890)\n"
            "• E-wallet number (e.g. DANA 0812xxxxxxx)\n"
            "• Wallet Address (Example: BTC ag6jwr#65a)\n\n"
            "Type /batal to cancel."
        ),
    },
    "cari_mendeteksi": {
        "id": "Mencari berdasarkan {jenis}: {nilai}",
        "en": "Searching by {jenis}: {nilai}",
    },
    "cari_tidak_ditemukan": {
        "id": (
            "Data tidak ditemukan.\n\n"
            "Tetap berhati-hati ketika melakukan transaksi karena tidak semua "
            "kasus telah dilaporkan."
        ),
        "en": (
            "No data found.\n\n"
            "Still stay careful when making a transaction, since not every "
            "case has been reported."
        ),
    },
    "cari_hasil_header": {
        "id": "Ditemukan {jumlah} laporan yang cocok.",
        "en": "Found {jumlah} matching report(s).",
    },
    "cari_hasil_isi": {
        "id": (
            "Laporan #{nomor}\n"
            "Username/Nama Terlapor: {username}\n"
            "Kontak/Rekening: {jenis} - {kontak}\n"
            "Tanggal Laporan: {tanggal}\n\n"
            "Kronologi:\n{kronologi}"
        ),
        "en": (
            "Report #{nomor}\n"
            "Reported Username/Name: {username}\n"
            "Contact/Account: {jenis} - {kontak}\n"
            "Report Date: {tanggal}\n\n"
            "Chronology:\n{kronologi}"
        ),
    },
    "cari_kirim_bukti": {
        "id": "Bukti laporan #{nomor}:",
        "en": "Evidence for report #{nomor}:",
    },

    # ------------------------------------------------------------
    # PELAPORAN
    # ------------------------------------------------------------
    "lapor_langkah1": {
        "id": (
            "Langkah 1/4\n\n"
            "Masukkan Username Telegram atau Nama Scammer yang ingin dilaporkan.\n\n"
            "Ketik /batal untuk membatalkan dan kembali ke menu awal."
        ),
        "en": (
            "Step 1/4\n\n"
            "Enter the Telegram username or name of the scammer being reported.\n\n"
            "Type /cancel to cancel and return to the main menu."
        ),
    },
    "lapor_langkah2": {
        "id": (
            "Langkah 2/4\n\n"
            "Masukkan Nomor Bank atau Nomor E-Wallet milik scammer tersebut.\n"
            "Contoh: BCA 1234567 atau DANA 0812xxxxxxx\n"
            "Contoh: BTC abcdefg9826habj#_uwjw\n\n"
            "Ketik /batal untuk membatalkan dan kembali ke menu awal."
        ),
        "en": (
            "Step 2/4\n\n"
            "Enter the scammer's bank account number or e-wallet number.\n"
            "Example: BCA 123456 or DANA 0812xxxxxxx.\n"
            "Example: BTC abcdefg9826habj#_uwjw\n\n"
            "Type /cancel to cancel and return to the main menu."
        ),
    },
    "lapor_langkah3": {
        "id": (
            "Langkah 3/4\n\n"
            "Ceritakan kronologi kejadiannya. Boleh ditulis panjang dan detail.\n\n"
            "Ketik /batal untuk membatalkan dan kembali ke menu awal."
        ),
        "en": (
            "Step 3/4\n\n"
            "Describe the chronology of what happened. Feel free to write in detail.\n\n"
            "Type /cancel to cancel and return to the main menu."
        ),
    },
    "lapor_langkah4": {
        "id": (
            "Langkah 4/4\n\n"
            "Kirim foto bukti (screenshot chat, bukti transfer, dsb).\n"
            "Bisa kirim lebih dari satu foto satu per satu.\n"
            "Tekan tombol \"Selesai Upload\" jika sudah selesai.\n\n"
            "Ketik /batal untuk membatalkan dan kembali ke menu awal."
        ),
        "en": (
            "Step 4/4\n\n"
            "Send evidence photos (chat screenshots, transfer proof, etc).\n"
            "You may send more than one photo, one at a time.\n"
            "Tap the \"Selesai Upload\" button when you are done.\n\n"
            "Type /cancel to cancel and return to the main menu."
        ),
    },
    "tombol_selesai_upload": {"id": "Selesai Upload", "en": "Selesai Upload"},
    "tombol_batal": {"id": "Batal", "en": "Cancel"},
    "lapor_mengunggah": {
        "id": "Mengunggah foto, mohon tunggu sebentar...",
        "en": "Uploading photo, please wait a moment...",
    },
    "lapor_foto_diterima": {
        "id": "Foto ke-{jumlah} diterima. Kirim foto lain atau tekan \"Selesai Upload\".",
        "en": "Photo #{jumlah} received. Send another photo or tap \"Selesai Upload\".",
    },
    "lapor_foto_gagal": {
        "id": "Foto gagal diunggah, silakan coba kirim ulang foto tersebut.",
        "en": "The photo failed to upload, please try sending it again.",
    },
    "lapor_butuh_minimal_satu_foto": {
        "id": "Minimal kirim 1 foto bukti sebelum menekan \"Selesai Upload\".",
        "en": "Please send at least 1 evidence photo before tapping \"Selesai Upload\".",
    },
    "lapor_minta_foto_bukan_teks": {
        "id": "Mohon kirim foto bukti, atau tekan \"Selesai Upload\" jika sudah selesai.",
        "en": "Please send an evidence photo, or tap \"Selesai Upload\" if you are done.",
    },
    "lapor_berhasil": {
        "id": (
            "Laporan berhasil diterima.\n\n"
            "Laporan sedang menunggu verifikasi admin.\n\n"
            "Terima kasih telah membantu masyarakat."
        ),
        "en": (
            "Your report has been received.\n\n"
            "The report is now waiting for admin verification.\n\n"
            "Thank you for helping the community."
        ),
    },
    "lapor_input_kosong": {
        "id": "Input tidak boleh kosong, silakan coba lagi.",
        "en": "Input cannot be empty, please try again.",
    },
    "lapor_batal": {
        "id": "Pelaporan dibatalkan.",
        "en": "The report has been cancelled.",
    },

    # ------------------------------------------------------------
    # UMUM / GENERIK
    # ------------------------------------------------------------
    "sesi_berakhir": {
        "id": "Sesi berakhir karena tidak ada aktivitas. Silakan mulai lagi dengan /start.",
        "en": "Session expired due to inactivity. Please start again with /start.",
    },
    "error_umum": {
        "id": "Terjadi kesalahan. Silakan coba lagi beberapa saat lagi.",
        "en": "Something went wrong. Please try again in a moment.",
    },
    "belum_pilih_bahasa": {
        "id": "Silakan jalankan /start terlebih dahulu.",
        "en": "Please run /start first.",
    },
    "masukan_tidak_dikenali": {
        "id": "Mohon ikuti instruksi di atas, atau ketik /batal untuk membatalkan.",
        "en": "Please follow the instructions above, or type /batal to cancel.",
    },

    # ------------------------------------------------------------
    # ADMIN
    # ------------------------------------------------------------
    "admin_bukan_admin": {
        "id": "Perintah ini khusus untuk admin.",
        "en": "This command is for admins only.",
    },
    "admin_menu_header": {
        "id": "Menu Admin — silakan pilih:",
        "en": "Admin Menu — please choose:",
    },
    "admin_tombol_pending": {"id": "1. Laporan Pending", "en": "1. Pending Reports"},
    "admin_tombol_acc": {"id": "2. ACC Laporan", "en": "2. Approve Report"},
    "admin_tombol_tolak": {"id": "3. Tolak Laporan", "en": "3. Reject Report"},
    "admin_tombol_list": {"id": "4. List Terlapor", "en": "4. List Reported"},
    "admin_tombol_hapus": {"id": "5. Hapus Terlapor", "en": "5. Delete Reported"},

    "admin_tidak_ada_pending": {
        "id": "Tidak ada laporan yang menunggu verifikasi saat ini.",
        "en": "There are no reports waiting for verification right now.",
    },
    "admin_daftar_pending_header": {
        "id": "Daftar Laporan Pending ({jumlah}):",
        "en": "Pending Report List ({jumlah}):",
    },
    "admin_daftar_baris": {
        "id": "{nomor}. {username} — {jenis} {kontak} — {tanggal}",
        "en": "{nomor}. {username} — {jenis} {kontak} — {tanggal}",
    },

    "admin_minta_nomor_acc": {
        "id": "Ketik nomor laporan pada daftar di atas yang ingin di-ACC.",
        "en": "Type the report number from the list above that you want to approve.",
    },
    "admin_minta_nomor_tolak": {
        "id": "Ketik nomor laporan pada daftar di atas yang ingin ditolak.",
        "en": "Type the report number from the list above that you want to reject.",
    },
    "admin_minta_nomor_hapus": {
        "id": "Ketik nomor terlapor pada daftar di atas yang ingin dihapus.",
        "en": "Type the reported-entry number from the list above that you want to delete.",
    },
    "admin_nomor_tidak_valid": {
        "id": "Nomor tidak valid. Ketik ulang nomor yang benar sesuai daftar di atas.",
        "en": "Invalid number. Re-type a valid number from the list above.",
    },
    "admin_acc_berhasil": {
        "id": "Laporan #{nomor} telah disetujui dan kini bisa ditemukan lewat pencarian.",
        "en": "Report #{nomor} has been approved and can now be found via search.",
    },
    "admin_tolak_berhasil": {
        "id": "Laporan #{nomor} telah ditolak dan dihapus dari daftar pending.",
        "en": "Report #{nomor} has been rejected and removed from the pending list.",
    },
    "admin_tidak_ada_terlapor": {
        "id": "Belum ada data terlapor yang disetujui.",
        "en": "There is no approved reported data yet.",
    },
    "admin_daftar_terlapor_header": {
        "id": "Daftar Terlapor ({jumlah}):",
        "en": "Reported List ({jumlah}):",
    },
    "admin_hapus_berhasil": {
        "id": "Data terlapor #{nomor} telah dihapus dari database.",
        "en": "Reported entry #{nomor} has been deleted from the database.",
    },
    "admin_batal": {
        "id": "Aksi admin dibatalkan.",
        "en": "Admin action cancelled.",
    },

    # ------------------------------------------------------------
    # LABEL UMUM (dipakai di berbagai tempat)
    # ------------------------------------------------------------
    "label_username": {"id": "Username/Nama", "en": "Username/Name"},
    "label_kontak": {"id": "Kontak/Rekening", "en": "Contact/Account"},
    "label_tanggal": {"id": "Tanggal", "en": "Date"},
    "label_pelapor": {"id": "Pelapor", "en": "Reporter"},
}


def t(kunci: str, bahasa: str, **kwargs: object) -> str:
    """
    Mengambil teks sesuai bahasa pilihan pengguna.

    Jika kunci atau bahasa tidak ditemukan, akan otomatis jatuh ke bahasa
    Indonesia, dan jika tetap tidak ada, mengembalikan kunci itu sendiri
    supaya bot tidak pernah crash hanya karena teks belum tersedia.
    """
    bahasa_dipakai = bahasa if bahasa in ("id", "en") else "id"
    entri = TEKS.get(kunci)
    if entri is None:
        return kunci

    teks = entri.get(bahasa_dipakai) or entri.get("id") or kunci
    if not kwargs:
        return teks
    try:
        return teks.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return teks
