from rest_framework import viewsets
from ..models import TemplateExercici
from ..serializers import TemplateExerciciSerializer


class TemplateExerciciViewSet(viewsets.ModelViewSet):
    queryset = TemplateExercici.objects.all().prefetch_related("instancies_exercici")
    serializer_class = TemplateExerciciSerializer
