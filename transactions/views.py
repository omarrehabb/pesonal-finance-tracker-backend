from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from .models import Transaction, UserProfile
from .serializers import TransactionSerializer, UserProfileSerializer
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['category', 'description']
    ordering_fields = ['date', 'amount']
    ordering = ['-date']  # Default ordering is by date, newest first

    def get_queryset(self):
        """
        This view should return a list of all transactions
        for the currently authenticated user.
        """
        user = self.request.user
        return Transaction.objects.filter(user=user)
    
    def perform_create(self, serializer):
        """Save the transaction and update user balance"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Return a summary of transactions by category
        """
        user = request.user
        
        # Get total income and expenses
        income = Transaction.objects.filter(
            user=user, 
            transaction_type='income'
        ).aggregate(total=Sum('amount'))
        
        expenses = Transaction.objects.filter(
            user=user, 
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))
        
        # Get expenses by category
        expenses_by_category = Transaction.objects.filter(
            user=user, 
            transaction_type='expense'
        ).values('category').annotate(total=Sum('amount'))
        
        # Get income by category
        income_by_category = Transaction.objects.filter(
            user=user, 
            transaction_type='income'
        ).values('category').annotate(total=Sum('amount'))
        
        return Response({
            'total_income': income['total'] or 0,
            'total_expenses': expenses['total'] or 0,
            'expenses_by_category': expenses_by_category,
            'income_by_category': income_by_category,
        })
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Return the last 5 transactions"""
        recent_transactions = self.get_queryset().order_by('-date')[:5]
        serializer = self.get_serializer(recent_transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def time_series(self, request):
        """Return time-based data for charts"""
        user = request.user
        period = request.query_params.get('period', 'month')
        
        # Set the truncation function based on period
        if period == 'week':
            trunc_func = TruncWeek('date')
            days_ago = 7 * 12  # Last 12 weeks
        elif period == 'day':
            trunc_func = TruncDay('date')
            days_ago = 30  # Last 30 days
        else:  # Default to month
            trunc_func = TruncMonth('date')
            days_ago = 30 * 12  # Last 12 months
        
        # Get start date
        start_date = timezone.now() - timedelta(days=days_ago)
        
        # Get income time series
        income_series = Transaction.objects.filter(
            user=user,
            transaction_type='income',
            date__gte=start_date
        ).annotate(
            period=trunc_func
        ).values('period').annotate(
            total=Sum('amount')
        ).order_by('period')
        
        # Get expense time series
        expense_series = Transaction.objects.filter(
            user=user,
            transaction_type='expense',
            date__gte=start_date
        ).annotate(
            period=trunc_func
        ).values('period').annotate(
            total=Sum('amount')
        ).order_by('period')
        
        return Response({
            'income_series': income_series,
            'expense_series': expense_series,
        })


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return UserProfile.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get the current user's profile"""
        user = request.user
        profile = UserProfile.objects.get(user=user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)