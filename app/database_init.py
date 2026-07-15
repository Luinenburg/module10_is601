from app.database import Base, engine
from app.models import Calculation, User  # noqa: F401


def init_db():
    Base.metadata.create_all(bind=engine)


def drop_db():
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception:
        # Some environments may fail when dropping tables with foreign keys before
        # the referenced tables are present; ignore and continue.
        pass

if __name__ == "__main__":
    init_db() # pragma: no cover