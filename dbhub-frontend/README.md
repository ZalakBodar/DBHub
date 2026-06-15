# DBHub

AI-Powered Multi-Database Management Platform

## Overview

DBHub is a full-stack database management platform built using Angular, FastAPI, and MSSQL.

It allows users to:

- Connect multiple database systems
- Manage metadata
- Explore database schemas
- Execute SQL queries
- View database relationships
- Generate SQL using AI
- Maintain query history
- Control access using user roles

---

## Features

### Dashboard
- Total Tables
- Total Users
- Database Status
- Connector Type
- Database Health
- Recent Activities

### Connectors
Supports:

- Microsoft SQL Server
- PostgreSQL
- Oracle

Functions:

- Add Connector
- Test Connection
- Activate Connector
- Delete Connector

### Metadata Management

Store business descriptions for:

- Tables
- Columns

Used by AI Assistant for better SQL generation.

### Data Viewer

- View table data
- Dynamic loading
- Database independent

### Query Runner

- Execute custom SQL
- View results instantly

### AI Assistant

Generate SQL using natural language.

Example:

Input:

```text
show all employees
```

Output:

```sql
SELECT * FROM Employees;
```

The AI uses:

- Database Schema
- Metadata Context
- Database Type

to generate accurate SQL.

### Query History

Stores:

- User Question
- Generated SQL
- Execution Timestamp

### Relationships

Displays foreign-key relationships between tables.

Example:

Departments.DepartmentID
↓
Employees.DepartmentID

### User Management

Roles:

- Admin
- Developer
- Viewer

Role-based access control is implemented.

---

## Technology Stack

### Frontend

- Angular
- TypeScript
- HTML
- CSS

### Backend

- FastAPI
- Python

### Databases

- Microsoft SQL Server
- PostgreSQL
- Oracle

### AI

- Large Language Model Integration

---

## Project Structure

DBHub

├── dbhub-frontend

│ ├── Dashboard

│ ├── Connectors

│ ├── Metadata

│ ├── Data Viewer

│ ├── Query Runner

│ ├── AI Assistant

│ ├── Query History

│ └── Relationships

│

└── dbhub-backend

├── FastAPI APIs

├── Database Connectors

├── AI SQL Generation

├── Query Execution

└── Metadata Engine

---

## Future Enhancements

- JWT Authentication
- Query Analytics
- ER Diagram Visualization
- Export Reports
- Audit Logs
- AI Query Optimization

---

## Author

Zalak Bodar

DBHub Project 