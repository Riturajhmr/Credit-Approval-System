from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from .models import Customer, Loan
from .services import calculate_credit_score, check_loan_eligibility, calculate_emi, update_customer_current_debt


class CustomerModelTest(TestCase):
    def test_customer_approved_limit_calculation(self):
        customer = Customer.objects.create(
            first_name="John",
            last_name="Doe",
            age=30,
            phone_number=9876543210,
            monthly_income=50000
        )
        
        expected_limit = round(36 * 50000 / 100000) * 100000
        self.assertEqual(customer.approved_limit, expected_limit)
    
    def test_customer_str_representation(self):
        customer = Customer.objects.create(
            first_name="Jane",
            last_name="Smith",
            age=25,
            phone_number=9876543211,
            monthly_income=60000
        )
        self.assertEqual(str(customer), f"Jane Smith (ID: {customer.customer_id})")


class LoanModelTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name="Test",
            last_name="User",
            age=30,
            phone_number=9876543212,
            monthly_income=50000
        )
    
    def test_loan_creation(self):
        loan = Loan.objects.create(
            customer=self.customer,
            loan_amount=Decimal('100000'),
            interest_rate=Decimal('12.0'),
            tenure=12,
            monthly_installment=Decimal('8884.91'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            status='active'
        )
        self.assertEqual(loan.customer, self.customer)
        self.assertEqual(loan.loan_amount, Decimal('100000'))
    
    def test_loan_str_representation(self):
        loan = Loan.objects.create(
            customer=self.customer,
            loan_amount=Decimal('50000'),
            interest_rate=Decimal('10.0'),
            tenure=6,
            monthly_installment=Decimal('8573.01'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=180),
            status='active'
        )
        self.assertIn(str(loan.loan_id), str(loan))
        self.assertIn(str(self.customer.customer_id), str(loan))


class CreditScoreCalculationTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name="Credit",
            last_name="Tester",
            age=35,
            phone_number=9876543213,
            monthly_income=100000,
            approved_limit=3600000
        )
    
    def test_customer_with_no_loans(self):
        score = calculate_credit_score(self.customer.customer_id)
        self.assertEqual(score, 50)
    
    def test_customer_with_high_emi_exceeds_limit(self):
        Loan.objects.create(
            customer=self.customer,
            loan_amount=Decimal('2000000'),
            interest_rate=Decimal('12.0'),
            tenure=24,
            monthly_installment=Decimal('500000'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=730),
            status='active'
        )
        
        score = calculate_credit_score(self.customer.customer_id)
        self.assertLessEqual(score, 50)
    
    def test_past_loans_paid_on_time_scoring(self):
        past_loan = Loan.objects.create(
            customer=self.customer,
            loan_amount=Decimal('100000'),
            interest_rate=Decimal('12.0'),
            tenure=12,
            monthly_installment=Decimal('8884.91'),
            emis_paid_on_time=12,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            status='completed'
        )
        
        score = calculate_credit_score(self.customer.customer_id)
        self.assertGreater(score, 25)
    
    def test_number_of_loans_scoring(self):
        for i in range(10):
            Loan.objects.create(
                customer=self.customer,
                loan_amount=Decimal('50000'),
                interest_rate=Decimal('10.0'),
                tenure=6,
                monthly_installment=Decimal('8573.01'),
                start_date=date(2022, 1, 1),
                end_date=date(2022, 6, 30),
                status='completed'
            )
        
        score = calculate_credit_score(self.customer.customer_id)
        self.assertGreater(score, 20)
    
    def test_current_year_activity_scoring(self):
        current_year = date.today().year
        for i in range(5):
            Loan.objects.create(
                customer=self.customer,
                loan_amount=Decimal('50000'),
                interest_rate=Decimal('10.0'),
                tenure=6,
                monthly_installment=Decimal('8573.01'),
                start_date=date(current_year, 1, 1),
                end_date=date(current_year, 6, 30),
                status='completed'
            )
        
        score = calculate_credit_score(self.customer.customer_id)
        self.assertGreater(score, 18)


class EMICalculationTest(TestCase):
    def test_emi_calculation_with_interest(self):
        principal = 100000
        interest_rate = 12
        tenure = 12
        
        emi = calculate_emi(principal, interest_rate, tenure)
        
        self.assertIsInstance(emi, float)
        self.assertGreater(emi, 0)
        self.assertLess(emi, principal)
    
    def test_emi_calculation_zero_interest(self):
        principal = 100000
        interest_rate = 0
        tenure = 12
        
        emi = calculate_emi(principal, interest_rate, tenure)
        
        expected_emi = principal / tenure
        self.assertEqual(emi, expected_emi)
    
    def test_emi_calculation_different_tenures(self):
        principal = 100000
        interest_rate = 12
        
        emi_12_months = calculate_emi(principal, interest_rate, 12)
        emi_24_months = calculate_emi(principal, interest_rate, 24)
        
        self.assertGreater(emi_12_months, 0)
        self.assertGreater(emi_24_months, 0)
        self.assertGreater(emi_12_months, emi_24_months)


class LoanEligibilityTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name="Loan",
            last_name="Applicant",
            age=30,
            phone_number=9876543214,
            monthly_income=100000,
            approved_limit=3600000
        )
    
    def test_eligibility_with_credit_score_zero(self):
        Loan.objects.create(
            customer=self.customer,
            loan_amount=Decimal('2000000'),
            interest_rate=Decimal('12.0'),
            tenure=24,
            monthly_installment=Decimal('500000'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=730),
            status='active'
        )
        
        result = check_loan_eligibility(self.customer.customer_id, 100000, 10, 12)
        self.assertFalse(result['approval'])
    
    def test_eligibility_with_high_emi_exceed_50_percent_salary(self):
        Loan.objects.create(
            customer=self.customer,
            loan_amount=Decimal('500000'),
            interest_rate=Decimal('12.0'),
            tenure=12,
            monthly_installment=Decimal('60000'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            status='active'
        )
        
        result = check_loan_eligibility(self.customer.customer_id, 100000, 10, 12)
        self.assertFalse(result['approval'])
        self.assertIn('50%', result['message'])
    
    def test_eligibility_credit_score_greater_than_50(self):
        for i in range(10):
            Loan.objects.create(
                customer=self.customer,
                loan_amount=Decimal('50000'),
                interest_rate=Decimal('10.0'),
                tenure=6,
                monthly_installment=Decimal('8573.01'),
                emis_paid_on_time=6,
                start_date=date.today() - timedelta(days=365),
                end_date=date.today() - timedelta(days=180),
                status='completed'
            )
        
        result = check_loan_eligibility(self.customer.customer_id, 100000, 10, 12)
        self.assertTrue(result['approval'])
    
    def test_interest_rate_correction_tier_30_to_50(self):
        Loan.objects.create(
            customer=self.customer,
            loan_amount=Decimal('50000'),
            interest_rate=Decimal('10.0'),
            tenure=6,
            monthly_installment=Decimal('8573.01'),
            emis_paid_on_time=6,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 6, 30),
            status='completed'
        )
        
        result = check_loan_eligibility(self.customer.customer_id, 100000, 10, 12)
        
        if not result['approval']:
            self.assertGreaterEqual(result['corrected_interest_rate'], 10)
    
    def test_eligibility_nonexistent_customer(self):
        result = check_loan_eligibility(99999, 100000, 10, 12)
        self.assertFalse(result['approval'])
        self.assertIn('not found', result['message'])


class CurrentDebtUpdateTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            first_name="Debt",
            last_name="Updater",
            age=30,
            phone_number=9876543215,
            monthly_income=100000,
            approved_limit=3600000
        )
    
    def test_update_current_debt_with_active_loans(self):
        Loan.objects.create(
            customer=self.customer,
            loan_amount=Decimal('100000'),
            interest_rate=Decimal('12.0'),
            tenure=12,
            monthly_installment=Decimal('8884.91'),
            emis_paid_on_time=2,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            status='active'
        )
        
        update_customer_current_debt(self.customer.customer_id)
        self.customer.refresh_from_db()
        
        self.assertGreater(self.customer.current_debt, 0)
    
    def test_update_debt_no_active_loans(self):
        update_customer_current_debt(self.customer.customer_id)
        self.customer.refresh_from_db()
        
        self.assertEqual(self.customer.current_debt, 0)


class IntegrationTest(TestCase):
    def test_complete_loan_flow(self):
        customer = Customer.objects.create(
            first_name="Integration",
            last_name="Test",
            age=30,
            phone_number=9876543216,
            monthly_income=100000,
            approved_limit=3600000
        )
        
        for i in range(5):
            Loan.objects.create(
                customer=customer,
                loan_amount=Decimal('50000'),
                interest_rate=Decimal('10.0'),
                tenure=6,
                monthly_installment=Decimal('8573.01'),
                emis_paid_on_time=6,
                start_date=date.today() - timedelta(days=365),
                end_date=date.today() - timedelta(days=180),
                status='completed'
            )
        
        score = calculate_credit_score(customer.customer_id)
        self.assertGreater(score, 0)
        
        result = check_loan_eligibility(customer.customer_id, 200000, 12, 24)
        self.assertTrue(result['approval'])
        
        if result['approval']:
            loan = Loan.objects.create(
                customer=customer,
                loan_amount=Decimal('200000'),
                interest_rate=result['corrected_interest_rate'],
                tenure=24,
                monthly_installment=result['emi'],
                start_date=date.today(),
                end_date=date.today() + timedelta(days=730),
                status='active'
            )
            
            update_customer_current_debt(customer.customer_id)
            customer.refresh_from_db()
            
            self.assertGreater(customer.current_debt, 0)
