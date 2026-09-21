import os
import subprocess

GAME_PKG = "com.ninjakiwi.sasza4"
BASE_PATH = f"/data/data/{GAME_PKG}/files"
LOCAL_STAGING = "temp_profile.save"

# Menyimpan path save yang aktif setelah auto-discovery
active_save_path = None


def run_su_command(command: str) -> tuple[bool, str]:
    try:
        process = subprocess.run(
            ["su", "-c", command],
            capture_output=True,
            text=True,
            check=True
        )
        return True, process.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()
    except FileNotFoundError:
        return False, "Binary 'su' tidak ditemukan. Pastikan perangkat sudah di-root."


def discover_save_path() -> tuple[bool, str]:
    """Mencari lokasi profile.save secara otomatis di dalam subfolder files/"""
    global active_save_path
    
    # Cari semua file profile.save di kedalaman subdirektori files
    find_cmd = f"find {BASE_PATH} -maxdepth 2 -name profile.save"
    success, output = run_su_command(find_cmd)
    
    if not success or not output:
        return False, "File profile.save tidak ditemukan di folder game."
    
    paths = [p.strip() for p in output.splitlines() if p.strip().endswith("profile.save")]
    if not paths:
        return False, "Tidak ada profile.save yang valid."

    # Ambil path pertama yang ditemukan (atau yang paling aktif)
    active_save_path = paths[0]
    return True, active_save_path


def pull_save_file() -> tuple[bool, str]:
    global active_save_path
    
    # Cari path save jika belum terdeteksi
    success, res = discover_save_path()
    if not success:
        return False, res

    local_abs = os.path.abspath(LOCAL_STAGING)
    cmd = f"cp {active_save_path} {local_abs} && chmod 666 {local_abs}"
    success, msg = run_su_command(cmd)
    
    if not success:
        return False, f"Gagal menyalin file save: {msg}"
    return True, local_abs


def push_save_file() -> tuple[bool, str]:
    global active_save_path
    if not active_save_path:
        return False, "Target save path belum teridentifikasi."

    local_abs = os.path.abspath(LOCAL_STAGING)
    # Kembalikan file, pulihkan permission, dan sesuaikan ownership dengan owner folder game
    cmd = (
        f"cp {local_abs} {active_save_path} && "
        f"chmod 660 {active_save_path} && "
        f"chown $(stat -c '%u:%g' {BASE_PATH}) {active_save_path}"
    )
    success, msg = run_su_command(cmd)
    
    if not success:
        return False, f"Gagal menerapkan file ke game: {msg}"
    return True, "Data berhasil diterapkan ke direktori akun game."