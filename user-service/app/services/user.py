# 2024 amicroservice author.

import datetime
import json
from logging import Logger

import asyncpg
import jwt
import protovalidate
from google.protobuf import any_pb2
from google.rpc import code_pb2, status_pb2
from grpc_status import rpc_status

import buf.user.user_pb2 as user_pb2
import buf.user.user_pb2_grpc as user_pb2_grpc
from db.models.group import GroupModel
from db.models.groupuser import GroupuserModel
from db.models.user import UserModel
from db.tables.group import GroupTable
from db.tables.groupuser import GroupuserTable
from db.tables.user import UserTable


class UserService(user_pb2_grpc.UserService):
    """
    User Service
    """

    def __init__(
        self,
        logger: Logger,
        group_table: GroupTable,
        groupuser_table: GroupuserTable,
        user_table: UserTable,
        jwt_secret: str,
    ) -> None:
        super().__init__()

        self.logger = logger
        self.user_table = user_table
        self.group_table = group_table
        self.groupuser_table = groupuser_table
        self.jwt_secret = jwt_secret

    async def user_authorization_context(self, context) -> UserModel:
        token = None
        for key, value in context.invocation_metadata():
            if key == "authorization":
                token = value

        if token:
            try:
                pay_load = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            except jwt.InvalidSignatureError:
                detail = any_pb2.Any()
                detail.Pack(user_pb2.ErrorField(name="authorization", code="invalid"))
                await context.abort_with_status(
                    rpc_status.to_status(
                        status_pb2.Status(
                            code=code_pb2.PERMISSION_DENIED,
                            message="Authorization token is invalid or expired",
                            details=[detail],
                        )
                    )
                )

            if pay_load:
                user = await self.user_table.get(id=pay_load.get("user_id"))
                return user

        detail = any_pb2.Any()
        detail.Pack(user_pb2.ErrorField(name="token", code="required"))
        await context.abort_with_status(
            rpc_status.to_status(
                status_pb2.Status(
                    code=code_pb2.UNAUTHENTICATED,
                    message="Authorization token is required",
                    details=[detail],
                )
            )
        )

    async def duplicate_email(
        self, email: str, context, err: asyncpg.UniqueViolationError
    ):
        if "users_group_id_email_key" in str(err.constraint_name):
            detail = any_pb2.Any()
            detail.Pack(user_pb2.ErrorField(name="email", code="already_exists"))
            await context.abort_with_status(
                rpc_status.to_status(
                    status_pb2.Status(
                        code=code_pb2.ALREADY_EXISTS,
                        message=f"Email {email} is already exists",
                        details=[detail],
                    )
                )
            )

    async def Register(self, request, context):
        """
        Register
        """
        register_request = user_pb2.RegisterRequest(
            group_id=request.group_id,
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
        )

        try:
            protovalidate.validate(register_request)
        except protovalidate.ValidationError as e:
            details = list()
            for err in e.errors():
                detail = any_pb2.Any()
                detail.Pack(
                    user_pb2.ErrorField(name=err.field_path, code=err.constraint_id)
                )
                details.append(detail)

            if len(details) > 0:
                await context.abort_with_status(
                    rpc_status.to_status(
                        status_pb2.Status(
                            code=code_pb2.INVALID_ARGUMENT,
                            message="Validation field is error",
                            details=details,
                        )
                    )
                )

        # Check if allowed register by Group
        group_model: GroupModel = await self.group_table.get(request.group_id)
        if not group_model:
            detail = any_pb2.Any()
            detail.Pack(user_pb2.ErrorField(name="group_id", code="not_found"))
            await context.abort_with_status(
                rpc_status.to_status(
                    status_pb2.Status(
                        code=code_pb2.NOT_FOUND,
                        message="Group is not found",
                        details=[detail],
                    )
                )
            )

        # Check allowed register by the group
        properties = json.loads(group_model.properties)
        if properties.get("invitation_only"):
            groupuser_model: GroupuserModel = (
                await self.groupuser_table.get_by_group_id_and_email(
                    group_id=request.group_id, email=request.email
                )
            )
            if not groupuser_model:
                detail = any_pb2.Any()
                detail.Pack(user_pb2.ErrorField(name="group_id", code="forbidden"))
                await context.abort_with_status(
                    rpc_status.to_status(
                        status_pb2.Status(
                            code=code_pb2.PERMISSION_DENIED,
                            message="This group is for invitation only",
                            details=[detail],
                        )
                    )
                )
            elif groupuser_model.user_id:
                detail = any_pb2.Any()
                detail.Pack(user_pb2.ErrorField(name="email", code="already_exists"))
                await context.abort_with_status(
                    rpc_status.to_status(
                        status_pb2.Status(
                            code=code_pb2.ALREADY_EXISTS,
                            message=f"Email {groupuser_model.email} in group {groupuser_model.group_id} is already exists",
                            details=[detail],
                        )
                    )
                )

        # Create a new user
        new_user_model = UserModel(
            group_id=request.group_id,
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            password=request.password,
        )

        try:
            await self.user_table.create(
                new_user_model
            )  # Create a new user to the database
        except asyncpg.UniqueViolationError as err:
            await self.duplicate_email(email=request.email, context=context, err=err)

        # Get a new User by email
        user_model = await self.user_table.get_by_groud_id_and_email(
            group_id=new_user_model.group_id, email=new_user_model.email
        )

        # Response endpoint
        return user_pb2.User(
            id=str(user_model.id),
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
            group_id=str(user_model.group_id),
            email=user_model.email,
            first_name=user_model.first_name,
            last_name=user_model.last_name,
        )

    async def Login(self, request, context):
        """
        Login User
        """
        login_request = user_pb2.LoginRequest(
            group_id=request.group_id,
            email=request.email,
            password=request.password,
        )

        try:
            protovalidate.validate(login_request)
        except protovalidate.ValidationError as e:
            details = list()
            for err in e.errors():
                detail = any_pb2.Any()
                detail.Pack(
                    user_pb2.ErrorField(name=err.field_path, code=err.constraint_id)
                )
                details.append(detail)

            if len(details) > 0:
                await context.abort_with_status(
                    rpc_status.to_status(
                        status_pb2.Status(
                            code=code_pb2.INVALID_ARGUMENT,
                            message="Validation field is error",
                            details=details,
                        )
                    )
                )

        # Get user by group and email
        user_model = await self.user_table.get_by_groud_id_and_email(
            group_id=request.group_id, email=request.email
        )
        if not user_model:
            detail = any_pb2.Any()
            detail.Pack(user_pb2.ErrorField(name="email", code="not_found"))
            await context.abort_with_status(
                rpc_status.to_status(
                    status_pb2.Status(
                        code=code_pb2.NOT_FOUND,
                        message=f"Email {request.email} in group {request.group_id} is not found",
                        details=[detail],
                    )
                )
            )

        if user_model.valid_password(password=request.password):
            # Add expire time
            payload = {
                "exp": datetime.datetime.now(tz=datetime.timezone.utc)
                + datetime.timedelta(days=30),
                "user_id": str(user_model.id),
            }

            # Encode token
            token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")

            return user_pb2.UserToken(token=token)
        else:
            detail = any_pb2.Any()
            detail.Pack(user_pb2.ErrorField(name="password", code="invalid"))
            await context.abort_with_status(
                rpc_status.to_status(
                    status_pb2.Status(
                        code=code_pb2.UNAUTHENTICATED,
                        message="Password is invalid or not correct",
                        details=[detail],
                    )
                )
            )

    async def Get(self, request, context):
        """
        Get User
        """
        user_model = await self.user_authorization_context(context=context)

        return user_pb2.User(
            id=str(user_model.id),
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
            group_id=str(user_model.group_id),
            email=user_model.email,
            first_name=user_model.first_name,
            last_name=user_model.last_name,
        )

    async def Update(self, request, context):
        """
        Update User
        """
        update_user_model = await self.user_authorization_context(context=context)

        update_user_model.update(
            email=request.email,
            first_name=request.first_name,
            last_name=request.last_name,
            password=request.password,
        )

        try:
            await self.user_table.update(user_model=update_user_model)
        except asyncpg.UniqueViolationError as err:
            await self.duplicate_email(email=request.email, context=context, err=err)

        user_model = await self.user_table.get(id=update_user_model.id)

        return user_pb2.User(
            id=str(user_model.id),
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
            group_id=str(user_model.group_id),
            email=user_model.email,
            first_name=user_model.email,
            last_name=user_model.last_name,
        )
