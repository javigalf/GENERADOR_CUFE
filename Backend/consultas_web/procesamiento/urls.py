from django.urls import path
from .views import UploadFileView, ProgressView, DownloadFileView, RegisterView

urlpatterns = [
    path('upload/', UploadFileView.as_view(), name='upload'),
    path('progress/<str:task_id>/', ProgressView.as_view(), name='progress'),
    path('download/<str:task_id>/', DownloadFileView.as_view(), name='download'),
    path('register/', RegisterView.as_view(), name='register'),
]