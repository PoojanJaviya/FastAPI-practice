from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse


app = FastAPI()

@app.get('/')
def index():
    return{
        "message" : "server running"
    }

@app.post('/contact')
def contact(
    name: str = Form(...),
    email : str = Form(...),
    message : str = Form(...)
):
    print("Name: ",name)
    print("email: ",email)
    print("message: ",message)

    return HTMLResponse(f"""
        <h1>Thanks, {name}</h1>
        <p> we recieved your message </p><br>
        <p> {message} </p>
    """)
    