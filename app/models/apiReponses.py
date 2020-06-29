from typing import Dict, Literal, Tuple, TypedDict, Union


class VerifyTokenOkResponse(TypedDict):
    user: int
    admin: bool
    data: dict  # TODO


class VerifyTokenErrorResponse(VerifyTokenOkResponse):
    error: str


VerifyTokenResponse = Union[VerifyTokenOkResponse, VerifyTokenErrorResponse]


class GenericJsonOk(TypedDict):
    ok: Literal[True]


class GenericJsonError(TypedDict):
    ok: Literal[False]
    error: str


class DbTestOkResponse(GenericJsonOk):
    count: int


DbTestResponse = Union[DbTestOkResponse, GenericJsonError]


# Todo: class ConfigResponse(GenericJsonOk):
# @see https://youtrack.jetbrains.com/issue/PY-43200
class ConfigResponse(TypedDict):
    jwturl: str
    karer: Dict[str, str]
    semesters: Dict[str, str]
    # TODO: ok: Literal[True]
    ok: bool


# Todo: class ImportReponse(GenericJsonOk):
# @see https://youtrack.jetbrains.com/issue/PY-43200
class ImportReponse(TypedDict):
    refrechUrl: str
    html: str
    # TODO: ok: Literal[True]
    ok: bool


class ImportStatusDoneResponse(TypedDict):
    ok: bool
    append: str


class ImportStatusWaitResponse(ImportStatusDoneResponse):
    ok: Literal[True]
    delay: int
    refrechUrl: str


ImportStatusResponse = Union[ImportStatusDoneResponse, ImportStatusWaitResponse, Tuple[GenericJsonError, Literal[404]]]
