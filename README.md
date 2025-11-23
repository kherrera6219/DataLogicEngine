# Universal Knowledge Graph (UKG) System

[![CI/CD Pipeline](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/ci.yml/badge.svg)](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/ci.yml)
[![Security Audit](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/security.yml/badge.svg)](https://github.com/kherrera6219/DataLogicEngine/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive AI knowledge management system with a 13-axis Universal Knowledge Graph, featuring advanced simulation capabilities, multi-persona analysis, and enterprise-grade security.

## 🌟 Features

- **13-Axis Knowledge Graph**: Multi-dimensional knowledge representation across domains, time, location, skills, roles, and more
- **AI-Powered Chat Interface**: Natural language interaction with the knowledge base
- **Multi-Persona Analysis**: KE (Knowledge Expert), SE (Skill Expert), RE (Role Expert), CE (Context Expert)
- **Live Agent Simulation**: Real-time simulation of knowledge acquisition and refinement
- **Enterprise Security**: OAuth/Azure AD integration, role-based access control, audit logging
- **Interactive Visualizations**: D3.js-powered honeycomb graphs, spiderweb diagrams, and force-directed graphs

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Installation](#installation)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Quick Start

### Prerequisites

- **Node.js** 18.x or higher
- **Python** 3.11 or higher
- **PostgreSQL** 14.x or higher (or SQLite for development)
- **Git**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/kherrera6219/DataLogicEngine.git
   cd DataLogicEngine
   ```

2. **Set up environment variables**
   ```bash
   cp .env.template .env
   python generate_secrets.py  # Generate secure secrets
   # Edit .env and add the generated secrets
   ```

3. **Install frontend dependencies**
   ```bash
   npm install
   ```

4. **Install backend dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Initialize the database**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

6. **Run the development servers**

   Terminal 1 (Frontend):
   ```bash
   npm run dev
   ```

   Terminal 2 (Backend):
   ```bash
   python app.py
   ```

7. **Open your browser**
   Navigate to `http://localhost:3000`

## 🏗️ Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Chat   │  │  Graph   │  │ Analytics│  │  Admin   │   │
│  │   UI     │  │  Viz     │  │Dashboard │  │  Panel   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                           ↓ HTTP/REST API
┌─────────────────────────────────────────────────────────────┐
│                   Backend (Flask/Python)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Auth   │  │  Query   │  │Simulation│  │  Admin   │   │
│  │  Layer   │  │  Engine  │  │  Engine  │  │   API    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                Core Knowledge Graph Engine                  │
│  ┌──────────────────────────────────────────────────┐      │
│  │         13-Axis Knowledge Representation         │      │
│  │  (Domain│Time│Location│Skills│Roles│Methods...)  │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│             Data Layer (PostgreSQL/SQLite)                  │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

**Frontend:**
- Next.js 14+ (React framework)
- Fluent UI React Components (Microsoft Design System)
- D3.js (Data visualization)
- React Force Graph (Network visualizations)
- Jest + React Testing Library (Testing)

**Backend:**
- Flask (Python web framework)
- SQLAlchemy (ORM)
- Flask-Login (Authentication)
- pytest (Testing)

**Infrastructure:**
- GitHub Actions (CI/CD)
- Docker (Containerization)
- PostgreSQL (Production database)
- Redis (Caching - optional)

## 💻 Development

### Project Structure

```
DataLogicEngine/
├── pages/              # Next.js pages and API routes
│   ├── api/           # API route handlers
│   ├── chat.js        # Chat interface
│   ├── login.js       # Authentication
│   └── ...
├── components/        # React components
│   └── ui/           # Reusable UI components
├── backend/          # Python backend services
│   ├── api.py        # Main API endpoints
│   ├── auth.py       # Authentication logic
│   ├── security/     # Security modules
│   └── ...
├── core/             # Core knowledge graph engine
│   ├── simulation/   # Simulation engine
│   ├── persona/      # Multi-persona system
│   └── ...
├── utils/            # Shared utilities
├── tests/            # Python tests
├── __tests__/        # JavaScript tests
├── .github/          # GitHub Actions workflows
│   └── workflows/
└── docs/             # Documentation
```

### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the existing code style
   - Write tests for new features
   - Update documentation as needed

3. **Run tests**
   ```bash
   # Frontend tests
   npm test

   # Backend tests
   python -m pytest tests/ -v
   ```

4. **Lint your code**
   ```bash
   npm run lint
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

6. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Style Guidelines

- **JavaScript/TypeScript**: Follow ESLint rules (next/core-web-vitals)
- **Python**: Follow PEP 8 style guide
- **Commit Messages**: Use conventional commits format
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation changes
  - `test:` for test additions
  - `refactor:` for code refactoring

## 🧪 Testing

### Frontend Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### Backend Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=backend --cov=core --cov-report=html

# Run specific test file
python -m pytest tests/test_validators.py -v
```

### Test Coverage Goals

- **Overall**: Minimum 60% coverage
- **Critical paths**: Minimum 80% coverage
- **New code**: Minimum 80% coverage

## 🚢 Deployment

### Environment Variables

Required environment variables for production:

```bash
# Security (REQUIRED)
SECRET_KEY=<64+ character random string>
JWT_SECRET_KEY=<64+ character random string>

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ukg_database

# Azure Integration
AZURE_AD_TENANT_ID=<your-tenant-id>
AZURE_AD_CLIENT_ID=<your-client-id>
AZURE_AD_CLIENT_SECRET=<your-client-secret>
AZURE_OPENAI_API_KEY=<your-api-key>

# CORS (comma-separated allowed origins)
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Environment
FLASK_ENV=production
NODE_ENV=production
```

### Docker Deployment

```bash
# Build the image
docker build -t ukg-system .

# Run the container
docker run -p 3000:3000 -p 5000:5000 --env-file .env ukg-system
```

### Production Checklist

- [ ] Set strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Configure PostgreSQL database
- [ ] Set up Azure AD/Entra ID integration
- [ ] Configure CORS with specific domains
- [ ] Enable HTTPS/TLS
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy
- [ ] Run security audit
- [ ] Enable rate limiting
- [ ] Configure CDN for static assets

## 🔒 Security

### Security Features

- **XSS Protection**: DOMPurify sanitization on all user-generated content
- **CSRF Protection**: Enabled on all forms
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **Secure Headers**: CSP, X-Frame-Options, X-Content-Type-Options, HSTS
- **Authentication**: HTTP-only cookies, bcrypt password hashing
- **Authorization**: Role-based access control (RBAC)
- **Audit Logging**: All sensitive operations logged
- **Dependency Scanning**: Automated security audits via GitHub Actions

### Reporting Security Issues

If you discover a security vulnerability, please email security@example.com instead of using the issue tracker.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/kherrera6219/DataLogicEngine/issues)
- **Discussions**: [GitHub Discussions](https://github.com/kherrera6219/DataLogicEngine/discussions)

## 🙏 Acknowledgments

- Microsoft Fluent UI for the design system
- D3.js community for visualization tools
- Flask and Next.js communities

---

**Built with ❤️ by the UKG Team**
