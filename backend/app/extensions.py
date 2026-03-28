import redis as redis_lib
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per hour", "50 per minute"],
)

# Redis client – initialised in create_app
redis_client: redis_lib.Redis = None  # type: ignore


def init_redis(app):
    global redis_client
    redis_client = redis_lib.from_url(
        app.config["REDIS_URL"], decode_responses=True
    )
    return redis_client
