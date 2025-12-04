from rest_framework import viewsets
from .models import Item
from .serializers import ItemSerializer
from rest_framework.response import Response
from rest_framework import status

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

    def destroy(self, request, *args, **kwargs):
        """Soft-delete: mark item inactive so dashboards can log the event."""
        instance = self.get_object()
        instance.is_active = False
        try:
            instance.updated_by = request.user
        except Exception:
            pass
        instance.save(update_fields=["is_active", "updated_at", "updated_by"])
        return Response(status=status.HTTP_204_NO_CONTENT)
