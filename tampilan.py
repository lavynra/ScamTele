"""
tampilan.py
===========
Seluruh tampilan terminal (CLI) Bot Info Scammer: banner startup, animasi
loading, panel statistik/dashboard, dan fungsi logging beraneka kategori.

Didesain ringan: tidak ada thread/loop tambahan yang berjalan di background.
Panel statistik dicetak sekali saat startup (bukan live-refresh terus
menerus) supaya tidak menambah beban CPU/RAM di perangkat Termux.
"""

import platform
import resource
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone

from rich.box import DOUBLE, ROUNDED
from rich.columns import Columns
from rich.console import Console
from rich.markup import escape as escape_markup
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

import config

konsol = Console()
WIB = timezone(timedelta(hours=7))

# Banner besar bergaya "ANSI Shadow", dipakai jika lebar terminal mencukupi.
_BANNER_LEBAR = r"""
██╗███╗   ██╗███████╗ ██████╗     ███████╗ ██████╗ █████╗ ███╗   ███╗███╗   ███╗███████╗██████╗
██║████╗  ██║██╔════╝██╔═══██╗    ██╔════╝██╔════╝██╔══██╗████╗ ████║████╗ ████║██╔════╝██╔══██╗
██║██╔██╗ ██║█████╗  ██║   ██║    ███████╗██║     ███████║██╔████╔██║██╔████╔██║█████╗  ██████╔╝
██║██║╚██╗██║██╔══╝  ██║   ██║    ╚════██║██║     ██╔══██║██║╚██╔╝██║██║╚██╔╝██║██╔══╝  ██╔══██╗
██║██║ ╚████║██║     ╚██████╔╝    ███████║╚██████╗██║  ██║██║ ╚═╝ ██║██║ ╚═╝ ██║███████╗██║  ██║
╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝     ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝
""".strip("\n")

_LEBAR_BANNER_BESAR = 98

# Warna tiap kategori log — dipilih dari palet elegan (biru, putih, cyan,
# hijau, kuning, merah) agar konsisten dan tidak norak.
_GAYA_KATEGORI: dict[str, str] = {
    "INFO": "cyan",
    "SUCCESS": "green",
    "WARNING": "yellow",
    "ERROR": "bold red",
    "SEARCH": "blue",
    "REPORT": "bold white",
    "ADMIN": "magenta",
    "DATABASE": "bright_blue",
    "UPLOAD": "bright_cyan",
}


# ==========================================================================
# STATISTIK SESI (khusus untuk panel dashboard, direset tiap kali bot start)
# ==========================================================================

class StatistikSesi:
    """Penghitung ringan untuk aktivitas sejak bot terakhir dijalankan."""

    def __init__(self) -> None:
        self.waktu_mulai = datetime.now(WIB)
        self.jumlah_pencarian = 0
        self.jumlah_error = 0

    def tambah_pencarian(self) -> None:
        self.jumlah_pencarian += 1

    def tambah_error(self) -> None:
        self.jumlah_error += 1


statistik_sesi = StatistikSesi()


# ==========================================================================
# BANNER & PANEL PEMBUKA
# ==========================================================================

def tampilkan_banner() -> None:
    """Menampilkan banner ASCII besar, atau versi ringkas jika terminal sempit."""
    lebar_terminal = shutil.get_terminal_size(fallback=(80, 24)).columns
    if lebar_terminal >= _LEBAR_BANNER_BESAR:
        konsol.print(_BANNER_LEBAR, style="bold cyan", justify="center")
    else:
        konsol.print(
            Panel(
                Text("INFO SCAMMER", style="bold cyan", justify="center"),
                box=DOUBLE,
                border_style="cyan",
            )
        )
    konsol.print(
        Text(
            f"Bot Informasi Awal Dugaan Penipuan — v{config.VERSI_BOT}",
            style="dim white",
            justify="center",
        )
    )
    konsol.print()


def buat_progres_loading() -> Progress:
    """Membuat objek Progress Rich untuk animasi loading saat startup."""
    return Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(bar_width=28, style="grey35", complete_style="cyan", finished_style="green"),
        console=konsol,
        transient=True,
    )


# ==========================================================================
# INFORMASI SISTEM
# ==========================================================================

def _pakai_ram_mb() -> float:
    """Memori (RSS) yang dipakai proses saat ini, dalam MB.

    Sengaja memakai modul stdlib `resource` (bukan psutil) agar bot tetap
    ringan tanpa dependency tambahan yang perlu dikompilasi di Termux.
    """
    puncak_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Di Linux (termasuk Termux/Android) ru_maxrss dalam KB; di macOS dalam byte.
    if platform.system() == "Darwin":
        return puncak_kb / 1024 / 1024
    return puncak_kb / 1024


def _jumlah_inti_cpu() -> int:
    return __import__("os").cpu_count() or 1


def _rata_beban_cpu() -> str:
    try:
        satu, lima, limabelas = __import__("os").getloadavg()
        return f"{satu:.2f} / {lima:.2f} / {limabelas:.2f}"
    except (OSError, AttributeError):
        return "n/a"


# ==========================================================================
# PANEL STATISTIK / DASHBOARD
# ==========================================================================

def tampilkan_panel_info(
    *,
    username_bot: str,
    id_bot: int,
    statistik_db: dict[str, int],
) -> None:
    """Menampilkan panel info bot & sistem, serta panel statistik database."""

    tabel_bot = Table(show_header=False, box=ROUNDED, border_style="cyan", expand=True)
    tabel_bot.add_column(style="dim white")
    tabel_bot.add_column(style="bold white")
    tabel_bot.add_row("Nama Bot", config.NAMA_BOT)
    tabel_bot.add_row("Versi", config.VERSI_BOT)
    tabel_bot.add_row("Status", "[bold green]AKTIF[/bold green]")
    tabel_bot.add_row("Bot Username", f"@{username_bot}")
    tabel_bot.add_row("Bot ID", str(id_bot))
    tabel_bot.add_row("Waktu Start", datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S WIB"))

    tabel_sistem = Table(show_header=False, box=ROUNDED, border_style="blue", expand=True)
    tabel_sistem.add_column(style="dim white")
    tabel_sistem.add_column(style="bold white")
    tabel_sistem.add_row("Python Version", platform.python_version())
    tabel_sistem.add_row("SQLite Version", sqlite3.sqlite_version)
    tabel_sistem.add_row("RAM Usage", f"{_pakai_ram_mb():.1f} MB")
    tabel_sistem.add_row("CPU Core", str(_jumlah_inti_cpu()))
    tabel_sistem.add_row("Load Average (1/5/15m)", _rata_beban_cpu())

    tabel_statistik = Table(show_header=False, box=ROUNDED, border_style="green", expand=True)
    tabel_statistik.add_column(style="dim white")
    tabel_statistik.add_column(style="bold white")
    tabel_statistik.add_row("Total Laporan", str(statistik_db["total_laporan"]))
    tabel_statistik.add_row("Pending", str(statistik_db["total_pending"]))
    tabel_statistik.add_row("Disetujui", str(statistik_db["total_disetujui"]))
    tabel_statistik.add_row("Total Pengguna", str(statistik_db["total_pengguna"]))
    tabel_statistik.add_row("User Aktif Hari Ini", str(statistik_db["user_hari_ini"]))

    konsol.print(
        Columns(
            [
                Panel(tabel_bot, title="Info Bot", border_style="cyan"),
                Panel(tabel_sistem, title="Info Sistem", border_style="blue"),
                Panel(tabel_statistik, title="Statistik Database", border_style="green"),
            ],
            equal=False,
            expand=False,
        )
    )
    konsol.print()


def tampilkan_statistik_sesi_saat_berhenti() -> None:
    """Ringkasan singkat aktivitas sesi, dicetak saat bot dimatikan (CTRL+C)."""
    durasi = datetime.now(WIB) - statistik_sesi.waktu_mulai
    tabel = Table(show_header=False, box=ROUNDED, border_style="yellow")
    tabel.add_column(style="dim white")
    tabel.add_column(style="bold white")
    tabel.add_row("Durasi Berjalan", str(durasi).split(".")[0])
    tabel.add_row("Jumlah Request Search", str(statistik_sesi.jumlah_pencarian))
    tabel.add_row("Jumlah Error", str(statistik_sesi.jumlah_error))
    konsol.print(Panel(tabel, title="Ringkasan Sesi", border_style="yellow"))


# ==========================================================================
# LOGGING TERMINAL
# ==========================================================================

def _cetak_log(kategori: str, pesan: str) -> None:
    gaya = _GAYA_KATEGORI.get(kategori, "white")
    waktu = datetime.now(WIB).strftime("%H:%M:%S")
    label = f"{kategori:<8}"
    # pesan bisa berasal dari input pengguna (username, kronologi, dsb) sehingga
    # WAJIB di-escape agar tanda kurung siku di dalamnya tidak ditafsirkan Rich
    # sebagai markup — bisa membuat log hilang, salah gaya, atau error.
    pesan_aman = escape_markup(str(pesan))
    konsol.print(f"[dim]{waktu}[/dim] │ [{gaya}]{label}[/{gaya}] │ {pesan_aman}")


def log_info(pesan: str) -> None:
    _cetak_log("INFO", pesan)


def log_sukses(pesan: str) -> None:
    _cetak_log("SUCCESS", pesan)


def log_peringatan(pesan: str) -> None:
    _cetak_log("WARNING", pesan)


def log_error(pesan: str) -> None:
    statistik_sesi.tambah_error()
    _cetak_log("ERROR", pesan)


def log_pencarian(pesan: str) -> None:
    statistik_sesi.tambah_pencarian()
    _cetak_log("SEARCH", pesan)


def log_laporan(pesan: str) -> None:
    _cetak_log("REPORT", pesan)


def log_admin(pesan: str) -> None:
    _cetak_log("ADMIN", pesan)


def log_database(pesan: str) -> None:
    _cetak_log("DATABASE", pesan)


def log_upload(pesan: str) -> None:
    _cetak_log("UPLOAD", pesan)
