from fastapi import HTTPException

class InvalidCredentialsError(HTTPException):
    def __init__(self):
        super().__init__(status_code=401, detail="Invalid credentials")

class NoteNotFoundError(HTTPException):
    def __init__(self):
        super().__init__(status_code=404, detail="Note not found")
