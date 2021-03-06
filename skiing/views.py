from django.http import HttpResponse, request

from pydantic import ValidationError
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Company, SkiLift, SkiResort, Tag, User
from .serializers import (
    CompanyPydantic,
    SkiLiftSerializer,
    SkiResortSerializer,
    TagSerializer,
    UserSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class SkiResortViewSet(viewsets.ModelViewSet):
    queryset = SkiResort.objects.all()
    serializer_class = SkiResortSerializer


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class SkiLiftViewSet(viewsets.ModelViewSet):
    queryset = SkiLift.objects.all()
    serializer_class = SkiLiftSerializer


class CompanyView(APIView):
    def get(self, req: request, pk: int = None) -> Response:
        if pk is None:
            response_data = [
                CompanyPydantic.from_orm(c).dict() for c in Company.objects.all()
            ]
        else:
            response_data = [
                CompanyPydantic.from_orm(Company.objects.get(pk=pk)).dict()
            ]
        return Response(response_data)

    def post(self, req: request) -> Response:
        validated_data = CompanyPydantic.parse_obj(req.data).dict()
        return Response(
            CompanyPydantic.from_orm(Company.objects.create(**validated_data)).dict()
        )

    def put(self, req: request, pk: int) -> Response:
        try:
            validated_data = CompanyPydantic.parse_obj(req.data).dict()
        except ValidationError as e:
            return Response(e.errors(), status=status.HTTP_400_BAD_REQUEST)

        Company.objects.filter(id=pk).update(**validated_data)

        return Response(validated_data)

    def delete(self, req: request, pk: int) -> Response:
        Company.objects.filter(id=pk).delete()
        return Response()


def index(request: request) -> HttpResponse:
    return HttpResponse("Hello world!")
