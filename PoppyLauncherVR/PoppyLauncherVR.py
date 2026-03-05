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

RUTA_UEVR_BACKEND = obtener_ruta_recurso(os.path.join("UEVR", "UEVRBackend.dll"))
RUTA_UEVR_LOADER  = obtener_ruta_recurso(os.path.join("UEVR", "openxr_loader.dll"))

def obtener_pid(nombre_ejecutable):
    for proceso in psutil.process_iter(['pid', 'name']):
        try:
            if proceso.info['name'].lower() == nombre_ejecutable.lower():
                return proceso.info['pid']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

class LauncherAPI:
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
        except Exception as e:
            print(f"Error al leer JSON de idioma: {e}")
            pass
        return "en"

    def check_files(self):
        try:
            available_chapters = []
            game_base_dir = self._get_game_base_dir()
            lang = self.get_language()
            
            if not os.path.exists(RUTA_UEVR_BACKEND) or not os.path.exists(RUTA_UEVR_LOADER):
                msg = "Faltan las dependencias de UEVR." if lang == "es" else "UEVR dependencies missing."
                hnt = "Verifica que la carpeta 'UEVR' esté junto al launcher." if lang == "es" else "Verify the 'UEVR' folder is next to the launcher."
                return {"status": "error", "message": msg, "hint": hnt}
            
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

    def launch_vr(self, chapter_id, mode):
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
                zip_abs_path = obtener_ruta_recurso(os.path.normpath(config["zip_path"]))
                if os.path.exists(zip_abs_path):
                    dest_folder = os.path.join(uevr_root, config["profile_name"])
                    if os.path.exists(dest_folder):
                        shutil.rmtree(dest_folder)
                    os.makedirs(dest_folder, exist_ok=True)
                    
                    with zipfile.ZipFile(zip_abs_path, 'r') as zip_ref:
                        zip_ref.extractall(dest_folder)
                        
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
                if os.path.exists(RUTA_UEVR_LOADER):
                    inject(pid, RUTA_UEVR_LOADER)
                    time.sleep(0.5)
                if os.path.exists(RUTA_UEVR_BACKEND):
                    inject(pid, RUTA_UEVR_BACKEND)
                    threading.Thread(target=self._wait_and_close, args=(game_process,), daemon=True).start()
                    return {"status": "success"}
                else:
                    msg = "UEVRBackend.dll no encontrado" if lang == "es" else "UEVRBackend.dll not found"
                    hnt = "Asegúrate de que la carpeta 'UEVR' esté incluida." if lang == "es" else "Make sure the 'UEVR' folder is included."
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