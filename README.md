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
* **Inventory Management**: The `Product` model now includes an `available_items` field for real-time stock management.
* **Closed Sales**: The `Sale` model has been extended to support closed sales, which are only accessible to specific users or groups.
* **Order Management**: An `Order` system allows users to finalize a purchase from their bucket, creating an immutable record of the transaction.
* **Version 2 (V2) API**: A second version of the marketplace API is available, introducing class-based views, pagination, and ViewSets for a more streamlined developer experience.
* **Test Suite**: The project now uses `factory_boy` for more robust and maintainable test data creation.

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

The marketplace now has two API versions, v1 and v2.

### V1 API Endpoints

These are the original function-based views.

* **Endpoint**: `/v1/marketplace/products/`
  * **Method**: `GET`
  * **Description**: Lists all products with optional filtering and sorting.
* **Endpoint**: `/v1/marketplace/bucket/`
  * **Method**: `GET`
  * **Description**: Retrieves the current user's shopping bucket.
* **Endpoint**: `/v1/marketplace/bucket/add/`
  * **Method**: `POST`
  * **Description**: Adds a product to the user's bucket or updates its quantity.
* **Endpoint**: `/v1/marketplace/bucket/<int:product_id>/update/`
  * **Method**: `POST`
  * **Description**: Updates the quantity of a specific product in the bucket.
* **Endpoint**: `/v1/marketplace/bucket/<int:product_id>/`
  * **Method**: `DELETE`
  * **Description**: Removes a product from the user's bucket.

### V2 API Endpoints

This is the new class-based API, with a more RESTful design using ViewSets and Pagination.

* **Endpoint**: `/v2/marketplace/products/`
  * **Method**: `GET`
  * **Description**: Lists all products with pagination, filtering, sorting, and displays sale prices.
  * **Query Parameters**: `page`, `page_size`, `sort`, `category`
* **Endpoint**: `/v2/marketplace/bucket/`
  * **Methods**: `GET`, `POST`
  * **Description**: A ViewSet for managing the user's bucket. `GET` lists all items, and `POST` adds a new item.
* **Endpoint**: `/v2/marketplace/bucket/{product_id}/`
  * **Methods**: `PUT`, `DELETE`
  * **Description**: Updates the quantity of a product (`PUT`) or deletes it (`DELETE`).
* **Endpoint**: `/v2/marketplace/create-order/`
  * **Method**: `POST`
  * **Description**: Finalizes the user's current bucket into an `Order`, clears the bucket, and updates product inventory.

### User Authentoication

* **Endpoint:** `v1/marketplace_auth/registration/`
  * **Method:** POST
  * **Description:** Creates a new user and returns an authentication token.
  * **Request Body:** `first_name`, `second_name`, `email`, `password`

## Running Tests

To run the full test suite for the `marketplace` and `marketplace_auth` apps, use the following commands:

```bash
python manage.py test marketplace
```
