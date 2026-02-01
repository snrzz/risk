from django.urls import path
from .views import TaskListView, TaskExecuteView, TaskStatusView

urlpatterns = [
    path('', TaskListView.as_view(), name='task-list'),
    path('execute/', TaskExecuteView.as_view(), name='task-execute'),
    path('status/', TaskStatusView.as_view(), name='task-status'),
]
