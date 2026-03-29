# Quant Trading AI System

A production-ready multi-agent AI system for quantitative trading analysis with real-time debate, risk management, and execution safety controls.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎯 Features

- **Multi-Agent Debate System**: 4 specialized AI agents (Analyst, Researcher, Trader, Risk Manager) debate trade decisions
- **Real-time Streaming**: Live SSE streams for agent debates
- **Execution Safety Layer**: Multi-layer safety system with training/execution/safe modes
- **Admin Dashboard**: Web-based control panel for system management
- **API Key Management**: Secure authentication with role-based access
- **High Availability**: Primary + backup server architecture
- **System Self-Modification**: Live parameter adjustment without restart

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     LOAD BALANCER (Nginx)                    │
│                    Ports: 80/443 → 5000/5001                 │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌───────────────┐         ┌───────────────┐
│   PRIMARY     │◄───────►│    BACKUP     │
│   Server      │ Failover│    Server     │
│   Port 5000   │         │   Port 5001   │
└───────┬───────┘         └───────────────┘
        │
┌───────┴─────────────────────────────────────┐
│           FLASK APPLICATION                    │
│  ┌─────────────┐  ┌─────────────┐             │
│  │ Multi-Agent │  │   Admin     │             │
│  │ Orchestrator│  │   Control   │             │
│  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐             │
│  │  Execution  │  │    File     │             │
│  │   Safety    │  │   Manager   │             │
│  └─────────────┘  └─────────────┘             │
└───────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

```bash
Python 3.9+
pip3
```

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/quant-trading-ai.git
cd quant-trading-ai

# Install dependencies
pip3 install -r requirements.txt

# Generate API key for frontend
python3 generate_api_key.py
```

### Running the System

```bash
# Terminal 1: Start Primary Server
python3 production_server.py

# Terminal 2: Start Backup Server
PORT=5001 python3 backup_server.py
```

### Access the Dashboard

- **Control Panel**: http://localhost:5000/control
- **API Base URL**: http://localhost:5000/api
- **Health Check**: http://localhost:5000/api/health

## 🔐 API Authentication

All API endpoints require authentication via Bearer token:

```http
Authorization: Bearer YOUR_API_KEY
```

Generate an API key:
```bash
python3 generate_api_key.py
```

## 📊 API Endpoints

### System Control
- `GET /api/admin/system/state` - Get current system state
- `POST /api/admin/mode/switch` - Switch system mode (training/execution/safe)
- `POST /api/admin/config/update` - Update system configuration

### Agents
- `GET /api/admin/agents` - List all agents
- `POST /api/admin/agent/toggle` - Enable/disable agent
- `POST /api/agents/run` - Run specific agent
- `GET /api/agents/history` - Get execution history

### File Management
- `GET /api/admin/files/list` - List files
- `GET /api/admin/files/read` - Read file content
- `POST /api/admin/files/write` - Write file content

### Monitoring
- `GET /api/admin/metrics` - System metrics (CPU, memory, etc.)
- `GET /api/admin/logs/recent` - Recent system logs

### Debate System
- `POST /api/v1/debate/start` - Start multi-agent debate
- `GET /api/v1/debate/stream/<id>` - Stream debate updates (SSE)
- `GET /api/v1/debate/status/<id>` - Get debate status
- `GET /api/v1/debate/result/<id>` - Get debate result

## 🎛️ System Modes

| Mode | Description | Risk Level |
|------|-------------|------------|
| **Training** | Paper trading, no real money at risk | Low |
| **Execution** | Live trading enabled | High |
| **Safe** | All trading blocked, analysis only | None |

## 🤖 AI Agents

1. **Data Collection Agent**: Gathers real-time market data
2. **Bullish Agent**: Analyzes buying opportunities
3. **Bearish Agent**: Analyzes risks and sell signals
4. **Risk Manager**: Evaluates portfolio risk
5. **Judge**: Final arbiter with position sizing

## 🛡️ Safety Features

- **Pre-execution Validation**: All trades validated before execution
- **Auto-fallback**: System falls back to safe mode on anomalies
- **Rate Limiting**: Configurable per API key
- **Audit Logging**: All actions logged with timestamps
- **IP Blocking**: Automatic blocking of suspicious IPs

## 📁 Project Structure

```
quant-trading-ai/
├── production_server.py      # Main Flask application
├── backup_server.py          # Backup server instance
├── wsgi.py                   # WSGI entry point
├── gunicorn.conf.py         # Gunicorn configuration
├── nginx_quant.conf         # Nginx load balancer config
├── requirements.txt         # Python dependencies
├── generate_api_key.py      # API key generator
├── start_production.sh      # Production startup script
├── stop_production.sh       # Production shutdown script
├── quant_ecosystem/         # Core modules
│   ├── multi_agent_orchestrator.py
│   ├── execution_safety.py
│   ├── api_key_manager.py
│   ├── admin_control.py
│   ├── windsurf_agent_bridge.py
│   └── ...
├── templates/               # HTML templates
│   └── control_panel.html
├── static/                # CSS, JS, assets
│   ├── css/
│   └── js/
└── data/                  # SQLite databases
    ├── api_keys.db
    ├── admin_control.db
    └── ...
```

## 🔧 Configuration

### Environment Variables

```bash
PORT=5000                    # Server port
HOST=0.0.0.0                 # Bind address
FLASK_ENV=production         # Environment mode
DEBUG=false                  # Debug mode
```

### Nginx Load Balancer

```bash
# Install Nginx
brew install nginx  # macOS
sudo apt install nginx  # Ubuntu

# Copy config
sudo cp nginx_quant.conf /etc/nginx/conf.d/
sudo nginx -s reload
```

### Production Deployment

```bash
# Using Gunicorn
pip3 install gunicorn

# Start with script
./start_production.sh

# Or manually
PORT=5000 gunicorn --config gunicorn.conf.py wsgi:application
PORT=5001 gunicorn --config gunicorn.conf.py wsgi:application
```

## 🧪 Testing

```bash
# Test connection
curl http://localhost:5000/api/test/connection

# Test authentication
curl -H "Authorization: Bearer YOUR_KEY" http://localhost:5000/api/test/auth

# Health check
curl http://localhost:5000/api/health
```

## 📈 Monitoring

System metrics available at:
- `GET /api/admin/metrics?hours=1`

Tracks:
- CPU usage
- Memory usage
- Active debates
- Active streams
- Request rates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Flask framework
- SQLite for persistence
- Windsurf Agent Bridge for agent management

---

**Note**: This system is for educational and research purposes. Use at your own risk for trading decisions.
