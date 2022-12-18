from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from multiselectfield import MultiSelectField
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU
from accounts.models import CustomUser
from taggit.managers import TaggableManager

# Create your models here.
class Studio(models.Model):
    name = models.CharField(null=False, max_length=200)
    address = models.CharField(max_length=200)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    postal_code = models.CharField(max_length=6)
    phone_number = PhoneNumberField()

    def __str__(self):
        return self.name

class StudioImage(models.Model):
    image = models.ImageField(upload_to='studio_images/')
    studio = models.ForeignKey(Studio, on_delete=models.CASCADE, related_name='images')

    def __str__(self):
        return self.image.url

class StudioAmenity(models.Model):
    name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    studio = models.ForeignKey(Studio, on_delete=models.CASCADE, related_name='amenities')

    class Meta:
        verbose_name_plural = 'amenities'

    def __str__(self):
        return f'{self.name} ({self.quantity})'

class Subscription(models.Model):
    class Plan(models.TextChoices):
        YEARLY = 'yearly'
        MONTHLY = 'monthly'

    frequency = models.CharField(choices=Plan.choices, max_length=7)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    studio = models.ForeignKey(Studio, on_delete=models.CASCADE, related_name='subscriptions')
    subscribers = models.ManyToManyField(CustomUser)

    def __str__(self):
        return f'${self.price} {self.frequency}'


DAYS = (('MO', 'Monday'),
        ('TU', 'Tuesday'),
        ('WE', 'Wednesday'),
        ('TH', 'Thursday'),
        ('FR', 'Friday'),
        ('SA', 'Saturday'),
        ('SU', 'Sunday'))

DAY_MAP = {'MO': MO, 'TU': TU, 'WE': WE, 'TH': TH, 'FR': FR, 'SA': SA, 'SU': SU}

def parse_day(day):
    return DAY_MAP[day]

class Class(models.Model):
    studio = models.ForeignKey(to=Studio, on_delete=models.CASCADE, null=True, related_name='classes')

    name = models.CharField(max_length=50)
    coach = models.CharField(max_length=100)  # coach should be a user
    #times = models.PositiveIntegerField()
    capacity = models.PositiveIntegerField()
    description = models.TextField(null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    recurrences = MultiSelectField(choices=DAYS, max_choices=7, max_length=20)
    end_date = models.DateField()
    keywords = TaggableManager()

    def save(self, *args, **kwargs):
        class_old = Class.objects.filter(pk=self.pk).first()
        old = set(class_old.recurrences) if class_old else set()
        curr = set(self.recurrences)
        added = curr.difference(old) if class_old else self.recurrences

        super().save(*args, **kwargs)

        if class_old:
            removed = old.difference(curr) # dates removed
            same = old.intersection(curr) # dates maintained

            for day in removed: # remove occurrences on deselected days
                f = ClassOccurrence.objects.filter(class_fk=self.pk, day=day).delete()

            if self.end_date < class_old.end_date: # remove occurrences if end date shrinks
                ClassOccurrence.objects.filter(class_fk=self.pk, day__in=same, date__range=[self.end_date + timedelta(days=1), class_old.end_date]).delete()
            elif self.end_date > class_old.end_date: # add occurrences if end date expands
                enrolled = Enrollment.objects.filter(available_class=self.pk).values_list('user').distinct()
                for day in same:
                    weekday = parse_day(day)
                    start = class_old.end_date + timedelta(days=1) + relativedelta(weekday=weekday)

                    while start <= self.end_date:
                        occur = ClassOccurrence.objects.create(date=start, day=day, available=self.capacity, cancelled=False, class_fk=self)
                        occur.save()
                        for user in enrolled:
                            enrollment = Enrollment.objects.create(available_class=self, occurrence=occur)
                            enrollment.user.set(user)
                            enrollment.save()
                            occur.available = occur.available - 1
                        occur.save()
                        
                        start += timedelta(weeks=1)

        now = datetime.now().date()
        for day in added: # add occurrences on newly selected days
            weekday = parse_day(day)
            start = now + relativedelta(weekday=weekday)
            while start <= self.end_date:
                occur = ClassOccurrence.objects.create(date=start, day=day, available=self.capacity, cancelled=False, class_fk=self)
                occur.save()
                start += timedelta(weeks=1)

    class Meta:
        verbose_name_plural = 'classes'

    def __str__(self):
        return f'{self.name} by coach {self.coach}'

class ClassOccurrenceManager(models.Manager):
    def create_classoccurrence(self, date, day, available, cancelled, class_fk):
        class_o = self.create(date=date, day=day, available=available, cancelled=cancelled, class_fk=class_fk)
        return class_o

class ClassOccurrence(models.Model):
    date = models.DateField()
    day = models.CharField(max_length=2)
    available = models.PositiveIntegerField()
    cancelled = models.BooleanField()
    class_fk = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='occurrences')

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f'{self.class_fk} on {self.date}'

    objects = ClassOccurrenceManager()

from creditcards.models import CardNumberField, CardExpiryField, SecurityCodeField

class PaymentManager(models.Manager):
    def create_payment(self, subscriber, subscription, cc_number, cc_expiry, cc_code, date):
        payment = self.create(subscriber=subscriber, subscription=subscription, cc_number=cc_number, cc_expiry=cc_expiry, cc_code=cc_code, date=date)
        return payment

class Payment(models.Model):
    subscriber = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payments')
    cc_number = CardNumberField() # 'card number'
    cc_expiry = CardExpiryField() # _('expiration date')
    cc_code = SecurityCodeField() # _('security code')
    date = models.DateField()
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.subscription.price} on {self.date}'

    objects = PaymentManager()


#*************************************ENROLLMENT**********************************
class EnrollmentManager(models.Manager):
    def create_enrollment(self, available_class, all_occurrences, occurrence):
        enrollment = self.create(available_class=available_class, all_occurrences=all_occurrences, occurrence=occurrence)
        return enrollment

class Enrollment(models.Model):
    user = models.ManyToManyField(to=CustomUser)
    available_class = models.ForeignKey(to=Class, on_delete=models.CASCADE, related_name='enrollments')
    all_occurrences = models.BooleanField(null=True, blank=True)
    occurrence = models.ForeignKey(null=True, blank=True, to=ClassOccurrence, on_delete=models.CASCADE, related_name='enrollments')

    def __str__(self):
        return f'{self.user} {self.available_class}'

    objects = EnrollmentManager()
