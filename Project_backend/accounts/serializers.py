from rest_framework import serializers
# Reference:
# https://www.django-rest-framework.org/api-guide/serializers/
# https://www.django-rest-framework.org/api-guide/fields/
from rest_framework.exceptions import ValidationError
from accounts.models import CustomUser
from studios.serializers import SubscriptionSerializer
#Reference:
#https://www.django-rest-framework.org/api-guide/authentication/
#https://www.django-rest-framework.org/api-guide/serializers/
#https://stackoverflow.com/questions/16906515/how-can-i-get-the-username-of-the-logged-in-user-in-django



class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ['avatar', 'phone_number', 'first_name', 'last_name', 'email', 'username']


class EditSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    password2 = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = CustomUser
        fields = ['username', 'avatar', 'phone_number',
                  'first_name', 'last_name', 'email', 'password', 'password2']
        optional_fields = ['password', 'password2']
    
    
    # def save(self, *args, **kwargs):
    #     kwargs["commit"]=False

  

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if validated_data.get('password'):
            user.set_password(validated_data['password'])
        # instance.username = "hhh"
        instance.username = validated_data.get('username', instance.username)
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.email = validated_data.get('email', instance.email)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance
        # return instance 


    def validate(self, data):
        # password = data['password']
        password = data.get('password')
        password2 = data.get('password2')
        if not password or not password2:
            return data

        if 0 <= len(password) < 8:
            raise serializers.ValidationError("Password is invalid.")
        elif password != password2:
            raise serializers.ValidationError("Password does not match.")
        return data


class GenerateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    password2 = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = CustomUser
        fields = ['username','first_name','last_name', 'avatar', 'phone_number',
                  'email','password', 'password2']
    def create(self, validated_data):
        user = CustomUser(
                        avatar=validated_data['avatar'],
                        email=validated_data['email'],
                        username=validated_data['username'],
                        phone_number=validated_data['phone_number'],
                        first_name=validated_data['first_name'],
                        last_name=validated_data['last_name'],
                        password=validated_data['password']
                    )
        user.set_password(validated_data['password'])
        user.save()
        return user
    
    def validate(self, data):
        if 0 <= len(data['password']) < 8:
            raise serializers.ValidationError("This password is too short. It must contain at least 8 characters.")
        elif data['password'] != data['password2'] or data['password'] == '':
            raise serializers.ValidationError("The two password fields didn't match")
        return data

from studios.models import Enrollment, Class
from studios.serializers import ClassOccurrenceSerializer

class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ['id', 'studio_id', 'name', 'coach']

class EnroledClassSerializer(serializers.ModelSerializer):
    available_class = ClassSerializer()
    occurrence = ClassOccurrenceSerializer()

    class Meta:
        model = Enrollment
        fields = ['available_class', 'all_occurrences', 'occurrence']

from studios.models import Payment
class PaymentSerializer(serializers.ModelSerializer):
    subscription = SubscriptionSerializer()
    
    class Meta:
        model = Payment
        fields = ['subscription', 'date', 'amount', 'paid', 'cc_number', 'cc_expiry', 'cc_code']
