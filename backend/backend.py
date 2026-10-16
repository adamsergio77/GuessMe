from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DB_PATH = "sqlite:///../words.base.db"


class Base(DeclarativeBase):
    pass


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    list_name = Column(String, nullable=False)


engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="GuessMe API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class WordBase(BaseModel):
    word: str
    translation: str
    list_name: str


class WordCreate(WordBase):
    pass


class WordRead(WordBase):
    id: int


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/words", response_model=List[WordRead])
def get_words(
    list_name: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
) -> List[Word]:
    query = db.query(Word)
    if list_name is not None:
        query = query.filter(Word.list_name == list_name)
    return query.order_by(Word.id).all()


@app.get("/words/{word_id}", response_model=WordRead)
def get_word(word_id: int, db: Session = Depends(get_db)) -> Word:
    word = db.query(Word).filter(Word.id == word_id).first()
    if word is None:
        raise HTTPException(status_code=404, detail="Word not found")
    return word


@app.post("/words", response_model=WordRead, status_code=201)
def create_word(word: WordCreate, db: Session = Depends(get_db)) -> Word:
    db_word = Word(
        word=word.word,
        translation=word.translation,
        list_name=word.list_name,
    )
    db.add(db_word)
    db.commit()
    db.refresh(db_word)
    return db_word


@app.delete("/words/{word_id}")
def delete_word(word_id: int, db: Session = Depends(get_db)) -> dict:
    word = db.query(Word).filter(Word.id == word_id).first()
    if word is None:
        raise HTTPException(status_code=404, detail="Word not found")

    db.delete(word)
    db.commit()
    return {"message": "Word deleted", "id": word_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.backend:app", host="127.0.0.1", port=8080, reload=True)
