file org info:

├── api                     # Contains the main application files
│   ├── __init__.py         # This file makes "app" a Python package
│   ├── main.py             # Initializes the FastAPI application
│   ├── dependencies.py     # Defines dependencies used by the routers
│   ├── routers             # Contains API route definitions
│   │   ├── __init__.py
│   │   ├── items.py        # Defines routes and endpoints related to items
│   │   └── users.py        # Defines routes and endpoints related to users
│   ├── crud                # Contains CRUD operations for database interaction
│   │   ├── __init__.py
│   │   ├── item.py         # CRUD operations for items
│   │   └── user.py         # CRUD operations for users
│   ├── schemas             # Defines Pydantic models for data validation
│   │   ├── __init__.py
│   │   ├── item.py         # Schemas for items
│   │   └── user.py         # Schemas for users
│   ├── models              # Defines SQLAlchemy database models
│   │   ├── __init__.py
│   │   ├── item.py         # Database models for items
│   │   └── user.py         # Database models for users
│   ├── external_services   # Handles integration with external services
│   │   ├── __init__.py
│   │   ├── email.py        # Functions for sending emails
│   │   └── notification.py # Functions for sending notifications
│   └── utils               # Contains helper functions
│       ├── __init__.py
│       ├── authentication.py # Functions for authentication
│       └── validation.py     # Functions for validation
├── tests                   # Contains test cases
│   ├── __init__.py
│   ├── test_main.py
│   ├── test_items.py        # Tests for the items module
│   └── test_users.py        # Tests for the users module
├── requirements.txt         # Lists required dependencies
├── .gitignore               # Git ignore file
└── README.md                # Project documentation

https://medium.com/@amirm.lavasani/how-to-structure-your-fastapi-projects-0219a6600a8f

---------------------------------------------------------------------------------------------------------------------------------------------

TODO

GitHub Actions:

Pipeline Flow   
🛠 Run unit tests (pytest) 
✅ If unit tests pass → Build & package the Lambda function done
🚀 Deploy to AWS Lambda                                     done
🔄 Run integration tests on the deployed URL 
🚨 If integration tests fail → Rollback deployment

----------------------------------------------------------------------------------------------------------------------
CREATE DB

https://www.youtube.com/watch?v=wqVyN2LAFDY



CREATE LAMBDA AWS

https://www.youtube.com/watch?v=UauMQGqaxGo&t=823s

add:
    - env variables
    - rds db connection
    - subnet for itenret connection !?