# Interview Bot - Backend Developer Project

## Project Overview
This project is a scalable backend system paired with a basic frontend UI, designed to simulate an interview preparation platform. It includes secure user authentication with JWT, role-based access control, and full CRUD operations for a task management entity, showcasing practical backend and frontend integration.

## Features

### Backend
- User registration and login with secure password hashing (`bcrypt`)
- JWT-based authentication and token management
- Role-based access control (Admin vs User)
- CRUD APIs for managing interview-related tasks/entities
- Input validation, error handling, and API versioning
- API documentation available via Swagger/OpenAPI
- MongoDB as the primary database for persistence
- Modular and scalable project architecture

### Frontend
- Simple UI using Streamlit for user registration, login, and dashboard
- JWT token usage to access protected routes
- Task management with create, read, update, and delete functionality
- Displays API response messages for success and errors

## Technologies Used
- Backend: Python, FastAPI/Flask (adjust according to your actual backend framework)
- Database: MongoDB
- Authentication: JWT, bcrypt
- Frontend: Streamlit
- API Documentation: Swagger (OpenAPI)
- Others: Python libraries for validation and security

## Setup Instructions

1. Clone the repository: 

2. Navigate to the backend directory and install dependencies:

3. Configure environment variables (e.g., MongoDB URI, JWT secret) in a `.env` file.

4. Run the backend server:

5. Open the frontend UI:

6. Access API documentation at:

## Scalability Notes
- Designed for modular expansion with separate modules for authentication, routes, and models.
- Scalable to microservices architecture if needed.
- Ready for caching implementation (e.g., Redis) to improve performance.
- Can be containerized using Docker for consistent deployment.
- Load balancing and horizontal scaling can be integrated for high traffic management.



Thank you for reviewing my project.
