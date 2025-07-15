import requests
import json
import itertools
from base64 import b64encode
from urllib.parse import quote
from models import *
from endpoints import *

class KovaakerClient:
    def __init__(self, username: str = None, password: str = None):
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._auth = {}

    def get_user_score(self, leaderboard_id: int, username: str) -> dict | None:
        try:
            for page in self.scenario_leaderboard(leaderboard_id, per_page=100, by_page=True):
                for score in page:
                    if score.webappUsername and score.webappUsername.lower() == username.lower():
                        return {"rank": score.rank, "score": score.score}
        except Exception as e:
            print(f"An error occurred while fetching user score: {e}")
            return None
        return None

    def scenario_leaderboard(self, id: int, start_page=0, per_page=10, max_page=-1, by_page=True) -> list[Score]:
        endpoint = SCENARIO_GLOBAL_LEADERBOARD
        for offset in (itertools.count() if max_page == -1 else range(max_page)):
            try:
                resp = self.session.get(endpoint % (id, start_page + offset, per_page))
                resp.raise_for_status()
                data = resp.json().get("data", [])
                if not data: break
                result = [Score(
                    entry.get("steamId"), entry.get("score"), entry.get("rank"), entry.get("steamAccountName"),
                    entry.get("kovaaksPlusActive"), entry.get("attributes", {}).get("fov"), entry.get("attributes", {}).get("hash"),
                    entry.get("attributes", {}).get("cm360"), entry.get("attributes", {}).get("epoch"), entry.get("attributes", {}).get("kills"),
                    entry.get("attributes", {}).get("avgFps"), entry.get("attributes", {}).get("avgTtk"), entry.get("attributes", {}).get("fovScale"),
                    entry.get("attributes", {}).get("vertSens"), entry.get("attributes", {}).get("horizSens"), entry.get("attributes", {}).get("resolution"),
                    entry.get("attributes", {}).get("sensScale"), entry.get("attributes", {}).get("accuracyDamage"),
                    entry.get("attributes", {}).get("challengeStart"), entry.get("attributes", {}).get("scenarioVersion"),
                    entry.get("attributes", {}).get("clientBuildVersion"), entry.get("webappUsername"),
                ) for entry in data]
                if by_page: yield result
                else:
                    for x in result: yield x
            except requests.exceptions.RequestException as e:
                print(f"Network error fetching leaderboard page: {e}")
                break

    def scenario_count(self) -> int:
        resp = self.session.get(POPULAR_SCENARIOS % (0, 1))
        resp.raise_for_status()
        return resp.json()["total"]

    def scenario_search(self, query: str = None, start_page=0, per_page=10, max_page=-1, by_page=True) -> list[Scenario]:
        for offset in (itertools.count() if max_page == -1 else range(max_page)):
            try:
                if query is None:
                    resp = self.session.get(POPULAR_SCENARIOS % (start_page + offset, per_page))
                else:
                    resp = self.session.get(POPULAR_SCENARIOS_SEARCH % (start_page + offset, per_page, query))
                resp.raise_for_status()
                data = resp.json().get("data", [])
                if not data: break
                result = [Scenario(
                    entry.get("rank"), entry.get("leaderboardId"), entry.get("scenarioName"),
                    entry.get("scenario", {}).get("aimType"), entry.get("scenario", {}).get("authors"),
                    entry.get("scenario", {}).get("description"), entry.get("counts", {}).get("plays"),
                    entry.get("counts", {}).get("entries"),
                ) for entry in data]
                if by_page: yield result
                else:
                    for x in result: yield x
            except requests.exceptions.RequestException as e:
                print(f"Network error during scenario search: {e}")
                break