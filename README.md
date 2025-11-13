# Unified Full-Stack Chatbot

A single-folder full-stack application with React frontend and Flask backend for AI file analysis.

## 🏗️ Unified Project Structure
chatbot/
├── src/                    # React components
│   ├── components/
│   ├── App.js
│   └── index.js
├── public/                 # Static assets
├── app.py                  # Flask backend
├── requirements.txt        # Python dependencies
├── package.json           # Node.js dependencies
├── start.bat              # One-command startup
└── README.md

## Quick Start
```bash
start.bat
```
Access: http://localhost:5000

## Manual Commands
```bash
# Install all dependencies
pip install -r requirements.txt
npm install

# Build and run
npm run build
python app.py
```

## Industry Standards & Deployment

### **Monorepo vs Separate Repos**
- **Monorepo** (This approach): Single repository, easier deployment
- **Microservices**: Separate repos for frontend/backend, better for large teams

### **Production Deployment Options**

#### **1. Platform-as-a-Service (PaaS)**
- **Heroku**: `git push heroku main`
- **Railway**: Connect GitHub repo
- **Render**: Auto-deploy from Git

#### **2. Cloud Providers**
- **AWS**: Elastic Beanstalk, EC2, Lambda
- **Google Cloud**: App Engine, Cloud Run
- **Azure**: App Service

#### **3. Containerization**
```dockerfile
FROM python:3.9
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN npm install && npm run build
CMD ["python", "app.py"]
```

### **Company Standard Structures**

#### **Small/Medium Projects** (Like yours)
```
project/
├── src/           # Frontend
├── app.py         # Backend
├── requirements.txt
└── package.json
```

#### **Enterprise Projects**
```
project/
├── frontend/      # React app
├── backend/       # API server
├── database/      # Migrations
├── docker/        # Containers
├── tests/         # Test suites
└── docs/          # Documentation
```

#### **Microservices Architecture**
```
company/
├── user-service/
├── chat-service/
├── file-service/
└── web-app/
```

## Your Current Setup Benefits
- ✅ Single command deployment
- ✅ No CORS issues
- ✅ Easy to understand
- ✅ Perfect for small-medium projects
- ✅ Cost-effective hosting
