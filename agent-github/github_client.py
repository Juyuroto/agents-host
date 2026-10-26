from datetime import datetime, timedelta, timezone

import requests
from config import GITHUB_TOKEN

API = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}
PER_PAGE = 100
PR_DAYS = 14
ISSUE_DAYS = 30


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


def _get_all(path: str, params: dict | None = None) -> list[dict]:
    items = []
    page = 1
    while True:
        batch = _get(path, {**(params or {}), "per_page": PER_PAGE, "page": page}).json()
        items.extend(batch)
        if len(batch) < PER_PAGE:
            return items
        page += 1


def age_alerts(issues: list[dict], prs: list[dict], now: datetime) -> list[str]:
    alerts = [
        f"PR #{p['number']} ouverte depuis plus de {PR_DAYS} jours : {p['title']}"
        for p in prs if now - datetime.fromisoformat(p["created_at"]) > timedelta(days=PR_DAYS)
    ]
    alerts += [
        f"Issue #{i['number']} ouverte depuis plus de {ISSUE_DAYS} jours : {i['title']}"
        for i in issues if now - datetime.fromisoformat(i["created_at"]) > timedelta(days=ISSUE_DAYS)
    ]
    return alerts


def _last_ci(full_name: str, branch: str) -> str | None:
    runs = _get(
        f"/repos/{full_name}/actions/runs", {"per_page": 1, "branch": branch}
    ).json()["workflow_runs"]
    return (runs[0]["conclusion"] or runs[0]["status"]) if runs else None


def _dependabot(full_name: str) -> str | None:
    r = requests.get(
        f"{API}/repos/{full_name}/dependabot/alerts",
        headers=HEADERS,
        params={"state": "open", "per_page": PER_PAGE},
        timeout=10,
    )
    if r.status_code in (403, 404):
        return "Alertes Dependabot inaccessibles (droits du token ou fonction désactivée)"
    r.raise_for_status()
    count = len(r.json())
    return f"{count} alerte(s) Dependabot ouverte(s)" if count else None


def analyze_repo_data(repo: dict, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    full_name = repo["full_name"]

    commits = _get(f"/repos/{full_name}/commits", {"per_page": 30}).json()
    issues = [
        i for i in _get_all(f"/repos/{full_name}/issues", {"state": "open"})
        if "pull_request" not in i
    ]
    prs = _get_all(f"/repos/{full_name}/pulls", {"state": "open"})
    ci = _last_ci(full_name, repo["default_branch"])

    alerts = age_alerts(issues, prs, now)
    if ci == "failure":
        alerts.append("Dernier run GitHub Actions de la branche par défaut en échec")
    dependabot = _dependabot(full_name)
    if dependabot:
        alerts.append(dependabot)

    return {
        "name": full_name,
        "description": repo.get("description"),
        "pushed_at": repo.get("pushed_at"),
        "nb_open_issues": len(issues),
        "nb_open_prs": len(prs),
        "open_issues": [i["title"] for i in issues[:30]],
        "open_prs": [p["title"] for p in prs[:30]],
        "recent_commits": [
            f'{c["commit"]["message"].splitlines()[0]} '
            f'({c["commit"]["author"]["date"]}, {c["commit"]["author"]["name"]})'
            for c in commits[:5]
        ],
        "has_readme": _has_readme(full_name),
        "alertes": alerts,
        "snapshot": {
            "commits": [c["sha"] for c in commits],
            "issues": [i["number"] for i in issues],
            "prs": [p["number"] for p in prs],
            "ci": ci,
        },
    }
