from drf_spectacular.extensions import OpenApiAuthenticationExtension

class FirebaseAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "users.authentication.FirebaseAuthentication"
    name = "FirebaseBearer"

    def get_security_definition(self, auto_schema):
        return {"type": "http", "scheme": "bearer", "bearerFormat": "Firebase ID token"}
