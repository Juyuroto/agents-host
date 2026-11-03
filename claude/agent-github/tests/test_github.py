import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from unittest import mock

for var in ("GITHUB_TOKEN", "ANTHROPIC_API_KEY", "DISCORD_GITHUB_WEBHOOK_URL", "DISCORD_BOT_TOKEN",
            "DISCORD_GITHUB_CHANNEL_ID", "DISCORD_OWNER_ID"):
    os.environ.setdefault(var, "test")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import github_client
import historique
import suivis

NOW = datetime(2026, 1, 31, 12, 0, tzinfo=timezone.utc)
REPOS = [{"full_name": "moi/alpha"}, {"full_name": "moi/beta"}]


def item(number, created):
    return {"number": number, "title": f"t{number}", "created_at": created}


class CommandTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        patcher = mock.patch.object(suivis, "PATH", os.path.join(tmp.name, "data", "suivis.json"))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_parse(self):
        self.assertEqual(suivis.parse_command("suivre alpha"), ("ajouter", "alpha"))
        self.assertEqual(suivis.parse_command("Ne plus suivre alpha"), ("retirer", "alpha"))
        self.assertEqual(suivis.parse_command("suivis"), ("suivis", ""))
        self.assertIsNone(suivis.parse_command("bonjour"))
        self.assertIsNone(suivis.parse_command("suivre"))

    def test_follow_unfollow_list(self):
        repos = lambda: REPOS
        self.assertIn("moi/alpha", suivis.execute("ajouter", "alpha", repos))
        self.assertEqual(suivis.load(), ["moi/alpha"])
        self.assertIn("moi/alpha", suivis.execute("suivis", "", repos))
        suivis.execute("retirer", "moi/alpha", repos)
        self.assertEqual(suivis.load(), [])
        self.assertEqual(suivis.execute("suivis", "", repos), "Aucun dépôt suivi.")

    def test_unknown_repo_refused(self):
        self.assertIn("inconnu", suivis.execute("ajouter", "zeta", lambda: REPOS))
        self.assertEqual(suivis.load(), [])
        self.assertIn("non suivi", suivis.execute("retirer", "zeta", lambda: REPOS))


class GithubTest(unittest.TestCase):
    def test_forks_filtered(self):
        resp = mock.Mock()
        resp.json.return_value = [
            {"full_name": "a", "fork": False},
            {"full_name": "b", "fork": True},
        ]
        with mock.patch.object(github_client, "_get", return_value=resp):
            self.assertEqual([r["full_name"] for r in github_client.list_repos()], ["a"])

    def test_age_alerts(self):
        prs = [item(1, "2026-01-17T11:59:00Z"), item(2, "2026-01-17T12:00:00Z")]
        issues = [item(3, "2025-12-31T11:59:00Z"), item(4, "2026-01-01T12:00:00Z")]
        alerts = github_client.age_alerts(issues, prs, NOW)
        self.assertEqual(len(alerts), 2)
        self.assertIn("PR #1", alerts[0])
        self.assertIn("Issue #3", alerts[1])


class HistoriqueTest(unittest.TestCase):
    def test_diff(self):
        prev = {"commits": ["a"], "issues": [1], "prs": [5, 6], "ci": "success"}
        cur = {"commits": ["c", "b", "a"], "issues": [1, 2], "prs": [6, 7], "ci": "failure"}
        self.assertEqual(
            historique.diff(prev, cur),
            ["2 nouveau(x) commit(s)", "Nouvelle issue #2", "PR ouverte #7", "PR fermée #5",
             "CI : success -> failure"],
        )
        self.assertEqual(historique.diff(cur, cur), [])

    def test_previous_is_latest_before_day(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(historique, "DIR", tmp):
            self.assertIsNone(historique.previous("2026-01-31"))
            historique.save("2026-01-29", {"x": 1})
            historique.save("2026-01-30", {"x": 2})
            historique.save("2026-01-31", {"x": 3})
            self.assertEqual(historique.previous("2026-01-31"), {"x": 2})


if __name__ == "__main__":
    unittest.main()
