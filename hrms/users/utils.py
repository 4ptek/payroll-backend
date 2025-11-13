import bcrypt

def make_password(raw_password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(raw_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(raw_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(raw_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        print("Password check error:", e)
        return False
