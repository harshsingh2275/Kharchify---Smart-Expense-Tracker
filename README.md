# Kharchify

Kharchify is a multi-user expense tracker built as a Python internship capstone project. It allows users to register, log in, record daily expenses, and view a monthly summary of their spending by category.

## Features

- User registration and login
- JWT authentication
- Add, edit, delete, and list expenses
- Category and date filtering
- Pagination
- Monthly spending summary
- Input validation
- Application logging
- Automated tests
- Swagger/OpenAPI documentation

## Technology Stack

- Python 3.11+
- FastAPI
- Uvicorn
- SQLite / sqlite3
- Pydantic v2
- PyJWT
- bcrypt
- HTML/CSS/vanilla JavaScript
- pytest / httpx

## Project Structure

```text
expense-tracker/
├── app/               # FastAPI application code (routers, repositories, schemas)
├── db/                # Database schema
├── static/            # Frontend (HTML, CSS, JS)
├── tests/             # Automated test suite
├── .env.example       # Example environment variables
├── requirements.txt   # Runtime dependencies
└── requirements-dev.txt # Development dependencies
```

## Installation

Clone the repository and install dependencies using a virtual environment:

```bash
git clone https://github.com/harshsingh2275/Kharchify---Smart-Expense-Tracker.git
cd "Kharchify - Smart Expense Tracker"
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Environment Configuration

The application reads real environment variables using `os.getenv` (it does not use `python-dotenv` or `.env` files automatically). 

For development, you can use the default settings or export the variables defined in `.env.example`.
For production, you **must** set the `SECRET_KEY` environment variable securely.

Example of setting variables in the terminal (Windows PowerShell):
```powershell
$env:SECRET_KEY="your-super-secret-key"
$env:APP_ENV="production"
```

## Run the Application

Start the development server:

```bash
uvicorn app.main:app --reload
```

## Run Tests

Run the complete test suite using pytest:

```bash
pytest -q
```

## API Documentation

When the application is running, the interactive Swagger/OpenAPI documentation is available at:

```text
http://127.0.0.1:8000/docs
```

For detailed endpoint specifications, refer to `API.md` in the repository.

## Live Demo

Live demo: <ADD LIVE LINK AFTER DEPLOYMENT>

## Design Decisions & Known Limitations

- **Database**: Uses raw `sqlite3` instead of an ORM to demonstrate fundamental SQL CRUD operations.
- **Data Access**: SQL queries are encapsulated in Repository classes.
- **Reporting**: Monthly summaries are calculated using SQL `GROUP BY` rather than relying on external data analysis libraries.
- **Data Types**: `REAL` is used for monetary amounts as a learning-project trade-off.
- **Authentication**: JWTs are stored in `localStorage` for simplicity in this frontend implementation.
- **Scope**: Features like password resets, email verification, custom categories, and rate limiting are deliberately excluded from this capstone project.

## Project Purpose

This project is a Python Programming Internship capstone demonstrating the full-stack skills learned across the internship, including Python fundamentals, REST APIs, database management, and frontend integration.
