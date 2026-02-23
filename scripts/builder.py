import os
import sys
import shutil
import subprocess
import glob

APP_NAME = "DispatchProtocol"
ENTRY_POINT = "src/main.py"
DIST_DIR = "dist"
BUILD_DIR = "build"

def clean_artifacts():
    print("[-] Removendo artefatos antigos...")
    if os.path.exists(DIST_DIR): shutil.rmtree(DIST_DIR)
    if os.path.exists(BUILD_DIR): shutil.rmtree(BUILD_DIR)
    for spec in glob.glob("*.spec"):
        try:
            os.remove(spec)
        except OSError:
            pass

def cleanup_specs():
    """Varre o perímetro atrás de arquivos .spec residuais e os elimina."""
    print("[-] Varrendo em busca de lixo .spec...")
    for spec in glob.glob("*.spec"):
        try:
            os.remove(spec)
        except OSError:
            pass

def fix_permissions(workspace):
    """Restaura a posse dos arquivos para o usuário hospedeiro, evitando bloqueio por root."""
    if os.name != 'nt':  # Necessário apenas se o hospedeiro for Linux/Mac
        uid, gid = os.getuid(), os.getgid()
        chown_cmd = [
            "docker", "run", "--rm",
            "-v", f"{os.getcwd()}:{workspace}:z",
            "alpine", "sh", "-c",
            f"chown -R {uid}:{gid} {workspace}/dist {workspace}/build {workspace}/*.spec 2>/dev/null || true"
        ]
        subprocess.check_call(chown_cmd)

def build_windows_target():
    print("[+] Acionando Docker (Wine) para WINDOWS...")
    workspace = "/src"

    # Override Tático: Ignorando o entrypoint defeituoso da imagem com nossa própria cadência.
    internal_script = (
        "pip install -r requirements.txt && "
        f"pyinstaller --noconfirm --clean --onefile --console --name={APP_NAME}_Windows --hidden-import=cryptography --paths=src {ENTRY_POINT}"
    )

    cmd = [
        "docker", "run", "--rm",
        "--entrypoint", "sh",
        "-v", f"{os.getcwd()}:{workspace}:z",
        "--workdir", workspace,
        "batonogov/pyinstaller-windows:latest",
        "-c", internal_script
    ]
    subprocess.check_call(cmd)
    fix_permissions(workspace)

def build_linux_target():
    print("[+] Acionando Docker (Python Slim) para o LINUX...")
    workspace = "/src"

    internal_script = (
        "apt-get update && apt-get install -y binutils && "
        "pip install pyinstaller cryptography && "
        f"pyinstaller --noconfirm --clean --onefile --console --name={APP_NAME}_Linux --hidden-import=cryptography --paths=src {ENTRY_POINT}"
    )

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{os.getcwd()}:{workspace}:z",
        "--workdir", workspace,
        "python:3.10-slim",
        "sh", "-c", internal_script
    ]
    subprocess.check_call(cmd)
    fix_permissions(workspace)

def main():
    print("--- BUILDER: APLICAÇÃO DOCKERIZADA ---")

    if shutil.which("docker") is None:
        print("[!] Daemon do Docker não encontrado.")
        sys.exit(1)

    clean_artifacts()

    try:
        build_linux_target()
        build_windows_target()
        cleanup_specs()
        print(f"\n[SUCESSO] Ambos os binários foram assegurados em '{DIST_DIR}/'.")
    except subprocess.CalledProcessError:
        print("\n[FALHA] Compilação comprometida. Verifique os logs do Docker/PyInstaller para identificar a pane.")
        sys.exit(1)

if __name__ == "__main__":
    main()
