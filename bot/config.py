from dataclasses import dataclass, asdict, field


@dataclass
class GAME_SETTINGS:
    maxNoofPlayers: int = field(default=5)
    timeInMsPerTick: int = field(default=250)
    obstaclesEnabled: bool = field(default=True)
    powerUpsEnabled: bool = field(default=True)
    addPowerUpLikelihood: int = field(default=15)
    removePowerUpLikelihood: int = field(default=5)
    trainingGame: bool = field(default=True)
    pointsPerTileOwned: int = field(default=1)
    pointsPerCausedStun: int = field(default=5)
    noOfTicksInvulnerableAfterStun: int = field(default=3)
    noOfTicksStunned: int = field(default=10)
    startObstacles: int = field(default=30)
    startPowerUps: int = field(default=0)
    gameDurationInSeconds: int = field(default=60)  # 60
    explosionRange: int = field(default=4)
    pointsPerTick: bool = field(default=False)


@dataclass
class Actions:
    up: str = "UP"
    down: str = "DOWN"
    left: str = "LEFT"
    right: str = "RIGHT"
    stay: str = "STAY"
    explode: str = "EXPLODE"


@dataclass
class Bot:
    name: str = "Pythonista"
