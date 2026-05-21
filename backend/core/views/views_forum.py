from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Q

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes

from ..models import Forum, ForumFavorit, Usuari, MissatgeForum
from ..serializers import (
    ForumSerializer,
    ForumFavoritSerializer,
    MissatgeForumSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=["Forum"],
        summary="Listar foros",
        responses={200: ForumSerializer(many=True)},
    ),
    create=extend_schema(
        tags=["Forum"],
        summary="Crear foro",
        responses={201: ForumSerializer},
    ),
    destroy=extend_schema(
        tags=["Forum"],
        summary="Eliminar foro",
        responses={
            204: OpenApiResponse(description="Fòrum eliminat"),
            403: OpenApiResponse(description="Només el creador pot eliminar"),
        },
    ),
)
class ForumViewSet(ModelViewSet):
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        qs = Forum.objects.select_related("creat_per").order_by("-creat_at")
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(Q(nom__icontains=search) | Q(descripcio__icontains=search))
        return qs

    def get_serializer_class(self):
        return ForumSerializer

    def perform_create(self, serializer):
        usuari = get_object_or_404(Usuari, pk=self.request.user.id)
        serializer.save(creat_per=usuari)

    def destroy(self, request, *args, **kwargs):
        forum = self.get_object()
        if forum.creat_per_id != request.user.id:
            return Response(
                {"detail": "Només el creador pot eliminar aquest fòrum."},
                status=status.HTTP_403_FORBIDDEN,
            )
        forum.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Forum"],
        summary="Historial de mensajes del foro",
        parameters=[
            OpenApiParameter(
                "limit", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
            OpenApiParameter(
                "before", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False
            ),
        ],
        responses={200: MissatgeForumSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="messages")
    def messages(self, request, pk=None):
        forum = self.get_object()
        limit = int(request.query_params.get("limit", 50))
        before = request.query_params.get("before")

        qs = forum.missatges.all()
        if before:
            qs = qs.filter(pk__lt=before)
        missatges = qs.order_by("-enviat_at")[:limit]

        serializer = MissatgeForumSerializer(reversed(list(missatges)), many=True)
        return Response(serializer.data)


class UsuariForumsFavoritsView(APIView):
    """
    GET    /api/usuaris/me/forums/             → llista favorits
    POST   /api/usuaris/me/forums/             → { "forum_id": int }
    DELETE /api/usuaris/me/forums/{forum_id}/  → treu de favorits
    """

    def _get_usuari(self, request):
        return get_object_or_404(Usuari, pk=request.user.id)

    def get(self, request):
        usuari = self._get_usuari(request)
        favorits = ForumFavorit.objects.filter(usuari=usuari).select_related("forum")
        serializer = ForumFavoritSerializer(favorits, many=True)
        return Response(serializer.data)

    def post(self, request):
        usuari = self._get_usuari(request)
        forum_id = request.data.get("forum_id")
        if not forum_id:
            return Response(
                {"detail": "Cal proporcionar forum_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        forum = get_object_or_404(Forum, pk=forum_id)
        favorit, created = ForumFavorit.objects.get_or_create(
            usuari=usuari, forum=forum
        )
        if not created:
            return Response(
                {"detail": "Aquest fòrum ja és als teus favorits."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ForumFavoritSerializer(favorit)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, forum_id):
        usuari = self._get_usuari(request)
        favorit = get_object_or_404(ForumFavorit, usuari=usuari, forum_id=forum_id)
        favorit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
