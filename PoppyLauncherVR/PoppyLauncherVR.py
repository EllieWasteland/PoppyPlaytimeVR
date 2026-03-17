import os
import sys
import time
import ctypes
import threading
import subprocess
import psutil
import webview
import json
import shutil
import zipfile
import urllib.request
import tempfile
import ssl
import webbrowser
from pyinjector import inject

CONFIG_JUEGOS = {
    1: {
        "exe": r"WindowsNoEditor\Poppy_Playtime\Binaries\Win64\Poppy_Playtime-Win64-Shipping.exe",
        "pak_folder": r"WindowsNoEditor\Poppy_Playtime\Content\Paks",
        "pak_file": "Z_agagaga_P.pak",
        "pak_source_path": r"chapters\ch1\Z_agagaga_P.pak",
        "profile_name": "Poppy_Playtime-Win64-Shipping",
        "zip_path": r"chapters\ch1\Poppy_Playtime-Win64-Shipping.zip"
    },
    2: {
        "exe": r"WindowsNoEditor\Playtime_Prototype4\Binaries\Win64\Playtime_Prototype4-Win64-Shipping.exe",
        "pak_folder": r"WindowsNoEditor\Playtime_Prototype4\Content\Paks",
        "pak_file": "Z_PPChapter2VR_P.pak",
        "pak_source_path": r"chapters\ch2\Z_PPChapter2VR_P.pak",
        "profile_name": "Playtime_Prototype4-Win64-Shipping",
        "zip_path": r"chapters\ch2\Playtime_Prototype4-Win64-Shipping.zip"
    },
    3: {
        "exe": r"PoppyPlaytime_Chapter3\Playtime_Chapter3\Binaries\Win64\Playtime_Chapter3-Win64-Shipping.exe",
        "profile_name": "Playtime_Chapter3-Win64-Shipping",
        "zip_path": r"chapters\ch3\Playtime_Chapter3-Win64-Shipping.zip"
    },
    4: {
        "exe": r"Playtime_Chapter4\ch4_pro\Binaries\Win64\ch4_pro-Win64-Shipping.exe",
        "profile_name": "ch4_pro-Win64-Shipping",
        "zip_path": r"chapters\ch4\ch4_pro-Win64-Shipping.zip"
    },
    5: {
        "exe": r"Chapter5\ch5_pro\Binaries\Win64\ch5_pro-Win64-Shipping.exe",
        "profile_name": "ch5_pro-Win64-Shipping",
        "zip_path": r"chapters\ch5\ch5_pro-Win64-Shipping.zip"
    }
}

def obtener_ruta_recurso(rel_path):
    if getattr(sys, 'frozen', False):
        ruta_meipass = os.path.join(sys._MEIPASS, rel_path)
        if os.path.exists(ruta_meipass):
            return ruta_meipass
        return os.path.join(os.path.dirname(sys.executable), rel_path)
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path)

def obtener_pid(nombre_ejecutable):
    for proceso in psutil.process_iter(['pid', 'name']):
        try:
            if proceso.info['name'].lower() == nombre_ejecutable.lower():
                return proceso.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

class LauncherAPI:
    def __init__(self):
        # Definiendo la versión actual de la aplicación
        self.CURRENT_VERSION = "v1.0.0-beta"

    def _wait_and_close(self, process):
        process.wait()
        self.close_app()
        
    def _get_game_base_dir(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def get_language(self):
        base_dir = self._get_game_base_dir()
        config_path = os.path.join(base_dir, "ConfigPPCVRLauncher.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get("language", "en")
        except Exception:
            pass
        return "en"

    def check_updates(self):
        """Verifica en GitHub si hay una nueva versión disponible basándose en el TAG de Releases."""
        try:
            url = "https://api.github.com/repos/EllieWasteland/PoppyPlaytimeVR/releases"
            req = urllib.request.Request(url, headers={'User-Agent': 'PoppyPlaytimeVR-Launcher'})
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Timeout reducido a 1.5 segundos para evitar bloqueos sin internet
            with urllib.request.urlopen(req, context=ctx, timeout=1.5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    if data and len(data) > 0:
                        # Obtenemos el release más reciente
                        latest_release = data[0]
                        latest_version = latest_release.get("tag_name", "")
                        release_url = latest_release.get("html_url", "")
                        
                        # Si la versión de GitHub no es la misma que la actual, notificamos
                        if latest_version and latest_version != self.CURRENT_VERSION:
                            return {"update_available": True, "version": latest_version, "url": release_url}
        except Exception as e:
            # Silenciar errores si el usuario no tiene internet para no molestar la experiencia offline
            pass
            
        return {"update_available": False}

    def open_url(self, url):
        """Abre un enlace en el navegador predeterminado del sistema operativo"""
        webbrowser.open(url)

    def _set_boot_status(self, text):
        try:
            if webview.windows:
                safe_text = text.replace("'", "\\'")
                webview.windows[0].evaluate_js(f"document.getElementById('boot-text').textContent = '{safe_text}';")
        except Exception:
            pass

    def _get_dll_paths(self, folder):
        """Busca recursivamente los DLLs requeridos y devuelve sus rutas absolutas."""
        paths = {}
        dlls_to_find = ["UEVRBackend.dll", "openxr_loader.dll", "openvr_api.dll"]
        
        if not os.path.exists(folder):
            return paths
            
        for root, dirs, files in os.walk(folder):
            for dll in dlls_to_find:
                if dll in files and dll not in paths:
                    paths[dll] = os.path.join(root, dll)
        return paths

    def _has_all_dlls(self, folder):
        paths = self._get_dll_paths(folder)
        return len(paths) == 3

    def _download_and_extract(self, url, dest_folder):
        """Descarga y extrae el ZIP desde una URL a la carpeta destino."""
        # Ignorar certificados SSL para evitar problemas de conexión en Windows
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        os.makedirs(dest_folder, exist_ok=True)
        temp_zip = os.path.join(tempfile.gettempdir(), "uevr_temp.zip")
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as response, open(temp_zip, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(dest_folder)
        
        os.remove(temp_zip)

    def check_files(self):
        try:
            available_chapters = []
            game_base_dir = self._get_game_base_dir()
            lang = self.get_language()
            
            # 1. Comprobación y Descarga de UEVR
            vr_files_dir = os.path.join(game_base_dir, "LauncherVRFiles")
            stable_dir = os.path.join(vr_files_dir, "UEVR Stable")
            nightly_dir = os.path.join(vr_files_dir, "UEVR Nightly")
            
            stable_url = "https://github.com/praydog/UEVR/releases/download/1.05/UEVR.zip"
            nightly_url = "https://github.com/praydog/UEVR-nightly/releases/download/nightly-01127-6f66affc01cea22e4b1b5a47986e1ade80ccbd26/uevr.zip"
            
            try:
                if not self._has_all_dlls(stable_dir):
                    msg_st = "DOWNLOADING UEVR STABLE..." if lang == "en" else "DESCARGANDO UEVR STABLE..."
                    self._set_boot_status(msg_st)
                    self._download_and_extract(stable_url, stable_dir)
                    
                if not self._has_all_dlls(nightly_dir):
                    msg_nt = "DOWNLOADING UEVR NIGHTLY..." if lang == "en" else "DESCARGANDO UEVR NIGHTLY..."
                    self._set_boot_status(msg_nt)
                    self._download_and_extract(nightly_url, nightly_dir)
            except Exception as e:
                msg = "Error al descargar dependencias de UEVR." if lang == "es" else "Error downloading UEVR dependencies."
                hnt = "Revisa tu conexión a internet." if lang == "es" else "Check your internet connection."
                return {"status": "error", "message": msg, "hint": f"{hnt} ({e})"}

            # Verificación final de los DLLs tras la posible descarga
            if not self._has_all_dlls(stable_dir) or not self._has_all_dlls(nightly_dir):
                msg = "Faltan archivos DLL de UEVR." if lang == "es" else "UEVR DLL files missing."
                hnt = "Tu antivirus podría estar bloqueando las descargas." if lang == "es" else "Your antivirus might be blocking the downloads."
                return {"status": "error", "message": msg, "hint": hnt}
            
            # Restaurar el texto del progreso
            self._set_boot_status("System ready." if lang == "en" else "Sistema listo.")
            
            # 2. Comprobación de los juegos (Archivos locales)
            for ch_id, config in CONFIG_JUEGOS.items():
                exe_abs_path = os.path.join(game_base_dir, os.path.normpath(config["exe"]))
                if os.path.exists(exe_abs_path):
                    zip_abs = obtener_ruta_recurso(os.path.normpath(config["zip_path"]))
                    if not os.path.exists(zip_abs):
                        msg = f"Falta el perfil VR (ZIP) del Capítulo {ch_id}." if lang == "es" else f"VR profile (ZIP) for Chapter {ch_id} missing."
                        hnt = f"Asegúrate de tener: {config['zip_path']}" if lang == "es" else f"Make sure you have: {config['zip_path']}"
                        return {"status": "error", "message": msg, "hint": hnt}
                        
                    if "pak_source_path" in config:
                        pak_abs = obtener_ruta_recurso(os.path.normpath(config["pak_source_path"]))
                        if not os.path.exists(pak_abs):
                            msg = f"Falta el archivo .pak del Capítulo {ch_id}." if lang == "es" else f"The .pak file for Chapter {ch_id} is missing."
                            hnt = f"Asegúrate de tener: {config['pak_source_path']}" if lang == "es" else f"Make sure you have: {config['pak_source_path']}"
                            return {"status": "error", "message": msg, "hint": hnt}
                            
                    available_chapters.append(ch_id)
            
            if not available_chapters:
                msg = "No se encontraron juegos instalados." if lang == "es" else "No installed games found."
                hnt = "Asegúrate de que el launcher esté en la carpeta base de 'Poppy Playtime'." if lang == "es" else "Make sure the launcher is in the 'Poppy Playtime' base folder."
                return {"status": "error", "message": msg, "hint": hnt}
                
            return {"status": "success", "available_chapters": available_chapters}
            
        except Exception as e:
            msg = "Error interno al verificar archivos." if lang == "es" else "Internal error verifying files."
            return {"status": "error", "message": msg, "hint": str(e)}

    def launch_vr(self, chapter_id, mode, uevr_version="stable", vr_api="openxr"):
        chapter_id = int(chapter_id)
        config = CONFIG_JUEGOS.get(chapter_id)
        lang = self.get_language()
        
        if not config:
            return {"status": "error", "message": "Chapter config not found.", "hint": ""}
            
        game_base_dir = self._get_game_base_dir()
        exe_abs_path = os.path.join(game_base_dir, os.path.normpath(config["exe"]))
        
        if not os.path.exists(exe_abs_path):
            msg = "Ejecutable no encontrado." if lang == "es" else "Executable not found."
            hnt = f"Faltan archivos del Capítulo {chapter_id}." if lang == "es" else f"Chapter {chapter_id} files are missing."
            return {"status": "error", "message": msg, "hint": hnt}
            
        base_dir = os.path.dirname(exe_abs_path)
        nombre_ejecutable = os.path.basename(exe_abs_path)

        app_data = os.environ.get('APPDATA', '')
        uevr_root = os.path.join(app_data, "UnrealVRMod")
        os.makedirs(uevr_root, exist_ok=True)
        
        try:
            if mode == "immersive":
                profile_dir = os.path.join(uevr_root, config["profile_name"])
                if os.path.exists(profile_dir):
                    shutil.rmtree(profile_dir)
                    
                if "pak_file" in config:
                    pak_abs_path = os.path.join(game_base_dir, os.path.normpath(config["pak_folder"]), config["pak_file"])
                    if os.path.exists(pak_abs_path):
                        os.remove(pak_abs_path)
                        
            elif mode in ["full_vr", "vr"]:
                # 1. Gestionar archivos .pak PRIMERO (Si el capítulo los utiliza)
                if "pak_file" in config:
                    pak_dest_folder = os.path.join(game_base_dir, os.path.normpath(config["pak_folder"]))
                    pak_dest = os.path.join(pak_dest_folder, config["pak_file"])
                    
                    if mode == "full_vr" and "pak_source_path" in config:
                        pak_src = obtener_ruta_recurso(os.path.normpath(config["pak_source_path"]))
                        if os.path.exists(pak_src):
                            os.makedirs(pak_dest_folder, exist_ok=True)
                            shutil.copy2(pak_src, pak_dest)
                    elif mode == "vr":
                        if os.path.exists(pak_dest):
                            os.remove(pak_dest)

                # 2. Descomprimir el ZIP del perfil y luego modificar config.txt
                zip_abs_path = obtener_ruta_recurso(os.path.normpath(config["zip_path"]))
                if os.path.exists(zip_abs_path):
                    dest_folder = os.path.join(uevr_root, config["profile_name"])
                    if os.path.exists(dest_folder):
                        shutil.rmtree(dest_folder)
                    os.makedirs(dest_folder, exist_ok=True)
                    
                    with zipfile.ZipFile(zip_abs_path, 'r') as zip_ref:
                        zip_ref.extractall(dest_folder)
                        
                    # --- LÓGICA DE CONFIG.TXT PARA OPENXR/OPENVR ---
                    config_txt_path = os.path.join(dest_folder, "config.txt")
                    target_runtime = "openvr_api.dll" if vr_api == "openvr" else "openxr_loader.dll"
                    
                    if os.path.exists(config_txt_path):
                        with open(config_txt_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            
                        runtime_found = False
                        for i, line in enumerate(lines):
                            if line.strip().startswith("Frontend_RequestedRuntime="):
                                lines[i] = f"Frontend_RequestedRuntime={target_runtime}\n"
                                runtime_found = True
                                break
                                
                        if not runtime_found:
                            lines.append(f"\nFrontend_RequestedRuntime={target_runtime}\n")
                            
                        with open(config_txt_path, 'w', encoding='utf-8') as f:
                            f.writelines(lines)
                    else:
                        with open(config_txt_path, 'w', encoding='utf-8') as f:
                            f.write(f"Frontend_RequestedRuntime={target_runtime}\n")
                    # -----------------------------------------------
                else:
                    msg = "Zip de perfil no encontrado." if lang == "es" else "Profile Zip not found."
                    hnt = f"Falta {config['zip_path']} en la carpeta." if lang == "es" else f"Missing {config['zip_path']} in folder."
                    return {"status": "error", "message": msg, "hint": hnt}
                    
        except Exception as e:
            msg = f"Error de configuración: {e}" if lang == "es" else f"Setup error: {e}"
            hnt = "Cierra el juego si ya se está ejecutando." if lang == "es" else "Close the game if it is already running."
            return {"status": "error", "message": msg, "hint": hnt}

        try:
            game_process = subprocess.Popen([exe_abs_path], cwd=base_dir)
        except Exception as e:
            msg = f"Error al abrir el juego: {e}" if lang == "es" else f"Error opening game: {e}"
            hnt = "Verifica los permisos o la integridad del archivo." if lang == "es" else "Check permissions or file integrity."
            return {"status": "error", "message": msg, "hint": hnt}

        pid = None
        for _ in range(20): 
            time.sleep(1)
            pid = obtener_pid(nombre_ejecutable)
            if pid:
                break

        if pid:
            time.sleep(8) 
            try:
                # Determinamos la carpeta según la versión elegida en el frontend (Stable o Nightly)
                version_folder = "UEVR Nightly" if uevr_version == "nightly" else "UEVR Stable"
                uevr_dir = os.path.join(game_base_dir, "LauncherVRFiles", version_folder)
                dlls = self._get_dll_paths(uevr_dir)
                
                ruta_loader = dlls.get("openvr_api.dll") if vr_api == "openvr" else dlls.get("openxr_loader.dll")
                ruta_backend = dlls.get("UEVRBackend.dll")
                
                if ruta_loader and os.path.exists(ruta_loader):
                    inject(pid, ruta_loader)
                    time.sleep(0.5)
                
                if ruta_backend and os.path.exists(ruta_backend):
                    inject(pid, ruta_backend)
                    threading.Thread(target=self._wait_and_close, args=(game_process,), daemon=True).start()
                    return {"status": "success"}
                else:
                    msg = f"UEVRBackend.dll no encontrado en {version_folder}" if lang == "es" else f"UEVRBackend.dll not found in {version_folder}"
                    hnt = "Elimina la carpeta LauncherVRFiles para forzar la descarga." if lang == "es" else "Delete the LauncherVRFiles folder to force redownload."
                    return {"status": "error", "message": msg, "hint": hnt}
            except Exception as e:
                msg = f"Error de inyección: {e}" if lang == "es" else f"Injection error: {e}"
                hnt = "Verifica que tu antivirus no bloquee pyinjector." if lang == "es" else "Verify your antivirus is not blocking pyinjector."
                return {"status": "error", "message": msg, "hint": hnt}
        else:
            msg = "No se pudo detectar el proceso del juego." if lang == "es" else "Could not detect game process."
            hnt = "El juego se cerró inesperadamente o tardó mucho." if lang == "es" else "The game closed unexpectedly or took too long."
            return {"status": "error", "message": msg, "hint": hnt}

    def launch_flat(self, chapter_id):
        chapter_id = int(chapter_id)
        config = CONFIG_JUEGOS.get(chapter_id)
        lang = self.get_language()
        
        if not config:
            return {"status": "error", "message": "Chapter not configured.", "hint": ""}
            
        game_base_dir = self._get_game_base_dir()
        exe_abs_path = os.path.join(game_base_dir, os.path.normpath(config["exe"]))
        
        if not os.path.exists(exe_abs_path):
            msg = "Ejecutable no encontrado." if lang == "es" else "Executable not found."
            hnt = f"Faltan archivos del Capítulo {chapter_id}." if lang == "es" else f"Chapter {chapter_id} files are missing."
            return {"status": "error", "message": msg, "hint": hnt}
            
        base_dir = os.path.dirname(exe_abs_path)

        try:
            if "pak_file" in config:
                pak_abs_path = os.path.join(game_base_dir, os.path.normpath(config["pak_folder"]), config["pak_file"])
                if os.path.exists(pak_abs_path):
                    os.remove(pak_abs_path)
        except Exception as e:
            pass 

        try:
            game_process = subprocess.Popen([exe_abs_path], cwd=base_dir)
            threading.Thread(target=self._wait_and_close, args=(game_process,), daemon=True).start()
            return {"status": "success"}
        except Exception as e:
            msg = f"Error al abrir el juego: {e}" if lang == "es" else f"Error opening game: {e}"
            hnt = "Verifica los permisos o la integridad del archivo." if lang == "es" else "Check permissions or file integrity."
            return {"status": "error", "message": msg, "hint": hnt}

    def close_app(self):
        if webview.windows:
            webview.windows[0].destroy()
        os._exit(0)

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
        exe_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        exe_dir = base_dir

    os.chdir(exe_dir)
    
    api = LauncherAPI()
    html_path = os.path.join(base_dir, "PoppyLauncherVR.html")

    window = webview.create_window(
        title='Poppy Playtime VR Launcher',
        url=html_path,
        js_api=api,
        width=1200,   
        height=750,   
        frameless=True,
        easy_drag=True,
        transparent=False,
        background_color='#0f172a' 
    )

    webview.start()