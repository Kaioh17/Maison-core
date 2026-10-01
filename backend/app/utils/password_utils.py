from passlib.context import CryptContext

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")

def hash(password: str):
    return pwd_context.hash(password)

def verify(plain_pwd, hashed_pwd):
    # Never compare plain to the stored hash directly: that would let a leaked hash log in.
    # No usable hash (e.g. a driver who has not finished onboarding) simply fails.
    if not hashed_pwd:
        return False
    try:
        return pwd_context.verify(plain_pwd, hashed_pwd)
    except (ValueError, TypeError):
        return False
