from datetime import timedelta

import jwt
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token, decode_token


def test_unverified_inspection_cannot_disable_later_claim_checks():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "jwt-regression-secret-at-least-32-bytes"
    JWTManager(app)
    with app.app_context():
        expired = create_access_token(
            identity="owner", expires_delta=timedelta(seconds=-1)
        )
        options = {"verify_signature": False}
        jwt.decode(expired, options=options)
        assert options == {"verify_signature": False}
        options["verify_signature"] = True
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(
                expired,
                app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"],
                options=options,
            )
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_token(expired)


def test_framework_still_rejects_wrong_audience_after_unverified_inspection():
    app = Flask(__name__)
    app.config.update(
        JWT_SECRET_KEY="jwt-regression-secret-at-least-32-bytes",
        JWT_DECODE_AUDIENCE="local-api",
    )
    JWTManager(app)
    with app.app_context():
        token = create_access_token(
            identity="owner", additional_claims={"aud": "other-api"}
        )
        jwt.decode(token, options={"verify_signature": False})
        with pytest.raises(jwt.InvalidAudienceError):
            decode_token(token)
