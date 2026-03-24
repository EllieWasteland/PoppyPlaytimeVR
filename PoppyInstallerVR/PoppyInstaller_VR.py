import webview
import os
import sys
import shutil
import json
from pyshortcuts import make_shortcut  # Reemplazamos win32com por pyshortcuts

def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

class InstallApi:
    def __init__(self):
        self.desktop_path = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
        self.base_dir = get_base_path()

    def get_common_steam_paths(self):
        """Devuelve una lista de rutas comunes donde suele instalarse el juego."""
        return [
            r"C:\Program Files (x86)\Steam\steamapps\common\Poppy Playtime",
            r"C:\Program Files\Steam\steamapps\common\Poppy Playtime",
            r"D:\SteamLibrary\steamapps\common\Poppy Playtime",
            r"E:\SteamLibrary\steamapps\common\Poppy Playtime",
            r"F:\SteamLibrary\steamapps\common\Poppy Playtime"
        ]

    def verify_exe(self, folder_path):
        """Verifica la estructura de carpetas de Poppy Playtime."""
        if not folder_path:
            return False
            
        folder_path = os.path.normpath(folder_path)
        
        # Buscamos directorios clave para validar que es la ruta correcta
        indicators = ["WindowsNoEditor", "Poppy_Playtime", "Playtime_Prototype4"]
        
        # Revisar si los indicadores están en la carpeta o la carpeta en sí es WindowsNoEditor
        if any(os.path.exists(os.path.join(folder_path, i)) for i in indicators) or "WindowsNoEditor" in folder_path:
            if "WindowsNoEditor" in folder_path:
                return folder_path.split("WindowsNoEditor")[0].rstrip(os.sep)
            return folder_path
            
        return False

    def auto_find_dir(self):
        """Busca automáticamente el directorio del juego en las rutas comunes."""
        for p in self.get_common_steam_paths():
            base = self.verify_exe(p)
            if base:
                return base
        return None

    def select_folder(self):
        """Abre un diálogo nativo para seleccionar la carpeta manualmente."""
        try:
            window = webview.windows[0]
            result = window.create_file_dialog(webview.FileDialog.FOLDER, directory="")
            if result and len(result) > 0:
                return result[0]
        except Exception as e:
            print(f"Error al abrir dialogo: {e}")
        return None

    def install(self, folder_path, lenguaje="en"):
        """Ejecuta la instalación: Copiar el .exe, crear JSON, acceso directo y eliminar OpenXR."""
        try:
            folder_path = os.path.normpath(folder_path)
            
            # 1. Copiar PoppyLauncherVR.exe
            exe_src = os.path.join(self.base_dir, "PoppyLauncherVR.exe")
            exe_dest = os.path.join(folder_path, "PoppyLauncherVR.exe")
            
            if os.path.exists(exe_src):
                shutil.copy2(exe_src, exe_dest)
            else:
                print("Advertencia: PoppyLauncherVR.exe no encontrado junto al instalador. Omitiendo copia.")

            # 2. Crear archivo JSON con el idioma seleccionado
            try:
                config_path = os.path.join(folder_path, "ConfigPPCVRLauncher.json")
                config_data = {
                    "lenguaje": lenguaje
                }
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config_data, f, indent=4)
            except Exception as e:
                print(f"No se pudo crear el archivo JSON de configuración: {e}")

            # 3. Crear Acceso Directo usando pyshortcuts
            try:
                icon_path = os.path.join(self.base_dir, "logo.ico") # <-- Obtenemos la ruta del icono
                make_shortcut(
                    script=exe_dest,       # El archivo base 
                    executable=exe_dest,   # Forzamos el ejecutable para evitar que use el Instalador
                    name='PoppyLauncherVR',
                    description='Launcher de Poppy Community VR',
                    icon=icon_path,        # <-- AÑADIDO: Le pasamos el icono al acceso directo
                    terminal=False,    
                    desktop=True,      
                    startmenu=True     
                )
                print("Acceso directo creado exitosamente con pyshortcuts.")
            except Exception as e:
                print(f"No se pudo crear el acceso directo: {e}")

            # 4. Eliminar la carpeta OpenXR si existe
            try:
                openxr_path = os.path.join(folder_path, "WindowsNoEditor", "Engine", "Binaries", "ThirdParty", "OpenXR")
                if os.path.exists(openxr_path):
                    shutil.rmtree(openxr_path)
                    print(f"Carpeta OpenXR eliminada exitosamente en: {openxr_path}")
                else:
                    print(f"La carpeta OpenXR no existe en la ruta especificada. Se omite la eliminación.")
            except Exception as e:
                print(f"No se pudo eliminar la carpeta OpenXR: {e}")

            return "success"
            
        except Exception as e:
            print(f"Error crítico en instalación: {e}")
            return "error"

    def close_app(self):
        """Cierra el instalador."""
        if len(webview.windows) > 0:
            webview.windows[0].destroy()

def main():
    api = InstallApi()
    
    webview.create_window(
        title='PoppyCommunityVR - Setup',
        url='Poppy_Installer.html',
        js_api=api,
        width=1200,
        height=750,
        frameless=True,
        easy_drag=False,
        background_color='#0F172A',
        transparent=False
    )
    
    webview.start(debug=False)

if __name__ == '__main__':
    main()