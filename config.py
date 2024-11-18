# 需要备份的目录（文件）
backup_dir = [
    "/var/www/geo.barku.re",
    "/var/www/file.barku.re",
    "/var/www/ai.barku.re",
    "/etc/caddy/Caddyfile",
]

# GitHub 仓库
repo = "barkure/Server-Backup"

# 文件大小限制（例如 100MB）
FILE_SIZE_LIMIT = 100 * 1024 * 1024

# 保留的备份次数
MAX_BACKUPS = 30