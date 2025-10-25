import pandas as pd
import random
from datetime import datetime, timedelta
import os

os.makedirs('data', exist_ok=True)

customers = []
for i in range(100):
    monthly_salary = random.randint(30000, 200000)
    approved_limit = round((36 * monthly_salary) / 100000) * 100000
    customers.append({
        'customer_id': i + 1,
        'first_name': f'Customer{i+1}',
        'last_name': 'Test',
        'phone_number': 9000000000 + i,
        'monthly_salary': monthly_salary,
        'approved_limit': approved_limit,
        'current_debt': random.randint(0, 500000)
    })

df_customers = pd.DataFrame(customers)
df_customers.to_excel('data/customer_data.xlsx', index=False)
print("✓ customer_data.xlsx created with 100 customers")

loans = []
loan_id = 1
for customer_id in range(1, 101):
    num_loans = random.randint(0, 5)
    for _ in range(num_loans):
        start_date = datetime.now() - timedelta(days=random.randint(30, 1000))
        tenure = random.randint(6, 36)
        end_date = start_date + timedelta(days=tenure * 30)
        
        loan_amount = random.randint(100000, 2000000)
        interest_rate = random.choice([10, 12, 14, 16, 18])
        
        monthly_rate = interest_rate / 12 / 100
        emi = loan_amount * monthly_rate * ((1 + monthly_rate) ** tenure) / (((1 + monthly_rate) ** tenure) - 1)
        
        emis_paid = random.randint(0, tenure) if end_date > datetime.now() else tenure
        
        loans.append({
            'customer_id': customer_id,
            'loan_id': loan_id,
            'loan_amount': loan_amount,
            'tenure': tenure,
            'interest_rate': interest_rate,
            'monthly_repayment': round(emi, 2),
            'EMIs_paid_on_time': emis_paid,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        })
        loan_id += 1

df_loans = pd.DataFrame(loans)
df_loans.to_excel('data/loan_data.xlsx', index=False)
print(f"✓ loan_data.xlsx created with {len(loans)} loans")
