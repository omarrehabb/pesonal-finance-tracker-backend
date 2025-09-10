# budgets/views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import calendar

from .models import Budget, BudgetAlert, BudgetTemplate
from .serializers import (
    BudgetSerializer, BudgetSummarySerializer, BudgetAlertSerializer,
    BudgetTemplateSerializer, BudgetRecommendationSerializer,
    CategoryStatsSerializer
)
from transactions.models import Transaction


class BudgetListCreateView(generics.ListCreateAPIView):
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user, is_active=True)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Add date parameters for calculations
        context['year'] = int(self.request.query_params.get('year', timezone.now().year))
        context['month'] = int(self.request.query_params.get('month', timezone.now().month))
        context['week'] = self.request.query_params.get('week')
        return context


class BudgetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = BudgetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['year'] = int(self.request.query_params.get('year', timezone.now().year))
        context['month'] = int(self.request.query_params.get('month', timezone.now().month))
        context['week'] = self.request.query_params.get('week')
        return context
    
    # def perform_destroy(self, instance):
    #     # Soft delete - mark as inactive instead of actual deletion
    #     instance.is_active = False
    #     instance.save()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def budget_summary(request):
    """Get comprehensive budget summary for a specific period"""
    user = request.user
    year = int(request.query_params.get('year', timezone.now().year))
    month = int(request.query_params.get('month', timezone.now().month))
    week = request.query_params.get('week')
    period = request.query_params.get('period', 'monthly')
    
    # Get user's active budgets
    budgets = Budget.objects.filter(user=user, is_active=True, period=period)
    
    if not budgets.exists():
        return Response({
            'total_budgets': 0,
            'total_budget_amount': '0.00',
            'total_spent': '0.00',
            'total_remaining': '0.00',
            'average_percentage_used': 0,
            'budgets_over_limit': 0,
            'budgets_at_warning': 0,
            'budgets_on_track': 0,
            'period': period,
            'year': year,
            'month': month if period == 'monthly' else None,
            'week': week if period == 'weekly' else None
        })
    
    # Calculate summary statistics
    total_budget_amount = Decimal('0.00')
    total_spent = Decimal('0.00')
    total_remaining = Decimal('0.00')
    percentage_sum = 0
    budgets_over_limit = 0
    budgets_at_warning = 0
    budgets_on_track = 0
    
    for budget in budgets:
        spent = budget.get_spent_amount(year, month, week)
        remaining = budget.get_remaining_amount(year, month, week)
        percentage = budget.get_percentage_used(year, month, week)
        status = budget.get_status(year, month, week)
        
        total_budget_amount += budget.amount
        total_spent += spent
        total_remaining += remaining
        percentage_sum += percentage
        
        if status == 'over':
            budgets_over_limit += 1
        elif status in ['warning', 'caution']:
            budgets_at_warning += 1
        else:
            budgets_on_track += 1
    
    average_percentage = percentage_sum / len(budgets) if budgets else 0
    
    summary_data = {
        'total_budgets': len(budgets),
        'total_budget_amount': total_budget_amount,
        'total_spent': total_spent,
        'total_remaining': total_remaining,
        'average_percentage_used': round(average_percentage, 1),
        'budgets_over_limit': budgets_over_limit,
        'budgets_at_warning': budgets_at_warning,
        'budgets_on_track': budgets_on_track,
        'period': period,
        'year': year,
        'month': month if period == 'monthly' else None,
        'week': week if period == 'weekly' else None
    }
    
    serializer = BudgetSummarySerializer(summary_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def budget_categories(request):
    """Get available categories from user's transactions"""
    user = request.user
    
    # Get categories from user's expense transactions
    expense_categories = Transaction.objects.filter(
        user=user,
        transaction_type='expense'
    ).values_list('category', flat=True).distinct().order_by('category')
    
    # Remove empty/null categories
    categories = [cat for cat in expense_categories if cat and cat.strip()]
    
    # If no categories, provide defaults
    if not categories:
        categories = ['Food', 'Dining', 'Travel', 'Entertainment', 'Transportation', 'Shopping', 'Bills', 'Healthcare', 'Other']
    
    return Response({'categories': categories})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def budget_recommendations(request):
    """Generate budget recommendations based on spending history"""
    user = request.user
    months = int(request.query_params.get('months', 3))
    
    # Calculate date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=months * 30)  # Approximate month calculation
    
    # Get transactions in the period
    transactions = Transaction.objects.filter(
        user=user,
        transaction_type='expense',
        date__range=[start_date, end_date]
    ).exclude(category__isnull=True).exclude(category='')
    
    if not transactions.exists():
        return Response({'recommendations': []})
    
    # Group by category and calculate stats
    category_stats = transactions.values('category').annotate(
        total_spent=Sum('amount'),
        transaction_count=Count('id'),
        avg_transaction=Avg('amount')
    ).order_by('-total_spent')
    
    recommendations = []
    for stat in category_stats:
        category = stat['category']
        total_spent = stat['total_spent']
        transaction_count = stat['transaction_count']
        
        # Calculate average monthly spending
        average_monthly = total_spent / months
        
        # Add 10% buffer for recommended budget
        recommended_amount = average_monthly * Decimal('1.1')
        
        # Determine confidence level
        confidence = 'high' if transaction_count >= 10 else 'medium' if transaction_count >= 5 else 'low'
        
        recommendations.append({
            'category': category,
            'recommended_amount': round(recommended_amount, 2),
            'average_spending': round(average_monthly, 2),
            'total_spent': total_spent,
            'confidence': confidence,
            'months_analyzed': months,
            'transaction_count': transaction_count
        })
    
    serializer = BudgetRecommendationSerializer(recommendations, many=True)
    return Response({'recommendations': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_stats(request):
    """Get spending statistics by category with budget comparison"""
    user = request.user
    year = int(request.query_params.get('year', timezone.now().year))
    month = int(request.query_params.get('month', timezone.now().month))
    
    # Get transactions for the period
    transactions = Transaction.objects.filter(
        user=user,
        transaction_type='expense',
        date__year=year,
        date__month=month
    ).exclude(category__isnull=True).exclude(category='')
    
    # Group by category
    category_spending = transactions.values('category').annotate(
        total_spent=Sum('amount'),
        transaction_count=Count('id'),
        avg_transaction=Avg('amount')
    ).order_by('-total_spent')
    
    # Get user's budgets
    budgets = {b.category: b for b in Budget.objects.filter(
        user=user, 
        is_active=True, 
        period='monthly'
    )}
    
    stats = []
    for spending in category_spending:
        category = spending['category']
        budget = budgets.get(category)
        
        stat_data = {
            'category': category,
            'total_spent': spending['total_spent'],
            'transaction_count': spending['transaction_count'],
            'average_transaction': spending['avg_transaction'],
            'has_budget': budget is not None
        }
        
        if budget:
            stat_data['budget_amount'] = budget.amount
            stat_data['budget_status'] = budget.get_status(year, month)
        
        stats.append(stat_data)
    
    serializer = CategoryStatsSerializer(stats, many=True)
    return Response({'category_stats': serializer.data})


# Budget Alert Views
class BudgetAlertListView(generics.ListAPIView):
    serializer_class = BudgetAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return BudgetAlert.objects.filter(
            budget__user=self.request.user
        ).order_by('-created_at')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_alert_read(request, alert_id):
    """Mark a budget alert as read"""
    try:
        alert = BudgetAlert.objects.get(
            id=alert_id,
            budget__user=request.user
        )
        alert.is_read = True
        alert.save()
        return Response({'status': 'success'})
    except BudgetAlert.DoesNotExist:
        return Response(
            {'error': 'Alert not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


# Budget Template Views
class BudgetTemplateListView(generics.ListAPIView):
    queryset = BudgetTemplate.objects.filter(is_active=True)
    serializer_class = BudgetTemplateSerializer
    permission_classes = [IsAuthenticated]