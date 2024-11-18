import os
import subprocess
from datetime import datetime
from config import backup_dir, repo, FILE_SIZE_LIMIT, MAX_BACKUPS


"""
1. 先拉取仓库（如果有的话），以保持本地仓库和远程仓库同步
"""
# 检查是否已有本地 Git 仓库
if not os.path.exists(os.path.join("backup", ".git")):
    # 检查是否有远程仓库
    remote_url = f"git@github.com:{repo}.git"
    result = subprocess.run(["git", "ls-remote", remote_url], capture_output=True, text=True)
    
    if result.returncode == 0:
        # 远程仓库存在，克隆到本地
        subprocess.run(["git", "clone", remote_url, "backup"], check=True)
        # 检查远程仓库是否有 main 分支
        result = subprocess.run(["git", "ls-remote", "--heads", "origin", "main"], cwd="backup", capture_output=True, text=True)
        if "refs/heads/main" not in result.stdout:
            # 如果没有 main 分支，初始化本地仓库并推送初始提交
            subprocess.run(["git", "init", "-b", "main"], cwd="backup", check=True)
            subprocess.run(["git", "commit", "--allow-empty", "-m", "Initial commit"], cwd="backup", check=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], cwd="backup", check=True)
    else:
        print("远程仓库不存在，请先创建远程仓库！")
else:
    # 拉取远程内容以保持同步
    subprocess.run(["git", "pull", "origin", "main", "--allow-unrelated-histories"], cwd="backup", check=True)


"""
2. 备份文件，更新备份列表文件，删除早期的备份，分割大文件
   如果文件大小超过 FILE_SIZE_LIMIT（默认为 100 MiB），则将文件分割为多个文件
"""
# 获取当前时间戳
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

# 创建带有时间戳的备份目录
backup_dir_path = f"backup/{timestamp}"
if not os.path.exists(backup_dir_path):
    os.makedirs(backup_dir_path)

# 处理需要备份的目录和文件
for path in backup_dir:
    try:
        if os.path.exists(path):
            if os.path.isdir(path):
                # 如果是目录，则打包压缩
                tar_file = os.path.join(backup_dir_path, os.path.basename(path) + ".tar.gz")
                subprocess.run(["tar", "-czf", tar_file, "-C", os.path.dirname(path), os.path.basename(path)], check=True)
                # 检查文件大小并分割大文件
                if os.path.getsize(tar_file) > FILE_SIZE_LIMIT:
                    subprocess.run(["split", "-b", f"{FILE_SIZE_LIMIT}", tar_file, tar_file + ".part_"], check=True)
                    os.remove(tar_file)
            else:
                # 如果是文件，则直接复制
                dest_file = os.path.join(backup_dir_path, os.path.basename(path))
                subprocess.run(["cp", path, dest_file], check=True)
                # 检查文件大小并分割大文件
                if os.path.getsize(dest_file) > FILE_SIZE_LIMIT:
                    subprocess.run(["split", "-b", f"{FILE_SIZE_LIMIT}", dest_file, dest_file + ".part_"], check=True)
                    os.remove(dest_file)
        else:
            print(f"Path {path} does not exist.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while processing {path}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# 更新备份列表文件
backup_list_file = "backup/backup_list.txt"
if not os.path.exists("backup"):
    os.makedirs("backup")

# 追加新的备份时间戳到备份列表文件
with open(backup_list_file, "a") as f:
    f.write(f"{timestamp}\n")

# 删除超过定义次数的备份
with open(backup_list_file, "r") as f:
    backup_dirs = f.readlines()

if len(backup_dirs) > MAX_BACKUPS:
    for old_backup in backup_dirs[:-MAX_BACKUPS]:
        old_backup = old_backup.strip()
        old_backup_path = os.path.join("backup", old_backup)
        subprocess.run(["rm", "-rf", old_backup_path])
    
    # 更新备份列表文件，保留最新的备份
    with open(backup_list_file, "w") as f:
        f.writelines(backup_dirs[-MAX_BACKUPS:])


"""
3. 推送备份文件到 GitHub
"""
try:
    # 添加所有文件
    subprocess.run(["git", "add", "."], cwd="backup", check=True)
    
    # 提交更改
    commit_message = f"Backup on {timestamp}"
    subprocess.run(["git", "commit", "-m", commit_message], cwd="backup", check=True)
    
    # 优化 Git 配置以减少内存使用
    subprocess.run(["git", "config", "pack.windowMemory", "10m"], cwd="backup", check=True)
    subprocess.run(["git", "config", "pack.packSizeLimit", "20m"], cwd="backup", check=True)
    subprocess.run(["git", "config", "pack.threads", "1"], cwd="backup", check=True)
    
    # 运行 git gc 来优化存储库
    subprocess.run(["git", "gc"], cwd="backup", check=True)
    
    # 推送到远程仓库
    subprocess.run(["git", "push", "-u", "origin", "main"], cwd="backup", check=True)
    print("Backup pushed to GitHub successfully.")

except subprocess.CalledProcessError as e:
    print(f"An error occurred while pushing to GitHub: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
