from typing import Dict, List, TypedDict


class JwtPayload(TypedDict):
    aud: str
    dob: str
    email: str
    exp: int
    iat: int
    iss: str
    karer: Dict[str, str]
    name: str
    roles: List[str];
    sub: str
