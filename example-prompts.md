# Example Prompts for Software Maker

This document contains example prompts you can use to test the Software Maker Platform.

## 🎯 Simple Examples (Good for First Test)

### 1. Hello World API
```
Create a simple FastAPI application with a single endpoint that returns "Hello, World!"
Include a health check endpoint and basic error handling.
```

### 2. Todo API
```
Build a REST API for a todo list application with:
- SQLite database
- CRUD endpoints (Create, Read, Update, Delete)
- Pydantic models for validation
- Simple in-memory storage
```

### 3. Static Website
```
Create a simple static website with:
- HTML, CSS, JavaScript
- Homepage with navigation
- About page
- Contact form
- Responsive design
```

## 🚀 Intermediate Examples

### 4. Blog API with Authentication
```
Build a blog API using FastAPI with:
- PostgreSQL database
- User authentication with JWT tokens
- Blog post CRUD operations
- Author-post relationships
- Comments system
- Password hashing with bcrypt
- API documentation with OpenAPI
```

### 5. React Dashboard
```
Create a React dashboard application with:
- TypeScript
- Component-based architecture
- Mock API integration
- Charts using Chart.js
- Dark/light mode toggle
- Responsive layout
- Local storage for preferences
```

### 6. File Upload Service
```
Build a file upload microservice with:
- FastAPI backend
- File validation (size, type)
- Storage in local filesystem
- File metadata in SQLite
- Download endpoints
- File listing with pagination
- Docker deployment
```

## 💼 Advanced Examples

### 7. E-commerce Backend
```
Create a complete e-commerce backend API with:
- User management and authentication
- Product catalog with categories
- Shopping cart functionality
- Order management
- Payment integration structure (Stripe-ready)
- PostgreSQL database with proper relationships
- Redis caching for product data
- RESTful API design
- Comprehensive error handling
- Unit and integration tests
- Docker deployment with docker-compose
```

### 8. Real-time Chat Application
```
Build a real-time chat application with:
- FastAPI backend with WebSocket support
- React frontend with TypeScript
- User authentication
- Multiple chat rooms
- Message history persistence (PostgreSQL)
- Online user status
- Typing indicators
- Message timestamps
- Responsive UI design
- Docker deployment
```

### 9. Task Management System
```
Create a task management system similar to Trello with:
- FastAPI backend
- React frontend with drag-and-drop
- User authentication and authorization
- Boards, lists, and cards structure
- Task assignment to users
- Due dates and priorities
- File attachments
- Activity log
- Email notifications structure
- PostgreSQL database
- Redis for caching
- Comprehensive test suite
- Docker deployment
```

### 10. Analytics Dashboard
```
Build an analytics dashboard with:
- Python backend (FastAPI) for data processing
- React frontend with TypeScript
- Data visualization using Chart.js and D3.js
- Real-time data updates via WebSockets
- PostgreSQL for data storage
- Data export functionality (CSV, JSON)
- Filters and date range selection
- Multiple chart types (line, bar, pie)
- Responsive design
- Authentication system
- API rate limiting
- Caching strategy with Redis
- Complete test coverage
- Docker deployment
```

## 🎓 Domain-Specific Examples

### 11. Healthcare Appointment System
```
Create a healthcare appointment scheduling system with:
- Patient management
- Doctor scheduling
- Appointment booking and cancellation
- Email/SMS notification structure
- Patient medical history
- Prescription management
- HIPAA compliance considerations
- Role-based access control (admin, doctor, patient)
- PostgreSQL database
- RESTful API
- Comprehensive logging
- Docker deployment
```

### 12. Learning Management System (LMS)
```
Build a learning management system with:
- Course management (create, edit, delete)
- Student enrollment system
- Progress tracking
- Quiz and assessment system
- Grade management
- Video content support
- Discussion forums
- Assignment submission
- Teacher and student roles
- PostgreSQL database
- File storage system
- RESTful API
- React frontend
- Docker deployment
```

### 13. Inventory Management System
```
Create an inventory management system with:
- Product catalog
- Stock level tracking
- Purchase orders
- Supplier management
- Low stock alerts
- Barcode scanning support
- Reports and analytics
- Multi-location support
- User permissions system
- PostgreSQL database
- RESTful API
- React admin dashboard
- Excel export functionality
- Docker deployment
```

## 🛠️ Utility Tools

### 14. Log Analyzer CLI
```
Build a command-line log analysis tool with:
- Python with Click framework
- Parse various log formats
- Filter by date, level, pattern
- Statistics and summaries
- Output formatting options
- Export to JSON/CSV
- Comprehensive help documentation
- Unit tests
```

### 15. API Documentation Generator
```
Create a tool to generate API documentation with:
- Parse OpenAPI/Swagger specifications
- Generate beautiful HTML documentation
- Interactive API explorer
- Code examples in multiple languages
- Search functionality
- Markdown support
- Customizable themes
- Export to PDF
```

## 📱 Full-Stack Examples

### 16. Social Media Platform (Simplified)
```
Build a simplified social media platform with:
- User profiles with avatars
- Post creation (text, images)
- Follow/unfollow system
- Like and comment functionality
- News feed algorithm (simple chronological)
- User search
- Hashtag support
- Notification system
- FastAPI backend
- React frontend
- PostgreSQL database
- Redis for caching
- Image storage system
- WebSocket for real-time updates
- Complete authentication system
- Comprehensive tests
- Docker deployment
```

### 17. Project Management Tool
```
Create a project management tool with:
- Project and workspace management
- Task boards (Kanban style)
- Sprint planning
- Time tracking
- Team collaboration features
- File sharing
- Comments and discussions
- Activity timeline
- Gantt chart view
- Reports and analytics
- User roles and permissions
- Email notifications
- FastAPI backend
- React frontend with TypeScript
- PostgreSQL database
- Redis caching
- WebSocket for real-time updates
- Comprehensive test suite
- Docker deployment
```

## 🔬 How to Use These Prompts

1. **Copy the prompt** you want to try
2. **Paste it** into the Software Maker dashboard, CLI, or API
3. **Wait** for the system to build the complete application
4. **Check the logs** to see progress
5. **Test the generated code** in the `projects/` directory

## 💡 Tips for Writing Good Prompts

1. **Be Specific**: Mention technologies you want (FastAPI, React, PostgreSQL, etc.)
2. **List Features**: Break down what functionality you need
3. **Include Non-functional Requirements**: Authentication, testing, deployment
4. **Specify Data Models**: Describe entities and relationships
5. **Mention Deployment**: Docker, docker-compose, etc.

## 🎯 Expected Outcomes

For each prompt, the system will:
- ✅ Generate complete, working code
- ✅ Create all necessary files
- ✅ Write tests
- ✅ Create Docker deployment files
- ✅ Fix any errors automatically
- ✅ Provide a fully functional application

## 🐛 If Something Goes Wrong

1. Check the logs: `smaker logs <project-id>`
2. View the system status: `curl http://localhost:8000/system/verify`
3. Check worker logs: `cd docker && docker-compose logs worker`
4. The system will auto-retry failed steps up to 5 times

---

Happy building! 🚀
