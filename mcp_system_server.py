"""
Servidor MCP - Ferramentas de Sistema para o Jarvis
Expõe: abrir aplicativos, controlar volume, listar/abrir arquivos, tirar screenshot.

Roda via stdio (o host conecta como subprocesso).
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

from mcp.server.mcpserver import MCPServer as FastMCP

mcp = FastMCP("jarvis-system")

SYSTEM = platform.system()  # "Windows", "Linux", "Darwin"


@mcp.tool()
def open_app(app_name: str) -> str:
    """Abre um aplicativo pelo nome (ex: 'notepad', 'chrome', 'calculator', 'code').

    Args:
        app_name: nome ou caminho do aplicativo a abrir
    """
    try:
        if SYSTEM == "Windows":
            os.startfile(app_name)  # type: ignore[attr-defined]
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", "-a", app_name])
        else:  # Linux
            subprocess.Popen([app_name])
        return f"Abrindo '{app_name}'."
    except Exception as e:
        return f"Não consegui abrir '{app_name}': {e}"


@mcp.tool()
def set_volume(level: int) -> str:
    """Define o volume do sistema (0 a 100).

    Args:
        level: nível de volume desejado, de 0 (mudo) a 100 (máximo)
    """
    level = max(0, min(100, level))
    try:
        if SYSTEM == "Windows":
            # Requer: pip install pycaw comtypes
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None
            )
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        elif SYSTEM == "Darwin":
            subprocess.run(
                ["osascript", "-e", f"set volume output volume {level}"],
                check=True,
            )
        else:  # Linux (PulseAudio/PipeWire)
            subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"],
                check=True,
            )
        return f"Volume ajustado para {level}%."
    except Exception as e:
        return f"Não consegui ajustar o volume: {e}"


@mcp.tool()
def list_files(directory: str = ".") -> str:
    """Lista arquivos e pastas de um diretório.

    Args:
        directory: caminho do diretório (padrão: diretório atual)
    """
    try:
        p = Path(directory).expanduser()
        items = sorted(p.iterdir())
        if not items:
            return f"'{directory}' está vazio."
        listing = "\n".join(
            f"{'[pasta] ' if i.is_dir() else ''}{i.name}" for i in items[:50]
        )
        return listing
    except Exception as e:
        return f"Não consegui listar '{directory}': {e}"


@mcp.tool()
def open_file(path: str) -> str:
    """Abre um arquivo com o aplicativo padrão do sistema.

    Args:
        path: caminho do arquivo a abrir
    """
    try:
        p = str(Path(path).expanduser())
        if SYSTEM == "Windows":
            os.startfile(p)  # type: ignore[attr-defined]
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", p])
        else:
            subprocess.Popen(["xdg-open", p])
        return f"Abrindo arquivo '{path}'."
    except Exception as e:
        return f"Não consegui abrir '{path}': {e}"


@mcp.tool()
def take_screenshot(save_path: str = "screenshot.png") -> str:
    """Tira um print da tela atual e salva em disco.

    Args:
        save_path: caminho onde salvar a imagem
    """
    try:
        import pyautogui  # requer: pip install pyautogui

        img = pyautogui.screenshot()
        img.save(save_path)
        return f"Screenshot salvo em '{save_path}'."
    except Exception as e:
        return f"Não consegui tirar o screenshot: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")