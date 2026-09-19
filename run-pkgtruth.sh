#!/data/data/com.termux/files/usr/bin/bash
# Обгортка для pkgtruth MCP — обхід бага shebang #!/usr/bin/env
# (Termux не має /usr/bin/env, той самий баг, що й у mcp-probe — TROUBLES.md)

exec /data/data/com.termux/files/usr/bin/node /data/data/com.termux/files/usr/bin/pkgtruth
