# Tender Intelligence Platform - Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Telegram Bot Token
- (Optional) Google Sheets API credentials

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd TENDER-INTELLIGENCE-PLATFORM/backend_py

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### 2. Database Setup

```bash
# Create PostgreSQL database
createdb tender

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials
```

Example `.env` file:
```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/tender
REDIS_URL=redis://localhost:6379/0

TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ALERT_CHAT_ID=your_chat_id_here

SCRAPE_EVERY_MINUTES=15
SCRAPE_HOUR=9
SCRAPE_MINUTE=0
```

### 3. Database Migration

```bash
# Run database migrations
alembic upgrade head

# Seed initial keywords
python scripts/seed_keywords.py

# Or reset and seed all keywords
python scripts/reset_and_seed_keywords.py
```

### 4. Start Services

#### Option A: Development Mode

```bash
# Terminal 1: Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# Terminal 3: Start Celery beat (scheduler)
celery -A app.workers.celery_app beat --loglevel=info
```

#### Option B: Production Mode (Windows)

```bash
# Start all Celery services
start_celery.bat

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Option C: Production Mode (Linux/Mac)

```bash
# Start all Celery services
chmod +x start_celery.sh
./start_celery.sh

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📊 API Endpoints

### Health Check
- `GET /health` - System health status

### Keywords Management
- `GET /api/keywords` - List all keywords
- `GET /api/keywords?active_only=true` - List active keywords only
- `POST /api/keywords` - Create new keyword
- `PUT /api/keywords/{id}` - Update keyword
- `DELETE /api/keywords/{id}` - Delete keyword
- `POST /api/keywords/batch` - Create multiple keywords
- `GET /api/keywords/stats/summary` - Keyword statistics

### Task Management
- `POST /api/tasks/trigger` - Manually trigger scraping task
- `GET /api/tasks/status/{task_id}` - Get task status
- `GET /api/tasks/logs` - Get task logs
- `GET /api/tasks/logs/stats` - Get task statistics
- `POST /api/tasks/test-keywords` - Test keyword matching
- `GET /api/tasks/health` - System health check

## 🔧 Configuration

### Celery Beat Schedule
The system is configured to automatically scrape sources at a specific time every day. This can be adjusted in the environment variables (e.g., in `.env` file) or in `app/core/config.py`:

```python
SCRAPE_HOUR = 9      # Hour of day (Tashkent time)
SCRAPE_MINUTE = 0    # Minute of hour
```

### Telegram Integration
1. Create a bot via @BotFather on Telegram
2. Get the bot token
3. Create a channel/group for alerts
4. Add the bot as administrator
5. Get the chat ID (negative for channels)
6. Update environment variables

### Keyword Management
Use the API endpoints or run scripts:

```bash
# Test current keyword coverage
python scripts/test_keyword_matching.py

# Check current keywords
python scripts/check_keywords.py

# Check current tenders
python scripts/check_tenders.py
```

## 📈 Monitoring

### System Health
- Check `/api/tasks/health` for system status
- Monitor logs in the `parser_logs` table
- Use Celery Flower for advanced monitoring (optional)

### Key Metrics
- Tender coverage percentage
- New tenders found per day
- Keyword match rates
- Task success/failure rates

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify DATABASE_URL in .env
   - Check database exists

2. **Redis Connection Failed**
   - Check Redis is running
   - Verify REDIS_URL in .env

3. **Telegram Alerts Not Working**
   - Verify bot token
   - Check chat ID format
   - Ensure bot is admin in channel

4. **No Tenders Found**
   - Check keyword list
   - Test keyword matching script
   - Verify UZEX API connectivity

5. **Celery Tasks Not Running**
   - Check worker is running: `celery -A app.workers.celery_app inspect active`
   - Check beat is running: `celery -A app.workers.celery_app inspect scheduled`
   - Restart services if needed

### Logs Location
- Celery logs: Console output
- Parser logs: Database `parser_logs` table
- Application logs: Console (configure file logging if needed)

## 🔒 Security Considerations

1. **Environment Variables**: Never commit .env files
2. **Database**: Use strong passwords
3. **API**: Consider authentication for production
4. **Network**: Use HTTPS in production
5. **Rate Limiting**: Monitor UZEX API usage

## 📝 Development

### Adding New Scrapers
1. Create new scraper in `app/scrapers/`
2. Add new task in `app/workers/tasks.py`
3. Update Celery beat schedule if needed
4. Add corresponding API endpoints

### Testing
```bash
# Test keyword matching
python scripts/test_keyword_matching.py

# Test API endpoints
curl http://localhost:8000/api/keywords
curl -X POST http://localhost:8000/api/tasks/trigger \
  -H "Content-Type: application/json" \
  -d '{"task_name": "scrape_uzex_etender", "immediate": true}'
```

## 🚀 Production Deployment

### Docker (Recommended)
```dockerfile
# Dockerfile example
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install

COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Monitoring Setup
- Use Prometheus + Grafana for metrics
- Set up alerts for failed tasks
- Monitor database performance
- Track keyword coverage over time

## 📞 Support

For issues:
1. Check logs in database
2. Verify all services are running
3. Test individual components
4. Review configuration

## 🔄 Updates

To update keywords:
```bash
# Add new keywords to scripts/seed_keywords.py
python scripts/seed_keywords.py
```

To update system:
```bash
git pull
pip install -r requirements.txt
alembic upgrade head
# Restart services
```
