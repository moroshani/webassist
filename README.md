# WebAssist

A Django application for managing and organizing web links with a clean, modern interface.

## Features

- Home page with welcome message and introduction
- Sites page with a table of stored links
- Search and filter functionality
- Admin interface for CRUD operations
- Responsive design using Bootstrap
- Clean and modern UI

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd webassist
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

7. Access the application:
- Home page: http://127.0.0.1:8000/
- Sites page: http://127.0.0.1:8000/sites/
- Admin interface: http://127.0.0.1:8000/admin/

## Technologies Used

- Django 5.0.2
- Bootstrap 5.3.0
- django-filter 23.5
- SQLite (development database) 