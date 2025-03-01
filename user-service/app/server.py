# 2024 amicroservice author.

import asyncio
import os

import grpc

import buf.user.user_pb2_grpc as user_pb2_grpc
from db.pool import Database
from db.tables.group import GroupTable
from db.tables.groupuser import GroupuserTable
from db.tables.user import UserTable
from services.user import UserService
from utils.logger import Logger


# Function to start and run the gRPC server
async def serve():
    # Get variables environments
    app_name = os.getenv("APP_NAME")
    port = os.getenv("GRPC_PORT")
    jwt_secret = os.getenv("JWT_SECRET")
    dsn = os.getenv("DSN")

    # Setting logging
    logger = Logger(name=app_name)

    # Create a database object
    database = Database(logger, dsn=dsn)

    # Connect to the database
    await database.setup()

    # Initial Table Group
    group_table = GroupTable(logger=logger, database=database)

    # Initial Table Groupuser
    groupuser_table = GroupuserTable(logger=logger, database=database)

    # Initial Table User
    user_table = UserTable(logger=logger, database=database)

    # Start the async gRPC server
    server = grpc.aio.server()

    # Register the User service implementation with the gRPC server
    user_pb2_grpc.add_UserServiceServicer_to_server(
        UserService(
            logger=logger,
            group_table=group_table,
            groupuser_table=groupuser_table,
            user_table=user_table,
            jwt_secret=jwt_secret,
        ),
        server,
    )

    # Bind the server to the specified port on all available network interfaces
    server.add_insecure_port("[::]:" + port)

    # Start the server in the background
    await server.start()

    # Log a startup message
    logger.info(f"{__name__}: Server started, listening on {port}")

    try:
        # Keep the server running until explicitly stopped
        await server.wait_for_termination()
    except asyncio.CancelledError:
        logger.info(f"{__name__}: Shutting down server...")

    # Shutdown gracefully
    await server.stop(grace=5)  # Graceful shutdown (in seconds)

    # Close the database connection
    await database.close()


# Entry point of the script
if __name__ == "__main__":
    asyncio.run(serve())  # Call the serve function to start the gRPC server
