import datetime

from dateutil.relativedelta import relativedelta
from django.urls import reverse
from django.utils import timezone

from rest_framework import serializers
from rest_framework.test import APITestCase
from typing import Dict, Any

from skiing.models import Company, SkiLift, SkiLiftLimit, SkiResort, User
from skiing.serializers import SkiLiftSerializer


class SkiLiftTest(APITestCase):
    url = reverse("skilift-list")

    def setUp(self) -> None:
        company = Company.objects.create(
            name="Test name", email="test_email@domain.com", city="Test city"
        )
        self.ski_resort = SkiResort.objects.create(
            name="skiresort",
            address="Test address",
            tracks_number=10,
            opened=True,
            description="Test description",
            phone_number="123456789",
            company=company,
        )
        self.default_status = SkiLiftLimit.objects.create(
            user_status="DEF",
            daily_limit=20,
            monthly_limit=100,
            days_in_row_limit=3,
            weekend_limit=2,
        )
        self.pro_status = SkiLiftLimit.objects.create(
            user_status="PRO",
            daily_limit=40,
            monthly_limit=200,
            days_in_row_limit=4,
        )
        self.user = User.objects.create_user(
            "test", password="1234", status=self.default_status
        )
        self.dictionary_ski_lift_data_without_date: Dict[str, Any] = {
            "ski_resort": 1,
            "user": 1,
        }
        self.ski_lift_data_without_date: Dict[str, Any] = {
            "ski_resort": self.ski_resort,
            "user": self.user,
        }
        self.todays_datetime = timezone.now()

    def test_creation(self) -> None:
        response = self.client.post(
            self.url, self.dictionary_ski_lift_data_without_date, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(SkiLift.objects.all().count(), 1)

    def test_date_from_future_raises_validation_error(self) -> None:
        date_from_future = self.todays_datetime + datetime.timedelta(days=1)

        ski_lift_from_future = self.ski_lift_data_without_date.copy()
        ski_lift_from_future.update({"date": date_from_future})

        with self.assertRaises(serializers.ValidationError):
            serializer = SkiLiftSerializer(data=ski_lift_from_future)
            serializer.is_valid(raise_exception=True)

    def test_exceeding_daily_limit(self) -> None:
        daily_limit = self.user.status.daily_limit

        for x in range(daily_limit):
            SkiLift.objects.create(**self.ski_lift_data_without_date)

        with self.assertRaises(serializers.ValidationError):
            serializer = SkiLiftSerializer(
                data=self.dictionary_ski_lift_data_without_date
            )
            serializer.is_valid(raise_exception=True)

        self.assertEqual(SkiLift.objects.all().count(), daily_limit)

    def test_exceeding_monthly_limit(self) -> None:
        monthly_limit = self.user.status.monthly_limit

        month_ago_date = self.todays_datetime - relativedelta(months=1)
        first_monday_of_month = self.get_first_monday_of_month(month_ago_date)
        ski_lift_date = first_monday_of_month

        ski_lift = self.ski_lift_data_without_date.copy()

        for x in range(monthly_limit):

            if ski_lift_date.weekday() >= 5:
                ski_lift_date += datetime.timedelta(days=2)

            if ski_lift_date.month is not month_ago_date.month:
                ski_lift_date = first_monday_of_month

            ski_lift.update({"date": ski_lift_date})

            SkiLift.objects.create(**ski_lift)

            ski_lift_date += datetime.timedelta(days=2)

        ski_lift_after_limit = self.dictionary_ski_lift_data_without_date.copy()
        ski_lift_after_limit.update({"date": first_monday_of_month})

        response = self.client.post(self.url, ski_lift_after_limit, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(SkiLift.objects.all().count(), monthly_limit)

    def test_exceeding_days_in_row_limit(self) -> None:
        days_in_row_limit = self.user.status.days_in_row_limit

        previous_days_list = [
            self.todays_datetime - datetime.timedelta(days=days_back)
            for days_back in range(1, days_in_row_limit + 1)
        ]

        ski_lift = self.dictionary_ski_lift_data_without_date.copy()
        for ski_lift_date in reversed(previous_days_list):
            ski_lift.update({"date": ski_lift_date})

            response = self.client.post(self.url, ski_lift, format="json")
            self.assertEqual(response.status_code, 201)

        ski_lift.update({"date": self.todays_datetime})

        response = self.client.post(self.url, ski_lift, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(SkiLift.objects.all().count(), days_in_row_limit)

    def test_exceeding_weekend_limit(self) -> None:
        weekend_limit = self.user.status.weekend_limit

        week_ago_datetime = self.todays_datetime - datetime.timedelta(weeks=1)
        past_saturday_date = self.get_past_saturday(week_ago_datetime)
        ski_lift_date = past_saturday_date

        ski_lift = self.dictionary_ski_lift_data_without_date.copy()
        for x in range(weekend_limit):
            ski_lift.update({"date": ski_lift_date})
            response = self.client.post(self.url, ski_lift, format="json")

            if ski_lift_date.weekday() == 6:
                ski_lift_date = past_saturday_date
            ski_lift_date += datetime.timedelta(days=1)

            self.assertEqual(response.status_code, 201)

        response = self.client.post(self.url, ski_lift, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(SkiLift.objects.all().count(), weekend_limit)

    def test_bypassing_days_in_row_limit_when_user_is_partner_of_ski_resort(
        self,
    ) -> None:
        days_in_row_limit = self.user.status.days_in_row_limit

        self.user.partnered_ski_resorts.add(self.ski_resort)

        previous_days_list = [
            self.todays_datetime - datetime.timedelta(days=days_back)
            for days_back in range(1, days_in_row_limit + 1)
        ]

        ski_lift = self.dictionary_ski_lift_data_without_date.copy()
        for ski_lift_date in reversed(previous_days_list):
            ski_lift.update({"date": ski_lift_date})

            response = self.client.post(self.url, ski_lift, format="json")
            self.assertEqual(response.status_code, 201)

        ski_lift.update({"date": self.todays_datetime})

        response = self.client.post(self.url, ski_lift, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(SkiLift.objects.all().count(), days_in_row_limit + 1)

    @staticmethod
    def get_past_saturday(date: datetime.datetime) -> datetime.datetime:
        days_to_add = 5 - date.weekday()
        days_to_add = days_to_add - 7 if days_to_add <= 0 else days_to_add
        return date + datetime.timedelta(days_to_add)

    @staticmethod
    def get_first_monday_of_month(date: datetime.datetime) -> datetime.datetime:
        date.replace(day=1)
        days_to_add = 1 - date.weekday()
        days_to_add = days_to_add + 7 if days_to_add <= 0 else days_to_add
        return date + datetime.timedelta(days_to_add)
