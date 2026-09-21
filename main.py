import flet as ft
import root_manager
from lib import utilities, profile, account

current_save_data = None
active_character_id = None


def main(page: ft.Page):
    page.title = "SAS4 Mobile Tool"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 16
    page.scroll = ft.ScrollMode.AUTO

    # Komponen Status & Akun
    lbl_status = ft.Text("Tekan tombol di bawah untuk membaca file game via root.", color=ft.colors.GREY_400)
    dd_profiles = ft.Dropdown(label="Pilih Karakter / Profil", width=320)

    # Input Fields
    txt_money = ft.TextField(label="Cash / Credits ($)", keyboard_type=ft.KeyboardType.NUMBER)
    txt_level = ft.TextField(label="Level Karakter (1 - 100)", keyboard_type=ft.KeyboardType.NUMBER)
    txt_black_keys = ft.TextField(label="Black Keys", keyboard_type=ft.KeyboardType.NUMBER)
    txt_aug_cores = ft.TextField(label="Elite Augment Cores", keyboard_type=ft.KeyboardType.NUMBER)
    txt_strongbox = ft.TextField(label="Black Strongboxes", keyboard_type=ft.KeyboardType.NUMBER)

    def show_alert(msg: str, is_err: bool = False):
        snack = ft.SnackBar(ft.Text(msg), bgcolor=ft.colors.RED_800 if is_err else ft.colors.GREEN_800)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def update_form_fields(prof_id: str):
        if not current_save_data or prof_id not in current_save_data.get('Inventory', {}):
            return
        inv = current_save_data['Inventory'][prof_id]
        txt_money.value = str(inv.get('Money', 0))
        txt_level.value = str(inv.get('Skills', {}).get('PlayerLevel', 1))
        txt_black_keys.value = str(inv.get('Skills', {}).get('AvailableBlackKeys', 0))
        txt_aug_cores.value = str(inv.get('Skills', {}).get('AvailableEliteAugmentCores', 0))
        boxes = inv.get('Skills', {}).get('AvailableBlackStrongboxes', [])
        txt_strongbox.value = str(len(boxes) if isinstance(boxes, list) else 0)
        page.update()

    def on_profile_selected(e):
        global active_character_id
        active_character_id = dd_profiles.value
        update_form_fields(active_character_id)

    dd_profiles.on_change = on_profile_selected

    def pull_data_click(e):
        global current_save_data, active_character_id
        lbl_status.value = "Mencari direktori & menyalin file via root..."
        page.update()

        success, res = root_manager.pull_save_file()
        if not success:
            lbl_status.value = "Gagal memuat save."
            show_alert(res, is_err=True)
            return

        current_save_data = utilities.loadSave(res)
        if not current_save_data:
            lbl_status.value = "Gagal mendekripsi save file."
            show_alert("Format save korup / tidak dikenali.", is_err=True)
            return

        # Ambil daftar profile aktif
        profiles_list = utilities.getProfiles(current_save_data)
        names_list = utilities.getNames(current_save_data)

        dd_profiles.options = [
            ft.dropdown.Option(key=pid, text=f"{pid} ({pname})")
            for pid, pname in zip(profiles_list, names_list)
        ]

        if profiles_list:
            dd_profiles.value = profiles_list[0]
            active_character_id = profiles_list[0]
            update_form_fields(active_character_id)

        lbl_status.value = f"Data berhasil dimuat! Ditemukan {len(profiles_list)} profil."
        show_alert("Save game berhasil dibaca via root!")
        page.update()

    def apply_mod_click(e):
        global current_save_data, active_character_id
        if not current_save_data or not active_character_id:
            show_alert("Muat data terlebih dahulu!", is_err=True)
            return

        try:
            # 1. Update atribut form karakter
            profile._setMoneyLogic(current_save_data, active_character_id, int(txt_money.value or 0))
            profile._setLevelLogic(current_save_data, active_character_id, int(txt_level.value or 1))
            profile._setBlackKeysLogic(current_save_data, active_character_id, int(txt_black_keys.value or 0))
            profile._setAugCoresLogic(current_save_data, active_character_id, int(txt_aug_cores.value or 0))
            profile._setRandBlackStrongboxLogic(current_save_data, active_character_id, int(txt_strongbox.value or 0))

            # 2. Tulis ke file staging lalu push via su
            utilities.writeSave(current_save_data, root_manager.LOCAL_STAGING)
            ok, msg = root_manager.push_save_file()

            if ok:
                show_alert("Perubahan berhasil diterapkan ke game!")
                lbl_status.value = "Perubahan telah tersinkronisasi."
            else:
                show_alert(msg, is_err=True)
        except Exception as err:
            show_alert(f"Gagal menerapkan: {err}", is_err=True)
        page.update()

    def quick_max_stats(e):
        global current_save_data, active_character_id
        if not current_save_data or not active_character_id:
            show_alert("Muat data terlebih dahulu!", is_err=True)
            return

        items = utilities.loadItems()
        amount = 2**31 - 2**20

        # Logika modifikasi instan
        account._setCreditsLogic(current_save_data, 'ALL', amount)
        account._setNightmareTicketsLogic(current_save_data, amount)
        account._setTokensLogic(current_save_data, amount)
        account._removeAdsLogic(current_save_data, True)
        profile._setMasteryLevelsLogic(current_save_data, active_character_id)
        profile._setAllAmmoLogic(current_save_data, active_character_id, amount)
        profile._setMoneyLogic(current_save_data, active_character_id, amount)
        profile._setAugCoresLogic(current_save_data, active_character_id, amount)
        profile._setBlackKeysLogic(current_save_data, active_character_id, amount)
        profile._setLevelLogic(current_save_data, active_character_id, 100)
        profile._setPremiumWeaponsLogic(current_save_data, active_character_id, items['premium'], 'ALL', 10, 4, 12)

        update_form_fields(active_character_id)
        show_alert("Max stats & perlengkapan berhasil diset in-memory! Klik Terapkan untuk simpan.")

    # Layout Aplikasi
    page.add(
        ft.Text("SAS4 Save Manager (Mobile Root)", style=ft.TextThemeStyle.HEADLINE_SMALL),
        ft.ElevatedButton("Muat Save Game (Auto Root)", icon=ft.icons.REFRESH, on_click=pull_data_click),
        ft.Divider(),
        dd_profiles,
        txt_level,
        txt_money,
        txt_black_keys,
        txt_aug_cores,
        txt_strongbox,
        ft.Row([
            ft.OutlinedButton("Quick Max Character", icon=ft.icons.FLASH_ON, on_click=quick_max_stats),
            ft.FilledButton("Terapkan ke Game", icon=ft.icons.SAVE, on_click=apply_mod_click)
        ]),
        ft.Divider(),
        lbl_status
    )


if __name__ == "__main__":
    ft.app(target=main)