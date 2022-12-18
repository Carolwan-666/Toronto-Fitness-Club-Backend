from django.urls import path, include
from studios.views import StudioListView, StudioFilterView, StudioDetailView, ClassListView, ClassFilterView, ClassDetailView, AddSubscriptionView, UnsubscribeView,EnrolView,DropView, OccurrenceListView

app_name = 'studios'

urlpatterns = [
    path('all/', StudioListView.as_view(), name="studio_list"),
    path('filter/', StudioFilterView.as_view(), name="studio_filter"),
    path('<slug:pk>/details/', StudioDetailView.as_view(), name="studio_detail"),
    path('<int:studio_id>/subscribe/', AddSubscriptionView.as_view(), name="studio_subscribe"),
    path('<int:studio_id>/subscribe/cancel/', UnsubscribeView.as_view(), name="studio_subscribe_cancel"),
    path('<int:studio_id>/classes/all/', ClassListView.as_view(), name="class_list"),
    path('<int:studio_id>/classes/filter/', ClassFilterView.as_view(), name="class_filter"),
    path('class/<slug:pk>/details/', ClassDetailView.as_view(), name="class_detail"),
    path('class/<slug:pk>/occurrences/all/', OccurrenceListView.as_view(), name="class_detail"),
    path('<int:studio_id>/enroll/', EnrolView.as_view()),
    path('<int:studio_id>/drop/',DropView.as_view()),
]
