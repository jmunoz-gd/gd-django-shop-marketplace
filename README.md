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

You can now access the following endpoints:

* **Django Admin:** <http://127.0.0.1:8000/admin/>

* **Products API:** <http://127.0.0.1:8000/v1/marketplace/products/>

## Kay API Endpoints

The primary API endpoint is ***/v1/marketplace/products/***.

### Filtering

| Parameter | Example                  | Description                                                |
| --------- | ------------------------ | ---------------------------------------------------------- |
| category  | /products/?category=5    | Returns products belonging to category with ID 5.          |
| category  | /products/?category=9,10 | Returns products from categories with IDs 9 or 10.         |
| category  | /products/?category=-6   | Returns products that do not belong to category with ID 6. |

### Sorting

| Parameter | Example                | Description                                  |
| --------- | ---------------------- | -------------------------------------------- |
| sort      | /products/?sort=name   | Sorts products by name in ascending order.   |
| sort      | /products/?sort=-price | Sorts products by price in descending order. |

## Running Tests

To run the full test suite for the **marketplace** app, use the following command:

```bash
python manage.py test marketplace
```
