import logging

import uvicorn

from app import create_app
from app.config import get_settings

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("service_registry")
app = create_app()


def main():
    uvicorn.run(app, host=settings.host, port=settings.port, reload=False)


if __name__ == "__main__":
    main()
