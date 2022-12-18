from django.contrib import admin
from django.urls import reverse
from django.utils.html import mark_safe
from django import forms
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU
from .models import Studio, StudioImage, StudioAmenity, Subscription, Class, ClassOccurrence, Payment, Enrollment

# Register your models here.

class SubscriptionAdminInline(admin.TabularInline):
    model = Subscription
    extra = 2
    exclude = ['subscribers']

class StudioAmenityAdmin(admin.TabularInline):
    model = StudioAmenity
    extra = 1

class StudioImageAdmin(admin.TabularInline):
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width=300>')
        else:
            return 'No Image'

    model = StudioImage
    extra = 2
    readonly_fields = ['image_preview']

class ClassFormInline(forms.ModelForm):
    class Meta:
        model = Class
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        if start_time and end_time and start_time > end_time:
            raise forms.ValidationError({'start_time': "Start time must be less than end time"})

        end_date = cleaned_data.get('end_date')
        now = datetime.now().date()
        if end_date and end_date < now:
            raise forms.ValidationError({'end_date': 'End date cannot be in the past'})

        return cleaned_data

class ClassAdminInline(admin.TabularInline):
    def class_link(self, obj):
        if obj.pk:
            return mark_safe('<a href="{}">See Class</a>'.format(
                reverse(f"admin:{obj._meta.app_label}_class_change", args=(obj.pk,))
            ))
        else:
            return 'N/A'

    model = Class
    form = ClassFormInline
    extra = 1
    readonly_fields = ['class_link']

class ClassOccurrenceAdmin(admin.TabularInline):
    model = ClassOccurrence
    extra = 1
    readonly_fields = ['date', 'day', 'available']

class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        if start_time and end_time and start_time > end_time:
            raise forms.ValidationError({'start_time': "Start time must be less than end time"})

        end_date = cleaned_data.get('end_date')
        if end_date and end_date < datetime.now().date():
            raise forms.ValidationError({'end_date': 'End date cannot be in the past'})

        return cleaned_data

class ClassAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    form = ClassForm
    inlines = [ClassOccurrenceAdmin]

class StudioAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'postal_code']
    inlines = [StudioImageAdmin, StudioAmenityAdmin, SubscriptionAdminInline, ClassAdminInline]


admin.site.register(Studio, StudioAdmin)
admin.site.register(Class, ClassAdmin)
admin.site.register(Payment)
admin.site.register(Subscription)
admin.site.register(Enrollment)