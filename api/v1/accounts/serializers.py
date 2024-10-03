from rest_framework import serializers
from accounts.models import User, Stakeholder


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'phone', 'user_type')
        

class StakeHolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stakeholder
        fields = ('id', 'stakeholder_id', 'name', 'address', 'mobile', 'email', 'type')