from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
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
            

class StakeholderView(viewsets.ModelViewSet):
    queryset = Stakeholder.objects.all()  # Full queryset for the viewset
    serializer_class = StakeHolderSerializer
    
    
        