#!/bin/python

import os
import yaml
import requests
import re

# Optional: GitHub-Token zur Erhöhung des API-Limits
GITHUB_TOKEN = None  # z. B. 'ghp_...'

HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

# Regex zum Erkennen von GitHub-Repository-URLs mit optionalem /releases
GITHUB_URL_RE = re.compile(r"https://github\.com/([^/\s]+)/([^/\s]+)(?:/releases)?")

# Basisverzeichnis mit Rollen
ROLES_DIR = "roles"

# Alle relevanten main.yml-Dateien finden
def find_yaml_files(root_dir):
    yaml_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file == "main.yml" and any(x in root for x in ["defaults", "vars"]):
                yaml_files.append(os.path.join(root, file))
    return yaml_files

# GitHub-URLs aus YAML extrahieren
def extract_github_urls_from_yaml(filepath):
    with open(filepath, "r") as f:
        try:
            data = yaml.safe_load(f)
            return find_github_urls(data)
        except yaml.YAMLError as e:
            print(f"⚠️ Fehler beim Parsen von {filepath}: {e}")
            return []

def find_github_urls(data):
    urls = []
    if isinstance(data, dict):
        for value in data.values():
            urls += find_github_urls(value)
    elif isinstance(data, list):
        for item in data:
            urls += find_github_urls(item)
    elif isinstance(data, str):
        match = GITHUB_URL_RE.search(data)
        if match:
            user, repo = match.groups()
            urls.append(f"https://github.com/{user}/{repo}")
    return urls

# Letztes Release über GitHub-API holen
def get_latest_release(repo_url):
    user_repo = "/".join(repo_url.rstrip("/").split("/")[-2:])
    api_url = f"https://api.github.com/repos/{user_repo}/releases/latest"
    response = requests.get(api_url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        return {
            "repo": repo_url,
            "tag": data.get("tag_name"),
            "published": data.get("published_at")
        }
    elif response.status_code == 404:
        return {
            "repo": repo_url,
            "tag": None,
            "published": None
        }
    else:
        return {
            "repo": repo_url,
            "error": f"Fehlercode {response.status_code}"
        }

# Hauptlogik
def main():
    yaml_files = find_yaml_files(ROLES_DIR)
    github_urls = set()
    for file in yaml_files:
        github_urls.update(extract_github_urls_from_yaml(file))

    print("📦 Gefundene GitHub-Repositories:\n")
    for url in sorted(github_urls):
        result = get_latest_release(url)
        if "error" in result:
            print(f"{result['repo']}: ⚠️ {result['error']}")
        elif result["tag"]:
            print(f"{result['repo']}: {result['tag']} (veröffentlicht am {result['published']})")
        else:
            print(f"{result['repo']}: ❌ Kein Release gefunden")

if __name__ == "__main__":
    main()
