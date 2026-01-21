import os
import time
import webbrowser
import subprocess

def run_cmd(cmd):
    os.system(cmd)

print("\n" + "="*50)
print("🦅 Octavia 云端部署助手 (Cloud Butler)")
print("="*50)
print("因为我无法替您输入 GitHub 密码，我将帮您打开网页，您只需要点 'Create'。")
print("\n[步骤 1/3]: 正在打开 GitHub 创建页面...")
time.sleep(2)

# 1. Open GitHub New Repo Page
webbrowser.open("https://github.com/new?name=super-assistant&private=true")

print("\n👉 请在浏览器里点击绿色的 'Create repository' 按钮。")
print("👉 创建成功后，复制浏览器地址栏的链接 (比如 https://github.com/Start-0/super-assistant)。")
repo_url = input("\n在此粘贴仓库链接 (Paste URL here): ").strip()

if repo_url:
    # Handle the .git suffix logic just in case
    if not repo_url.endswith(".git"):
        repo_url += ".git"
    
    print(f"\n[步骤 2/3]: 正在上传代码到 {repo_url} ...")
    run_cmd("git branch -M main")
    run_cmd(f"git remote add origin {repo_url}")
    # Try push, might ask for login in a popup
    run_cmd("git push -u origin main")

    print("\n✅ 代码上传完成！")
    print("\n[步骤 3/3]: 准备部署到 Streamlit Cloud...")
    print("👉 我将为您打开部署页面。请在页面上点击 'Deploy'。")
    print("👉 关键点：点击 'Advanced Settings' -> 'Secrets'，然后填入以下内容：")
    
    # Read secrets from local files to display them
    secrets_content = ""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        secrets_content += f'GEMINI_API_KEY = "{api_key}"\n\n'
        
        with open("service_account.json", "r") as f:
            import json
            creds = json.load(f)
            secrets_content += "[gcp_service_account]\n"
            for k, v in creds.items():
                secrets_content += f'{k} = "{v}"\n'
    except:
        secrets_content = "Error reading local secrets."

    print("-" * 30)
    print(secrets_content)
    print("-" * 30)
    print("(这些内容已经帮您格式化好了，直接复制上面的所有内容，粘贴到 Secrets 框框里即可)")
    
    input("\n准备好了吗？按回车键打开部署页面...")
    webbrowser.open(f"https://share.streamlit.io/deploy?repository={repo_url.replace('.git','').replace('https://github.com/', '')}&branch=main&mainModule=app.py")

    print("\n🚀 祝贺！部署完成后，您将获得一个永久网址。")
else:
    print("❌ 未提供链接，任务取消。")
