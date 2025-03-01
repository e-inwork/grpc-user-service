# 2024 amicroservice author.

import json
import logging
import sys

import grpc
from faker import Faker
from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct
from grpc_status import rpc_status

import buf.group.group_pb2 as group_pb2
import buf.group.group_pb2_grpc as group_pb2_grpc
import buf.groupuser.groupuser_pb2 as groupuser_pb2
import buf.groupuser.groupuser_pb2_grpc as groupuser_pb2_grpc
import buf.superuser.superuser_pb2 as superuser_pb2
import buf.superuser.superuser_pb2_grpc as superuser_pb2_grpc
import buf.user.user_pb2 as user_pb2
import buf.user.user_pb2_grpc as user_pb2_grpc

# Setting up the basic configuration for logging
logging.basicConfig(
    level=logging.INFO,  # Set the minimum level to capture (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
    datefmt="%Y-%m-%d %H:%M:%S",  # Date format
    handlers=[
        logging.StreamHandler(sys.stdout),  # Log to the console
    ],
)

# Creating a logger instance
logger = logging.getLogger("userservice-client")

fake = Faker()


def test_userservice_client():
    """
    Test to create a group
    """
    logger.info("Connect to the Superuser Service server...")
    with grpc.insecure_channel(
        "host.docker.internal:50051"
    ) as superuser_service_channel:
        superuser_service_stub = superuser_pb2_grpc.SuperuserServiceStub(
            superuser_service_channel
        )
        # Fake email & password
        email = fake.email()
        password = "Password1212"

        # Register a user
        superuser_service_stub.Register(
            superuser_pb2.RegisterRequest(
                email=email,
                password=password,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )
        )

        # Login a User
        login_response = superuser_service_stub.Login(
            superuser_pb2.LoginRequest(email=email, password=password)
        )

        # Convert to variable token
        superuser_token = superuser_pb2.SuperserToken(token=login_response.token)

        # Show a token on logger
        logger.info("-- Response - Login --")
        logger.info("token: " + superuser_token.token)

    logger.info("Connect to the Group Service server...")
    with grpc.insecure_channel("host.docker.internal:50052") as group_service_channel:
        group_service_stub = group_pb2_grpc.GroupServiceStub(group_service_channel)

        # Create a Group
        name = fake.name()
        domain = name.replace(" ", "")
        properties = Struct()
        properties.update({"invitation_only": True})

        create_reponse = group_service_stub.Create(
            group_pb2.CreateRequest(name=name, domain=domain, properties=properties),
            metadata=(("authorization", superuser_token.token),),
        )

        # Convert to variable Grup
        create_group = group_pb2.Group(
            id=create_reponse.id,
            created_at=create_reponse.created_at,
            updated_at=create_reponse.updated_at,
            name=create_reponse.name,
            domain=create_reponse.domain,
            properties=create_reponse.properties,
        )

        # Show on logger
        logger.info("-- Response - Create Group --")
        logger.info(
            "id: "
            + create_group.id
            + " created_at: "
            + str(create_group.created_at)
            + " updated_at: "
            + str(create_group.updated_at)
            + " name: "
            + create_group.name
            + " domain: "
            + create_group.domain
            + " properties: "
            + json.dumps(MessageToDict(create_group.properties))
        )

    logger.info("Connect to the Groupuser Service server...")
    with grpc.insecure_channel(
        "host.docker.internal:50054"
    ) as groupuser_service_channel:
        groupuser_service_stub = groupuser_pb2_grpc.GroupuserServiceStub(
            groupuser_service_channel
        )

        # Create Groupuser
        email = fake.email()
        group_id = create_group.id

        create_reponse = groupuser_service_stub.Create(
            groupuser_pb2.CreateRequest(group_id=group_id, email=email),
            metadata=(("authorization", superuser_token.token),),
        )

        # Convert to variable Groupuser
        create_groupuser = groupuser_pb2.Groupuser(
            id=create_reponse.id,
            created_at=create_reponse.created_at,
            updated_at=create_reponse.updated_at,
            group_id=create_reponse.group_id,
            email=create_reponse.email,
            user_id=create_reponse.user_id,
        )

        # Show on logger
        logger.info("-- Response - Create Groupuser --")
        logger.info(
            "id: "
            + create_groupuser.id
            + " created_at: "
            + str(create_groupuser.created_at)
            + " updated_at: "
            + str(create_groupuser.updated_at)
            + " group_id: "
            + create_groupuser.group_id
            + " email: "
            + create_groupuser.email
            + " user_id: "
            + create_groupuser.user_id
        )

        logger.info("Connect to the User Service server...")
        with grpc.insecure_channel(
            "host.docker.internal:50053"
        ) as user_service_channel:
            user_service_stub = user_pb2_grpc.UserServiceStub(user_service_channel)

            # Register a user
            user_email = create_groupuser.email
            user_password = "Password1212"
            user_group_id = create_groupuser.group_id

            register_response = user_service_stub.Register(
                user_pb2.RegisterRequest(
                    group_id=user_group_id,
                    email=user_email,
                    password=user_password,
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                )
            )

            # Convert to variable User
            register_user = user_pb2.User(
                id=register_response.id,
                created_at=register_response.created_at,
                updated_at=register_response.updated_at,
                group_id=register_response.group_id,
                email=register_response.email,
                first_name=register_response.first_name,
                last_name=register_response.last_name,
            )

            # Show on logger
            logger.info("-- Reponse - Register User --")
            logger.info(
                "id: "
                + register_user.id
                + " created_at: "
                + str(register_user.created_at)
                + " updated_at: "
                + str(register_user.updated_at)
                + " group_id: "
                + register_user.group_id
                + " email: "
                + register_user.email
                + " first_name: "
                + register_user.first_name
                + " last_name: "
                + register_user.last_name
            )

            # Login a User
            login_response = user_service_stub.Login(
                user_pb2.LoginRequest(
                    group_id=user_group_id, email=user_email, password=user_password
                )
            )

            # Convert to variable token
            user_token = user_pb2.UserToken(token=login_response.token)

            # Show on logger
            logger.info("-- Reponse - Login User --")
            logger.info("token: " + user_token.token)

            # Get a User
            get_response = user_service_stub.Get(
                user_pb2.GetRequest(), metadata=(("authorization", user_token.token),)
            )

            # Convert to variable User
            get_user = user_pb2.User(
                id=get_response.id,
                created_at=get_response.created_at,
                updated_at=get_response.updated_at,
                email=get_response.email,
                first_name=get_response.first_name,
                last_name=get_response.last_name,
            )

            # Show on logger
            logger.info("-- Reponse - Get User --")
            logger.info(
                "id: "
                + get_user.id
                + " created_at: "
                + str(get_user.created_at)
                + " updated_at: "
                + str(get_user.updated_at)
                + " group_id: "
                + get_user.group_id
                + " email: "
                + get_user.email
                + " first_name: "
                + get_user.first_name
                + " last_name: "
                + get_user.last_name
            )

            #  Update a User
            update_response = user_service_stub.Update(
                user_pb2.UpdateRequest(
                    email=fake.email(),
                    password=fake.password(),
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                ),
                metadata=(("authorization", user_token.token),),
            )

            # Convert to variable
            updated_user = user_pb2.User(
                id=update_response.id,
                created_at=update_response.created_at,
                updated_at=update_response.updated_at,
                group_id=update_response.group_id,
                email=update_response.email,
                first_name=update_response.first_name,
                last_name=update_response.last_name,
            )

            # Show on logger
            logger.info("-- Reponse - Update User --")
            logger.info(
                "id: "
                + updated_user.id
                + " created_at: "
                + str(updated_user.created_at)
                + " updated_at: "
                + str(updated_user.updated_at)
                + " group_id: "
                + updated_user.group_id
                + " email: "
                + updated_user.email
                + " first_name: "
                + updated_user.first_name
                + " last_name: "
                + updated_user.last_name
            )

            # Register with blank fields
            try:
                user_service_stub.Register(
                    user_pb2.RegisterRequest(
                        group_id="",
                        email="",
                        password="",
                        first_name="",
                        last_name="",
                    )
                )
            except grpc.RpcError as rpc_error:
                # gRPC Status codes
                # https://grpc.io/docs/guides/status-codes/
                logger.error("-- Reponse - Register User - Error Field Validate --")
                status = rpc_status.from_call(rpc_error)
                logger.error(
                    "Status - code: "
                    + str(status.code)
                    + ", message: "
                    + status.message
                )
                for detail in status.details:
                    if detail.Is(user_pb2.ErrorField.DESCRIPTOR):
                        info = user_pb2.ErrorField()
                        detail.Unpack(info)
                        logger.error("name: " + info.name + ", code: " + info.code)

            # Get a user without a autorization token
            try:
                user_service_stub.Get(user_pb2.GetRequest())
            except grpc.RpcError as rpc_error:
                # gRPC Status codes
                # https://grpc.io/docs/guides/status-codes/
                logger.error("-- Reponse - Get User - Error Field Token Required --")
                status = rpc_status.from_call(rpc_error)
                logger.error(
                    "Status - code: "
                    + str(status.code)
                    + ", message: "
                    + status.message
                )
                for detail in status.details:
                    if detail.Is(user_pb2.ErrorField.DESCRIPTOR):
                        info = user_pb2.ErrorField()
                        detail.Unpack(info)
                        logger.error("name: " + info.name + ", code: " + info.code)


def main():
    test_userservice_client()


if __name__ == "__main__":
    main()
