import os
import sys

repo_path = '/content/KeyDpt'
scripts_path = '/content/KeyDpt/pygob'

if os.path.exists(repo_path):
    sys.path.append(repo_path)
if os.path.exists(scripts_path):
    sys.path.append(scripts_path)
    os.chdir(scripts_path)

try:
    import pygob
    print("✅ pygob 导入成功！")
    print(f"📍 库文件位置: {pygob.__file__}")
except ImportError:
    print("❌ 导入失败！")
    print(f"当前目录内容: {os.listdir('.')}")