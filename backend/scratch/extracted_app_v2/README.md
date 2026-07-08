# Personal Notes App
=====================

A personal notes app where users can sign up, create private notes, and only the note's author can view, edit, or delete it.

## Setup Instructions

1. Clone the repository: `git clone https://github.com/your-username/personal-notes-app.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with the following environment variables:
	* `DATABASE_URL`: the URL of your database (e.g. `sqlite:///notes.db`)
	* `SECRET_KEY`: a secret key for authentication (e.g. `your_secret_key_here`)
4. Run the application: `uvicorn main:app --host 0.0.0.0 --port 8000`

## Environment Variables

* `DATABASE_URL`: the URL of your database (e.g. `sqlite:///notes.db`)
* `SECRET_KEY`: a secret key for authentication (e.g. `your_secret_key_here`)

## API Endpoints

| Method | Path | Description | Requires Auth |
| --- | --- | --- | --- |
| POST | /auth/register | Register a new user | No |
| POST | /auth/login | Login a user | No |
| POST | /notes | Create a new note | Yes |
| GET | /notes/{id} | Get a note by ID | Yes |
| GET | /notes | List all notes for the current user | Yes |
| PUT | /notes/{id} | Update a note (must be owned by user) | Yes |
| DELETE | /notes/{id} | Delete a note (must be owned by user) | Yes |