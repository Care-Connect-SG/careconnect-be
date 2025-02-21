from fastapi import HTTPException, status
from auth.hashing import Hash
from auth.jwttoken import create_access_token

async def register_user(db, user_data):
    # Check if the user already exists
    existing_user = await db["users"].find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    # Hash the password and create the user object
    hashed_pass = Hash.bcrypt(user_data.password)
    user_object = user_data.dict()
    user_object["password"] = hashed_pass

    await db["users"].insert_one(user_object)
    return {"res": "User created successfully"}

async def login_user(db, username: str, password: str):
    # Retrieve user by email (username)
    user = await db["users"].find_one({"email": username})
    if not user or not Hash.verify(user["password"], password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Create and return the access token along with user email
    access_token = create_access_token(data={"sub": user["email"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": user["email"]
    }
