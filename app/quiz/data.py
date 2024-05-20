from app.quiz.models import Answer, Question

answers1 = [
    Answer(title="Еду", score=43),
    Answer(title="свадьбу", score=27),
    Answer(title="природу", score=15),
    Answer(title="животных", score=15),
]

question1 = Question(
    title="Кого или что чаще всего снимает фотограф!!?",
    theme_id=1,
    answers=answers1,
)

answers2 = [
    Answer(title="Москва", score=34),
    Answer(title="санкт-петербург", score=17),
    Answer(title="новосибирск", score=14),
    Answer(title="казань", score=12),
    Answer(title="екатеринбург", score=8),
    Answer(title="Самара", score=15),
]

question2 = Question(
    title="В каком городе России есть метро?",
    theme_id=1,
    answers=answers2,
)

answers3 = [
    Answer(title="Пингвина", score=30),
    Answer(title="Медведя", score=20),
    Answer(title="Моржа", score=19),
    Answer(title="Рыбака", score=12),
    Answer(title="Тюленя", score=11),
    Answer(title="Человека", score=8),
]

question3 = Question(
    title="Кого можно увидеть на огромной льдине?",
    theme_id=1,
    answers=answers3,
)

default_questions = [question1, question2, question3]
