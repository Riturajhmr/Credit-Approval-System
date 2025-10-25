import pandas as pd
from datetime import datetime
from celery import shared_task
from core.models import Customer, Loan
from django.utils import timezone

@shared_task
def ingest_customer_data(file_path):
    try:
        df = pd.read_excel(file_path)
        created_count = 0
        updated_count = 0
        
        for _, row in df.iterrows():
            customer_id = int(row['customer_id'])
            customer, created = Customer.objects.update_or_create(
                customer_id=customer_id,
                defaults={
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'phone_number': int(row['phone_number']),
                    'monthly_income': int(row['monthly_salary']),
                    'approved_limit': int(row['approved_limit']),
                    'current_debt': int(row['current_debt']),
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        return f"Customer data ingested: {created_count} created, {updated_count} updated"
    except Exception as e:
        return f"Error ingesting customer data: {str(e)}"

@shared_task
def ingest_loan_data(file_path):
    try:
        df = pd.read_excel(file_path)
        created_count = 0
        
        for _, row in df.iterrows():
            customer_id = int(row['customer_id'])
            try:
                customer = Customer.objects.get(customer_id=customer_id)
                
                start_date = pd.to_datetime(row['start_date']).date()
                end_date = pd.to_datetime(row['end_date']).date()
                
                loan, created = Loan.objects.update_or_create(
                    loan_id=int(row['loan_id']),
                    defaults={
                        'customer': customer,
                        'loan_amount': float(row['loan_amount']),
                        'interest_rate': float(row['interest_rate']),
                        'tenure': int(row['tenure']),
                        'monthly_installment': float(row['monthly_repayment']),
                        'emis_paid_on_time': int(row['EMIs_paid_on_time']),
                        'start_date': start_date,
                        'end_date': end_date,
                        'status': 'completed' if end_date < timezone.now().date() else 'active'
                    }
                )
                if created:
                    created_count += 1
            except Customer.DoesNotExist:
                continue
        
        return f"Loan data ingested: {created_count} loans created"
    except Exception as e:
        return f"Error ingesting loan data: {str(e)}"
