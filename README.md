# PoseWeaver

Your AI co-writer for immersive roleplay. PoseWeaver transforms simple poses
into rich narratives and generates vivid descriptions from images. Built
specifically for MUSH (Multi-User Shared Hallucination) roleplayers with
character-aware AI that follows proper roleplay etiquette.

## Features

- **Character Management**: Create and manage multiple characters with detailed
  profiles (Free: 3, Basic: 10, Pro: unlimited)
- **AI Pose Enhancement**: Transform simple poses into rich, engaging narratives
  with character-aware AI
- **Image Description Writer**: Upload images and generate detailed, vivid
  descriptions for characters and scenes
- **Advanced Customization**: Three enhancement styles, refinement tools,
  version history, and advanced settings
- **Smart AI Integration**: Powered by OpenRouter AI's multimodal models with
  MUSH roleplay etiquette validation
- **Mobile-Responsive Design**: Works seamlessly across desktop and mobile
  devices

## Technology Stack

### Frontend (App Router)

- **Next.js 15.2** - React Framework with Server Components and App Router
- **React 19** - Latest React features (Server Actions, `useActionState`, etc.)
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling framework with `tailwindcss-animate`
- **Radix UI** - Accessible UI primitives
- **Zod** - Schema validation

### Backend

- **Flask** - Python web framework
- **OpenRouter.ai API** - AI model integration
- **MongoDB** - Data persistence (via `pymongo`)
- **Redis** - Caching and session management (Planned)
- **pytest** - Testing framework
- **Docker** - Containerization

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- OpenRouter.ai API key

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd poseweaver
   ```

2. **Set up environment variables**
   ```bash
   cp backend/env.example backend/.env
   # Edit backend/.env with your OpenRouter.ai API key
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
   # Edit .env with your OpenRouter.ai API key
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
make build     # Build Docker images
make logs      # Show application logs
make test      # Run all tests
```

## API Endpoints

### Character Processing

- `POST /api/characters/brain-dump` - Process character descriptions
- `POST /api/characters/pose-context` - Analyze pose context

### Pose Generation

- `POST /api/pose/generate` - Generate enhanced poses

### Health Check

- `GET /health` - Application health status

## Development Workflow

1. **Frontend**: We use Next.js App Router. Place pages in `app/`. Use Server
   Components by default.
2. **Backend**: Flask API. Follow TDD.
3. **Git**: Create feature branches.

## Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Submit a pull request**
