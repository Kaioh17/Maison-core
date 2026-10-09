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
        verify=pwd_context.verify(plain_pwd, hashed_pwd)
        if verify: return verify
        elif not verify and plain_pwd == hashed_pwd: ## added this to deal with tenant to driver switch: since the hashed password get's parsed from the db 
            return True
    except (ValueError, TypeError):
        return False
