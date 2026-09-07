from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets
from rest_framework import viewsets, filters
from rest_framework.filters import OrderingFilter
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from importlib import import_module
from .serializers import UserSerializer
from api.v1.inventory.serializers import StakeHolderSerializer

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
            

from rest_framework.decorators import action
from django.utils import timezone


class StakeholderView(viewsets.ModelViewSet):
    queryset = Stakeholder.objects.all().order_by('-date_added')
    serializer_class = StakeHolderSerializer
    permission_classes = (IsAuthenticated, )
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_fields = {
        'type': ['exact', 'icontains'],
        'name': ['exact', 'icontains'],
        'city': ['exact', 'icontains'],
        'is_deleted': ['exact'],
        'is_active': ['exact'],
    }
    ordering_fields = ['name', 'date_added', 'opening_balance', 'type', 'stakeholder_id']
    ordering = ['-date_added']
    search_fields = ['id', 'stakeholder_id', 'name', 'company_name', 'contact_person', 'type', 'address', 'city', 'mobile', 'email', 'tax_id']

    def destroy(self, request, *args, **kwargs):
        """
        Referential integrity guard: block deletion if stakeholder has active relations
        """
        instance = self.get_object()

        # Check related orders
        has_orders = instance.order_set.exists()

        # Check related returns
        from inventory.models import Return, Payment
        has_returns = Return.objects.filter(original_order__stakeholder=instance).exists()

        # Check related payments
        has_payments = Payment.objects.filter(company=instance).exists() or Payment.objects.filter(order__stakeholder=instance).exists()

        # Check pending balance
        has_balance = (instance.total_pending_amount or 0) > 0

        if has_orders or has_returns or has_payments or has_balance:
            reasons = []
            if has_orders:
                reasons.append(f"{instance.order_set.count()} order(s)")
            if has_returns:
                reasons.append(f"{Return.objects.filter(original_order__stakeholder=instance).count()} return(s)")
            if has_payments:
                reasons.append("linked payment record(s)")
            if has_balance:
                reasons.append(f"outstanding balance of ₹{instance.total_pending_amount}")

            return Response(
                {
                    "error": f"Cannot permanently delete '{instance.name}' because it has active transaction records: {', '.join(reasons)}.",
                    "suggestion": "Please deactivate this stakeholder instead of deleting it to preserve financial and audit histories."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """
        Toggles is_deleted and is_active for the stakeholder
        """
        stakeholder = self.get_object()
        stakeholder.is_deleted = not stakeholder.is_deleted
        stakeholder.is_active = not stakeholder.is_deleted
        stakeholder.save()
        status_label = "Deactivated" if stakeholder.is_deleted else "Activated"
        return Response({
            "message": f"Stakeholder '{stakeholder.name}' has been {status_label.lower()} successfully.",
            "is_deleted": stakeholder.is_deleted,
            "is_active": stakeholder.is_active,
            "data": StakeHolderSerializer(stakeholder).data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Aggregated summary KPIs for the master dashboard
        """
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total_stakeholders = Stakeholder.objects.count()
        active_customers = Stakeholder.objects.filter(type='Customer', is_deleted=False).count()
        active_suppliers = Stakeholder.objects.filter(type='Supplier', is_deleted=False).count()
        inactive_records = Stakeholder.objects.filter(is_deleted=True).count()
        new_this_month = Stakeholder.objects.filter(date_added__gte=start_of_month).count()

        # Calculate receivables (from active Customers) and payables (from active Suppliers)
        customers = Stakeholder.objects.filter(type='Customer', is_deleted=False)
        total_receivable = sum(c.total_pending_amount for c in customers)

        suppliers = Stakeholder.objects.filter(type='Supplier', is_deleted=False)
        total_payable = sum(s.total_pending_amount for s in suppliers)

        return Response({
            "total_stakeholders": total_stakeholders,
            "active_customers": active_customers,
            "active_suppliers": active_suppliers,
            "inactive_records": inactive_records,
            "new_this_month": new_this_month,
            "total_receivable": total_receivable,
            "total_payable": total_payable,
        }, status=status.HTTP_200_OK)

    
        