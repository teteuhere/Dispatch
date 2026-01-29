#!/bin/bash
echo "--- DISPATCH: INITIATING WINDOWS BUILD SEQUENCE ---"

if [ ! -d "src" ]; then
    echo "ERROR: 'src' directory not found."
    exit 1
fi

echo "TARGET: Native Windows App (dispatch.exe)"

# Dockerized PyInstaller
docker run --rm \
  -v "$(pwd):/src:z" \
  cdrx/pyinstaller-windows \
  "pyinstaller --clean --onefile \
   --name dispatch \
   --noconsole \
   --add-data 'src/frontend;src/frontend' \
   --hidden-import='uvicorn.logging' \
   --hidden-import='uvicorn.loops' \
   --hidden-import='uvicorn.loops.auto' \
   --hidden-import='uvicorn.protocols' \
   --hidden-import='uvicorn.protocols.http' \
   --hidden-import='uvicorn.protocols.http.auto' \
   --hidden-import='uvicorn.lifespan' \
   --hidden-import='uvicorn.lifespan.on' \
   --hidden-import='dotenv' \
   --hidden-import='webview' \
   --hidden-import='cryptography' \
   src/dispatch/server.py"  <-- UPDATED PATH

echo "---------------------------------------------------"
echo "MISSION COMPLETE. Artifact located in 'dist/dispatch.exe'"
echo "---------------------------------------------------"
