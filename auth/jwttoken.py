from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from utils.config import SECRET_KEY
from fastapi import HTTPException

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def refresh_access_token(refresh_token: str) -> dict:
    """
    Verifies the provided refresh token and generates a new access token.
    """
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        email = payload.get("sub")
        role = payload.get("role")
        if user_id is None or email is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token(
        data={"id": user_id, "sub": email, "role": role}
    )

    return {"access_token": new_access_token, "token_type": "bearer"}


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("id")
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None or email is None or role is None:
            print(
                "Missing fields in token. id:", user_id, "email:", email, "role:", role
            )
            raise HTTPException(status_code=401, detail="Invalid token: Missing fields")
        return {"id": user_id, "email": email, "role": role}
    except jwt.ExpiredSignatureError:
        print("Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as e:
        print("JWTError:", e)
        raise credentials_exception
