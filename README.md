# MUSH Pose Editor

An AI-powered writing assistant specifically designed for MUSH (Multi-User Shared Hallucination) roleplayers. This application helps enhance roleplay poses, develop consistent characters, and analyze scene context using Venice.ai's Dolphin uncensored thinking model.

## Features

- **Character Brain Dump Processing**: Transform free-form character descriptions into structured profiles
- **Pose Context Analysis**: Analyze poses from other players to identify key response elements
- **Intelligent Pose Enhancement**: Transform basic actions into rich, detailed narratives
- **Uncensored AI Support**: Handle mature roleplay content appropriately without restrictions
- **Character Voice Consistency**: Maintain established character personalities and speech patterns
- **Mobile-Responsive Design**: Works seamlessly across desktop and mobile devices

## Technology Stack

### Backend
- **Flask** - Python web framework
- **Venice.ai API** - AI model integration (Dolphin uncensored thinking)
- **pytest** - Testing framework
- **Docker** - Containerization

### Frontend
- **React 18** - User interface framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling framework
- **Vite** - Build tool and development server
- **Vitest** - Testing framework

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- Venice.ai API key

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mush-pose-editor
   ```

2. **Set up environment variables**
   ```bash
   cp backend/env.example backend/.env
   # Edit backend/.env with your Venice.ai API key
   ```

3. **Start the development environment**
   ```bash
   make start
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000

### Local Development

1. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp env.example .env
   # Edit .env with your Venice.ai API key
   python app.py
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Development Commands

The project includes a Makefile with convenient development commands:

```bash
make help      # Show all available commands
make start     # Start development environment
make stop      # Stop development environment
make test      # Run all tests
make clean     # Clean up containers and volumes
make build     # Build Docker images
make logs      # Show application logs
make lint      # Run linting
make format    # Format code
```

## API Endpoints

### Character Processing
- `POST /api/characters/brain-dump` - Process character descriptions
- `POST /api/characters/pose-context` - Analyze pose context

### Pose Generation
- `POST /api/pose/generate` - Generate enhanced poses

### Health Check
- `GET /health` - Application health status

## Testing

The project follows Test-Driven Development (TDD) principles with comprehensive test coverage:

### Backend Testing
```bash
# Run all backend tests
cd backend && pytest

# Run with coverage
cd backend && pytest --cov=app --cov-report=html
```

### Frontend Testing
```bash
# Run all frontend tests
cd frontend && npm test

# Run with coverage
cd frontend && npm run test:coverage
```

### End-to-End Testing
```bash
# Run E2E tests (coming soon)
npm run test:e2e
```

## Project Structure

```
mush-pose-editor/
├── backend/                 # Flask backend
│   ├── app/
│   │   ├── __init__.py     # Flask app factory
│   │   ├── api/            # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── models/         # Data models
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend container
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   ├── types/          # TypeScript types
│   │   └── utils/          # Utility functions
│   ├── tests/              # Frontend tests
│   ├── package.json        # Node.js dependencies
│   └── Dockerfile         # Frontend container
├── docker-compose.yml      # Development environment
├── Makefile               # Development commands
└── README.md              # This file
```

## Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Venice AI Configuration
VENICE_API_KEY=your_venice_api_key_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Model Configuration
DEFAULT_MODEL=dolphin-2.9-llama3-70b
DEFAULT_TEMPERATURE=0.7
DEFAULT_MAX_TOKENS=1000
```

### Model Configuration

The application uses Venice.ai's Dolphin uncensored thinking model by default. You can configure:

- **Temperature**: Controls creativity (0.0 - 1.0)
- **Max Tokens**: Maximum response length
- **Model**: Specific model variant

## Contributing

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Follow TDD principles**
   - Write tests first
   - Implement functionality
   - Ensure >90% test coverage
4. **Run tests and linting**
   ```bash
   make test
   make lint
   ```
5. **Submit a pull request**

## Development Workflow

1. **Write tests first** (TDD approach)
2. **Implement functionality** to pass tests
3. **Refactor** while maintaining test coverage
4. **Run full test suite** before committing
5. **Use meaningful commit messages**

## Performance Targets

- **API Response Time**: < 30 seconds for AI processing
- **UI Interactions**: < 2 seconds
- **Test Coverage**: > 90%
- **Uptime**: 99.5%

## Security

- Input validation and sanitization
- API key protection
- CORS configuration
- Content security headers
- Rate limiting (planned)

## License

[License information to be added]

## Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Follow the contributing guidelines
- Ensure all tests pass

## Roadmap

- [x] Project setup and infrastructure
- [ ] Venice.ai integration
- [ ] Character brain dump processing
- [ ] Pose context analysis
- [ ] Pose enhancement engine
- [ ] Frontend components
- [ ] Testing suite
- [ ] Production deployment

---

**Built with ❤️ for the MUSH roleplay community** 