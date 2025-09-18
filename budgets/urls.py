from django.urls import path
from . import views

app_name = 'budgets'

urlpatterns = [
    # Budget CRUD operations
    path('', views.BudgetListCreateView.as_view(), name='budget-list-create'),
    path('<int:pk>/', views.BudgetDetailView.as_view(), name='budget-detail'),
    
    # Budget analytics and summaries
    path('summary/', views.budget_summary, name='budget-summary'),
    path('categories/', views.budget_categories, name='budget-categories'),
    path('recommendations/', views.budget_recommendations, name='budget-recommendations'),
    path('category-stats/', views.category_stats, name='category-stats'),
    
    # Budget alerts
    path('alerts/', views.BudgetAlertListView.as_view(), name='budget-alerts'),
    path('alerts/<int:alert_id>/read/', views.mark_alert_read, name='mark-alert-read'),
    
    # Budget templates
    path('templates/', views.BudgetTemplateListView.as_view(), name='budget-templates'),
]