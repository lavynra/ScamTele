import asyncio
import io

import requests
from PIL import Image
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import config
import database
import tampilan
from bahasa import t


CARI_INPUT = 0
LAPOR_USERNAME, LAPOR_KONTAK, LAPOR_KRONOLOGI, LAPOR_BUKTI = range(1, 5)
ADMIN_MENU, ADMIN_ACC, ADMIN_TOLAK, ADMIN_HAPUS = range(5, 9)



async def ambil_bahasa_pengguna(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    if "bahasa" in context.user_data:
        return context.user_data["bahasa"]
    telegram_id = update.effective_user.id
    bhs = database.pengguna_ambil_bahasa(telegram_id) or config.BAHASA_DEFAULT
    context.user_data["bahasa"] = bhs
    return bhs


def _label_jenis(jenis: str, bhs: str) -> str:
    pemetaan = {
        "telepon": {"id": "Nomor HP", "en": "Phone Number"},
        "rekening": {"id": "Nomor Rekening", "en": "Account Number"},
        "username": {"id": "Username", "en": "Username"},
        "Kontak": {"id": "Kontak", "en": "Contact"},
        "tidak_diketahui": {"id": "Tidak diketahui", "en": "Unknown"},
    }
    if jenis in pemetaan:
        return pemetaan[jenis].get(bhs, pemetaan[jenis]["id"])
    return jenis  


async def tampilkan_menu_utama(chat_id: int, context: ContextTypes.DEFAULT_TYPE, bhs: str) -> None:
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t("tombol_cari_scammer", bhs), callback_data="menu_cari")],
            [InlineKeyboardButton(t("tombol_lapor_scammer", bhs), callback_data="menu_lapor")],
        ]
    )
    await context.bot.send_message(chat_id=chat_id, text=t("menu_utama_prompt", bhs), reply_markup=keyboard)


async def masukan_tidak_dikenali(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    bhs = await ambil_bahasa_pengguna(update, context)
    if update.message:
        await update.message.reply_text(t("masukan_tidak_dikenali", bhs))


async def batal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    bhs = await ambil_bahasa_pengguna(update, context)
    context.user_data.pop("lapor", None)
    context.user_data.pop("admin", None)
    if update.message:
        await update.message.reply_text(t("lapor_batal", bhs))
        await tampilkan_menu_utama(update.effective_chat.id, context, bhs)
    return ConversationHandler.END


async def sesi_habis(update: object, context: ContextTypes.DEFAULT_TYPE) -> int:
    bhs = context.user_data.get("bahasa", config.BAHASA_DEFAULT) if context.user_data else config.BAHASA_DEFAULT
    if isinstance(update, Update) and update.effective_chat:
        try:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=t("sesi_berakhir", bhs))
        except Exception as kesalahan:
            tampilan.log_error(f"Gagal mengirim notifikasi sesi berakhir: {kesalahan}")
    return ConversationHandler.END



async def mulai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pengguna = update.effective_user

    if not database.pengguna_terdaftar(pengguna.id):
        tampilan.log_info(f"Pengguna baru: {pengguna.id} (@{pengguna.username or '-'})")
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(t("tombol_bahasa_id", "id"), callback_data="bahasa_id"),
                    InlineKeyboardButton(t("tombol_bahasa_en", "en"), callback_data="bahasa_en"),
                ]
            ]
        )
        teks = f'{t("pilih_bahasa", "id")}\n{t("pilih_bahasa", "en")}'
        await update.message.reply_text(teks, reply_markup=keyboard)
        return

    bhs = database.pengguna_ambil_bahasa(pengguna.id) or config.BAHASA_DEFAULT
    context.user_data["bahasa"] = bhs
    database.pengguna_perbarui_aktivitas(pengguna.id, pengguna.username)
    await kirim_sambutan(update.effective_chat.id, context, bhs, pengguna.first_name or "")


async def pilih_bahasa_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    bhs = "id" if query.data == "bahasa_id" else "en"
    pengguna = update.effective_user

    database.pengguna_simpan(pengguna.id, pengguna.username, bhs)
    context.user_data["bahasa"] = bhs
    tampilan.log_info(f"Pengguna {pengguna.id} memilih bahasa: {bhs}")

    await kirim_sambutan(update.effective_chat.id, context, bhs, pengguna.first_name or "")


async def kirim_sambutan(chat_id: int, context: ContextTypes.DEFAULT_TYPE, bhs: str, nama: str) -> None:
    caption = t("sambutan_caption", bhs, nama=nama)
    try:
        if config.PATH_FOTO_SAMBUTAN.exists():
            with open(config.PATH_FOTO_SAMBUTAN, "rb") as berkas_foto:
                await context.bot.send_photo(chat_id=chat_id, photo=berkas_foto, caption=caption)
        else:
            await context.bot.send_message(chat_id=chat_id, text=caption)
    except Exception as kesalahan:
        tampilan.log_error(f"Gagal mengirim foto sambutan: {kesalahan}")
        await context.bot.send_message(chat_id=chat_id, text=caption)

    await tampilkan_menu_utama(chat_id, context, bhs)



async def cari_mulai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    bhs = await ambil_bahasa_pengguna(update, context)
    await query.message.reply_text(t("cari_prompt", bhs))
    return CARI_INPUT


async def cari_proses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    bhs = await ambil_bahasa_pengguna(update, context)
    teks_masukan = (update.message.text or "").strip()

    if not teks_masukan:
        await update.message.reply_text(t("lapor_input_kosong", bhs))
        return CARI_INPUT

    jenis, nilai = database.deteksi_jenis_data(teks_masukan)
    tampilan.log_pencarian(f"User {update.effective_user.id} mencari [{jenis}] {nilai or teks_masukan}")
    await update.message.reply_text(
        t("cari_mendeteksi", bhs, jenis=_label_jenis(jenis, bhs), nilai=nilai or teks_masukan)
    )

    try:
        hasil = database.laporan_cari(jenis, nilai or teks_masukan)
    except Exception as kesalahan:
        tampilan.log_error(f"Gagal melakukan pencarian: {kesalahan}")
        await update.message.reply_text(t("error_umum", bhs))
        await tampilkan_menu_utama(update.effective_chat.id, context, bhs)
        return ConversationHandler.END

    if not hasil:
        await update.message.reply_text(t("cari_tidak_ditemukan", bhs))
        await tampilkan_menu_utama(update.effective_chat.id, context, bhs)
        return ConversationHandler.END

    await update.message.reply_text(t("cari_hasil_header", bhs, jumlah=len(hasil)))
    for nomor, laporan in enumerate(hasil, start=1):
        kronologi_tampil = laporan.kronologi
        if len(kronologi_tampil) > config.PANJANG_MAKSIMAL_KRONOLOGI_TAMPIL:
            kronologi_tampil = kronologi_tampil[: config.PANJANG_MAKSIMAL_KRONOLOGI_TAMPIL] + "…"

        await update.message.reply_text(
            t(
                "cari_hasil_isi",
                bhs,
                nomor=nomor,
                username=laporan.username_terlapor,
                jenis=_label_jenis(laporan.jenis_kontak, bhs),
                kontak=laporan.nomor_kontak,
                tanggal=laporan.tanggal_laporan,
                kronologi=kronologi_tampil,
            )
        )
        if laporan.daftar_url_bukti:
            await update.message.reply_text(t("cari_kirim_bukti", bhs, nomor=nomor))
            await kirim_bukti_gambar(update.effective_chat.id, context, laporan.daftar_url_bukti, nomor)

    await tampilkan_menu_utama(update.effective_chat.id, context, bhs)
    return ConversationHandler.END


async def kirim_bukti_gambar(
    chat_id: int, context: ContextTypes.DEFAULT_TYPE, daftar_url: list[str], nomor_laporan: int
) -> None:
    if not daftar_url:
        return
    try:
        if len(daftar_url) == 1:
            await context.bot.send_photo(chat_id=chat_id, photo=daftar_url[0])
            return
        for awal in range(0, len(daftar_url), 10):
            kelompok = daftar_url[awal : awal + 10]
            media = [InputMediaPhoto(media=url) for url in kelompok]
            await context.bot.send_media_group(chat_id=chat_id, media=media)
    except Exception as kesalahan:
        tampilan.log_error(f"Gagal mengirim bukti gambar laporan #{nomor_laporan}: {kesalahan}")



def _keyboard_selesai_upload(bhs: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(t("tombol_selesai_upload", bhs), callback_data="lapor_selesai")]]
    )


async def lapor_mulai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    bhs = await ambil_bahasa_pengguna(update, context)
    context.user_data["lapor"] = {}
    await query.message.reply_text(t("lapor_langkah1", bhs))
    return LAPOR_USERNAME


async def lapor_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    bhs = await ambil_bahasa_pengguna(update, context)
    teks = (update.message.text or "").strip()
    if not teks:
        await update.message.reply_text(t("lapor_input_kosong", bhs))
        return LAPOR_USERNAME

    context.user_data["lapor"]["username_terlapor"] = teks.lstrip("@")
    await update.message.reply_text(t("lapor_langkah2", bhs))
    return LAPOR_KONTAK


async def lapor_kontak(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    bhs = await ambil_bahasa_pengguna(update, context)
    teks = (update.message.text or "").strip()
    if not teks:
        await update.message.reply_text(t("lapor_input_kosong", bhs))
        return LAPOR_KONTAK

    jenis, nilai = database.deteksi_jenis_data(teks)
    if jenis == "username":
        jenis, nilai = "Kontak", teks

    context.user_data["lapor"]["jenis_kontak"] = jenis
    context.user_data["lapor"]["nomor_kontak"] = nilai
    await update.message.reply_text(t("lapor_langkah3", bhs))
    return LAPOR_KRONOLOGI


async def lapor_kronologi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    bhs = await ambil_bahasa_pengguna(update, context)
    teks = (update.message.text or "").strip()
    if not teks:
        await update.message.reply_text(t("lapor_input_kosong", bhs))
        return LAPOR_KRONOLOGI

    context.user_data["lapor"]["kronologi"] = teks
    context.user_data["lapor"]["bukti"] = []
    await update.message.reply_text(t("lapor_langkah4", bhs), reply_markup=_keyboard_selesai_upload(bhs))
    return LAPOR_BUKTI


async def lapor_terima_foto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    bhs = await ambil_bahasa_pengguna(update, context)

    foto = update.message.photo[-1]  
    berkas = await context.bot.get_file(foto.file_id)
    data_gambar = await berkas.download_as_bytearray()

    pesan_proses = await update.message.reply_text(t("lapor_mengunggah", bhs))
    url = await unggah_ke_imgbb(bytes(data_gambar))
    try:
        await pesan_proses.delete()
    except Exception:
        pass  

    if url is None:
        await update.message.reply_text(t("lapor_foto_gagal", bhs), reply_markup=_keyboard_selesai_upload(bhs))
        return LAPOR_BUKTI

    context.user_data["lapor"]["bukti"].append(url)
    jumlah = len(context.user_data["lapor"]["bukti"])
    tampilan.log_upload(f"Foto ke-{jumlah} dari user {update.effective_user.id} berhasil diunggah ke imgbb")
    await update.message.reply_text(
        t("lapor_foto_diterima", bhs, jumlah=jumlah), reply_markup=_keyboard_selesai_upload(bhs)
    )
    return LAPOR_BUKTI


async def lapor_bukan_foto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    bhs = await ambil_bahasa_pengguna(update, context)
    await update.message.reply_text(t("lapor_minta_foto_bukan_teks", bhs), reply_markup=_keyboard_selesai_upload(bhs))
    return LAPOR_BUKTI


async def lapor_selesai_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    bhs = await ambil_bahasa_pengguna(update, context)
    data_lapor = context.user_data.get("lapor", {})
    daftar_bukti = data_lapor.get("bukti", [])

    if not daftar_bukti:
        await query.message.reply_text(
            t("lapor_butuh_minimal_satu_foto", bhs), reply_markup=_keyboard_selesai_upload(bhs)
        )
        return LAPOR_BUKTI

    pengguna = update.effective_user
    username_pelapor = f"@{pengguna.username}" if pengguna.username else str(pengguna.id)

    try:
        id_laporan = database.laporan_tambah_pending(
            username_terlapor=data_lapor["username_terlapor"],
            jenis_kontak=data_lapor["jenis_kontak"],
            nomor_kontak=data_lapor["nomor_kontak"],
            kronologi=data_lapor["kronologi"],
            daftar_url_bukti=daftar_bukti,
            id_pelapor=pengguna.id,
            username_pelapor=username_pelapor,
        )
    except Exception as kesalahan:
        tampilan.log_error(f"Gagal menyimpan laporan baru ke database: {kesalahan}")
        await query.message.reply_text(t("error_umum", bhs))
        context.user_data.pop("lapor", None)
        await tampilkan_menu_utama(update.effective_chat.id, context, bhs)
        return ConversationHandler.END

    tampilan.log_laporan(f"Laporan baru #{id_laporan} dari {username_pelapor} ({len(daftar_bukti)} foto bukti)")
    await query.message.reply_text(t("lapor_berhasil", bhs))
    context.user_data.pop("lapor", None)
    await tampilkan_menu_utama(update.effective_chat.id, context, bhs)
    return ConversationHandler.END



def _kompres_gambar(data_gambar: bytes) -> bytes:
    gambar = Image.open(io.BytesIO(data_gambar))
    gambar = gambar.convert("RGB")

    sisi_terpanjang = max(gambar.size)
    if sisi_terpanjang > config.UKURAN_MAKSIMAL_SISI_GAMBAR:
        rasio = config.UKURAN_MAKSIMAL_SISI_GAMBAR / sisi_terpanjang
        ukuran_baru = (int(gambar.width * rasio), int(gambar.height * rasio))
        gambar = gambar.resize(ukuran_baru, Image.LANCZOS)

    buffer = io.BytesIO()
    gambar.save(buffer, format="JPEG", quality=config.KUALITAS_KOMPRESI_JPEG)
    return buffer.getvalue()


def _unggah_ke_imgbb_sinkron(data_gambar: bytes) -> str | None:
    """Bagian blocking (requests) dari proses upload, dijalankan di thread terpisah."""
    try:
        respons = requests.post(
            config.URL_API_IMGBB,
            data={"key": config.KUNCI_API_IMGBB},
            files={"image": ("bukti.jpg", data_gambar)},
            timeout=config.BATAS_WAKTU_UPLOAD_DETIK,
        )
        respons.raise_for_status()
        hasil = respons.json()
        if not hasil.get("success"):
            return None
        data = hasil.get("data", {})
        return data.get("display_url") or data.get("url")
    except (requests.RequestException, ValueError):
        return None


async def unggah_ke_imgbb(data_gambar: bytes) -> str | None:
    """Mengompres lalu mengunggah satu gambar ke imgbb. Mengembalikan URL, atau None jika gagal."""
    try:
        data_terkompresi = await asyncio.to_thread(_kompres_gambar, data_gambar)
    except Exception as kesalahan:
        tampilan.log_peringatan(f"Kompresi gambar gagal, memakai gambar asli: {kesalahan}")
        data_terkompresi = data_gambar

    return await asyncio.to_thread(_unggah_ke_imgbb_sinkron, data_terkompresi)



def _keyboard_menu_admin(bhs: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(t("admin_tombol_pending", bhs), callback_data="admin_pending")],
            [InlineKeyboardButton(t("admin_tombol_acc", bhs), callback_data="admin_acc")],
            [InlineKeyboardButton(t("admin_tombol_tolak", bhs), callback_data="admin_tolak")],
            [InlineKeyboardButton(t("admin_tombol_list", bhs), callback_data="admin_list")],
            [InlineKeyboardButton(t("admin_tombol_hapus", bhs), callback_data="admin_hapus")],
        ]
    )


async def admin_mulai(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    pengguna = update.effective_user
    bhs = await ambil_bahasa_pengguna(update, context)

    if pengguna.id not in config.DAFTAR_ID_ADMIN:
        await update.message.reply_text(t("admin_bukan_admin", bhs))
        tampilan.log_peringatan(f"Percobaan akses /admin ditolak dari user {pengguna.id}")
        return ConversationHandler.END

    await update.message.reply_text(t("admin_menu_header", bhs), reply_markup=_keyboard_menu_admin(bhs))
    return ADMIN_MENU


async def admin_menu_teks_tidak_dikenal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    bhs = await ambil_bahasa_pengguna(update, context)
    await update.message.reply_text(t("admin_menu_header", bhs), reply_markup=_keyboard_menu_admin(bhs))
    return ADMIN_MENU


async def _kirim_daftar(query, bhs: str, daftar: list, kunci_header: str, kunci_kosong: str) -> bool:
    """Mengirim daftar laporan (pending/disetujui) bernomor urut. True jika ada isinya."""
    if not daftar:
        await query.message.reply_text(t(kunci_kosong, bhs))
        return False

    daftar_terbatas = daftar[: config.BATAS_BARIS_DAFTAR_ADMIN]
    baris = [
        t(
            "admin_daftar_baris",
            bhs,
            nomor=i,
            username=laporan.username_terlapor,
            jenis=_label_jenis(laporan.jenis_kontak, bhs),
            kontak=laporan.nomor_kontak,
            tanggal=laporan.tanggal_laporan,
        )
        for i, laporan in enumerate(daftar_terbatas, start=1)
    ]
    teks = t(kunci_header, bhs, jumlah=len(daftar)) + "\n\n" + "\n".join(baris)
    await query.message.reply_text(teks)
    return True


async def admin_menu_pilih(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    bhs = await ambil_bahasa_pengguna(update, context)
    aksi = query.data

    if aksi == "admin_pending":
        daftar = database.laporan_ambil_semua_pending()
        await _kirim_daftar(query, bhs, daftar, "admin_daftar_pending_header", "admin_tidak_ada_pending")
        await query.message.reply_text(t("admin_menu_header", bhs), reply_markup=_keyboard_menu_admin(bhs))
        return ADMIN_MENU

    if aksi == "admin_list":
        daftar = database.laporan_ambil_semua_disetujui()
        await _kirim_daftar(query, bhs, daftar, "admin_daftar_terlapor_header", "admin_tidak_ada_terlapor")
        await query.message.reply_text(t("admin_menu_header", bhs), reply_markup=_keyboard_menu_admin(bhs))
        return ADMIN_MENU

    if aksi == "admin_acc":
        daftar = database.laporan_ambil_semua_pending()
        ada_isi = await _kirim_daftar(query, bhs, daftar, "admin_daftar_pending_header", "admin_tidak_ada_pending")
        if not ada_isi:
            await query.message.reply_text(t("admin_menu_header", bhs), reply_markup=_keyboard_menu_admin(bhs))
            return ADMIN_MENU
        context.user_data["admin"] = {"peta": {i: lap.id for i, lap in enumerate(daftar, start=1)}}
        await query.message.reply_text(t("admin_minta_nomor_acc", bhs))
        return ADMIN_ACC

    if aksi == "admin_tolak":
        daftar = database.laporan_ambil_semua_pending()
        ada_isi = await _kirim_daftar(query, bhs, daftar, "admin_daftar_pending_header", "admin_tidak_ada_pending")
        if not ada_isi:
            await query.message.reply_text(t("admin_menu_header", bhs), reply_markup=_keyboard_menu_admin(bhs))
            return ADMIN_MENU
        context.user_data["admin"] = {"peta": {i: lap.id for i, lap in enumerate(daftar, start=1)}}
        await query.message.reply_text(t("admin_minta_nomor_tolak", bhs))
        return ADMIN_TOLAK

    if aksi == "admin_hapus":
        daftar = database.laporan_ambil_semua_disetujui()
        ada_isi = await _kirim_daftar(query, bhs, daftar, "admin_daftar_terlapor_header", "admin_tidak_ada_terlapor")
        if not ada_isi:
            await query.message.reply_text(t("admin_menu_header", bhs), reply_markup=_keyboard_menu_admin(bhs))
            return ADMIN_MENU
        context.user_data["admin"] = {"peta": {i: lap.id for i, lap in enumerate(daftar, start=1)}}
        await query.message.reply_text(t("admin_minta_nomor_hapus", bhs))
        return ADMIN_HAPUS

    return ADMIN_MENU


async def _admin_proses_nomor(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    status_sekarang: int,
    fungsi_aksi,
    kunci_sukses: str,
    nama_aksi_log: str,
) -> int:
    bhs = await ambil_bahasa_pengguna(update, context)
    teks = (update.message.text or "").strip()
    peta = context.user_data.get("admin", {}).get("peta", {})

    if not teks.isdigit() or int(teks) not in peta:
        await update.message.reply_text(t("admin_nomor_tidak_valid", bhs))
        return status_sekarang

    nomor_tampil = int(teks)
    id_asli = peta[nomor_tampil]
    berhasil = fungsi_aksi(id_asli)

    if berhasil:
        tampilan.log_admin(f"Admin {update.effective_user.id} '{nama_aksi_log}' pada laporan id={id_asli}")
        await update.message.reply_text(t(kunci_sukses, bhs, nomor=nomor_tampil))
    else:
        await update.message.reply_text(t("admin_nomor_tidak_valid", bhs))

    context.user_data.pop("admin", None)
    await update.message.reply_text(t("admin_menu_header", bhs), reply_markup=_keyboard_menu_admin(bhs))
    return ADMIN_MENU


async def admin_proses_acc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _admin_proses_nomor(
        update, context,
        status_sekarang=ADMIN_ACC,
        fungsi_aksi=database.laporan_setujui,
        kunci_sukses="admin_acc_berhasil",
        nama_aksi_log="ACC",
    )


async def admin_proses_tolak(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _admin_proses_nomor(
        update, context,
        status_sekarang=ADMIN_TOLAK,
        fungsi_aksi=database.laporan_tolak,
        kunci_sukses="admin_tolak_berhasil",
        nama_aksi_log="TOLAK",
    )


async def admin_proses_hapus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    return await _admin_proses_nomor(
        update, context,
        status_sekarang=ADMIN_HAPUS,
        fungsi_aksi=database.laporan_hapus_disetujui,
        kunci_sukses="admin_hapus_berhasil",
        nama_aksi_log="HAPUS",
    )



async def penanganan_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangkap seluruh error yang tidak tertangani agar bot tidak pernah crash."""
    tampilan.log_error(f"Kesalahan tak tertangani: {context.error!r}")
    if isinstance(update, Update) and update.effective_chat:
        bhs = (context.user_data or {}).get("bahasa", config.BAHASA_DEFAULT)
        try:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=t("error_umum", bhs))
        except Exception:
            pass  



def _validasi_konfigurasi() -> list[str]:
    peringatan = []
    if config.TOKEN_BOT in ("", "GANTI_DENGAN_TOKEN_BOT_ANDA"):
        peringatan.append("TOKEN_BOT belum diisi di config.py — bot tidak akan bisa terhubung.")
    if not config.DAFTAR_ID_ADMIN:
        peringatan.append("DAFTAR_ID_ADMIN masih kosong di config.py — menu /admin belum bisa dipakai siapa pun.")
    if config.KUNCI_API_IMGBB in ("", "GANTI_DENGAN_API_KEY_IMGBB_ANDA"):
        peringatan.append("KUNCI_API_IMGBB belum diisi di config.py — upload foto bukti akan gagal.")
    return peringatan


def _bangun_aplikasi() -> Application:
    aplikasi = Application.builder().token(config.TOKEN_BOT).build()

    aplikasi.add_handler(CommandHandler("start", mulai))
    aplikasi.add_handler(CallbackQueryHandler(pilih_bahasa_callback, pattern="^bahasa_(id|en)$"))

    percakapan_cari = ConversationHandler(
        entry_points=[CallbackQueryHandler(cari_mulai, pattern="^menu_cari$")],
        states={
            CARI_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, cari_proses)],
            ConversationHandler.TIMEOUT: [
                MessageHandler(filters.ALL, sesi_habis),
                CallbackQueryHandler(sesi_habis),
            ],
        },
        fallbacks=[CommandHandler("batal", batal), MessageHandler(filters.ALL, masukan_tidak_dikenali)],
        conversation_timeout=config.BATAS_WAKTU_SESI_DETIK,
        name="percakapan_cari",
    )

    percakapan_lapor = ConversationHandler(
        entry_points=[CallbackQueryHandler(lapor_mulai, pattern="^menu_lapor$")],
        states={
            LAPOR_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, lapor_username)],
            LAPOR_KONTAK: [MessageHandler(filters.TEXT & ~filters.COMMAND, lapor_kontak)],
            LAPOR_KRONOLOGI: [MessageHandler(filters.TEXT & ~filters.COMMAND, lapor_kronologi)],
            LAPOR_BUKTI: [
                MessageHandler(filters.PHOTO, lapor_terima_foto),
                CallbackQueryHandler(lapor_selesai_upload, pattern="^lapor_selesai$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, lapor_bukan_foto),
            ],
            ConversationHandler.TIMEOUT: [
                MessageHandler(filters.ALL, sesi_habis),
                CallbackQueryHandler(sesi_habis),
            ],
        },
        fallbacks=[CommandHandler("batal", batal), MessageHandler(filters.ALL, masukan_tidak_dikenali)],
        conversation_timeout=config.BATAS_WAKTU_SESI_DETIK,
        name="percakapan_lapor",
    )

    percakapan_admin = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_mulai)],
        states={
            ADMIN_MENU: [
                CallbackQueryHandler(admin_menu_pilih, pattern="^admin_(pending|acc|tolak|list|hapus)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_menu_teks_tidak_dikenal),
            ],
            ADMIN_ACC: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_proses_acc)],
            ADMIN_TOLAK: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_proses_tolak)],
            ADMIN_HAPUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_proses_hapus)],
            ConversationHandler.TIMEOUT: [
                MessageHandler(filters.ALL, sesi_habis),
                CallbackQueryHandler(sesi_habis),
            ],
        },
        fallbacks=[CommandHandler("batal", batal), MessageHandler(filters.ALL, masukan_tidak_dikenali)],
        conversation_timeout=config.BATAS_WAKTU_SESI_DETIK,
        name="percakapan_admin",
    )

    aplikasi.add_handler(percakapan_cari)
    aplikasi.add_handler(percakapan_lapor)
    aplikasi.add_handler(percakapan_admin)
    aplikasi.add_handler(CommandHandler("batal", batal))
    aplikasi.add_error_handler(penanganan_error)

    return aplikasi


async def main_async() -> None:
    tampilan.tampilkan_banner()

    aset_ok = True
    daftar_peringatan: list[str] = []
    aplikasi: Application

    with tampilan.buat_progres_loading() as progres:
        tugas = progres.add_task("Status Checking...", total=6)

        progres.update(tugas, description="Status Checking...")
        daftar_peringatan = _validasi_konfigurasi()
        progres.advance(tugas)

        progres.update(tugas, description="Loading Database...")
        database.inisialisasi_database()
        progres.advance(tugas)

        progres.update(tugas, description="Checking Assets...")
        aset_ok = config.PATH_FOTO_SAMBUTAN.exists()
        progres.advance(tugas)

        progres.update(tugas, description="Loading Telegram...")
        aplikasi = _bangun_aplikasi()
        progres.advance(tugas)

        progres.update(tugas, description="Connecting...")
        await aplikasi.initialize()
        progres.advance(tugas)

        progres.update(tugas, description="Done.")
        progres.advance(tugas)

    for pesan in daftar_peringatan:
        tampilan.log_peringatan(pesan)
    if not aset_ok:
        tampilan.log_peringatan(f"File foto sambutan tidak ditemukan di {config.PATH_FOTO_SAMBUTAN}")

    tampilan.tampilkan_panel_info(
        username_bot=aplikasi.bot.username or config.USERNAME_BOT,
        id_bot=aplikasi.bot.id,
        statistik_db=database.statistik_hitung(),
    )
    tampilan.log_database("Database siap digunakan")

    await aplikasi.start()
    await aplikasi.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    tampilan.log_sukses("Bot berjalan dan siap menerima pesan. Tekan CTRL+C untuk berhenti.")

    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        tampilan.log_info("Menghentikan bot...")
        await aplikasi.updater.stop()
        await aplikasi.stop()
        await aplikasi.shutdown()
        tampilan.tampilkan_statistik_sesi_saat_berhenti()


def main() -> None:
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        tampilan.log_info("Bot dihentikan oleh pengguna.")


if __name__ == "__main__":
    main()
