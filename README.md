# Your Meal Planner Deluxe Edition

A comprehensive meal planning and shopping list application that helps users create personalized meal plans, generate automated shopping lists, and efficiently track ingredients for a healthier lifestyle.

## Overview

YMP (Your Meal Planner) Deluxe Edition is a modern, backend web application designed to simplify meal planning and grocery shopping. Built with Python and FastAPI, this application provides a robust API-driven solution for managing recipes, creating meal plans, and organizing shopping lists with a focus on user experience and data consistency.

## Key Features

### Recipe Management
- **Comprehensive Recipe Database**: Store and organize recipes with detailed ingredients and cooking instructions
- **Recipe Categories**: Organize recipes by meal type (breakfast, lunch, dinner, dessert)
- **Personal Recipe Collection**: Create and customize your own recipe collection
- **Ingredient Tracking**: Detailed ingredient lists with quantities and preparation notes

### Meal Planning
- **Weekly Meal Plans**: Plan meals for multiple days with flexible scheduling
- **Meal Type Organization**: Separate planning for breakfast, lunch, dinner, and desserts
- **Calendar Integration**: Visual meal planning interface with date-based organization
- **Plan Persistence**: Save and reuse meal plans for future weeks

### Smart Shopping Lists
- **Automatic List Generation**: Generate shopping lists based on planned meals
- **Ingredient Consolidation**: Smart aggregation of ingredients across multiple recipes
- **Shopping List Management**: Add, edit, and organize shopping items efficiently
- **Cross-referencing**: Link shopping items back to their respective recipes

### User Management
- **Secure Authentication**: JWT-based authentication system with session management
- **User Profiles**: Personal user accounts with individual meal plans and recipes
- **Data Privacy**: User-specific data isolation and secure access controls
- **Session Management**: Redis-based session storage for optimal performance

## Technology Stack

### Backend
- **Python 3.12+**: Modern Python with type hints and async support
- **FastAPI**: High-performance, modern web framework for building APIs
- **SQLAlchemy**: Advanced ORM with support for complex relationships
- **PostgreSQL**: Robust relational database for data persistence
- **Redis**: In-memory data structure store for session management
- **Alembic**: Database migration tool for schema version control

### DevOps & Deployment
- **Docker**: Containerized deployment with multi-service orchestration
- **Docker Compose**: Local development environment setup
- **UV**: Fast Python package installer and resolver
- **Uvicorn**: ASGI server for high-performance application serving

### Code Quality
- **MyPy**: Static type checking for improved code reliability
- **Ruff**: Fast Python linter and code formatter
- **Pytest**: Comprehensive testing framework with async support
- **Type Hints**: Full type annotation coverage for better IDE support

## Architecture

The application follows a clean, layered architecture pattern:

```
src/
├── models/          # SQLAlchemy ORM models
│   └── recipes.py   # User, Recipe, and UserPlan models
├── services/        # Business logic layer
│   ├── recipe_manager.py
│   ├── shopping_list_service.py
│   ├── user_auth_manager.py
│   └── user_plan_manager.py
├── resources/       # API endpoints and request handlers
├── helpers/         # Utility functions and helpers
├── alembic/         # Database migration scripts
├── app.py          # FastAPI application factory
├── config.py       # Application configuration
├── dependencies.py # Dependency injection setup
└── extensions.py   # Third-party extensions setup
```

## Getting Started

### Prerequisites
- Python 3.12 or higher
- Docker and Docker Compose
- PostgreSQL
- Redis

### Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/toster3d/YMP-deluxe-edition.git
   cd YMP-deluxe-edition
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. **Docker Deployment (Recommended)**
   ```bash
   docker-compose up --build
   ```

4. **Local Development Setup**
   ```bash
   # Install dependencies
   uv pip install -e .
   
   # Run database migrations
   alembic upgrade head
   
   # Start the development server
   uvicorn src.app:app --host 0.0.0.0 --port 5000 --reload
   ```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Downgrade to previous version
alembic downgrade -1
```

## Database Schema

### Core Models

**User Model**
- User authentication and profile management
- Links to personal recipes and meal plans

**Recipe Model**
- Recipe details with ingredients and instructions
- Categorized by meal type (breakfast, lunch, dinner, dessert)
- Linked to user accounts for personalization

**UserPlan Model**
- Date-based meal planning
- Supports multiple meals per day
- Flexible meal assignment system

## Configuration

### Environment Variables

```bash
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=recipes
ASYNC_DATABASE_URI=postgresql+asyncpg://user:pass@host:port/db

# Application Settings
PYTHONPATH=/app/src
DEBUG=True
SECRET_KEY=your_secret_key

# Redis Configuration (for sessions)
REDIS_URL=redis://localhost:6379
```

# Testing Section Update

## Testing

The project uses **nox** for test automation, which provides isolated virtual environments and cross-version testing capabilities. Nox uses a `noxfile.py` configuration file to define test sessions.

### Available Commands

```bash
# List all available nox sessions
nox --list
# or
nox -l

# Run all test sessions
nox

# Run specific test session
nox --session tests
# or
nox -s tests

# Run tests with coverage
nox --session coverage
# or
nox -s coverage

# Run tests for specific Python versions
nox --python 3.11
nox --python 3.10 3.11 3.12

# Run tests with custom arguments (passed to pytest)
nox --session tests -- --verbose
nox --session tests -- tests/test_recipe_manager.py
nox --session tests -- --maxfail=1

# Run tests and pass coverage arguments
nox --session coverage -- --cov-report=html
```

### Common Session Examples

Based on typical nox configurations, the project likely includes sessions such as:

```python
@nox.session(python=["3.10", "3.11", "3.12"])
def tests(session):
    """Run the test suite."""
    session.install("pytest", "pytest-asyncio")
    session.install("-e", ".")
    session.run("pytest", *session.posargs)

@nox.session(python="3.11")
def coverage(session):
    """Run tests with coverage reporting."""
    session.install("pytest", "pytest-cov", "pytest-asyncio")
    session.install("-e", ".")
    session.run("pytest", "--cov=src", "--cov-report=html", *session.posargs)
```

## Performance & Scalability

- **Async/Await Support**: Full asynchronous request handling for improved performance
- **Connection Pooling**: PostgreSQL connection pooling for efficient database access
- **Redis Caching**: Session data and frequently accessed information cached in Redis
- **Docker Optimization**: Multi-stage builds and optimized container images
- **Database Indexing**: Properly indexed database tables for fast queries

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive tests for new features
- Update documentation for API changes
- Use conventional commit messages

## API Documentation

Once the application is running, visit:
- **Swagger UI**: `http://localhost:5000/docs`
- **ReDoc**: `http://localhost:5000/redoc`

### Key Endpoints

```
GET    /health              # Health check endpoint
POST   /auth/login          # User authentication
POST   /auth/register       # User registration
GET    /recipes             # List user recipes
POST   /recipes             # Create new recipe
GET    /meal-plans          # Get user meal plans
POST   /meal-plans          # Create meal plan
GET    /shopping-lists      # Generate shopping list
```

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Bcrypt password hashing with salt
- **Session Management**: Secure session handling with Redis
- **Input Validation**: Comprehensive input validation and sanitization
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection attacks

## Docker Support

The application includes comprehensive Docker support:

- **Multi-service Setup**: PostgreSQL, Redis, and application containers
- **Health Checks**: Built-in health monitoring for all services
- **Volume Persistence**: Data persistence across container restarts
- **Environment Isolation**: Separate environments for development and production

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with ❤️ using modern Python technologies
- Inspired by the need for simple, effective meal planning solutions
- Thanks to the open-source community for excellent tools and libraries

## Support

For support, questions, or feature requests:
- Create an issue on GitHub
- Contact the development team
- Check the documentation

---

**Your Meal Planner Deluxe Edition** - Making meal planning simple, efficient, and enjoyable!
