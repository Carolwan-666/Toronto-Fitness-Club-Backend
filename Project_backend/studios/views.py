from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch, Q
from .models import Studio, Class, ClassOccurrence, Subscription, Payment, Enrollment
from rest_framework import viewsets, permissions, generics, filters, serializers
from .serializers import ClassOccurrenceSerializer, StudioSerializer, ClassSerializer, PaymentSubscriptionSerializer,EnrolSerializer
import math
from decimal import Decimal, getcontext
from datetime import datetime
from dateutil.relativedelta import relativedelta
from rest_framework.generics import CreateAPIView


# Create your views here.
class StudioListView(generics.ListAPIView):
    serializer_class = StudioSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'amenities__name', 'classes__name', 'classes__coach']
    # permission_classes = []

    def get_queryset(self):
        queryset = Studio.objects.all()

        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)

        amenity = self.request.query_params.get('amenity')
        if amenity:
            queryset = queryset.filter(amenities__name__icontains=amenity)

        class_name = self.request.query_params.get('class')
        if class_name:
            queryset = queryset.filter(classes__name__icontains=class_name)

        coach = self.request.query_params.get('coach')
        if coach:
            queryset = queryset.filter(classes__coach__icontains=coach)

        lat = self.request.query_params.get('lat')
        lon = self.request.query_params.get('lon')

        if lat and lon:
            queryset = sorted(queryset, key=lambda x: math.sqrt((Decimal(lat) - x.lat) ** 2 + (Decimal(lon) - x.lon) ** 2))
        else:
            queryset = queryset.order_by('id')

        return queryset

class StudioFilterView(generics.ListAPIView):
    serializer_class = StudioSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'amenities__name', 'classes__name', 'classes__coach']
    ordering_fields = '__all__'

    def get_queryset(self):
        queryset = Studio.objects.all()

        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)

        amenity = self.request.query_params.get('amenity')
        if amenity:
            queryset = queryset.filter(amenities__name__icontains=amenity)

        class_name = self.request.query_params.get('class')
        if class_name:
            queryset = queryset.filter(classes__name__icontains=class_name)

        coach = self.request.query_params.get('coach')
        if coach:
            queryset = queryset.filter(classes__coach__icontains=coach)

        return queryset

class StudioDetailView(generics.RetrieveAPIView):
    queryset = Studio.objects.all()
    serializer_class = StudioSerializer

# As a user, I can subscribe to one of the options, do first payment and another payment beginning of their period.
class AddSubscriptionView(generics.CreateAPIView, generics.UpdateAPIView):
    serializer_class = PaymentSubscriptionSerializer

    # Make sure user successfully signed in
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Payment.objects.filter(subscriber=self.request.user).first()
        return queryset

    def get_object(self):
        return self.get_queryset()

    def perform_update(self, serializer):
        sub = Subscription.objects.get(id=self.request.data['subscription'])
        payments = Payment.objects.filter(subscriber=self.request.user, subscription__studio_id=sub.studio.id, paid=False)
        cc_number = self.request.data.get('cc_number')
        cc_expiry = self.request.data.get('cc_expiry')
        cc_code = self.request.data.get('cc_code')
        payments.update(cc_number=cc_number, cc_expiry=cc_expiry, cc_code=cc_code)

    def perform_create(self, serializer):
        sub = Subscription.objects.get(id=self.request.data['subscription'])

        if sub:
            studio = Studio.objects.get(id=sub.studio.id)
            others = studio.subscriptions.filter(~Q(id=sub.id), subscribers=self.request.user)
            if studio.id != self.kwargs['studio_id']:
                raise serializers.ValidationError({'detail':'Subscription plan does not belong to studio'})

            date = datetime.now().date()
            swap = False
            if sub.subscribers.filter(username=self.request.user.username).count():
                raise serializers.ValidationError({'detail':'You have already subscribed to this plan'})
            elif others.count():
                for other in others: # remove user from other subscription plans
                    other.subscribers.remove(self.request.user)

                payments = Payment.objects.filter(subscriber=self.request.user, subscription__studio_id=studio.id, paid=False)
                for payment in payments:
                    payment.delete() # delete future payments

            last_payment = Payment.objects.filter(subscriber=self.request.user, subscription__studio_id=self.kwargs['studio_id'], paid=True).order_by('-date')
            if last_payment.count() > 0:
                last_payment = last_payment.first()

                if last_payment.subscription.frequency == Subscription.Plan.MONTHLY:
                    date = last_payment.date + relativedelta(months=+1)
                else:
                    date = last_payment.date + relativedelta(years=+1)
                swap = True

            sub.subscribers.add(self.request.user)
            serializer.save(subscriber=self.request.user, date=date, swap=swap)
        else:
            raise serializers.ValidationError({'detail':'Studio not found'})

class UnsubscribeView(generics.DestroyAPIView):
    queryset = Subscription.objects.all()
    serializer_class = PaymentSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Subscription.objects.get(studio_id=self.kwargs['studio_id'], subscribers=self.request.user)
        return queryset

    def get_object(self):
        return self.get_queryset()

    def perform_destroy(self, serializer):
        sub = Subscription.objects.get(studio_id=self.kwargs['studio_id'], subscribers=self.request.user)

        if not sub:
            raise serializers.ValidationError({'detail':'No subscription with current studio'})

        sub.subscribers.remove(self.request.user) # remove user from subscription
        Payment.objects.filter(subscriber=self.request.user, subscription__studio_id=self.kwargs['studio_id'], paid=False).delete() # remove Future payments for subscription
        # remove user from enrolled classes after current period ends
        last_payment = Payment.objects.filter(subscriber=self.request.user, subscription__studio_id=self.kwargs['studio_id'], paid=True).order_by('-date').first()
        period = last_payment.date
        if last_payment.subscription.frequency == Subscription.Plan.MONTHLY:
            period += relativedelta(months=+1)
        else:
            period += relativedelta(years=+1)

        enrollments = Enrollment.objects.filter(user=self.request.user, available_class__studio=sub.studio, occurrence__date__gte=period)

        for enrollment in enrollments:
            enrollment.occurrence.available = enrollment.occurrence.available + 1
            enrollment.occurrence.save()
        enrollments.delete()


class ClassListView(generics.ListAPIView):
    def get_queryset(self):
        queryset = Class.objects.filter(studio=self.kwargs['studio_id'])
        queryset = queryset.prefetch_related(Prefetch('occurrences', queryset=ClassOccurrence.objects.filter(date__gte=datetime.now().date(), cancelled=False)))
        return queryset

    serializer_class = ClassSerializer

class OccurrenceListView(generics.ListAPIView):
    def get_queryset(self):
        queryset = ClassOccurrence.objects.filter(class_fk=self.kwargs['pk'])
        queryset = queryset.filter(date__gte=datetime.now().date(), cancelled=False)
        return queryset

    serializer_class = ClassOccurrenceSerializer

class ClassFilterView(generics.ListAPIView):
    serializer_class = ClassSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'coach']
    ordering_fields = ['name', 'coach', 'capacity', 'start_time', 'end_time']

    def get_queryset(self):
        queryset = Class.objects.filter(studio=self.kwargs['studio_id'])

        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)

        coach = self.request.query_params.get('coach')
        if coach:
            queryset = queryset.filter(coach__icontains=coach)

        start_time = self.request.query_params.get('start_time')
        if start_time:
            queryset = queryset.filter(start_time__gte=start_time)

        end_time = self.request.query_params.get('end_time')
        if end_time:
            queryset = queryset.filter(start_time__gte=end_time)

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.prefetch_related(Prefetch('occurrences', queryset=ClassOccurrence.objects.filter(date__range=[start_date, end_date], cancelled=False)))
        elif start_date and not end_date:
            queryset = queryset.prefetch_related(Prefetch('occurrences', queryset=ClassOccurrence.objects.filter(date__gte=start_date, cancelled=False)))
        elif not start_date and end_date:
            queryset = queryset.prefetch_related(Prefetch('occurrences', queryset=ClassOccurrence.objects.filter(date__lte=end_date, cancelled=False)))

        return queryset

class ClassDetailView(generics.RetrieveAPIView):
    queryset = Class.objects.all().prefetch_related(Prefetch('occurrences', queryset=ClassOccurrence.objects.filter(date__gte=datetime.now().date(), cancelled=False)))
    serializer_class = ClassSerializer


#*************************************ENROLLMENT**********************************
from rest_framework import status
from rest_framework.response import Response

class EnrolView(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EnrolSerializer
    def get(self, request, *args, **kwargs):
#         print(5555)
#         print(f"args={args}")
#         print(f"kwargs={kwargs}")
        return Response({})
    #
    def post(self, request, *args, **kwargs):
        # print(6666)
        classes = Class.objects.filter(studio=self.kwargs['studio_id'])
        class_id = int(self.request.data['available_class'])
        enroll_all = self.request.data.get('all_occurrences')
        ocurrence_id = self.request.data.get('occurrence')

        if not (enroll_all or ocurrence_id):
            raise serializers.ValidationError({'detail':'Please provide a valid occurrence or all_occurrences.'})

        if classes.count() == 0:
            raise serializers.ValidationError({'detail':'Studio not found'})

        last_payment = Payment.objects.filter(subscriber=self.request.user, subscription__studio_id=self.kwargs['studio_id']).order_by('-date')
        if last_payment.count() == 0:
            raise serializers.ValidationError({'response': 'You must subscribed to the studio to enroll in classes.'})
        last_payment = last_payment.first()
        period = last_payment.date
        if last_payment.subscription.frequency == Subscription.Plan.MONTHLY:
            period += relativedelta(months=+1)
        else:
            period += relativedelta(years=+1)

        ocurrences = ClassOccurrence.objects.filter(class_fk_id=class_id)
        if ocurrences.count() == 0:
            return Response({'response': 'The class is not in current studio.'}, status=status.HTTP_400_BAD_REQUEST)

        for ocurrence in ocurrences:
            enrolled = Enrollment.objects.filter(user=self.request.user, occurrence=ocurrence)
            if ocurrence_id and int(ocurrence.id) != int(ocurrence_id):
                continue
            if ocurrence_id:
                if period < ocurrence.date:
                    raise serializers.ValidationError({'response': 'Your last payment does not cover this period'})
                elif enrolled.count() != 0 or int(ocurrence.available) == 0:
                    return Response({'response': 'No available space for the ocurrence or the user already enrolled.'}, status=status.HTTP_400_BAD_REQUEST)
            if period >= ocurrence.date and enrolled.count() == 0 and int(ocurrence.available) > 0:
                enrollment = Enrollment.objects.create(available_class_id=class_id, occurrence=ocurrence)
                enrollment.save()
                enrollment.user.add(self.request.user)
                ocurrence.available = int(ocurrence.available) - 1
                ocurrence.save()
                if enroll_all:
                    continue
                return Response({'available_class': class_id, 'occurence': ocurrence.id})
        if not enroll_all and ocurrence_id:
            return Response({'response': 'The ocurrence does match to the class.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'available_class': class_id, 'all_occurrences': True})


class DropView(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = EnrolSerializer

    def get(self, request, *args, **kwargs):
        return Response({})

    #
    def post(self, request, *args, **kwargs):
        # print(6666)
        class_id = int(self.request.data['available_class'])
        drop_all = self.request.data.get('all_occurrences')
        ocurrence_id = self.request.data.get('occurrence')

        if not (drop_all or ocurrence_id):
            raise serializers.ValidationError({'detail':'Please provide a valid occurrence or all_occurrences.'})

        if Class.objects.filter(studio=self.kwargs['studio_id']).count() == 0:
            raise serializers.ValidationError({'detail':'Studio not found'})

        ocurrences = ClassOccurrence.objects.filter(class_fk_id=class_id)
        if ocurrence_id and not drop_all:
            for ocurrence in ocurrences:
                enrolled = Enrollment.objects.filter(user=self.request.user, occurrence=ocurrence)
                if int(ocurrence.id) == int(ocurrence_id) and enrolled.count() > 0:
                    enrolled = enrolled.first()
                    enrolled.delete()
                    ocurrence.available = int(ocurrence.available) + 1
                    ocurrence.save()
                    return Response({'available_class': class_id, 'occurence': ocurrence.id})
                elif int(ocurrence.id) == ocurrence_id:
                    return Response({'response': ' User has not enrolled in this class occurrence yet'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'response': 'The class is not in current studio or the ocurrence does match to the class.'}, status=status.HTTP_400_BAD_REQUEST)

        for ocurrence in ocurrences:
            enrolled = Enrollment.objects.filter(user=self.request.user, occurrence=ocurrence)
            if enrolled.count() > 0:
                enrolled = enrolled.first()
                enrolled.delete()
                ocurrence.available = int(ocurrence.available) + 1
                ocurrence.save()
        return Response({'available_class': class_id, 'all_occurrences': True})
