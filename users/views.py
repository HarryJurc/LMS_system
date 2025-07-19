from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, filters, permissions, generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from materials.models import Course, Lesson, Subscription
from materials.serializers import CourseSerializer, LessonSerializer
from .models import Payment
from .permissions import IsModeratorOrReadOnly
from .serializers import UserSerializer, PaymentSerializer, RegisterSerializer, UserPublicSerializer
from .filters import PaymentFilter
from .services import create_stripe_product, create_stripe_price, create_checkout_session, retrieve_checkout_session
from .tasks import send_course_update_email


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

    def perform_update(self, serializer):
        instance = serializer.save()

        subscribers = Subscription.objects.filter(course=instance).select_related('user')

        for sub in subscribers:
            send_course_update_email.delay(instance.title, sub.user.email)


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsModeratorOrReadOnly]

class CreatePaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        course_id = request.data.get("course_id")
        course = get_object_or_404(Course, id=course_id)

        payment, created = Payment.objects.get_or_create(user=user, course=course)

        if not payment.stripe_product_id:
            product = create_stripe_product(name=course.name)
            payment.stripe_product_id = product['id']

        if not payment.stripe_price_id:
            unit_amount = int(course.price * 100)
            price = create_stripe_price(product_id=payment.stripe_product_id, unit_amount=unit_amount, currency="rub")
            payment.stripe_price_id = price['id']

        success_url = request.build_absolute_uri('/payment-success/')
        cancel_url = request.build_absolute_uri('/payment-cancel/')

        session = create_checkout_session(price_id=payment.stripe_price_id, success_url=success_url, cancel_url=cancel_url)
        payment.stripe_checkout_session_id = session['id']
        payment.payment_url = session['url']
        payment.save()

        return Response({
            "payment_url": payment.payment_url,
            "session_id": payment.stripe_checkout_session_id
        }, status=status.HTTP_201_CREATED)

class PaymentStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        session_id = request.query_params.get('session_id')
        if not session_id:
            return Response({"error": "session_id required"}, status=400)

        session = retrieve_checkout_session(session_id)
        return Response({
            "payment_status": session.payment_status,
            "payment_intent": session.payment_intent,
            "customer_details": session.customer_details,
        })
