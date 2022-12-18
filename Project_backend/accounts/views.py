from datetime import datetime
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from rest_framework import status, authentication, generics
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import RetrieveAPIView, ListAPIView, CreateAPIView, UpdateAPIView
from django.shortcuts import get_object_or_404
#Reference:
#https://www.django-rest-framework.org/tutorial/3-class-based-views/
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.models import CustomUser
from accounts.serializers import UserSerializer, GenerateUserSerializer,EnroledClassSerializer
from accounts.serializers import EditSerializer, PaymentSerializer, SubscriptionSerializer
from studios.models import Enrollment, Payment, Subscription
from datetime import datetime


class RegisterView(CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = GenerateUserSerializer

class DetailView(RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    def get_object(self):
        return self.request.user


class EditView(RetrieveAPIView, UpdateAPIView):
    serializer_class = EditSerializer
    permission_classes = [IsAuthenticated]
    

    def get_object(self):
        return self.request.user


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        # print(user)
        # print(CustomUser.objects.filter(username=request.data['username']))
        if not user:
            user = CustomUser.objects.filter(username=request.data['username'])
            if len(user) == 0:
                return Response({'response': 'User does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'response': 'Password does not match.'}, status=status.HTTP_400_BAD_REQUEST)
        login(request, user)
        return Response({'response': 'Successfully login!'}, status=status.HTTP_202_ACCEPTED)


# class LogoutView(APIView):
#     def get(self, request, *args, **kwargs):
#         auth = request.user.is_authenticated
#         if not auth:
#             return Response({'response': 'Login first, please!'}, status=status.HTTP_400_BAD_REQUEST)
#         logout(request)
#         return Response({'response': 'Successfully logout !'}, status=status.HTTP_202_ACCEPTED)


class EnrolledView(generics.ListAPIView):
    serializer_class = EnroledClassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Enrollment.objects.all()
        # print(1, len(queryset))
        user = self.request.user
        queryset = queryset.filter(user=user).order_by('occurrence__date')

        past = self.request.query_params.get('past')
        if past:
            queryset = queryset.filter(occurrence__date__lt=datetime.now().date())
        else:
            queryset = queryset.filter(occurrence__date__gte=datetime.now().date())
        # print(2, len(queryset))
        # print(self.request.user)
        return queryset

class EnrolledClassOccurrenceView(generics.ListAPIView):
    serializer_class = EnroledClassSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user, available_class_id=self.kwargs['pk'], occurrence__date__gte=datetime.now().date()).order_by('occurrence__date')

class SubscriptionView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subscription.objects.filter(subscribers=self.request.user).order_by('studio_id')

class PaymentView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(subscriber=self.request.user).order_by('date')
