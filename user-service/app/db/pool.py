# 2024 amicroservice author.

import asyncpg

from utils.logger import Logger


class Database:
    """
    Implement Pool database
    """

    def __init__(self, logger: Logger, dsn: str):
        # Initialize
        self.logger = logger
        self.dsn = dsn
        self.pool: asyncpg.pool.Pool = None

    async def setup(self):
        try:
            self.pool = await asyncpg.create_pool(dsn=self.dsn)
            self.logger.info(
                f"{__name__}: Connection to PostgreSQL database is established successfully!"
            )
        except Exception as e:
            self.logger.critical(f"{__name__}: Error connecting to database: {e}")
            raise e

    async def close(self):
        if self.pool:
            await self.pool.close()

            self.pool = None
            self.logger.info(f"{__name__}: Connection closed.")
