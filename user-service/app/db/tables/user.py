# 2024 amicroservice author.

import asyncpg

from db.models.user import UserModel
from utils.logger import Logger
from db.pool import Database


class UserTable:
    """
    Implement connection to database and record transactions with the user table.
    """

    def __init__(self, logger: Logger, database: Database):
        """
        Initialize connection details
        """
        self.logger = logger
        self.database = database

    def ready(self):
        """
        Check if pool already setup
        """
        if not self.database.pool:
            self.logger.critical(f"{__name__}: Not connected to the database.")
            return None

    async def create(self, user_model: UserModel):
        """
        Create
        """
        self.ready()

        try:
            async with self.database.pool.acquire() as connection:
                async with connection.transaction():
                    await connection.execute(
                        """
                        INSERT INTO users (group_id, email, password_hash, first_name, last_name )
                        VALUES ($1, $2, $3, $4, $5)
                        """,
                        user_model.group_id,
                        user_model.email,
                        user_model.password_hash,
                        user_model.first_name,
                        user_model.last_name,
                    )

        except asyncpg.PostgresError as e:
            self.logger.error(
                f"{__name__}: Error inserting superuser {user_model.email} - {e}"
            )
            raise e

    async def get_by_groud_id_and_email(self, group_id: str, email: str) -> UserModel:
        """
        Retrieve by group_id and email
        """

        try:
            async with self.database.pool.acquire() as connection:
                record: asyncpg.Record = await connection.fetchrow(
                    """
                    SELECT 
                        id, 
                        created_at, 
                        updated_at, 
                        group_id,
                        email, 
                        password_hash, 
                        first_name, 
                        last_name 
                    FROM users 
                    WHERE group_id = $1 AND email = $2 LIMIT 1
                    """,
                    group_id,
                    email,
                )

                if record:
                    user_model = UserModel(
                        group_id=record["group_id"],
                        email=record["email"],
                        first_name=record["first_name"],
                        last_name=record["last_name"],
                    )

                    user_model.id = record["id"]
                    user_model.created_at = record["created_at"]
                    user_model.updated_at = record["updated_at"]
                    user_model.password_hash = record["password_hash"]

                    return user_model
                else:
                    return None

        except asyncpg.PostgresError as e:
            self.logger.error(
                f"{__name__}: Error retrieving user by group_id {group_id} and email {email} - {e}"
            )
            raise e

    async def get(self, id: str) -> UserModel:
        """
        Retrieve
        """
        self.ready()

        try:
            async with self.database.pool.acquire() as connection:
                record: asyncpg.Record = await connection.fetchrow(
                    """
                    SELECT 
                        id, 
                        created_at, 
                        updated_at, 
                        group_id,
                        email, 
                        password_hash, 
                        first_name, 
                        last_name 
                    FROM users 
                    WHERE id = $1 LIMIT 1
                    """,
                    id,
                )

                if record:
                    user_model = UserModel(
                        group_id=record["group_id"],
                        email=record["email"],
                        first_name=record["first_name"],
                        last_name=record["last_name"],
                    )

                    user_model.id = record["id"]
                    user_model.created_at = record["created_at"]
                    user_model.updated_at = record["updated_at"]
                    user_model.password_hash = record["password_hash"]

                    return user_model
                else:
                    return None

        except asyncpg.PostgresError as e:
            self.logger.error(f"{__name__}: Error retrieving user by ID {id} - {e}")
            raise e

    async def update(self, user_model: UserModel):
        """
        Update
        """
        self.ready()

        try:
            async with self.database.pool.acquire() as connection:
                async with connection.transaction():
                    await connection.execute(
                        """
                        UPDATE superusers
                        SET updated_at = $1,
                            email = $2,
                            password_hash = $3,
                            first_name = $4,
                            last_name = $5  
                        WHERE id = $6
                        """,
                        user_model.updated_at,
                        user_model.email,
                        user_model.password_hash,
                        user_model.first_name,
                        user_model.last_name,
                        user_model.id,
                    )

        except asyncpg.PostgresError as e:
            self.logger.error(
                f"{__name__}: Error updating superuser {user_model.id} - {e}"
            )
            raise e
