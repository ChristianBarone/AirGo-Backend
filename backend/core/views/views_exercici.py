from rest_framework import viewsets
from ..models import TemplateExercici
from ..serializers import TemplateExerciciSerializer

class TemplateExerciciViewSet(viewsets.ModelViewSet):
    queryset = TemplateExercici.objects.all()
    serializer_class = TemplateExerciciSerializer