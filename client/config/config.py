from dataclasses import dataclass, field
from PyInquirer import style_from_dict, Token
import platform


@dataclass
class MutableConfig:
    latest_game_mode: str = ""
    latest_game_settings: str = ""
    latest_game_link: str = ""


@dataclass
class GameMode:
    training = "TRAINING"
    tournament = "TOURNAMENT"


@dataclass
class Message:
    # Exceptions
    InvalidMessage = "se.cygni.paintbot.api.exception.InvalidMessage"
    InvalidPlayerName = "se.cygni.paintbot.api.exception.InvalidPlayerName"
    NoActiveTournament = "se.cygni.paintbot.api.exception.NoActiveTournament"

    # Responses
    HeartbeatResponse = "se.cygni.paintbot.api.response.HeartBeatResponse"
    PlayerRegistered = "se.cygni.paintbot.api.response.PlayerRegistered"

    # Events
    GameLink = "se.cygni.paintbot.api.event.GameLinkEvent"
    GameStarting = "se.cygni.paintbot.api.event.GameStartingEvent"
    MapUpdate = "se.cygni.paintbot.api.event.MapUpdateEvent"
    CharacterStunned = "se.cygni.paintbot.api.event.CharacterStunnedEvent"
    GameResult = "se.cygni.paintbot.api.event.GameResultEvent"
    GameEnded = "se.cygni.paintbot.api.event.GameEndedEvent"
    TournamentEnded = "se.cygni.paintbot.api.event.TournamentEndedEvent"

    # Requests
    ClientInfo = "se.cygni.paintbot.api.request.ClientInfo"
    StartGame = "se.cygni.paintbot.api.request.StartGame"
    RegisterPlayer = "se.cygni.paintbot.api.request.RegisterPlayer"
    RegisterMove = "se.cygni.paintbot.api.request.RegisterMove"
    HeartbeatRequest = "se.cygni.paintbot.api.request.HeartBeatRequest"


@dataclass
class Config:
    host: str = "ws://localhost:8080"
    # host: str = "wss://server.paintbot.cygni.se"
    # venue: str = "training"
    venue: str = "tournament"
    auto_start: bool = True
    HEARTBEAT_INTERVAL: int = 5  # Python sleep is in seconds
    SUPPORTED_GAME_MODES = frozenset(["TRAINING", "TOURNAMENT"])
    game_mode: GameMode = GameMode

    # Mutable settings
    mutable: MutableConfig = MutableConfig


client_info = {
    "type": Message.ClientInfo,
    "clientVersion": "0.1.0",
    "operatingSystem": platform.system(),
    "operatingSystemVersion": platform.release(),
    "language": "Python",
    "languageVersion": "3.6.5 64-bit",
}

prompt_style = style_from_dict(
    {
        Token.Separator: "#cc5454",
        Token.QuestionMark: "#673ab7 bold",
        Token.Selected: "#cc5454",  # default
        Token.Pointer: "#673ab7 bold",
        Token.Instruction: "",  # default
        Token.Answer: "#f44336 bold",
        Token.Question: "",
    }
)