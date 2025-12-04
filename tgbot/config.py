from dataclasses import dataclass

from environs import Env


@dataclass
class DbConfig:
    host: str
    password: str
    user: str
    database: str


@dataclass
class TgBot:
    client_token: str  
    staff_token: str   
    admin_ids: list[int]
    use_redis: bool
    redis_host: str


@dataclass
class Auth1C:
    login: str
    password: str


@dataclass
class Bitrix:
    token: str
    user_id: str


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig
    one_c: Auth1C
    bitrix: Bitrix


def load_config(path):
    env = Env()
    env.read_env(path)

    return Config(
        tg_bot=TgBot(
            client_token=env.str("CLIENT_BOT_TOKEN"),
            staff_token=env.str("STAFF_BOT_TOKEN"),
            admin_ids=list(map(int, env.list("ADMINS"))),
            use_redis=env.bool("USE_REDIS"),
            redis_host=env.str("REDIS_HOST")
        ),
        db=DbConfig(
            host=env.str('DB_HOST'),
            password=env.str('DB_PASS'),
            user=env.str('DB_USER'),
            database=env.str('DB_NAME')
        ),
        one_c=Auth1C(
            login=env.str('LOGIN_1C'),
            password=env.str('PASS_1C')
        ),
        bitrix=Bitrix(
            token=env.str('BITRIX_TOKEN'),
            user_id=env.str('BITRIX_USER_ID')
        )
    )


