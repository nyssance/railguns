import time
from functools import cache
from typing import Any, get_type_hints
lazy from collections.abc import Awaitable, Callable

import jwt
from django.conf import settings
from django.contrib.auth import aauthenticate, get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.utils.module_loading import import_string
from freeman.auth import IsAuthenticated, JWTAuthentication
from freeman.auth.revocation import DjangoCacheRevocation
from freeman.auth.tokens import TokenRotationError, create_token_pair, rotate_refresh_token
from freeman.exceptions import HTTPException
from pydantic import BaseModel, TypeAdapter, create_model
lazy from django.contrib.auth.models import AbstractBaseUser
lazy from freeman import Request

from railguns.django.db._introspect import default_manager

__all__ = [
    "IsAuthenticated",
    "JWTAuthentication",
    "access_auth",
    "issue_tokens",
    "login_handler",
    "login_result",
    "logout",
    "logout_all",
    "refresh",
    "token_store",
]

token_store = DjangoCacheRevocation()
access_auth = JWTAuthentication(token_type="access", revocation_store=token_store)

ACCESS_TTL = 300
REFRESH_TTL = 86400


class Credentials(BaseModel):
    username: str
    password: str


class Refresh(BaseModel):
    refresh: str


class TokenPair(BaseModel):
    access: str
    refresh: str


class Done(BaseModel):
    ok: bool = True


# token 和 access 相同, 给旧客户端. Any: create_model 的字段定义, 值是 (类型, 默认值)
TOKEN_FIELDS: dict[str, Any] = {"token": (str, ...), "access": (str, ...), "refresh": (str, ...)}


async def issue_tokens(user: AbstractBaseUser) -> dict[str, str]:
    """给用户签发一对令牌.

    Returns:
        token, access, refresh 三个令牌.

    """
    version = await token_store.get_user_version(str(user.pk))
    pair = create_token_pair(user, access_ttl=ACCESS_TTL, refresh_ttl=REFRESH_TTL, version=version)
    return {"token": pair.access_token, "access": pair.access_token, "refresh": pair.refresh_token}


@cache
def profile_function() -> tuple[Callable[[AbstractBaseUser], object], type[BaseModel]] | tuple[None, None]:
    """(函数, 它的返回类型). 由项目在配置里指定: RAILGUNS_LOGIN_PROFILE = "项目.模块.函数". 没有配置时是 (None, None).

    函数的返回类型必须是 Pydantic 模型: 登录的响应类型由它生成, 客户端才有每个字段的类型.

    Returns:
        (函数, 它的返回类型), 没有配置时是 (None, None).

    Raises:
        ImproperlyConfigured: 函数没有声明返回类型, 返回类型不是 Pydantic 模型, 或者有令牌的字段.

    """
    path = getattr(settings, "RAILGUNS_LOGIN_PROFILE", None)
    if not path:
        return None, None
    function = import_string(path)
    returns = get_type_hints(function).get("return")
    if not (isinstance(returns, type) and issubclass(returns, BaseModel)):
        msg = (
            f"RAILGUNS_LOGIN_PROFILE 指定的 {path} 必须声明返回类型, 并且是 Pydantic 模型: "
            "def profile(user) -> Profile."
        )
        raise ImproperlyConfigured(msg)
    if clash := set(returns.model_fields) & set(TOKEN_FIELDS):
        msg = f"{path} 的返回类型 {returns.__name__} 不能有令牌的字段: {sorted(clash)}."
        raise ImproperlyConfigured(msg)
    return function, returns


@cache
def login_result() -> type[BaseModel]:
    """登录的响应类型: 项目的用户资料的字段, 再加 token, access, refresh, 都在同一层. 没有配置资料时只有令牌.

    Returns:
        生成的 Pydantic 模型.

    """
    _, profile = profile_function()
    return create_model("LoginResult", __base__=profile or BaseModel, __module__=__name__, **TOKEN_FIELDS)


async def session(user: AbstractBaseUser) -> dict:
    """用户资料加令牌, 就是登录的响应. 注册这类接口之后直接是登录状态时也用它.

    Returns:
        用户资料的字段和令牌.

    """
    function, profile = profile_function()
    fields = {}
    if function is not None and profile is not None:
        adapter = TypeAdapter(profile)
        fields = adapter.dump_python(adapter.validate_python(function(user), from_attributes=True))
    return {**fields, **await issue_tokens(user)}


def login_handler() -> Callable[[Credentials], Awaitable[dict]]:
    """登录的处理函数. 返回类型在注册时才能确定 (见 login_result), 所以由函数生成.

    Returns:
        登录的处理函数.

    """
    result = login_result()

    async def login(data: Credentials) -> result:
        user = await aauthenticate(username=data.username, password=data.password)
        if user is None or not user.is_active:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return await session(user)

    return login


def refresh_claims(token: str) -> dict:
    """刷新令牌的声明.

    Returns:
        令牌的声明.

    Raises:
        jwt.InvalidTokenError: 签名不对, 过期, 或者不是刷新令牌.

    """
    claims = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"],
        options={"require": ["sub", "exp", "typ", "fam", "jti", "iat", "ver"]},
    )
    if claims["typ"] != "refresh":
        msg = "not a refresh token"
        raise jwt.InvalidTokenError(msg)
    return claims


async def logout(request: Request, data: Refresh) -> Done:
    """登出这一次登录: 作废手上的访问令牌, 和这个刷新令牌所在的整条续期链. 其他设备上的登录不受影响.

    Returns:
        完成.

    Raises:
        HTTPException: 刷新令牌无效, 或者不是这个用户的 (401).

    """
    try:
        claims = refresh_claims(data.refresh)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
    if str(claims["sub"]) != str(request.context["user_id"]):
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    access = request.context["auth_claims"]
    await token_store.revoke(access["jti"], exp=access.get("exp"))
    # 另一个进程可能刚用这个令牌续期过, 新令牌比它晚过期, 所以这条记录要活到新令牌过期
    await token_store.revoke_family(claims["fam"], exp=max(int(time.time()) + REFRESH_TTL, claims["exp"]))
    return Done()


async def logout_all(request: Request) -> Done:
    """登出所有设备: 这个用户所有的刷新令牌立刻作废, 这台设备的访问令牌也立刻作废.

    其他设备手上的访问令牌不逐个查库, 会活到它自己过期, 最长 ACCESS_TTL (5 分钟). 这是无状态令牌的代价.

    Returns:
        完成.

    """
    access = request.context["auth_claims"]
    await token_store.revoke(access["jti"], exp=access.get("exp"))
    await token_store.bump_user_version(str(request.context["user_id"]))
    return Done()


async def refresh(data: Refresh) -> TokenPair:
    try:
        claims = refresh_claims(data.refresh)
        users = default_manager(get_user_model())
        if not await users.filter(pk=claims["sub"], is_active=True).aexists():
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        pair = await rotate_refresh_token(claims, store=token_store, access_ttl=ACCESS_TTL, refresh_ttl=REFRESH_TTL)
    except (jwt.InvalidTokenError, TokenRotationError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
    return TokenPair(access=pair.access_token, refresh=pair.refresh_token)
