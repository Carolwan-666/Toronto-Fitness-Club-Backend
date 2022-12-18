from .models import Studio, Class, ClassOccurrence, Subscription, Payment
from rest_framework import serializers
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from taggit.serializers import TagListSerializerField, TaggitSerializer


class ClassOccurrenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassOccurrence
        fields = ['id', 'date', 'day', 'available', 'cancelled']

class ClassSerializer(TaggitSerializer, serializers.ModelSerializer):
    keywords = TagListSerializerField()

    class Meta:
        model = Class
        fields = ['id', 'name', 'coach', 'capacity', 'description', 'keywords', 'start_time', 'end_time', 'recurrences', 'studio_id']

class StudioInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Studio
        fields = ['id', 'name']

class SubscriptionSerializer(serializers.ModelSerializer):
    studio = StudioInfoSerializer()

    class Meta:
        model = Subscription
        fields = ['id', 'frequency', 'price', 'studio']

class StudioSerializer(serializers.ModelSerializer):
    images = serializers.StringRelatedField(many=True)
    amenities = serializers.StringRelatedField(many=True)
    # subscriptions = serializers.StringRelatedField(many=True)
    subscriptions = SubscriptionSerializer(many=True)
    # classes = ClassSerializer(many=True)
    classes = serializers.StringRelatedField(many=True)

    class Meta:
        model = Studio
        fields = ['id', 'name', 'address', 'postal_code', 'lat', 'lon', 'phone_number', 'images', 'amenities', 'subscriptions', 'classes']

class PaymentSubscriptionSerializer(serializers.ModelSerializer):
    # subscription = serializers.StringRelatedField(many=True)

    class Meta:
        model = Payment
        fields = ['subscription', 'cc_number', 'cc_expiry', 'cc_code']

    # update payment method
    def update(self, instance, paymentMethod):
        instance.method = paymentMethod
        instance.save()
        return instance

    # do same payment after a specific period
    def partial_update(self, instance, date):
        instance.last_modified = date
        instance.save()
        return instance

    # Create a new payment
    def create(self, validated_data):
        sub = Subscription.objects.get(id=validated_data.get('subscription').id)
        date = validated_data.get('date')
        del validated_data['date']
        swap = validated_data.get('swap')
        del validated_data['swap']
        # paid = True if init_amount else False

        payment = Payment.objects.create(**validated_data, date=date, paid=not swap, amount=sub.price)
        payment.save()

        if not swap:
            if sub.frequency == Subscription.Plan.MONTHLY:
                payment = Payment.objects.create(**validated_data, date=date + relativedelta(months=+1), amount=sub.price)
            else:
                payment = Payment.objects.create(**validated_data, date=date + relativedelta(years=+1), amount=sub.price)
            payment.save()

        return payment

#*************************************ENROLLMENT**********************************
from studios.models import Enrollment
class EnrolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['available_class', 'all_occurrences', 'occurrence']
