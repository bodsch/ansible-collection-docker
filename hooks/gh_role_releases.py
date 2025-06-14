#!/bin/python

import yaml
import requests

# GitHub API Base URL
GITHUB_API = "https://api.github.com/repos"

# Optional: GitHub Token zur Erhöhung des API-Limits
GITHUB_TOKEN = None  # z.B. 'ghp_xxx'

# Konfigurationsdatei laden
with open("role_repositories.yml", "r") as f:
    config = yaml.safe_load(f)

headers = {}
if GITHUB_TOKEN:
    headers["Authorization"] = f"token {GITHUB_TOKEN}"

print("Letzte Releases der Repositories:\n")

for repo in config.get("repositories", []):
    url = repo["url"]
    try:
        parts = url.rstrip("/").split("/")[-2:]
        api_url = f"{GITHUB_API}/{parts[0]}/{parts[1]}/releases/latest"
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            print(f"{url}: {data.get('tag_name')} (veröffentlicht am {data.get('published_at')})")
        elif response.status_code == 404:
            print(f"{url}: ❌ Kein Release gefunden")
        else:
            print(f"{url}: ⚠️ Fehler beim Abrufen (Statuscode {response.status_code})")
    except Exception as e:
        print(f"{url}: ❌ Fehler: {e}")
