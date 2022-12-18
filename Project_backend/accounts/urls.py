from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView
from accounts.views import DetailView, EditView, RegisterView, LoginView, EnrolledView, PaymentView, EnrolledClassOccurrenceView, SubscriptionView
#LogoutView
from django.views.decorators.csrf import ensure_csrf_cookie

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', ensure_csrf_cookie(LoginView.as_view())),
    # path('logout/', LogoutView.as_view()),
    path('profile/', DetailView.as_view()),
    path('profile/edit/', ensure_csrf_cookie(EditView.as_view())),
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh', TokenRefreshView.as_view()),
    path('profile/classes/', EnrolledView.as_view()),
    path('profile/classes/<slug:pk>/enrolls/all/', EnrolledClassOccurrenceView.as_view()),
    path('profile/payments/', PaymentView.as_view()),
    path('profile/subscriptions/', SubscriptionView.as_view()),
    # path('ListHistoryView', ListHistoryView.as_view()),
    # path('AddSubscriptionView', AddSubscriptionView.as_view()),

]
