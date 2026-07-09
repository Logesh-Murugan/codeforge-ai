# Personal Notes App
=====================

## Project Description
--------------------

A personal notes app where users can sign up, create private notes, and only the note's author can view, edit, or delete it.

## Setup Instructions
---------------------

1. Clone the repository: `git clone https://github.com/your-username/personal-notes-app.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with the following environment variables:
	* `DATABASE_URL`: the URL of your database (e.g. `sqlite:///notes.db`)
	* `SECRET_KEY`: a secret key for authentication (e.g. `your_secret_key_here`)
4. Run the application: `uvicorn main:app --host 0.0.0.0 --port 8000`

## Environment Variables
-------------------------

* `DATABASE_URL`: the URL of your database (e.g. `sqlite:///notes.db`)
* `SECRET_KEY`: a secret key for authentication (e.g. `your_secret_key_here`)

## API Endpoints
----------------

| Method | Path | Description | Requires Auth |
| --- | --- | --- | --- |
| POST | /auth/register | Register a new user | False |
| POST | /auth/login | Login a user | False |
| POST | /notes | Create a new note | True |
| GET | /notes/{id} | Get a note by ID | True |
| GET | /notes | List all notes for the authenticated user | True |
| PUT | /notes/{id} | Update a note | True |
| DELETE | /notes/{id} | Delete a note | True |
| DELETE | /users | Delete a user account and associated notes | True |