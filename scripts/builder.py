import os
import sys
import shutil
import platform
import subprocess

# --- CONFIGURAÇÃO DA MISSÃO ---
APP_NAME = "DispatchProtocol"
ENTRY_POINT = "src/main.py"
DIST_DIR = "dist"
BUILD_DIR = "build"

def clean_artifacts():
    """Limpa restos de batalhas anteriores."""
    print(f"[-] Limpando área de construção...")
    if os.path.exists(DIST_DIR): shutil.rmtree(DIST_DIR)
    if os.path.exists(BUILD_DIR): shutil.rmtree(BUILD_DIR)
    spec_file = f"{APP_NAME}.spec"
    if os.path.exists(spec_file): os.remove(spec_file)

def build_windows_native():
    """Estratégia para quem já está no Windows."""
    print("[+] Detectado ambiente WINDOWS. Iniciando compilação nativa...")

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--console",
        f"--name={APP_NAME}",
        "--hidden-import=cryptography",
        "--paths=src",
        ENTRY_POINT
    ]

    try:
        subprocess.check_call(cmd)
        print(f"\n[SUCESSO] Executável pronto em: {os.path.join(DIST_DIR, APP_NAME + '.exe')}")
    except subprocess.CalledProcessError:
        print("\n[FALHA] Erro durante a compilação.")
        sys.exit(1)

def build_linux_cross_compile():
    """Estratégia para criar .exe estando no Linux (via Docker)."""
    print("[+] Detectado ambiente LINUX. Iniciando protocolo Docker (Cross-Compile)...")

    # Verifica se Docker está instalado
    if shutil.which("docker") is None:
        print("[ERRO] Docker não encontrado. Para criar .exe no Linux, o Docker é obrigatório.")
        sys.exit(1)

    # Comando PyInstaller que vai rodar DENTRO do container
    pyinstaller_cmd = (
        f"pyinstaller --clean --onefile --console --name {APP_NAME} "
        f"--hidden-import cryptography --paths src {ENTRY_POINT}"
    )

    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{os.getcwd()}:/src",  # Monta a pasta atual
        "cdrx/pyinstaller-windows",   # Imagem especialista
        pyinstaller_cmd
    ]

    try:
        subprocess.check_call(docker_cmd)
        print(f"\n[SUCESSO] Executável (Windows) gerado em: {os.path.join(DIST_DIR, APP_NAME + '.exe')}")
    except subprocess.CalledProcessError:
        print("\n[FALHA] O Docker não conseguiu completar a missão.")
        sys.exit(1)

def main():
    print(f"--- DISPATCH BUILDER: {APP_NAME} ---")
    clean_artifacts()

    system_os = platform.system()

    if system_os == "Windows":
        build_windows_native()
    elif system_os == "Linux":
        build_linux_cross_compile()
    else:
        print(f"[ERRO] Sistema operacional não suportado para esta operação: {system_os}")

if __name__ == "__main__":
    main()
