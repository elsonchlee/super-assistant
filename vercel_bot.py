import requests
import os

# Base URL for Vercel API
BASE_URL = "https://api.vercel.com"

def get_headers():
    token = os.getenv("VERCEL_TOKEN")
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def get_latest_deployments(limit=3):
    """获取最新的部署状态"""
    headers = get_headers()
    if not headers:
        return "❌ 没找到 VERCEL_TOKEN，请去 .env 文件里配置。"
        
    try:
        url = f"{BASE_URL}/v6/deployments?limit={limit}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            deployments = data.get('deployments', [])
            
            if not deployments:
                return "没有找到任何近期部署。"
                
            report = []
            for d in deployments:
                # Calculate time ago roughly or just show raw string for now
                state = d.get('state')
                name = d.get('name')
                url = d.get('url')
                icon = "✅" if state == "READY" else "❌" if state == "ERROR" else "⏳"
                
                report.append(f"{icon} **{name}**: {state} (https://{url})")
                
            return "\n\n".join(report)
        else:
            return f"❌ Vercel API Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"❌ System Error: {e}"

def get_project_list():
    """列出所有项目"""
    headers = get_headers()
    if not headers:
        return "❌ 没找到 VERCEL_TOKEN"
        
    try:
        url = f"{BASE_URL}/v9/projects"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            projects = data.get('projects', [])
            names = [p.get('name') for p in projects]
            return f"📦 项目列表 ({len(names)}): " + ", ".join(names)
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {e}"
