from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
import database, models
import secrets

from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
import database, models
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models, database, hashlib
from schemas import UserCreate
router = APIRouter()
security = HTTPBearer()

# ---------- Token verification ----------
def get_current_user(x_api_key: str = Header(...), db: Session = Depends(database.get_db)):
    token = db.query(models.Token).filter(models.Token.token == x_api_key).first()
    if not token:
        raise HTTPException(status_code=403, detail="Invalid token")
    return token.owner

# ---------- Admin: Create token ----------
def create_token(user, db: Session, name: str):
    token_str = secrets.token_hex(16)
    new_token = models.Token(token=token_str, owner=user)
    db.add(new_token)
    db.commit()
    db.refresh(new_token)
    return new_token

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import secrets, database, models
from schemas import TokenCreate

router = APIRouter()

#@router.post("v1/admin/tokens")
def create_token(token_in: TokenCreate, db: Session = Depends(database.get_db)):
    # Find the user by username
    user = db.query(models.User).filter(models.User.username == token_in.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate random token
    token_str = secrets.token_hex(16)  # 32-character hex string

    # Create and store the token
    token = models.Token(token=token_str, owner=user)
    db.add(token)
    db.commit()
    db.refresh(token)

    return {
        "token": token.token,
        "name": token_in.name,
        "user_email": user.username,
        "created_at": token.created_at
    }


#@router.post("v1/admin/users")
def create_user(user_in: UserCreate, db: Session = Depends(database.get_db)):
    existing = db.query(models.User).filter(models.User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_password = hashlib.sha256(user_in.password.encode()).hexdigest()
    user = models.User(username=user_in.username, hashed_password=hashed_password, role=user_in.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role}