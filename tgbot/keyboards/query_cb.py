from typing import Optional, Union
from aiogram.utils.callback_data import CallbackData


ChoiceCallback = CallbackData(
    'choice', 'choice', 'action'
)

ReviewCallback = CallbackData(
    'review', 'grade', 'action'
)

CalendarCallback = CallbackData(
    'post', 'id', 'action'
)

GenderCallback = CallbackData(
    'post', 'gender', 'action'
)

FaqCallback = CallbackData(
    'faq', 'chapter', 'lvl', 'action'
)

AuthCallback = CallbackData(
    'auth', 'id', 'action'
)

ContinueCallback = CallbackData(
    'continue', 'action'
)

FaqNewCallback = CallbackData(
    'faq', 'chapter', 'action'
)

MailingsNewCallback = CallbackData(
    'mailing', 'answer', 'action'
)

OperatorCallback = CallbackData(
    'operator', 'time', 'action'
)

AnswerCallback = CallbackData(
    "answer", "ans", 'id', 'action'
)


ProbationPeriodActionCallback = CallbackData(
    'probation_period',
    'current_day',
    "action",
    "value"
)

LocalCallback = CallbackData(
    "local",
    "lang",
    'action'
)

UniversalCallback = CallbackData(
    'universal',
    'action'
)
