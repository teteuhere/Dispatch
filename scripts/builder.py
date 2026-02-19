import os
import sys
import shutil
import platform
import subprocess

APP_NAME = "DispatchProtocol"
ENTRY_POINT = "src/main.py"
DIST_DIR = "dist"
BUILD_DIR = "build"

def clean_artifacts():
    print("[-] Clearing staging area...")
    if os.path.exists(DIST_DIR):
        shutil.rmtree(DIST_DIR)
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    spec_file = f"{APP_NAME}.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)

def build_windows_native():
    print("[+] WINDOWS perimeter detected. Initiating native compilation...")
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
        print(f"\n[SUCCESS] Executable secured at: {os.path.join(DIST_DIR, APP_NAME + '.exe')}")
    except subprocess.CalledProcessError:
        print("\n[FAILURE] Native compilation compromised.")
        sys.exit(1)

def build_linux_cross_compile():
    print("[+] LINUX perimeter detected. Initiating Docker (Cross-Compile) protocol...")

    if shutil.which("docker") is None:
        print("[ERROR] Docker daemon not found. Target unreachable.")
        sys.exit(1)

    workspace_mnt = "/src"
    host_uid = str(os.getuid())
    host_gid = str(os.getgid())

    internal_cmd = (
        f"pyinstaller --noconfirm --clean --onefile --console --name={APP_NAME} "
        f"--hidden-import=cryptography --paths=src {ENTRY_POINT} && "
        f"chown -R {host_uid}:{host_gid} dist/ build/ {APP_NAME}.spec"
    )

    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{os.getcwd()}:{workspace_mnt}:z",
        "--workdir", workspace_mnt,
        "batonogov/pyinstaller-windows:latest",
        "sh", "-c", internal_cmd
    ]

    try:
        subprocess.check_call(docker_cmd)
        print(f"\n[SUCCESS] Windows executable secured at: {os.path.join(DIST_DIR, APP_NAME + '.exe')}")
    except subprocess.CalledProcessError:
        print("\n[FAILURE] Docker task force compromised.")
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
        print(f"[ERROR] Unsupported OS perimeter: {system_os}")

if __name__ == "__main__":
    main()
