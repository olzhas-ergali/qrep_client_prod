from pathlib import Path

from service.tgbot.misc.probation import ProbationEvents, ProbationMessageEvent

PROBATION_PERIOD_DAYS = 4

TGBOT_DIRECTORY = Path(__file__).parent.parent
FILES_DIRECTORY = TGBOT_DIRECTORY / 'data' / 'files'
