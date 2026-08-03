"""
database.py
===========
Seluruh interaksi dengan SQLite untuk Bot Info Scammer ada di modul ini.
Modul lain (bot.py) tidak boleh menulis query SQL sendiri, cukup memanggil
fungsi-fungsi di sini agar query tetap konsisten dan aman (parameterized).

Catatan desain:
- Setiap operasi membuka koneksi baru lalu menutupnya kembali (bukan satu
  koneksi global) sehingga aman dipakai oleh banyak handler asyncio tanpa
  perlu thread lock tambahan, dan tetap ringan untuk perangkat Termux.
- Mode jurnal SQLite sengaja dibiarkan default (bukan WAL) karena project
  ini secara resmi ditujukan berjalan dari /sdcard (filesystem FUSE) yang
  tidak selalu mendukung shared-memory locking yang dibutuhkan mode WAL.
  PRAGMA busy_timeout dipakai untuk menangani akses bersamaan secara aman.
"""

import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import config

# Waktu Indonesia Barat, dipakai konsisten untuk seluruh pencatatan waktu.
WIB = timezone(timedelta(hours=7))

_POLA_TELEPON = re.compile(r"^(?:\+62|62|0)8[0-9]{7,12}$")


# ==========================================================================
# STRUKTUR DATA HASIL PENCARIAN / LAPORAN
# ==========================================================================

@dataclass
class Laporan:
    """Representasi satu baris laporan (pending maupun disetujui)."""

    id: int
    username_terlapor: str
    jenis_kontak: str
    nomor_kontak: str
    kronologi: str
    daftar_url_bukti: list[str]
    tanggal_laporan: str
    id_pelapor: int
    username_pelapor: str

    @staticmethod
    def dari_baris(baris: sqlite3.Row) -> "Laporan":
        try:
            daftar_url = json.loads(baris["url_bukti"]) if baris["url_bukti"] else []
        except (json.JSONDecodeError, TypeError):
            daftar_url = []
        return Laporan(
            id=baris["id"],
            username_terlapor=baris["username_terlapor"],
            jenis_kontak=baris["jenis_kontak"],
            nomor_kontak=baris["nomor_kontak"],
            kronologi=baris["kronologi"],
            daftar_url_bukti=daftar_url,
            tanggal_laporan=baris["tanggal_laporan"],
            id_pelapor=baris["id_pelapor"],
            username_pelapor=baris["username_pelapor"],
        )


# ==========================================================================
# UTILITAS WAKTU & KONEKSI
# ==========================================================================

def waktu_sekarang() -> str:
    """Mengembalikan waktu sekarang (WIB) sebagai teks 'YYYY-MM-DD HH:MM:SS'."""
    return datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")


def _buka_koneksi() -> sqlite3.Connection:
    """Membuka satu koneksi SQLite baru dengan pengaturan yang aman & ringan."""
    koneksi = sqlite3.connect(str(config.PATH_DATABASE), timeout=10)
    koneksi.row_factory = sqlite3.Row
    koneksi.execute("PRAGMA busy_timeout = 8000")
    koneksi.execute("PRAGMA foreign_keys = ON")
    return koneksi


def inisialisasi_database() -> None:
    """Membuat seluruh tabel & index jika belum ada. Aman dipanggil berulang."""
    config.PATH_DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with closing(_buka_koneksi()) as koneksi, koneksi:
        koneksi.execute(
            """
            CREATE TABLE IF NOT EXISTS pengguna (
                telegram_id           INTEGER PRIMARY KEY,
                username_telegram     TEXT,
                bahasa                TEXT NOT NULL DEFAULT 'id',
                waktu_daftar          TEXT NOT NULL,
                waktu_aktif_terakhir  TEXT NOT NULL
            )
            """
        )
        koneksi.execute(
            """
            CREATE TABLE IF NOT EXISTS laporan_pending (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                username_terlapor  TEXT NOT NULL,
                jenis_kontak       TEXT NOT NULL,
                nomor_kontak       TEXT NOT NULL,
                kronologi          TEXT NOT NULL,
                url_bukti          TEXT NOT NULL,
                tanggal_laporan    TEXT NOT NULL,
                id_pelapor         INTEGER NOT NULL,
                username_pelapor   TEXT NOT NULL
            )
            """
        )
        koneksi.execute(
            """
            CREATE TABLE IF NOT EXISTS laporan_disetujui (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                username_terlapor  TEXT NOT NULL,
                jenis_kontak       TEXT NOT NULL,
                nomor_kontak       TEXT NOT NULL,
                kronologi          TEXT NOT NULL,
                url_bukti          TEXT NOT NULL,
                tanggal_laporan    TEXT NOT NULL,
                id_pelapor         INTEGER NOT NULL,
                username_pelapor   TEXT NOT NULL,
                tanggal_disetujui  TEXT NOT NULL
            )
            """
        )
        koneksi.execute(
            "CREATE INDEX IF NOT EXISTS idx_nomor_kontak ON laporan_disetujui (nomor_kontak)"
        )
        koneksi.execute(
            "CREATE INDEX IF NOT EXISTS idx_username_terlapor ON laporan_disetujui (username_terlapor)"
        )


# ==========================================================================
# DETEKSI & NORMALISASI JENIS DATA
# ==========================================================================

def normalisasi_nomor_hp(nomor: str) -> str:
    """Menormalkan nomor HP ke format berawalan 0. Contoh: +62812xxxx -> 0812xxxx."""
    bersih = nomor.strip().replace(" ", "").replace("-", "")
    if bersih.startswith("+62"):
        bersih = "0" + bersih[3:]
    elif bersih.startswith("62"):
        bersih = "0" + bersih[2:]
    return bersih


def deteksi_jenis_data(teks: str) -> tuple[str, str]:
    """
    Mendeteksi jenis data yang dikirim pengguna (untuk pencarian & pelaporan).

    Mengembalikan tuple (jenis, nilai_bersih):
    - ("username", "namaakun")   -> username Telegram / nama scammer
    - ("telepon", "0812xxxxxxx") -> nomor HP (juga dipakai e-wallet umumnya)
    - ("DANA"/"OVO"/..., nomor)  -> e-wallet dengan nama diketahui
    - ("BCA"/"BRI"/..., nomor)   -> bank dengan nama diketahui
    - ("rekening", "1234567890") -> deretan angka tanpa nama bank/ewallet
    """
    mentah = teks.strip()
    if not mentah:
        return "tidak_diketahui", ""

    if mentah.startswith("@"):
        return "username", mentah[1:]

    tanpa_pemisah = mentah.replace(" ", "").replace("-", "")

    if _POLA_TELEPON.match(tanpa_pemisah):
        return "telepon", normalisasi_nomor_hp(tanpa_pemisah)

    kata_kunci = mentah.upper()
    digit_dalam_teks = re.sub(r"[^0-9]", "", mentah)

    for nama_ewallet in config.DAFTAR_EWALLET:
        if nama_ewallet in kata_kunci:
            nilai = normalisasi_nomor_hp(digit_dalam_teks) if digit_dalam_teks else ""
            return nama_ewallet, nilai

    for nama_bank in config.DAFTAR_BANK:
        if nama_bank in kata_kunci:
            return nama_bank, digit_dalam_teks

    if tanpa_pemisah.isdigit() and len(tanpa_pemisah) >= 6:
        return "rekening", tanpa_pemisah

    return "username", mentah


# ==========================================================================
# PENGGUNA
# ==========================================================================

def pengguna_terdaftar(telegram_id: int) -> bool:
    """Mengecek apakah pengguna sudah pernah memilih bahasa (pernah /start)."""
    with closing(_buka_koneksi()) as koneksi:
        baris = koneksi.execute(
            "SELECT 1 FROM pengguna WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        return baris is not None


def pengguna_ambil_bahasa(telegram_id: int) -> str | None:
    """Mengambil bahasa pilihan pengguna, atau None jika belum terdaftar."""
    with closing(_buka_koneksi()) as koneksi:
        baris = koneksi.execute(
            "SELECT bahasa FROM pengguna WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        return baris["bahasa"] if baris else None


def pengguna_simpan(telegram_id: int, username_telegram: str | None, bahasa: str) -> None:
    """Menyimpan pengguna baru atau memperbarui bahasa & username pengguna lama."""
    sekarang = waktu_sekarang()
    with closing(_buka_koneksi()) as koneksi, koneksi:
        koneksi.execute(
            """
            INSERT INTO pengguna (telegram_id, username_telegram, bahasa, waktu_daftar, waktu_aktif_terakhir)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username_telegram    = excluded.username_telegram,
                bahasa                = excluded.bahasa,
                waktu_aktif_terakhir  = excluded.waktu_aktif_terakhir
            """,
            (telegram_id, username_telegram, bahasa, sekarang, sekarang),
        )


def pengguna_perbarui_aktivitas(telegram_id: int, username_telegram: str | None = None) -> None:
    """Memperbarui waktu aktif terakhir pengguna (dipanggil di setiap interaksi)."""
    sekarang = waktu_sekarang()
    with closing(_buka_koneksi()) as koneksi, koneksi:
        if username_telegram is not None:
            koneksi.execute(
                "UPDATE pengguna SET waktu_aktif_terakhir = ?, username_telegram = ? WHERE telegram_id = ?",
                (sekarang, username_telegram, telegram_id),
            )
        else:
            koneksi.execute(
                "UPDATE pengguna SET waktu_aktif_terakhir = ? WHERE telegram_id = ?",
                (sekarang, telegram_id),
            )


# ==========================================================================
# LAPORAN — PENDING
# ==========================================================================

def laporan_tambah_pending(
    username_terlapor: str,
    jenis_kontak: str,
    nomor_kontak: str,
    kronologi: str,
    daftar_url_bukti: list[str],
    id_pelapor: int,
    username_pelapor: str,
) -> int:
    """Menyimpan laporan baru berstatus pending. Mengembalikan id laporan."""
    with closing(_buka_koneksi()) as koneksi, koneksi:
        kursor = koneksi.execute(
            """
            INSERT INTO laporan_pending
                (username_terlapor, jenis_kontak, nomor_kontak, kronologi,
                 url_bukti, tanggal_laporan, id_pelapor, username_pelapor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                username_terlapor,
                jenis_kontak,
                nomor_kontak,
                kronologi,
                json.dumps(daftar_url_bukti, ensure_ascii=False),
                waktu_sekarang(),
                id_pelapor,
                username_pelapor,
            ),
        )
        return int(kursor.lastrowid)


def laporan_ambil_semua_pending() -> list[Laporan]:
    """Mengambil seluruh laporan pending, terlama lebih dulu."""
    with closing(_buka_koneksi()) as koneksi:
        baris_semua = koneksi.execute(
            "SELECT * FROM laporan_pending ORDER BY id ASC"
        ).fetchall()
        return [Laporan.dari_baris(baris) for baris in baris_semua]


def laporan_ambil_pending_by_id(id_laporan: int) -> Laporan | None:
    """Mengambil satu laporan pending berdasarkan id asli di database."""
    with closing(_buka_koneksi()) as koneksi:
        baris = koneksi.execute(
            "SELECT * FROM laporan_pending WHERE id = ?", (id_laporan,)
        ).fetchone()
        return Laporan.dari_baris(baris) if baris else None


def laporan_setujui(id_laporan: int) -> bool:
    """Memindahkan satu laporan dari pending ke disetujui. True jika berhasil."""
    with closing(_buka_koneksi()) as koneksi, koneksi:
        baris = koneksi.execute(
            "SELECT * FROM laporan_pending WHERE id = ?", (id_laporan,)
        ).fetchone()
        if baris is None:
            return False
        koneksi.execute(
            """
            INSERT INTO laporan_disetujui
                (username_terlapor, jenis_kontak, nomor_kontak, kronologi,
                 url_bukti, tanggal_laporan, id_pelapor, username_pelapor, tanggal_disetujui)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                baris["username_terlapor"], baris["jenis_kontak"], baris["nomor_kontak"],
                baris["kronologi"], baris["url_bukti"], baris["tanggal_laporan"],
                baris["id_pelapor"], baris["username_pelapor"], waktu_sekarang(),
            ),
        )
        koneksi.execute("DELETE FROM laporan_pending WHERE id = ?", (id_laporan,))
        return True


def laporan_tolak(id_laporan: int) -> bool:
    """Menghapus satu laporan dari daftar pending. True jika berhasil."""
    with closing(_buka_koneksi()) as koneksi, koneksi:
        kursor = koneksi.execute("DELETE FROM laporan_pending WHERE id = ?", (id_laporan,))
        return kursor.rowcount > 0


# ==========================================================================
# LAPORAN — DISETUJUI (TERLAPOR)
# ==========================================================================

def laporan_ambil_semua_disetujui() -> list[Laporan]:
    """Mengambil seluruh laporan yang sudah disetujui, terbaru lebih dulu."""
    with closing(_buka_koneksi()) as koneksi:
        baris_semua = koneksi.execute(
            "SELECT * FROM laporan_disetujui ORDER BY id DESC"
        ).fetchall()
        return [Laporan.dari_baris(baris) for baris in baris_semua]


def laporan_hapus_disetujui(id_laporan: int) -> bool:
    """Menghapus satu data terlapor yang sudah disetujui. True jika berhasil."""
    with closing(_buka_koneksi()) as koneksi, koneksi:
        kursor = koneksi.execute("DELETE FROM laporan_disetujui WHERE id = ?", (id_laporan,))
        return kursor.rowcount > 0


def laporan_cari(jenis: str, nilai: str) -> list[Laporan]:
    """Mencari laporan yang SUDAH disetujui berdasarkan jenis data yang terdeteksi."""
    if not nilai:
        return []
    with closing(_buka_koneksi()) as koneksi:
        if jenis == "username":
            baris_semua = koneksi.execute(
                """
                SELECT * FROM laporan_disetujui
                WHERE LOWER(username_terlapor) LIKE LOWER(?)
                ORDER BY id DESC
                """,
                (f"%{nilai}%",),
            ).fetchall()
        else:
            # telepon / nama bank / nama e-wallet / rekening umum -> cocokkan
            # persis pada nomor_kontak supaya tidak salah menampilkan akun lain.
            baris_semua = koneksi.execute(
                "SELECT * FROM laporan_disetujui WHERE nomor_kontak = ? ORDER BY id DESC",
                (nilai,),
            ).fetchall()
        return [Laporan.dari_baris(baris) for baris in baris_semua]


# ==========================================================================
# STATISTIK (untuk panel CLI)
# ==========================================================================

def statistik_hitung() -> dict[str, int]:
    """Menghitung ringkasan statistik database untuk ditampilkan di panel CLI."""
    hari_ini = datetime.now(WIB).strftime("%Y-%m-%d")
    with closing(_buka_koneksi()) as koneksi:
        total_pending = koneksi.execute(
            "SELECT COUNT(*) AS c FROM laporan_pending"
        ).fetchone()["c"]
        total_disetujui = koneksi.execute(
            "SELECT COUNT(*) AS c FROM laporan_disetujui"
        ).fetchone()["c"]
        user_hari_ini = koneksi.execute(
            "SELECT COUNT(*) AS c FROM pengguna WHERE waktu_aktif_terakhir LIKE ?",
            (f"{hari_ini}%",),
        ).fetchone()["c"]
        total_pengguna = koneksi.execute(
            "SELECT COUNT(*) AS c FROM pengguna"
        ).fetchone()["c"]
    return {
        "total_pending": total_pending,
        "total_disetujui": total_disetujui,
        "total_laporan": total_pending + total_disetujui,
        "user_hari_ini": user_hari_ini,
        "total_pengguna": total_pengguna,
    }
