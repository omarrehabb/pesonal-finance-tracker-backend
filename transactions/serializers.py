from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Transaction, UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'balance']
        read_only_fields = ['id']


class TransactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    username = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'username', 'transaction_type', 'amount', 'category', 'description', 'date']
        read_only_fields = ['id', 'user']
    
    def get_username(self, obj):
        return obj.user.username
        
    def create(self, validated_data):
        # Get user from context
        user = self.context['request'].user
        
        # Remove user from validated_data if it exists
        if 'user' in validated_data:
            validated_data.pop('user')
        
        # Create transaction
        transaction = Transaction.objects.create(
            user=user,
            **validated_data
        )
        
        # Update user profile balance
        profile = UserProfile.objects.get(user=user)
        if transaction.transaction_type == 'income':
            profile.balance += transaction.amount
        else:  # expense
            profile.balance -= transaction.amount
        profile.save()
        
        return transaction