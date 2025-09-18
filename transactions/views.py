from rest_framework import viewsets, permissions, filters, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from .models import Transaction, UserProfile
from .serializers import TransactionSerializer, UserProfileSerializer, RegisterSerializer, UserSerializer
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET


def update_user_balance(user):
    # Calculate balance from all transactions
    income = Transaction.objects.filter(
        user=user, 
        transaction_type='income'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    expenses = Transaction.objects.filter(
        user=user, 
        transaction_type='expense'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Update user profile balance
    profile, created = UserProfile.objects.get_or_create(user=user, defaults={'balance': 0})
    profile.balance = income - expenses
    profile.save()
    
    return profile


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
        transaction = serializer.save(user=self.request.user)
        update_user_balance(self.request.user)

    def perform_update(self, serializer):
        transaction = serializer.save()
        update_user_balance(transaction.user)

    def perform_destroy(self, instance):
        user = instance.user
        instance.delete()
        update_user_balance(user)
            
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

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "message": "User registered successfully",
        }, status=status.HTTP_201_CREATED)
        return Response(serializer.data)
    

class CustomLoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            return Response({
                'success': True,
                'username': user.username
            })
        else:
            return Response({
                'success': False,
                'message': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response({'success': True})


@ensure_csrf_cookie
@require_GET
def get_csrf(request):
    return JsonResponse({"detail": "ok"})
