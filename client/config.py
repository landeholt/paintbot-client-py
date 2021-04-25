from dataclasses import dataclass


@dataclass
class Config:
    host: str = "wss://server.paintbot.cygni.se"
    venue: str = "training"


@dataclass(frozen=True)
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
