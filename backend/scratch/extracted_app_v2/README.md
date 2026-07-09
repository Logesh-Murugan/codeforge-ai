# Personal Notes App
=====================

## Project Description
--------------------

A personal notes app where users can sign up, create private notes, and only the note's author can view, edit, or delete it.

## Setup Instructions
---------------------

### Prerequisites

* Python 3.8+
* pip
* A database system (e.g., SQLite, PostgreSQL)

### Installation

1. Clone the repository: `git clone https://github.com/your-username/personal-notes-app.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Create a database: `python db.py create`
4. Run the app: `python main.py`

### Environment Variables

* `DATABASE_URL`: the URL of the database system (e.g., `sqlite:///notes.db`)
* `SECRET_KEY`: a secret key for authentication (e.g., `your-secret-key-here`)

## API Endpoints
----------------

| Method | Path | Description | Requires Auth |
| --- | --- | --- | --- |
| POST | /auth/register | Register a new user | No |
| POST | /auth/login | Login a user | No |
| GET | /users/me | Get the current user's profile | Yes |
| PATCH | /users/me | Update the current user's profile | Yes |
| POST | /notes | Create a new note | Yes |
| GET | /notes | List all notes for the current user | Yes |
| GET | /notes/{id} | Get a note by ID | Yes |
| PATCH | /notes/{id} | Update a note | Yes |
| DELETE | /notes/{id} | Delete a note | Yes |

Note: `{id}` is a path parameter representing the ID of the note.