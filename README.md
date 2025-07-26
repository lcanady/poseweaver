# PoseWeaver

Your AI co-writer for immersive roleplay. PoseWeaver transforms simple poses into rich narratives and generates vivid descriptions from images. Built specifically for MUSH (Multi-User Shared Hallucination) roleplayers with character-aware AI that follows proper roleplay etiquette.

## Features

- **Character Management**: Create and manage multiple characters with detailed profiles (Free: 3, Basic: 10, Pro: unlimited)
- **AI Pose Enhancement**: Transform simple poses into rich, engaging narratives with character-aware AI
- **Image Description Writer**: Upload images and generate detailed, vivid descriptions for characters and scenes
- **Advanced Customization**: Three enhancement styles, refinement tools, version history, and advanced settings
- **Smart AI Integration**: Powered by Venice AI's multimodal models with MUSH roleplay etiquette validation
- **Flexible Pricing**: Start free (20 generations/month), upgrade to Basic ($9.99 - 200/month) or Pro ($19.99 - 500/month)
- **Mobile-Responsive Design**: Works seamlessly across desktop and mobile devices

## Technology Stack

### Backend
- **Flask** - Python web framework
- **Venice.ai API** - AI model integration (Dolphin uncensored thinking)
- **MongoDB Atlas** - Cloud database for user and character data
- **pytest** - Testing framework

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling framework
- **React 18** - User interface library

### Process Management
- **PM2** - Production process manager for Node.js and Python applications
- **Concurrently** - Development tool for running multiple processes

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- Venice.ai API key
- MongoDB Atlas account (or local MongoDB installation)
- PM2 (for production deployment)

### Development Setup

1. **Clone and Install Dependencies**
   ```bash
   git clone <repository-url>
   cd poseweaver
   
   # Install root dependencies (includes PM2 and concurrently)
   npm install
   
   # Install backend dependencies
   cd backend
   pip install -r requirements.txt
   
   # Install frontend dependencies
   cd ../frontend
   npm install
   cd ..
   ```

2. **Environment Configuration**
   ```bash
   # Copy environment template
   cp backend/.env.example backend/.env
   
   # Edit backend/.env with your configuration:
   # - VENICE_API_KEY=your_venice_api_key
   # - MONGODB_URI=your_mongodb_atlas_connection_string
   # - STRIPE_SECRET_KEY=your_stripe_key (optional)
   ```

3. **Start Development Servers**
   ```bash
   # Option 1: Use PM2 (recommended)
   pm2 start ecosystem.config.js --env development
   
   # Option 2: Use npm script with concurrently
   npm run dev
   
   # Option 3: Manual start (separate terminals)
   # Terminal 1 - Backend
   cd backend && python app.py
   
   # Terminal 2 - Frontend
   cd frontend && npm run dev
   ```

4. **Access Your Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5001

## Development Commands

### PM2 Process Management
```bash
# View running processes
pm2 status

# View logs
pm2 logs                    # All processes
pm2 logs poseweaver-backend # Backend only
pm2 logs poseweaver-frontend # Frontend only

# Restart services
pm2 restart all
pm2 restart poseweaver-backend
pm2 restart poseweaver-frontend

# Stop services
pm2 stop all
pm2 delete all              # Stop and remove from PM2
```

### Make Commands
The project includes a Makefile with convenient development commands:

```bash
make help      # Show all available commands
make install   # Install dependencies
make dev       # Start development servers (shows manual commands)
make test      # Run all tests
make clean     # Clean up build artifacts
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

## MongoDB Setup

### MongoDB Atlas (Recommended)
1. Create a free account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a new cluster
3. Create a database user with read/write permissions
4. Get your connection string from the "Connect" button
5. Add the connection string to your `backend/.env` file:
   ```
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/poseweaver?retryWrites=true&w=majority
   ```

### Local MongoDB (Alternative)
If you prefer to run MongoDB locally:
```bash
# Install MongoDB (macOS)
brew install mongodb-community

# Start MongoDB
brew services start mongodb-community

# Use local connection string in .env
MONGODB_URI=mongodb://localhost:27017/poseweaver
```

## Production Deployment

### Using PM2 (Recommended)
```bash
# Start in production mode
pm2 start ecosystem.config.js --env production

# Save PM2 configuration
pm2 save

# Setup PM2 to start on system boot
pm2 startup
```

### Environment Variables for Production
Ensure these are set in your production environment:
- `MONGODB_URI` - Your MongoDB connection string
- `VENICE_API_KEY` - Your Venice.ai API key
- `SECRET_KEY` - Flask secret key for sessions
- `FLASK_ENV=production`
- `NODE_ENV=production`

## Project Structure

```
poseweaver/
├── backend/                 # Flask backend
│   ├── app/
│   │   ├── __init__.py     # Flask app factory
│   │   ├── api/            # API endpoints
│   │   ├── services/       # Business logic
│   │   ├── models/         # Data models
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment template
├── frontend/               # Next.js frontend
│   ├── app/                # App Router pages
│   ├── components/         # React components
│   ├── lib/                # Utility libraries
│   ├── public/             # Static assets
│   └── package.json        # Node.js dependencies
├── ecosystem.config.js     # PM2 configuration
├── package.json            # Root dependencies (PM2, concurrently)
├── Makefile               # Development commands
└── README.md              # This file
```

## Recent Changes: Docker to PM2 Migration

**🚀 We've migrated from Docker to PM2 for better development experience!**

### What Changed:
- ✅ **Removed Docker**: No more Docker containers, Dockerfiles, or docker-compose files
- ✅ **Added PM2**: Production-ready process manager for both Node.js and Python
- ✅ **Simplified Setup**: Direct native development without virtualization overhead
- ✅ **Better Performance**: Faster startup times and easier debugging
- ✅ **MongoDB Atlas**: Cloud database instead of local Docker containers

### Migration Benefits:
- **Faster Development**: No container build times
- **Easier Debugging**: Direct access to processes and logs
- **Better Resource Usage**: No Docker overhead
- **Simplified Deployment**: PM2 handles process management natively
- **Cross-Platform**: Works consistently across macOS, Linux, and Windows

### If You Had Docker Setup Before:
```bash
# Remove old Docker artifacts (if any)
docker-compose down
docker system prune -f

# Follow the new setup instructions above
npm install
pm2 start ecosystem.config.js --env development
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