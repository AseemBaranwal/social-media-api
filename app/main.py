from fastapi import FastAPI, Response, status, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import time

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
        conn = psycopg2.connect(host='localhost', database='fastapi', user='postgres', password='admin@123',
                                cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        print("Database connection was successful")
        break
    except Exception as error:
        print("Connecting to database failed with error: ", error)
        time.sleep(2)

allPosts = []


def find_post_idx(post_idx):
    for idx, post in enumerate(allPosts):
        if post['id'] == post_idx:
            return idx
    return -1


def find_post(post_id: int):
    for post in allPosts:
        if post['id'] == post_id:
            return post
    return None


# Refers to the below thing as a path operation
# async keyword makes sure that the app is asynchronous
# Below is the decorator (@app) that is built on top of the app object of FastAPI Class
# Get is an HTTP Method, and the ("/") represents the path from where we get our operations
@app.get("/")
def root():
    return {"message": "Welcome to her API"}


@app.get("/posts")
def get_posts():
    cursor.execute("""SELECT * FROM posts""")
    posts = cursor.fetchall()
    return {"data": posts}


@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(post: Post):
    cursor.execute("""INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING * """,
                   (post.title, post.content, post.published))
    new_post = cursor.fetchone()
    conn.commit()  # Staged changes are committed over here
    return {"data": new_post}


@app.get("/posts/latest")
def get_last_post():
    cursor.execute("""SELECT * FROM posts ORDER BY id DESC LIMIT 1""")
    latest_post = cursor.fetchone()
    return {"latest post": latest_post}


@app.get("/posts/{post_id}")
def get_post(post_id: int):
    cursor.execute(f"""SELECT * from posts where id = %s """, str(post_id))
    post = cursor.fetchone()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id = {post_id} was not found")
    return {"post_detail": post}


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int):
    cursor.execute(f"""DELETE from posts where id = %s RETURNING *""", str(post_id))
    deleted_post = cursor.fetchone()
    if not deleted_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id = {post_id} was not found")
    conn.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.put("/posts/{post_id}", status_code=status.HTTP_202_ACCEPTED)
def update_post(post_id: int, post: Post):
    cursor.execute("""UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s RETURNING * """,
                   (post.title, post.content, post.published, str(post_id)))
    updated_post = cursor.fetchone()
    if not updated_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id = {post_id} was not found")
    conn.commit()
    return {'data': updated_post}

# New post should look like in this manner 
# (title str, content str, [extend later] category str, published bool)
