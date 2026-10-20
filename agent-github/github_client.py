import requests
from config import GITHUB_TOKEN

API = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}
PER_PAGE = 100


def _get(path: str, params: dict | None = None) -> requests.Response:
    r = requests.get(f"{API}{path}", headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    return r


def list_repos() -> list[dict]:
    repos = []
    page = 1
    while True:
        items = _get(
            "/user/repos",
            {"type": "owner", "per_page": PER_PAGE, "sort": "pushed", "page": page},
        ).json()
        repos.extend(r for r in items if not r["fork"])
        if len(items) < PER_PAGE:
            return repos
        page += 1


def _has_readme(full_name: str) -> bool:
    r = requests.get(f"{API}/repos/{full_name}/readme", headers=HEADERS, timeout=10)
    if r.status_code == 404:
        return False
    r.raise_for_status()
    return True


def analyze_repo_data(repo: dict) -> dict:
    full_name = repo["full_name"]

    commits = _get(f"/repos/{full_name}/commits", {"per_page": 5}).json()
    issues = _get(f"/repos/{full_name}/issues", {"state": "open", "per_page": 30}).json()
    prs = _get(f"/repos/{full_name}/pulls", {"state": "open", "per_page": 30}).json()

    return {
        "name": full_name,
        "description": repo.get("description"),
        "pushed_at": repo.get("pushed_at"),
        "open_issues": [i["title"] for i in issues if "pull_request" not in i],
        "open_prs": [p["title"] for p in prs],
        "recent_commits": [
            f'{c["commit"]["message"].splitlines()[0]} '
            f'({c["commit"]["author"]["date"]}, {c["commit"]["author"]["name"]})'
            for c in commits
        ],
        "has_readme": _has_readme(full_name),
    }
