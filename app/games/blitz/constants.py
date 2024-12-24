from enum import Enum


class GameStage(Enum):
    WAIT_INIT = "WAIT_INIT"
    WAITING_ANSWER = "WAITING_ANSWER"
    FINISHED = "FINISHED"
    CANCELED = "CANCELED"
