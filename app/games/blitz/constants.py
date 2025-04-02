from enum import Enum


class BlitzGameStage(Enum):
    WAITING_ANSWER = "WAITING_ANSWER"
    PAUSE = "PAUSE"
    FINISHED = "FINISHED"
    CANCELED = "CANCELED"
