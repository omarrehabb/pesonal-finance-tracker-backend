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

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        # Remove password2 as it's only used for validation
        validated_data.pop('password2')
        
        # Create user
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        
        # Set password
        user.set_password(validated_data['password'])
        user.save()
        
        # Create user profile if one doesn't already exist
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'balance': 0}
        )
        
        return user
    