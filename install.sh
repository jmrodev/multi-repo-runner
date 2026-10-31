#!/usr/bin/env bash
set -e
INSTALL_DIR="${HOME}/.local/bin"
SCRIPT_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/repo_runner.py"

mkdir -p "${INSTALL_DIR}"
cat << WRAPPEREOF > "${INSTALL_DIR}/repo-all"
#!/usr/bin/env bash
python3 "${SCRIPT_SRC}" "\$@"
WRAPPEREOF

chmod +x "${INSTALL_DIR}/repo-all"
chmod +x "${SCRIPT_SRC}"
echo "✅ repo-all instalado en ${INSTALL_DIR}/repo-all"
