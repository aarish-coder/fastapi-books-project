import re
from fastapi import FastAPI, Query
from typing import Optional, Union
import json
def load_db():
    try:
        with open("books.json","r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return[]
def save_db(data_to_save):
    with open("books.json", "w") as f:
        json.dump(data_to_save, f, indent=4)

def natural_sort_key(s):
    # Alphanumeric sorting logic
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', str(s))]

app = FastAPI()
db=load_db()
if not db:
    db = [
        {"id": 1, "name": "python", "author": "aarish"},
        {"id": 2, "name": "java", "author": "athi"},
        {"id": 3, "name": "sql", "author": "bharath"}
    ]
    save_db(db)

@app.get("/db")
def search_book(book_id:Optional[str]=None, book_name:Optional[str]=None, author:Optional[str]=None):
    # Search logic
    for book in db:
        if (str(book["id"]) == book_id) or (book_name and book["name"].lower() == book_name.lower()) or (author and book["author"].lower()==author.lower()):
            return {"status": "found", "book_details": book}
    
    
    return {"status": "Not found"}

@app.delete("/delete-book")
def delete_book(book_id:Optional[str]=None, name:Optional[str]=None, author:Optional[str]=None):
    matched_books=[]
    for book in db:
        match=True
        if book_id is not None and book["id"] !=book_id:
            match=False
        if name is not None and book["name"].lower() !=name.lower():
            match=False
        if author is not None and book["author"].lower() != author.lower():
            match = False
        if match and (book_id is not None or name is not None or author is not None):
            matched_books.append(book)
    if not matched_books:
            return{"status":"error","message":"no books found matching the critera"}
    if len(matched_books) >1:
            return{"status":"multiple found",
                   "message":f"found {len(matched_books)} books",
                   "books_found":matched_books,
                   "instruction":"try adding 'author' or 'book_id' to narrow down the search"
                   }
    back_to_remove=matched_books[0]
    db.remove(back_to_remove)
    save_db(db)
    return{"status":"success",
           "message":f"book '{back_to_remove['name']}' deleted successfully.",
           "updated_db":db}
    
@app.post("/add-book")
def add_book(book_id : str, name : str, author : str, force_add : bool = Query(False)):
    id_exists=any(book["id"]==book_id for book in db)
    if id_exists and not force_add :
        return{"status": "warning",
            "message": f"Book ID {book_id} already exists. Do you still want to add this?",
            "instruction": "If YES, please tick the 'force_add' checkbox and execute again."
        }
    
    new_book={"id": book_id, "name": name, "author": author}
    db.append(new_book)
    save_db(db)
    return{"message":"book added successfully", "updated db": db}

@app.put("/update-book/{id}")
def update_book(id :str, new_id :Optional[str]=None, name :Optional[str]=None, author :Optional[str]=None):
    for book in db:
        if str(book["id"]) == id:
            if new_id: book["id"] = new_id
            if name: book["name"] = name
            if author: book["author"] = author
            save_db(db)
            return {"message": "book updated successfully.", "updated_book": book}
    return {"message": "book not found"}
@app.post("/insert-book")
def insert_book(book_id: str, name: str, author: str, position: Optional[int]=Query(None), allow_duplicate: bool=Query(False)):
    id_exists=any(book["id"]==book_id for book in db)
    if id_exists and not allow_duplicate:
        return{"status":"error","message":f"Book ID {book_id} already exists. Use update-book to change it or set allow_duplicate=True to add anyway."}
    new_book={"id":book_id, "name":name, "author":author}
    if position is not None:
        target_index= position -1
        if target_index < 0: target_index = 0
        if target_index > len(db): target_index = len(db)
        db.insert(target_index, new_book)
        save_db(db)
        return{"message":f"book inserted at position {position}", "data":db}
    else:
        db.append(new_book)
        db.sort(key=lambda x: natural_sort_key(x["id"]))
        save_db(db)
        return{"message":"book added and sorted by id", "data":db}

@app.get("/all-books")
def get_all_books():
    return{"total books": len(db), "data": db}

@app.get("/")
def home():
    return {"message": "Server is running! Go to /db?book_id=1 to search."}
