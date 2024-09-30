from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, login
from django.conf import settings
from importlib import import_module
from .serializers import UserSerializer, StakeHolderSerializer

from accounts.models import Stakeholder



class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        print(user)
        if user is not None:
            login(request, user)
            SessionStore = import_module(settings.SESSION_ENGINE).SessionStore
            session = SessionStore()
            
            session['user_id'] = user.id
            session.save()
            return Response(
                {
                    'message': 'Login successful',
                    'sessionId': session.session_key,
                    'data': UserSerializer(user).data
                },
                status=status.HTTP_200_OK
                )
        else:
            return Response(
                {
                   'message': 'Invalid credentials'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
            

class StakeholderView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        name = request.data.get('name')
        address = request.data.get('address')
        phone = request.data.get('phone')
        email = request.data.get('email')
        type = request.data.get('type')
        
        stakeholder = Stakeholder.objects.create(
            stakeholder_name=name,
            stakeholder_address=address,
            stakeholder_mobile=phone,
            stakeholder_email=email,
            stakeholder_type=type
        )
        return Response(
            {
                'message': 'Created successfully',
                'data': StakeHolderSerializer(stakeholder).data
            },
            status=status.HTTP_200_OK
            )
    
    
        