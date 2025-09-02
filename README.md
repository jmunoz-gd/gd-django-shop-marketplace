# GD Django Shop Marketplace

This project is a Django-based e-commerce marketplace application, developed as a practice for a GD course. It features a RESTful API for products, a shopping bucket system, and an authentication module. The architecture is designed to be scalable, utilizing Celery for background tasks and Redis as a message broker.

## Table of Contents

* [Features](#features)
* [Setup Local Environment](#setup-local-environment)
* [Key API Endpoints](#key-api-endpoints)

## Features

* **RESTful API**: Provides a comprehensive set of endpoints for products, user authentication, and shopping bucket management.

* **Token-Based Authentication**: Implements user registration and authentication using Django Rest Framework's TokenAuthentication.

* **Shopping Bucket**: A dedicated system for authenticated users to add, update, and remove products from a shopping bucket.

* **Background Tasks**: Integrates Celery and Redis to handle periodic tasks, such as sales announcements.

* **Database Management**: Uses Django-Celery-Beat to schedule and manage tasks from the Django Admin interface.

* **Extensible Data Models**: Well-defined models for Category, Product, and Sale that support a flexible product catalog.

* **Comprehensive Test Suite**: Includes unit and integration tests for key API functionalities.

## Setup Local Environment

1. Create a Python venv:

```bash
python -m venv venv
source venv/bin/activate
```

2. Install all Python dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your environment variables. Create a `.env` file in the project root with at least `SECRET_KEY` and `DEBUG` variables:

```bash
# .env
SECRET_KEY=your_secret_key_here
DEBUG=True
```

4. Run the database migrations:

```bash
python manage.py migrate
```

5. Run the Redis server using Docker:

```bash
docker-compose up -d redis
```

6. Run the development server and Celery worker:

```bash
# In a separate terminal, start the Celery worker
celery -A shop worker --loglevel=info

# In a new terminal, start the Celery Beat scheduler
celery -A shop beat --loglevel=info

# In the main terminal, run the Django development server
python manage.py runserver
```

You can now access the following endpoints:

* **Django Admin:** <http://127.0.0.1:8000/admin/>

* **Products API:** <http://127.0.0.1:8000/v1/marketplace/products/>

## Key API Endpoints

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

### User Authentoication

* **Endpoint:** `v1/marketplace_auth/registration/`

* **Method:** POST

* **Description:** Creates a new user and returns an authentication token.

* **Request Body:** `first_name`, `second_name`, `email`, `password`

### Shopping Bucket

The shopping bucket requires authentication via an `Authorization: Token <your_token>` header.

* **Endpoint:** `v1/marketplace/bucket/`

* **Method:** GET

* **Description:** Retrieves the current user's shopping bucket, including products and the total cost.

* **Endpoint:** `v1/marketplace/bucket/add/`

* **Method:** POST

* **Description:** Adds a product to the user's bucket or updates its quantity if it already exists.

* **Request Body:** `id` (product ID), `number` (quantity, defaults to 1).

* **Endpoint:** `v1/marketplace/bucket/<int:product_id>/`

* **Method:** DELETE

* **Description:** Removes a product from the user's bucket.

* **Endpoint:** `v1/marketplace/bucket/<int:product_id>/update/`

* **Method:** POST

* **Description:** Updates the quantity of a specific product in the bucket.

* **Request Body:** `number` (new quantity).

## Running Tests

To run the full test suite for the `marketplace` and `marketplace_auth` apps, use the following commands:

```bash
python manage.py test marketplace
```
