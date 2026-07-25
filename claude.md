# Gestionale Backend

FastAPI backend for the Gestionale business management application.

## Communication

- Always communicate with the user in English.

## Main technologies

- FastAPI
- SQLModel / SQLAlchemy
- PostgreSQL
- AWS Lambda
- Mangum
- AWS Cognito
- AWS S3

## Coding rules

- Follow the existing project structure.
- Keep routers thin; move reusable business logic into helper/service functions.
- Reuse existing endpoints and helper functions before creating new ones.
- Avoid duplicate database queries.
- Preserve existing API response formats unless explicitly requested.
- Do not rename database fields or API properties without checking frontend compatibility.
- Make small, focused changes.
- Avoid unnecessary refactors.

## Important project areas

- Routers: `routers/`
- Models: `models/`
- Database: `database.py`
- Authentication: `dependecies.py`
- S3 uploads/downloads: `routers/img_S3.py`
- PDF parsing: `routers/progetti_parsing.py`

## Before editing

- Read the relevant router, model and helper functions.
- Search for existing implementations before creating new ones.
- Follow existing patterns whenever possible.
- Check whether a change affects the React frontend before modifying API contracts.
- If a change affects multiple modules, briefly explain the proposed approach before implementing it.

## Database

- Use SQLModel/SQLAlchemy patterns already present in the project.
- Avoid unnecessary commits inside loops.
- Keep related database operations in a single transaction.
- Be careful with SQLAlchemy identity-map conflicts.
- Preserve existing relationships and foreign keys.

## Authentication

- Existing protected endpoints use `verify_cognito_token`.
- Do not remove authentication unless explicitly requested.

## API

- Keep REST endpoints consistent with the existing routers.
- Use proper HTTP status codes.
- Raise `HTTPException` for errors.
- Preserve backwards compatibility whenever possible.

## Validation

- Validate request data.
- Handle nullable values safely.
- Do not trust frontend validation alone.

## AWS

- The application runs on AWS Lambda using Mangum.
- Do not modify deployment or infrastructure unless explicitly requested.
- Keep S3 access consistent with the existing `img_S3` router.

## Architecture

- Prefer consistency over introducing new patterns.
- Reuse existing services and utilities.
- Keep `main.py` responsible only for application setup and router registration.