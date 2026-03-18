<div align="center">

# Poppy Playtime: Community VR Mod Installer

![Release](https://img.shields.io/badge/Release-Latest-blue?style=for-the-badge)
![Windows](https://img.shields.io/badge/OS-Windows_Only-0078D6?style=for-the-badge&logo=windows&logoColor=white)
![VR](https://img.shields.io/badge/VR-OpenXR_%7C_OpenVR-22c55e?style=for-the-badge)
![License](https://img.shields.io/badge/License-Non--Profit_Fan_Project-a855f7?style=for-the-badge)

</div>

Poppy Playtime VR Mod is a virtual reality modification that completely transforms the base game experience by introducing full 6 degrees of freedom (6DOF) movement and native compatibility with both OpenXR and OpenVR standards for headsets like Meta Quest and SteamVR. Designed exclusively for Windows environments, this mod safely injects into the original game, allowing players to explore the Playtime Co. factory with unprecedented immersion, all managed through an intuitive installer and a dedicated VR Launcher.

## Mod Features

- **Full 6DOF Movement:** Total freedom to move, lean, and explore the environment in 3D space.
- **OpenXR & OpenVR Compatibility:** Works natively with the vast majority of modern headsets (Oculus, SteamVR, HTC, etc.).
- **Dual UEVR Support (Stable & Nightly):** The launcher now securely downloads both the Stable and Nightly UEVR builds directly from their original repositories. You can select which version to boot with using the toggle in the top-left corner of the launcher.
  - *Important Note:* The **Stable** version is only supported up to Chapter 3. For any chapters beyond that, you must use the **Nightly** version (which is fully compatible with all chapters).
- **Windows Exclusive:** Specifically optimized for the operating system where the base game runs.
- **Dedicated VR Launcher:** A unified launcher that integrates the necessary profiles and settings to run each chapter in VR, fully independent from the standard Steam execution.
- **Multi-Chapter Support:** Run any chapter you have installed directly from the launcher interface.

## Recent Fixes & Improvements

- **Chapter 1 Initialization Fix:** Corrected an issue within the installer that occasionally prevented the first chapter from initializing and launching properly.

## Download and Installation

The automated web installer (`PoppyInstaller_VR.exe`) is available in the **[Releases](../../releases)** section of this repository. **We highly recommend using this standard version** to ensure you always receive the latest updates, movement profiles, and bug fixes directly from the repositories.

**💾 Full Offline Build (March 2026) - *Fallback Only***
In addition to the standard web installer, the Releases section now includes a **Full Offline Installer**. **Please only use this version if the standard online installer fails for any reason.** This is a frozen, fully self-contained package compiled in March 2026. It comes pre-packaged with all the necessary movement profiles, the complete UEVR engine, and every dependency required. It is specifically designed to run in environments with zero or poor internet connection, and serves as a permanent backup in case the original download services go offline or remote resources are ever deleted.

**Steps:**

1. Download the latest version (Web Installer or Full Offline) from the *Releases* tab.
2. Run the installer and grant Administrator permissions when prompted, as they are required to apply the necessary patches.
3. The installer will attempt to detect your game folder automatically. If it does not, manually select the installation directory for each chapter.
4. Click **Install** and wait for the process to complete.
5. Once finished, open the desktop shortcut to launch the VR Launcher. From there you can select your preferred UEVR version (top-left corner) and run any chapter you have available.

## Credits

This project is made possible by the hard work of the VR developer community:

- **MalaBG:** For the configuration and fine-tuning of the movement profiles.
- **UEVR:** For providing the powerful base virtual reality injection engine.

## Legal Disclaimer

This mod is a non-profit fan project. No copyright infringement is intended in any way. *Poppy Playtime* and all its characters, models, and assets are the exclusive intellectual property of **Mob Entertainment**. It is mandatory to own a legitimate copy of the base game to use this modification.
"""

# Si deseas imprimirlo en la consola para verificar su contenido:
# print(readme_content)