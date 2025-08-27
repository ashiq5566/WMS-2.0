# stakeholders/management/commands/import_stakeholders.py
import os
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from accounts.models import Stakeholder   

class Command(BaseCommand):
    help = "Import stakeholders from Excel file"

    # def add_arguments(self, parser):
    #     parser.add_argument("~/data/stakeholders", type=str, help="Path to the .xlsx file")

    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, "data", "stakeholders.xlsx")

        df = pd.read_excel(file_path)

        for _, row in df.iterrows():
            stakeholder, created = Stakeholder.objects.update_or_create(
                stakeholder_id=row["Stakeholder ID"],
                defaults={
                    "name": row["Name"],
                    "address": row["Address"],
                    "mobile": str(row["Mobile"]),
                    "email": row["Email"],
                    "type": row["Type"],
                    "opening_balance": row["Opening Balance"],
                },
            )
            status = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{status} {stakeholder.stakeholder_id}"))
