from datetime import datetime, timedelta
from jose import JWTError, jwt
from config import SECRET_KEY
from fastapi import HTTPException


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token: Missing 'sub' field")
        
        return {"email": email}
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")