from rest_framework import viewsets, filters, permissions, generics
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied

from materials.models import Course, Lesson
from materials.serializers import CourseSerializer, LessonSerializer
from .models import Payment
from .permissions import IsModeratorOrReadOnly
from .serializers import UserSerializer, PaymentSerializer, RegisterSerializer, UserPublicSerializer
from .filters import PaymentFilter
from django.contrib.auth import get_user_model



User = get_user_model()

class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PaymentFilter
    ordering_fields = ['payment_date']
    ordering = ['-payment_date']


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.user.id == self.kwargs.get('pk', None) or self.action == 'create':
            return UserSerializer
        if self.action in ['retrieve', 'list']:
            return UserPublicSerializer
        return UserSerializer

    def get_queryset(self):
        return User.objects.all()

    def perform_update(self, serializer):
        if self.get_object() != self.request.user:
            raise PermissionDenied("You can only edit your own profile.")
        serializer.save()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsModeratorOrReadOnly]


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsModeratorOrReadOnly]

