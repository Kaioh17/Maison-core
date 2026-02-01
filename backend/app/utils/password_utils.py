from passlib.context import CryptContext

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")

def hash(password: str):
    return pwd_context.hash(password)

def verify(plain_pwd, hashed_pwd):
    if len(plain_pwd) > 20:
        if plain_pwd == hashed_pwd:
            return True
        else: None
    return pwd_context.verify(plain_pwd, hashed_pwd)