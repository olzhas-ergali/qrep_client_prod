from sqlalchemy import Column, Integer, BigInteger, ForeignKey, Text, DateTime, func

from tgbot.models.database.base import Base


class ProbationPeriodAnswer(Base):
    __tablename__ = "probation_period_answers"

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = Column(
        BigInteger,
        ForeignKey('users.id', ondelete='CASCADE'),
    )

    day = Column(
        Integer
    )

    question = Column(
        Text,
    )

    answer = Column(
        Text
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )
