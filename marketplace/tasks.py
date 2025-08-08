# marketplace/tasks.py

import csv
import logging
from datetime import datetime
from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Sale

# Get a logger instance for this task file
logger = logging.getLogger(__name__)


@shared_task
def announce_sales():
    logger.info("Starting 'announce_sales' periodic task.")

    try:
        sales_to_announce = (
            Sale.objects.filter(
                was_announced=False, announcement_date__lte=timezone.now()
            )
            .select_related()
            .prefetch_related("products", "categories")
        )

        if not sales_to_announce:
            logger.info("No sales to announce at this time.")
            return "No sales to announce."

        # --- REFINED QUERY: Fetch only non-staff users for the campaign ---
        all_users = User.objects.filter(is_active=True, is_staff=False).values_list(
            "email", flat=True
        )
        if not all_users:
            logger.warning("No regular users found to send announcements to.")
            return "No regular users found."

        file_path = f'sales_announcements_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv'
        total_emails_sent = 0

        with open(file_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["email", "subject", "discount", "products", "categories"])

            for sale in sales_to_announce:
                product_names = ", ".join(sale.products.values_list("name", flat=True))
                category_names = ", ".join(
                    sale.categories.values_list("name", flat=True)
                )
                subject = f"New Sale: {sale.name} is here!"

                for user_email in all_users:
                    writer.writerow(
                        [
                            user_email,
                            subject,
                            sale.discount,
                            product_names,
                            category_names,
                        ]
                    )
                    total_emails_sent += 1

                sale.was_announced = True
                sale.save()

        logger.info(
            "Successfully announced %d sales to %d users. "
            "%d email entries written to %s",
            sales_to_announce.count(),
            len(all_users),
            total_emails_sent,
            file_path,
        )
        return (
            f"Announced {sales_to_announce.count()} sales. "
            f"{total_emails_sent} email entries written to {file_path}"
        )

    except Exception as e:
        logger.error(
            f"An unexpected error occurred in announce_sales task: {e}", exc_info=True
        )
        raise
