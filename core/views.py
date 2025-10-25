from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from datetime import datetime, date, timedelta
from .models import Customer, Loan
from .serializers import *
from .services import check_loan_eligibility, calculate_emi, update_customer_current_debt

# Create your views here.

class RegisterCustomerView(APIView):
    def post(self, request):
        serializer = RegisterCustomerSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            approved_limit = round((36 * data['monthly_income']) / 100000) * 100000
            
            customer = Customer.objects.create(
                first_name=data['first_name'],
                last_name=data['last_name'],
                age=data['age'],
                monthly_income=data['monthly_income'],
                phone_number=data['phone_number'],
                approved_limit=approved_limit,
                current_debt=0
            )
            
            response_data = {
                'customer_id': customer.customer_id,
                'name': f"{customer.first_name} {customer.last_name}",
                'age': customer.age,
                'monthly_income': customer.monthly_income,
                'approved_limit': customer.approved_limit,
                'phone_number': customer.phone_number
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckEligibilityView(APIView):
    def post(self, request):
        serializer = CheckEligibilitySerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            eligibility_result = check_loan_eligibility(
                customer_id=data['customer_id'],
                loan_amount=data['loan_amount'],
                interest_rate=data['interest_rate'],
                tenure=data['tenure']
            )
            
            if eligibility_result['approval']:
                response_data = {
                    'customer_id': data['customer_id'],
                    'approval': True,
                    'interest_rate': data['interest_rate'],
                    'corrected_interest_rate': eligibility_result['corrected_interest_rate'],
                    'tenure': data['tenure'],
                    'monthly_installment': eligibility_result['emi']
                }
            else:
                emi = calculate_emi(
                    data['loan_amount'],
                    eligibility_result['corrected_interest_rate'],
                    data['tenure']
                )
                
                response_data = {
                    'customer_id': data['customer_id'],
                    'approval': False,
                    'interest_rate': data['interest_rate'],
                    'corrected_interest_rate': eligibility_result['corrected_interest_rate'],
                    'tenure': data['tenure'],
                    'monthly_installment': emi
                }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateLoanView(APIView):
    def post(self, request):
        serializer = CreateLoanSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            eligibility_result = check_loan_eligibility(
                customer_id=data['customer_id'],
                loan_amount=data['loan_amount'],
                interest_rate=data['interest_rate'],
                tenure=data['tenure']
            )
            
            if not eligibility_result['approval']:
                return Response({
                    'loan_id': None,
                    'customer_id': data['customer_id'],
                    'loan_approved': False,
                    'message': eligibility_result['message'],
                    'monthly_installment': None
                }, status=status.HTTP_200_OK)
            
            try:
                customer = Customer.objects.get(customer_id=data['customer_id'])
                
                start_date = date.today()
                end_date = start_date + timedelta(days=data['tenure'] * 30)
                
                loan = Loan.objects.create(
                    customer=customer,
                    loan_amount=data['loan_amount'],
                    interest_rate=eligibility_result['corrected_interest_rate'],
                    tenure=data['tenure'],
                    monthly_installment=eligibility_result['emi'],
                    emis_paid_on_time=0,
                    start_date=start_date,
                    end_date=end_date,
                    status='active'
                )
                
                update_customer_current_debt(data['customer_id'])
                
                return Response({
                    'loan_id': loan.loan_id,
                    'customer_id': data['customer_id'],
                    'loan_approved': True,
                    'message': 'Loan approved successfully',
                    'monthly_installment': float(loan.monthly_installment)
                }, status=status.HTTP_201_CREATED)
            
            except Customer.DoesNotExist:
                return Response({
                    'loan_id': None,
                    'customer_id': data['customer_id'],
                    'loan_approved': False,
                    'message': 'Customer not found',
                    'monthly_installment': None
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ViewLoanView(APIView):
    def get(self, request, loan_id):
        try:
            loan = Loan.objects.get(loan_id=loan_id)
            customer = loan.customer
            
            response_data = {
                'loan_id': loan.loan_id,
                'customer': {
                    'id': customer.customer_id,
                    'first_name': customer.first_name,
                    'last_name': customer.last_name,
                    'phone_number': customer.phone_number,
                    'age': customer.age
                },
                'loan_amount': float(loan.loan_amount),
                'interest_rate': float(loan.interest_rate),
                'monthly_installment': float(loan.monthly_installment),
                'tenure': loan.tenure
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Loan.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)

class ViewLoansView(APIView):
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(customer_id=customer_id)
            loans = Loan.objects.filter(customer=customer)
            
            loans_data = []
            for loan in loans:
                repayments_left = loan.tenure - loan.emis_paid_on_time
                loans_data.append({
                    'loan_id': loan.loan_id,
                    'loan_amount': float(loan.loan_amount),
                    'interest_rate': float(loan.interest_rate),
                    'monthly_installment': float(loan.monthly_installment),
                    'repayments_left': repayments_left
                })
            
            return Response(loans_data, status=status.HTTP_200_OK)
        
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
