from enum import Enum


class BlitzGameStage(Enum):
    WAIT_INIT = "WAIT_INIT"
    WAITING_ANSWER = "WAITING_ANSWER"
    FINISHED = "FINISHED"
    CANCELED = "CANCELED"
