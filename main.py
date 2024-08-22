from fastapi import FastAPI, HTTPException, Depends, Form, Header
from sqlalchemy import create_engine, MetaData, insert, update, select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt, JWTError
from models.models import users, shanyraks, comments, metadata
from config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME 


DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


app = FastAPI()
metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"


def get_session():
    with SessionLocal() as session:
        yield session


class UserCreate(BaseModel):
    username: str
    phone: str
    password: str
    name: str = None
    city: str = None


class UserUpdate(BaseModel):
    phone: str = None
    name: str = None
    city: str = None


class ShanyrakCreate(BaseModel):
    type: str
    price: int
    address: str
    area: float
    rooms_count: int
    description: str = None


class ShanyrakUpdate(BaseModel):
    type: str = None
    price: int = None
    address: str = None
    area: float = None
    rooms_count: int = None
    description: str = None


class CommentCreate(BaseModel):
    content: str


class CommentUpdate(BaseModel):
    content: str


@app.post("/auth/users/")
def register_user(user: UserCreate, session: Session = Depends(get_session)):
    hashed_password = pwd_context.hash(user.password)
    stmt = insert(users).values(
        username=user.username,
        phone=user.phone,
        password=hashed_password,
        name=user.name,
        city=user.city,
    )
    try:
        session.execute(stmt)
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "User created successfully"}


@app.post("/auth/users/login")
def login(username: str = Form(...), password: str = Form(...), session: Session = Depends(get_session)):
    stmt = select(users).where(users.c.username == username)
    result = session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = jwt.encode({"sub": user.username}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token}


@app.get("/auth/users/me")
def get_user_info(token: str = Header(...), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(users).where(users.c.username == username)
    result = session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "phone": user.phone,
        "name": user.name,
        "city": user.city
    }


@app.patch("/auth/users/me")
def update_user(data: UserUpdate, token: str = Header(...), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = update(users).where(users.c.username == username).values(**data.dict(exclude_unset=True))
    result = session.execute(stmt)
    session.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User data updated successfully"}


@app.post("/shanyraks/")
def create_shanyrak(shanyrak: ShanyrakCreate, token: str = Header(...), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(users).where(users.c.username == username)
    result = session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stmt = insert(shanyraks).values(
        type=shanyrak.type,
        price=shanyrak.price,
        address=shanyrak.address,
        area=shanyrak.area,
        rooms_count=shanyrak.rooms_count,
        description=shanyrak.description,
        user_id=user.id
    )
    result = session.execute(stmt)
    session.commit()
    shanyrak_id = result.inserted_primary_key[0]

    return {"id": shanyrak_id}


@app.get("/shanyraks/{id}")
def get_shanyrak(id: int, session: Session = Depends(get_session)):
    stmt = select(shanyraks).where(shanyraks.c.id == id)
    result = session.execute(stmt)
    shanyrak = result.scalar_one_or_none()

    if not shanyrak:
        raise HTTPException(status_code=404, detail="Shanyrak not found")

    return {
        "id": shanyrak.id,
        "type": shanyrak.type,
        "price": shanyrak.price,
        "address": shanyrak.address,
        "area": shanyrak.area,
        "rooms_count": shanyrak.rooms_count,
        "description": shanyrak.description,
        "user_id": shanyrak.user_id
    }


@app.patch("/shanyraks/{id}")
def update_shanyrak(id: int, data: ShanyrakUpdate, token: str = Header(...), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(users).join(shanyraks).where(users.c.username == username, shanyraks.c.id == id)
    result = session.execute(stmt)
    shanyrak = result.scalar_one_or_none()

    if not shanyrak:
        raise HTTPException(status_code=404, detail="Shanyrak not found")

    stmt = update(shanyraks).where(shanyraks.c.id == id).values(**data.dict(exclude_unset=True))
    result = session.execute(stmt)
    session.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Shanyrak not found")

    return {"message": "Shanyrak updated successfully"}


@app.delete("/shanyraks/{id}")
def delete_shanyrak(id: int, token: str = Header(...), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(users).join(shanyraks).where(users.c.username == username, shanyraks.c.id == id)
    result = session.execute(stmt)
    shanyrak = result.scalar_one_or_none()

    if not shanyrak:
        raise HTTPException(status_code=404, detail="Shanyrak not found")

    stmt = delete(shanyraks).where(shanyraks.c.id == id)
    session.execute(stmt)
    session.commit()

    return {"message": "Shanyrak deleted successfully"}


@app.post("/shanyraks/{id}/comments")
def add_comment(id: int, comment: CommentCreate, token: str = Header(...), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(users).where(users.c.username == username)
    result = session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stmt = insert(comments).values(
        content=comment.content,
        user_id=user.id,
        shanyrak_id=id
    )
    session.execute(stmt)
    session.commit()

    return {"message": "Comment added successfully"}


@app.get("/shanyraks/{id}/comments")
def get_comments(id: int, session: Session = Depends(get_session)):
    stmt = select(comments).where(comments.c.shanyrak_id == id)
    result = session.execute(stmt)
    comment_list = result.fetchall()

    return {"comments": [
        {
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at,
            "author_id": comment.user_id
        } for comment in comment_list
    ]}


@app.patch("/shanyraks/{id}/comments/{comment_id}")
def update_comment(id: int, comment_id: int, comment: CommentUpdate, token: str = Header(...), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(users).join(comments).where(users.c.username == username, comments.c.id == comment_id)
    result = session.execute(stmt)
    existing_comment = result.scalar_one_or_none()

    if not existing_comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    stmt = update(comments).where(comments.c.id == comment_id).values(content=comment.content)
    result = session.execute(stmt)
    session.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Comment not found")

    return {"message": "Comment updated successfully"}


@app.delete("/shanyraks/{id}/comments/{comment_id}")
def delete_comment(id: int, comment_id: int, token: str = Header(...), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    stmt = select(users).join(comments).where(users.c.username == username, comments.c.id == comment_id)
    result = session.execute(stmt)
    existing_comment = result.scalar_one_or_none()

    if not existing_comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    stmt = delete(comments).where(comments.c.id == comment_id)
    session.execute(stmt)
    session.commit()

    return {"message": "Comment deleted successfully"}
