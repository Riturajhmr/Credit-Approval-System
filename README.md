# Credit Approval System

A Django REST API application for managing credit approval and loan processing with background data ingestion using Celery.

## Features

- Customer registration with automatic approved limit calculation
- Credit score calculation based on historical loan data
- Loan eligibility checking with interest rate correction
- Loan creation and management
- View loan details by customer
- Background data ingestion from Excel files using Celery
- Dockerized for easy deployment

## Tech Stack

- **Backend**: Django 4.2.7, Django REST Framework
- **Database**: PostgreSQL 15
- **Task Queue**: Celery with Redis
- **Containerization**: Docker & Docker Compose

## Prerequisites

- Docker
- Docker Compose
- Git

## Project Structure

```
credit_approval_system/
├── config/              # Django project settings
├── core/                # Main application logic
│   ├── models.py       # Customer and Loan models
│   ├── views.py        # API endpoints
│   ├── serializers.py  # Request/Response serializers
│   ├── services.py     # Business logic (credit score, eligibility)
│   └── tasks.py        # Celery tasks for data ingestion
├── data/               # Excel data files
├── docker-compose.yml  # Docker services configuration
├── Dockerfile          # Django app container
└── requirements.txt    # Python dependencies
```

## Setup & Installation

1. **Clone the repository**

2. **Navigate to project directory**
```bash
cd credit_approval_system
```

3. **Start services with Docker**
```bash
docker-compose up -d
```

4. **Run database migrations**
```bash
docker-compose exec web python manage.py migrate
```

5. **Ingest sample data (background task)**
```bash
docker-compose exec celery python manage.py shell
```
```python
from core.tasks import ingest_customer_data, ingest_loan_data
ingest_customer_data('data/customer_data.xlsx')
ingest_loan_data('data/loan_data.xlsx')
```

## API Endpoints

### 1. Register Customer

**POST** `/register`

Request Body:
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "age": 30,
  "monthly_income": 50000,
  "phone_number": 9876543210
}
```

Response:
```json
{
  "customer_id": 101,
  "name": "John Doe",
  "age": 30,
  "monthly_income": 50000,
  "approved_limit": 1800000,
  "phone_number": 9876543210
}
```

### 2. Check Eligibility

**POST** `/check-eligibility`

Request Body:
```json
{
  "customer_id": 1,
  "loan_amount": 500000,
  "interest_rate": 11,
  "tenure": 12
}
```

Response:
```json
{
  "customer_id": 1,
  "approval": true,
  "interest_rate": 11.0,
  "corrected_interest_rate": 11.0,
  "tenure": 12,
  "monthly_installment": 44160.85
}
```

### 3. Create Loan

**POST** `/create-loan`

Request Body:
```json
{
  "customer_id": 1,
  "loan_amount": 500000,
  "interest_rate": 11,
  "tenure": 12
}
```

Response:
```json
{
  "loan_id": 234,
  "customer_id": 1,
  "loan_approved": true,
  "message": "Loan approved successfully",
  "monthly_installment": 44160.85
}
```

### 4. View Loan Details

**GET** `/view-loan/<loan_id>`

Response:
```json
{
  "loan_id": 234,
  "customer": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": 9876543210,
    "age": 30
  },
  "loan_amount": 500000.0,
  "interest_rate": 11.0,
  "monthly_installment": 44160.85,
  "tenure": 12
}
```

### 5. View All Loans by Customer

**GET** `/view-loans/<customer_id>`

Response:
```json
[
  {
    "loan_id": 234,
    "loan_amount": 500000.0,
    "interest_rate": 11.0,
    "monthly_installment": 44160.85,
    "repayments_left": 12
  }
]
```

## Credit Score Calculation

The credit score (0-100) is calculated based on:

1. **Past Loans Paid on Time (30%)**: Ratio of EMIs paid on time
2. **Number of Loans (20%)**: More loans indicate better credit history
3. **Loan Activity in Current Year (20%)**: Active borrowing pattern
4. **Loan Approved Volume (15%)**: Total amount of loans taken
5. **Current Debt Management (15%)**: Current debt vs approved limit

## Loan Eligibility Rules

### Credit Score Tiers:

- **Score > 50**: Approved if interest rate ≥ 10%
- **30 < Score ≤ 50**: Approved if interest rate ≥ 12%
- **10 < Score ≤ 30**: Approved if interest rate ≥ 16%
- **Score ≤ 10**: Not approved

### Additional Rules:

- If `current EMIs > 50% of monthly salary` → Rejected
- If `total current EMIs > approved limit` → Credit score = 0

## Testing

### Running Unit Tests

Run all unit tests:
```bash
docker-compose exec web python manage.py test core.tests
```

The test suite includes:
- Customer model tests (approved limit calculation, string representation)
- Loan model tests (creation, string representation)
- Credit score calculation tests (no loans, high EMI, past loans, number of loans)
- EMI calculation tests (with interest, zero interest, different tenures)
- Loan eligibility tests (credit score checks, EMI limits, interest rate correction)
- Current debt update tests
- Integration tests (complete loan flow)

**Test Results**: All 20 tests passing ✅

### Manual API Testing

1. **Start the application**:
```bash
docker-compose up
```

2. **Access the API**:
```
http://localhost:8000
```

3. **Test endpoints using curl or Postman**:
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"first_name":"John","last_name":"Doe","age":30,"monthly_income":50000,"phone_number":9876543210}'
```

## Data Ingestion

The system supports background ingestion of Excel data files:

- **Customer Data**: `data/customer_data.xlsx`
- **Loan Data**: `data/loan_data.xlsx`

Replace these files with your own data and trigger ingestion using Celery tasks.

## Docker Commands

- **Start services**: `docker-compose up -d`
- **Stop services**: `docker-compose down`
- **View logs**: `docker-compose logs -f`
- **Access Django shell**: `docker-compose exec web python manage.py shell`
- **Run migrations**: `docker-compose exec web python manage.py migrate`

## License

MIT
