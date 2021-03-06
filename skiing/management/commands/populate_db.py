from django.core.management.base import BaseCommand

from faker import Faker
from skiing.models import Company, SkiResort, Tag


class Command(BaseCommand):
    help = "Populates database"

    def handle(self, *args, **kwargs) -> None:
        fake = Faker("pl-PL")
        for i in range(0, 10):
            company = Company.objects.create(
                name=fake.company(), email=fake.email(), city=fake.city()
            )

            for y in range(10):
                skiresort = SkiResort.objects.create(
                    name=fake.company(),
                    address=fake.address(),
                    tracks_number=4,
                    opened=fake.boolean(),
                    description=fake.paragraph(),
                    rating=6,
                    phone_number=fake.phone_number(),
                    company=company,
                )
                for x in range(10):
                    skiresort.tags.add(Tag.objects.create(name=fake.word()))
