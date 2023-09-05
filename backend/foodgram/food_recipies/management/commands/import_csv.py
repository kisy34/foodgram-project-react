import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from food_recipies.models import Ingredients


class Command(BaseCommand):
    help = 'Import data from CSV files to Django.'

    path = os.path.join(settings.STATICFILES_DIRS[0], 'data')

    assignments = {
        'ingredients': Ingredients,
    }

    def handle(self, *args, **options):
        for name in self.assignments:
            count = 0
            model = self.assignments[name]
            file_path = os.path.join(self.path, f'{name}.csv')

            with open(file_path, 'r') as file:
                reader = csv.reader(file)
                headers = next(reader)
                for row in reader:
                    count += 1
                    dict = {}
                    for i, key in enumerate(headers):
                        value = row[i]
                        if value:
                            field = model._meta.get_field(key)
                            if field.is_relation:
                                related_model = field.related_model
                                value = related_model.objects.get(id=value)
                            dict[field.name] = value
                    object = model(**dict)
                    object.save()

                if count == 0:
                    message = 'нет обновленных объектов!'
                elif count % 10 == 1 and count % 100:
                    message = f'обновлен {count} объект!'
                elif 2 <= count % 10 <= 4 and (
                    count % 100 < 10 or count % 100 >= 20
                ):
                    message = f'обновлено {count} объекта!'
                else:
                    message = f'обновлено {count} объектов!'

                self.stdout.write(f'{file_path} - {model} - {message}')
