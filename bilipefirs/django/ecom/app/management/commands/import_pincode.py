import csv
from django.core.management.base import BaseCommand
from app.models import Pincode

class Command(BaseCommand):
    help = "Import pincode data from a CSV file"

    def handle(self, *args, **kwargs):
        file_path = "/home/henilshingala/Bilipefirs/bilipefirs/django/ecom/app/pincode-dataset.csv"
        with open(file_path, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            pincode_objects = [
                Pincode(pincode=row["pincode"], district=row["district"], state=row["state"])
                for row in reader
            ]
            Pincode.objects.bulk_create(pincode_objects, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS("Successfully imported pincode data!"))
