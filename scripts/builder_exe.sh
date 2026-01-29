#!/bin/bash

# --- BUILDER PROTOCOL: LINUX TO WINDOWS ---

echo "--- DISPATCH: INITIATING WINDOWS BUILD SEQUENCE ---"

if [ ! -d "src" ]; then
    echo "ERROR: 'src' directory not found. Execute from project root."
    exit 1
fi

echo "TARGET: Windows Executable (dispatch.exe)"
echo "COMPILER: cdrx/pyinstaller-windows (Docker)"
echo "STATUS: Compiling..."


docker run --rm \
  -v "$(pwd):/src:z" \
  cdrx/pyinstaller-windows \
  "pyinstaller --clean --onefile \
   --name dispatch \
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
   src/teamsintegration/server.py"

echo "---------------------------------------------------"
echo "MISSION COMPLETE. Artifact located in 'dist/dispatch.exe'"
echo "---------------------------------------------------"
