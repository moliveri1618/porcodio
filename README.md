# 🚀 Microservice Project Template

A **FastAPI-based application** with AWS Lambda deployment, RDS database integration, and GitHub Actions for CI/CD.

---

## 📂 Project Structure

```
├── api                     # Main application directory
│   ├── __init__.py         # Marks "api" as a package
│   ├── main.py             # Initializes FastAPI application
│   ├── dependencies.py     # Common dependencies used across routers
│   ├── routers             # API route definitions
│   │   ├── __init__.py
│   │   ├── items.py        # Routes related to items
│   │   └── users.py        # Routes related to users
│   ├── crud                # Database CRUD operations
│   │   ├── __init__.py
│   │   ├── item.py         # CRUD logic for items
│   │   └── user.py         # CRUD logic for users
│   ├── schemas             # Pydantic models for request validation
│   │   ├── __init__.py
│   │   ├── item.py         # Schemas for items
│   │   └── user.py         # Schemas for users
│   ├── models              # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── item.py         # Database model for items
│   │   └── user.py         # Database model for users
│   ├── external_services   # Integrations with external services
│   │   ├── __init__.py
│   │   ├── email.py        # Email sending functions
│   │   └── notification.py # Notification handling functions
│   ├── utils               # Helper functions
│   │   ├── __init__.py
│   │   ├── authentication.py # Auth-related functions
│   │   └── validation.py     # Data validation utilities
├── tests                   # Unit and integration tests
│   ├── __init__.py
│   ├── test_main.py
│   ├── test_items.py        # Tests for the items module
│   └── test_users.py        # Tests for the users module
├── requirements.txt         # List of dependencies
├── .gitignore               # Git ignore rules
└── README.md                # Project documentation
```

---

## 🛠️ GitHub Actions (CI/CD Pipeline)

### Pipeline Flow:
1️⃣ **Run Unit Tests** (`pytest`)<br>
2️⃣ ✅ **If tests pass → Build & package the Lambda function** <br>
3️⃣ 🚀 **Deploy to AWS Lambda** <br>
4️⃣ 🔄 **Run Integration Tests on the deployed URL**<br>
5️⃣ 🚨 **If integration tests fail → Rollback deployment**<br>

---

## 📌 How to Run the Project

### 1️⃣ Set Up the Virtual Environment
```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# (Linux/macOS)
source venv/bin/activate
```

### 2️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Start FastAPI
```bash
uvicorn api.main:app --reload
```

### 4️⃣ Copy Github Secrets
Check the secrets in **main.yaml** to be copied in your github repository for this project


---

## 📦 Dependency Management

Whenever you install a new dependency, it has to be installed inside the virtual environment:
```bash
pip install <package-name>
```
Then **update `requirements.txt`** to install them during the deployment to AWS Lambda:
```bash
pip freeze > requirements.txt
```

---

## 📊 Database Setup

Follow this tutorial to set up the database:  
🔗 [Database Setup Guide](https://www.youtube.com/watch?v=wqVyN2LAFDY)

---

## 🚀 Deploying to AWS Lambda

For AWS Lambda deployment, follow this guide:  
🔗 [AWS Lambda Deployment](https://www.youtube.com/watch?v=UauMQGqaxGo&t=823s)

### Additional Steps in AWS Lambda:
1. Add the same **environment variables** that you can find in **.env** 
2. Configure **RDS database connection** 
3. Set up a **subnet for internet access** (if required)  

---

## 🔑 How to Generate an Authentication Token for API Testing

Use **AWS Cognito** to generate a token for API testing:  
```bash
aws cognito-idp initiate-auth \
    --client-id obemnph8vgsfrcip0s3bg4flm \
    --auth-flow USER_PASSWORD_AUTH \
    --auth-parameters USERNAME="70bcc95c-b0f1-70e3-5c17-ee40967d4051",PASSWORD="NewSecurePass123!" \
    --region eu-north-1 \
    --output json > token_response.json
```

