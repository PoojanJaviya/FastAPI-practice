from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from models import StudentDB, Base
from database import engine, SessionLocal
from sqlalchemy.orm import Session



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base.metadata.create_all(bind=engine)


app = FastAPI()

students = {
    1 : {
        "name" : "Poojan",
        "age" : 19
    },
    2 : {
        "name" : "Sankalp",
        "age" : 20
    },
    3 : {
        "name" : "Om",
        "age" : 21
    }
}

class Student(BaseModel):
    name : str
    age : int = Field(gt=0)

class StudentOut(BaseModel):
    name : str
    age : int = Field(gt=0)


@app.get('/')
def root():
    return {"message" : "Server is running"}

# @app.get('/students', response_model = list[StudentOut])
# def get_students():
#     return list(students.values())

@app.get("/students", response_model=list[StudentOut])
def get_students(db = Depends(get_db)):
    students = db.query(StudentDB).all()
    return students


@app.get('/student/{id}', response_model = StudentOut)
def get_student_by_id(id : int):
    if id not in students:
        raise HTTPException(
            status_code = 404,
            detail="Student not found"
        )
    return students[id]



# @app.post('/add_student', status_code = 201)
# def add_student(student : Student):

#     # if(student.age <= 0):
#     #     return {"Error" : "Invalid Age"}
#     n = len(students) + 1
#     students[n] = {"name" : f"{student.name}", "age" : student.age}
#     return {"message" : f"{student.name} added successfully added in database.",
#             "new list of students" : students}

@app.post('/add_student', status_code=201)
def add_student(student: Student, db: Session = Depends(get_db)):
    new_student = StudentDB(
        name=student.name,
        age=student.age
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return {
        "message": "Student added successfully",
        "student": {
            "id": new_student.id,
            "name": new_student.name,
            "age": new_student.age
        }
    }



# @app.delete('/student/{id}')
# def delete_student(id : int):
#     if id not in students:
#         raise HTTPException(
#             status_code = 404,
#             detail="Student not found"
#         )
    
#     students.pop(id)

#     return {
#         "success" : f"student with id {id} removed",
#         "updated students list" : students
#     }

@app.delete("/student/{id}")
def delete_student(
    id: int,
    db: Session = Depends(get_db)
):
    db_student = db.query(StudentDB).filter(StudentDB.id == id).first()

    if db_student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    db.delete(db_student)
    db.commit()

    return {
        "message": f"Student with id {id} deleted successfully"
    }


# @app.put('/student/{id}')
# def update(id : int , student : Student):
#     if id not in students:
#         raise HTTPException(
#             status_code = 404,
#             detail="Student not found"
#         )
    
#     students[id] = {
#         "name" : f"{student.name}",
#         "age" : student.age
#     }

#     return {
#         "success" : f"student with id {id} updated.",
#         "updated_list" : students
#     }

@app.put("/student/{id}")
def update_student(
    id: int,
    student: Student,
    db: Session = Depends(get_db)
):
    db_student = db.query(StudentDB).filter(StudentDB.id == id).first()

    if db_student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    db_student.name = student.name
    db_student.age = student.age

    db.commit()
    db.refresh(db_student)

    return {
        "message": "Student updated successfully",
        "student": {
            "id": db_student.id,
            "name": db_student.name,
            "age": db_student.age
        }
    }
