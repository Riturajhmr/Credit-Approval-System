from decimal import Decimal
from datetime import datetime, date
from .models import Customer, Loan

def calculate_credit_score(customer_id):
    try:
        customer = Customer.objects.get(customer_id=customer_id)
        loans = Loan.objects.filter(customer=customer)
        
        if not loans.exists():
            return 50
        
        total_emi = sum([float(loan.monthly_installment) for loan in loans if loan.status == 'active'])
        
        if total_emi > customer.approved_limit:
            return 0
        
        past_loans_paid_on_time_score = 0
        total_loans_count_score = 0
        current_year_activity_score = 0
        loan_approved_volume_score = 0
        current_debt_management_score = 0
        
        total_loans = loans.count()
        total_paid_on_time = sum([loan.emis_paid_on_time for loan in loans])
        total_tenures = sum([loan.tenure for loan in loans])
        on_time_ratio = total_paid_on_time / total_tenures if total_tenures > 0 else 0
        
        past_loans_paid_on_time_score = min(on_time_ratio * 30, 30)
        
        if total_loans >= 10:
            total_loans_count_score = 20
        elif total_loans >= 5:
            total_loans_count_score = 15
        elif total_loans >= 2:
            total_loans_count_score = 10
        else:
            total_loans_count_score = 5
        
        current_year = datetime.now().year
        current_year_loans = loans.filter(start_date__year=current_year).count()
        
        if current_year_loans >= 5:
            current_year_activity_score = 20
        elif current_year_loans >= 2:
            current_year_activity_score = 15
        elif current_year_loans >= 1:
            current_year_activity_score = 10
        else:
            current_year_activity_score = 0
        
        total_approved_volume = sum([float(loan.loan_amount) for loan in loans])
        
        if total_approved_volume > 10000000:
            loan_approved_volume_score = 15
        elif total_approved_volume > 5000000:
            loan_approved_volume_score = 12
        elif total_approved_volume > 1000000:
            loan_approved_volume_score = 8
        else:
            loan_approved_volume_score = 5
        
        if customer.current_debt == 0:
            current_debt_management_score = 15
        elif customer.current_debt < customer.approved_limit * 0.3:
            current_debt_management_score = 12
        elif customer.current_debt < customer.approved_limit * 0.6:
            current_debt_management_score = 8
        else:
            current_debt_management_score = 4
        
        credit_score = (
            past_loans_paid_on_time_score +
            total_loans_count_score +
            current_year_activity_score +
            loan_approved_volume_score +
            current_debt_management_score
        )
        
        return min(max(credit_score, 0), 100)
    
    except Customer.DoesNotExist:
        return 0
    except Exception as e:
        return 0

def check_loan_eligibility(customer_id, loan_amount, interest_rate, tenure):
    try:
        customer = Customer.objects.get(customer_id=customer_id)
        credit_score = calculate_credit_score(customer_id)
        
        current_active_loans = Loan.objects.filter(customer=customer, status='active')
        total_current_emi = sum([float(loan.monthly_installment) for loan in current_active_loans])
        
        if credit_score == 0:
            return {
                'approval': False,
                'corrected_interest_rate': interest_rate,
                'message': 'Credit score is 0'
            }
        
        if total_current_emi > customer.monthly_income * 0.5:
            return {
                'approval': False,
                'corrected_interest_rate': interest_rate,
                'message': 'Total EMIs exceed 50% of monthly income'
            }
        
        corrected_interest_rate = interest_rate
        
        if credit_score > 50:
            if interest_rate >= 10:
                approval = True
            else:
                approval = False
                corrected_interest_rate = 10
        elif credit_score > 30:
            if interest_rate >= 12:
                approval = True
            else:
                approval = False
                corrected_interest_rate = 12
        elif credit_score > 10:
            if interest_rate >= 16:
                approval = True
            else:
                approval = False
                corrected_interest_rate = 16
        else:
            approval = False
        
        if not approval:
            return {
                'approval': False,
                'corrected_interest_rate': corrected_interest_rate,
                'message': f'Loan approved only at interest rate >= {corrected_interest_rate}%'
            }
        
        emi = calculate_emi(loan_amount, corrected_interest_rate, tenure)
        
        return {
            'approval': True,
            'corrected_interest_rate': corrected_interest_rate,
            'emi': emi,
            'message': 'Loan approved'
        }
    
    except Customer.DoesNotExist:
        return {
            'approval': False,
            'corrected_interest_rate': interest_rate,
            'message': 'Customer not found'
        }

def calculate_emi(principal, interest_rate, tenure):
    if interest_rate == 0:
        return float(principal) / tenure
    
    r = interest_rate / (12 * 100)
    n = tenure
    
    emi = principal * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)
    return round(float(emi), 2)

def update_customer_current_debt(customer_id):
    try:
        customer = Customer.objects.get(customer_id=customer_id)
        active_loans = Loan.objects.filter(customer=customer, status='active')
        total_debt = sum([float(loan.loan_amount) for loan in active_loans])
        
        remaining_installments = sum([
            (loan.tenure - loan.emis_paid_on_time) * float(loan.monthly_installment)
            for loan in active_loans
        ])
        
        customer.current_debt = int(remaining_installments)
        customer.save()
    
    except Customer.DoesNotExist:
        pass
