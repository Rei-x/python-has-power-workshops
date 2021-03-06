import datetime
from abc import ABC, abstractmethod
from collections import OrderedDict

from django.utils import timezone

from rest_framework import serializers
from skiing.models import SkiResort


class SkiLiftValidatorBase(ABC):
    def __init__(self, data: OrderedDict) -> None:
        self.user = data["user"]
        self.ski_resort = data["ski_resort"]
        self.date = data["date"] if "date" in data else timezone.now()

    @abstractmethod
    def validate(self) -> None:
        pass


class CheckIfUsedXTimesPerDay(SkiLiftValidatorBase):
    def validate(self) -> None:
        ski_lifts_per_day = self.get_today_ski_lift_uses()
        limit_of_uses_per_day = self.get_daily_limit()

        if ski_lifts_per_day >= limit_of_uses_per_day:
            raise serializers.ValidationError(
                f"You can use ski lift only {limit_of_uses_per_day} times per day"
            )

    def get_today_ski_lift_uses(self) -> int:
        return self.user.skilift_set.filter(date__date=self.date).count()

    def get_daily_limit(self) -> int:
        return self.user.status.daily_limit


class CheckIfUsedXTimesPerMonth(SkiLiftValidatorBase):
    def validate(self) -> None:
        ski_lifts_per_month = self.get_this_month_ski_lift_uses()
        limit_of_uses_per_month = self.get_monthly_limit()

        if ski_lifts_per_month >= limit_of_uses_per_month:
            raise serializers.ValidationError(
                f"You can use ski lift only {limit_of_uses_per_month} times per month"
            )

    def get_this_month_ski_lift_uses(self) -> int:
        return self.user.skilift_set.filter(date__month=self.date.month).count()

    def get_monthly_limit(self) -> int:
        return self.user.status.monthly_limit


class CheckIfUsedXDaysInRow(SkiLiftValidatorBase):
    def validate(self) -> None:
        if self.is_user_partner_of_ski_resort(self.ski_resort):
            return

        limit_of_uses_in_row = self.get_limit_of_uses_in_row()

        from_day = self.date - datetime.timedelta(days=limit_of_uses_in_row)
        number_of_days_that_ski_lift_was_used = (
            self.get_number_of_unique_dates_from_date_to_yesterday(from_day)
        )

        if number_of_days_that_ski_lift_was_used >= limit_of_uses_in_row:
            raise serializers.ValidationError(
                f"You can use ski lift only {limit_of_uses_in_row} days in a row"
            )

    def is_user_partner_of_ski_resort(self, ski_resort: SkiResort) -> bool:
        return self.user.partnered_ski_resorts.filter(id=ski_resort.id).exists()

    def get_limit_of_uses_in_row(self) -> int:
        return self.user.status.days_in_row_limit

    def get_number_of_unique_dates_from_date_to_yesterday(
        self, date: datetime.date
    ) -> int:
        ski_lift_datetimes_tuples = self.user.skilift_set.filter(
            date__gte=date, date__lt=self.date
        ).values_list("date")

        ski_lift_dates = [
            ski_lift_datetime[0].date()
            for ski_lift_datetime in ski_lift_datetimes_tuples
        ]

        ski_lift_unique_dates = set(ski_lift_dates)

        return len(ski_lift_unique_dates)


class CheckIfDateIsNotInFuture(SkiLiftValidatorBase):
    def validate(self) -> None:
        if timezone.now() < self.date:
            raise serializers.ValidationError("You cannot use ski lift in future")


class CheckIfUsedXTimesDuringWeekend(SkiLiftValidatorBase):
    def validate(self) -> None:
        if self.date.weekday() not in [5, 6]:
            return

        uses_in_weekend = self.get_this_weekend_ski_lift_uses()
        weekend_limit = self.get_weekend_limit()

        if uses_in_weekend >= weekend_limit != 0:
            raise serializers.ValidationError(
                f"You can use ski lift only {weekend_limit} times during weekend"
            )

    def get_this_weekend_ski_lift_uses(self) -> int:
        return self.user.skilift_set.filter(
            date__week_day__in=(1, 7),
            date__week=int(self.date.strftime("%V")),
            date__year=self.date.year,
        ).count()

    def get_weekend_limit(self) -> int:
        return self.user.status.weekend_limit
