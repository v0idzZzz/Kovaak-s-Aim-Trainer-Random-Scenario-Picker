from dataclasses import dataclass
from enum import Enum
from datetime import datetime

@dataclass
class Scenario:
    rank: int
    leaderboardId: int
    scenarioName: str
    aimType: str
    authors: list[str]
    description: str
    plays: int
    entries: int

@dataclass
class Score:
    steamId: str
    score: float
    rank: int
    steamAccountName: str
    kovaaksPlusActive: bool
    fov: int
    hash: str
    cm360: float
    epoch: int
    kills: int
    avgFps: float
    avgTtk: float
    fovScale: str
    vertSens: float
    horizSens: float
    resolution: str
    sensScale: str
    accuracyDamage: int
    challengeStart: datetime
    scenarioVersion: str
    clientBuildVersion: str
    webappUsername: str

class LeaderboardFilter(Enum):
    GLOBAL = 1
    VIP = 2
    FRIENDS = 3
    MY_POSITION = 4

class NoCredentials(Exception): pass