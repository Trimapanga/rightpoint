"""Import product catalog from the catalog.json file.

This command reads the catalog.json file and updates the products in the database
with the images and descriptions from the catalog.
"""

import json
import os

from django.core.management.base import BaseCommand
from django.db import transaction

from products.models import Brand, Product, ProductCategory


class Command(BaseCommand):
    help = "Import product catalog from catalog.json with images and descriptions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="catalog.json",
            help="Path to the catalog.json file (default: catalog.json)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options["file"]
        
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f"Catalog file not found: {file_path}")
            )
            return

        with open(file_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        products_data = catalog.get("products", [])
        updated_count = 0
        created_count = 0
        skipped_count = 0

        for product_data in products_data:
            sku = product_data.get("sku")
            name = product_data.get("name")
            brand_name = product_data.get("brand")
            category_name = product_data.get("category")
            description = product_data.get("description")
            features = product_data.get("features")
            image_filename = product_data.get("image_filename")

            if not sku or not name:
                self.stdout.write(
                    self.style.WARNING(f"Skipping product missing sku or name: {product_data}")
                )
                skipped_count += 1
                continue

            # Find or create brand
            brand_slug = brand_name.lower().replace(" ", "-")
            brand, _ = Brand.objects.get_or_create(
                slug=brand_slug,
                defaults={"name": brand_name, "website": ""}
            )

            # Find or create category
            category_slug = category_name.lower().replace(" ", "-")
            category, _ = ProductCategory.objects.get_or_create(
                slug=category_slug,
                defaults={"name": category_name, "description": ""}
            )

            # Create slug from sku
            slug = sku.lower().replace("_", "-")

            # Prepare product data
            product_defaults = {
                "title": name,
                "brand": brand,
                "category": category,
                "eyebrow": product_data.get("eyebrow", ""),
                "body": description or "",
                "features": features or "",
                "order": 0,
                "is_published": True,
            }

            # Update or create product
            product, created = Product.objects.update_or_create(
                slug=slug,
                defaults=product_defaults
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Created product: {name} (slug: {slug})")
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Updated product: {name} (slug: {slug})")
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Import complete: {created_count} created, {updated_count} updated, "
                f"{skipped_count} skipped"
            )
        )
