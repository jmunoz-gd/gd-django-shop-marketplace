# GD Django Shop Marketplace

Practice GD course - A Django e-commerce project with a marketplace app

## Setup Local Environment

1. Create a Python venv:

```bash
python -m venv venv
source venv/bin/activate
```

2. Install Django and Other Dependencies

```bash
pip install Django djangorestframework python-dotenv
```

3. Generate ***requirements.txt***

```bash
pip freeze > requirements.txt
```

4. Run Database Migrations

```bash
python manage.py migrate
```

5. Create a Superuser

```bash
python manage.py createsuperuser
```

6. Run Development server

```bash
python manage.py runserver
```
