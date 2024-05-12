from app.game.models import Game, GameStage
from app.store.vk_api.dataclasses import Update


class GameLogic:
    def __init__(self, game: Game, update: Update):
        self._game = game
        self.update = update

    def check_status_game(self):
        if self._game.game_stage is GameStage.WAITING_ANSWER:
            return True
        return False

    def check_answer(self, player_answer):
        # запросить вопрос
        answers = Game.question
        if player_answer in answers:
            return answers

    def game_logic(self):
        if self.check_status_game() is False:
            return "Игра не идет"

        return "Заработал столько то очков"
