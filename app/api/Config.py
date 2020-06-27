import os
from auth.XOrigin import XOrigin


class ConfigResource(XOrigin):
    def get(self):
        return {"ok": True, "jwturl": os.getenv("JWT_URL")}
