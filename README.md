# Product & Category Management API

A REST API built with **FastAPI** and **MySQL** for managing products and categories, with image upload support.

## Tech Stack

- **Python 3.10+**
- **FastAPI** — web framework with auto-generated Swagger docs
- **MySQL** — relational database
- **uvicorn** — ASGI server

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd pavansgroup_task
```

### 2. Create and activate virtual environment

```bash
python -m venv .venv

# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# macOS / Linux:
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure database credentials

```bash
cp .env.example .env
```

Edit `.env` with your MySQL credentials:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=product_api
```

### 5. Create database and tables

```bash
mysql -u root -p < schema.sql
```

Or paste the contents of `schema.sql` into phpMyAdmin / MySQL Workbench.

### 6. Run the server

```bash
uvicorn app.main:app --reload
```

### 7. Open API documentation

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## API Endpoints

### Categories

| Method | Endpoint            | Description          |
| ------ | ------------------- | -------------------- |
| GET    | `/categories`       | List all categories  |
| POST   | `/categories`       | Create a category    |
| PUT    | `/categories/{id}`  | Update a category    |
| DELETE | `/categories/{id}`  | Delete a category    |

### Products

| Method | Endpoint            | Description                                    |
| ------ | ------------------- | ---------------------------------------------- |
| GET    | `/products`         | List all products (optional `?category_id=X`)  |
| POST   | `/products`         | Create product with image upload               |
| PUT    | `/products/{id}`    | Update product (optional new image)            |
| DELETE | `/products/{id}`    | Delete product and its image file              |
| GET    | `/product/{id}`     | Product detail with category names resolved    |

## Project Structure

```
pavansgroup_task/
├── app/
│   ├── __init__.py
│   ├── main.py              ← FastAPI app entry point
│   ├── database.py          ← MySQL connection (reads from .env)
│   ├── models.py            ← Pydantic request/response schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── categories.py    ← Category CRUD endpoints
│   │   └── products.py      ← Product CRUD + image endpoints
│   └── utils/
│       ├── __init__.py
│       └── file_handler.py  ← Image save/delete helpers
├── uploads/                 ← Uploaded product images
├── schema.sql               ← Database CREATE TABLE statements
├── requirements.txt
├── .env                     ← DB credentials (not committed)
├── .env.example             ← Template for .env
├── .gitignore
└── README.md
```

## Postman Collection

Import the auto-generated OpenAPI spec into Postman:

1. Open Postman → **Import** → **Link**
2. Paste: `http://localhost:8000/openapi.json`
3. Click **Continue** → **Import**

This creates a ready-to-use collection of all 9 endpoints.
