from fastapi import FastAPI, Response, status, HTTPException, Depends
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import time

from sqlalchemy.orm import Session

from . import models
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Below code makes sure that the data published(POST) to the API is always following the given certain constraints
# and if the application does not honor the constraints, the data is not sent

# Also this code returns the objects in a pydantic model which is different from a dictionary and can be converted
# easily using the syntax obj.dict()
class Post(BaseModel):
    title: str
    content: str
    published: bool = True


while True:
    try:
        conn = psycopg2.connect(host='localhost', database='fastapi', user='postgres', password='admin1234',
                                cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print("Database connection was successful")
        break
    except Exception as error:
        print("Connecting to database failed with error: ", error)
        time.sleep(2)


# Refers to the below thing as a path operation
# async keyword makes sure that the app is asynchronous
# Below is the decorator (@app) that is built on top of the app object of FastAPI Class
# Get is an HTTP Method, and the ("/") represents the path from where we get our operations
@app.get("/")
def root():
    return {"message": "Welcome to her API"}


@app.get("/posts")
def get_posts(db: Session = Depends(get_db)):
    # Way using PostgreSQL directly
    # cursor.execute("""SELECT * FROM posts""")
    # posts = cursor.fetchall()

    # Getting same stuff done using ORM
    posts = db.query(models.Post).all()
    return {"data": posts}


@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(post: Post, db: Session = Depends(get_db)):
    # Way using PostgreSQL directly
    # cursor.execute("""INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING * """,
    #                (post.title, post.content, post.published))
    # new_post = cursor.fetchone()
    # conn.commit()  # Staged changes are committed over here

    # Getting same stuff done using ORM
    new_post = models.Post(**post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return {"data": new_post}


@app.get("/posts/latest")
def get_last_post():
    cursor.execute("""SELECT * FROM posts ORDER BY id DESC LIMIT 1""")
    latest_post = cursor.fetchone()
    return {"latest post": latest_post}


@app.get("/posts/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db)):
    # Way using PostgreSQL directly
    # cursor.execute(f"""SELECT * from posts where id = %s """, str(post_id))
    # post = cursor.fetchone()

    # Getting same stuff done using ORM
    post = db.query(models.Post).filter(post_id == models.Post.id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id = {post_id} was not found")
    return {"post_detail": post}


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    # Way using PostgreSQL directly
    # cursor.execute(f"""DELETE from posts where id = %s RETURNING *""", str(post_id))
    # deleted_post = cursor.fetchone()

    # Getting same stuff done using ORM
    deleted_post = db.query(models.Post).filter(post_id == models.Post.id)
    if not deleted_post.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id = {post_id} was not found")
    deleted_post.delete(synchronize_session=False)
    db.commit()
    # conn.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.put("/posts/{post_id}", status_code=status.HTTP_202_ACCEPTED)
def update_post(post_id: int, updated_post: Post, db: Session = Depends(get_db)):
    # Way using PostgreSQL directly
    # cursor.execute("""UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s RETURNING * """,
    #                (post.title, post.content, post.published, str(post_id)))
    # updated_post = cursor.fetchone()

    # Getting same stuff done using ORM
    post_query = db.query(models.Post).filter(models.Post.id == post_id)
    post = post_query.first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id = {post_id} was not found")
    post_query.update(updated_post.dict(), synchronize_session=False)
    db.commit()
    # conn.commit()
    return {'data': post_query.first()}

# New post should look like in this manner 
# (title str, content str, [extend later] category str, published bool)
