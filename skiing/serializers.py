from collections import OrderedDict

from pydantic import BaseModel, EmailStr
from rest_framework import serializers

from .models import SkiLift, SkiResort, Tag, User
from .validators import SkiLiftValidator


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class SkiResortSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(min_value=1, max_value=10, allow_null=True)
    tags = TagSerializer(many=True)
    company_id = serializers.IntegerField()

    class Meta:
        model = SkiResort
        fields = "__all__"

    def create(self, validated_data: OrderedDict) -> SkiResort:
        tags = validated_data.pop("tags")
        ski_resort = SkiResort.objects.create(**validated_data)
        for tag in tags:
            ski_resort.tags.create(**tag)
        return ski_resort


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "password",
            "partnered_ski_resorts",
            "status",
        ]

    def create(self, validated_data: OrderedDict) -> User:
        partnered_ski_resorts = []

        if "partnered_ski_resorts" in validated_data:
            partnered_ski_resorts = validated_data.pop("partnered_ski_resorts")

        user = User.objects.create_user(**validated_data)

        for ski_resort in partnered_ski_resorts:
            user.partnered_ski_resorts.add(ski_resort)

        return user


class SkiLiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkiLift
        fields = "__all__"

    def validate(self, data: OrderedDict) -> OrderedDict:
        return SkiLiftValidator.validate(data)


class CompanyPydantic(BaseModel):
    name: str
    email: EmailStr
    city: str

    class Config:
        orm_mode = True
