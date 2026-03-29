# Stock Prediction AI Agents API Documentation

## Overview

This API provides access to a sophisticated AI agents system for stock prediction:
- **1 Stock Data Collection Agent** - Gathers real-time market data and fundamentals
- **4 Debate Agents** - Bullish, Bearish, Risk Critic, and Judge agents that argue and vote on predictions
- **Full Ecosystem** - Advanced quantitative models, regime detection, and meta-learning

## Base Setup

```javascript
// JavaScript/TypeScript
import StockPredictionAPI from './api_pipeline';

const api = new StockPredictionAPI('http://localhost:5000', 'your-api-key');
```

```python
# Python
from api_pipeline import StockPredictionAPI, APIConfig

api = StockPredictionAPI(APIConfig(
    base_url="http://localhost:5000",
    api_key="your-api-key"
))
```

## Core Endpoints

### 1. Get Stock Intelligence (Data Collection Agent Only)

**Endpoint:** `GET /api/v1/intel/stock`

**Purpose:** Get factual market data from the observer-only Stock Intel agent

```javascript
const stockIntel = await api.getStockIntel('AAPL', '3mo');
```

```python
stock_intel = api.get_stock_intel('AAPL', '3mo')
```

**Response Format:**
```json
{
  "symbol": "AAPL",
  "role": "observer",
  "mandate": "Collect and normalize factual market data; do not debate or vote on strategies.",
  "fetched_at_utc": "2024-03-21T18:00:00Z",
  "data_sources": ["yfinance", "server_live_cache"],
  "fast_metrics": {
    "currency": "USD",
    "exchange": "NASDAQ",
    "market_cap": 3000000000000
  },
  "fundamentals": {
    "longName": "Apple Inc.",
    "sector": "Technology",
    "trailingPE": 28.5,
    "beta": 1.2,
    "currentPrice": 175.43
  },
  "recent_history": {
    "bars": 63,
    "last_close": 175.43,
    "return_total": 0.085,
    "vol_ann_hint": 0.22
  }
}
```

### 2. Full AI Agents Analysis (All 5 Agents)

**Endpoint:** `POST /api/v1/intelligence/analyze`

**Purpose:** Complete analysis with Stock Data Agent + 4 Debate Agents + full ecosystem

```javascript
const fullAnalysis = await api.analyzeWithDebate('AAPL', {
  period: '2y',
  userProfile: {
    risk_tolerance: 0.7,
    investment_horizon: 'medium'
  },
  whatIf: {
    'fed_rate_hike': 0.5,
    'inflation_shock': 0.3
  },
  includeCrossMarket: true,
  includeStockIntel: true,
  maxHypotheses: 4,
  topModels: 2
});
```

```python
full_analysis = api.analyze_with_debate(
    'AAPL',
    period='2y',
    user_profile={
        'risk_tolerance': 0.7,
        'investment_horizon': 'medium'
    },
    what_if={
        'fed_rate_hike': 0.5,
        'inflation_shock': 0.3
    },
    include_cross_market=True,
    include_stock_intel=True,
    max_hypotheses=4,
    top_models=2
)
```

**Response Format (Key Sections):**

```json
{
  "ok": true,
  "symbol": "AAPL",
  "stock_intel": { /* Stock Data Agent output */ },
  "debate": {
    "symbol": "AAPL",
    "agents": [
      {
        "role": "bull",
        "stance": "constructive",
        "points": [
          "Trend regime reads bull; momentum aligns with stated direction bullish.",
          "Model confidence 0.72 supports incremental long bias if risk allows."
        ],
        "confidence": 0.81
      },
      {
        "role": "bear", 
        "stance": "skeptical",
        "points": [
          "Volatility regime normal may punish directional bets.",
          "Mean reversion risk rises after extended moves; confirmation needed."
        ],
        "confidence": 0.60
      },
      {
        "role": "risk",
        "stance": "critique", 
        "points": [
          "Drawdown proxy from metrics: 0.12",
          "Sharpe-like gauge: 1.45",
          "Microstructure stress: 0.25"
        ],
        "confidence": 0.75
      }
    ],
    "judge": {
      "action": "buy",
      "score": 0.21,
      "rationale": "Judge weighs trend/vol against model confidence and risk flags.",
      "risk_flags": ["Microstructure stress: 0.25"]
    }
  },
  "regime": {
    "trend": "bull",
    "volatility": "normal", 
    "driver": "momentum",
    "confidence": 0.68,
    "strategy_weights_by_regime": {
      "trend_following": 0.4,
      "mean_reversion": 0.3,
      "momentum": 0.3
    }
  },
  "ecosystem": {
    "cycle": 1,
    "hypotheses": [ /* AI-generated trading strategies */ ],
    "reality_reports": [ /* Backtest validation results */ ],
    "meta": {
      "retrain_ids": [],
      "discard_ids": ["model_123"],
      "weights": {"strategy_x": 0.6, "strategy_y": 0.4}
    }
  }
}
```

### 3. Simplified Debate Analysis

**Purpose:** Just the core debate between 4 agents without full ecosystem

```javascript
const debateAnalysis = await api.getDebateAnalysis('AAPL');
```

```python
debate_analysis = api.get_debate_analysis('AAPL')
```

**Response Format:**
```json
{
  "symbol": "AAPL",
  "debate": { /* Same debate structure as above */ },
  "prediction": {
    "direction": "bullish",
    "confidence": 0.72,
    "action": "buy"
  },
  "regime": { /* Market regime info */ },
  "risk_metrics": {
    "sharpe": 1.45,
    "max_drawdown": 0.12
  }
}
```

### 4. Complete Agent Summary

**Purpose:** Get a consolidated view of all 5 agents' output

```javascript
const agentSummary = await api.getAgentSummary('AAPL');
```

```python
agent_summary = api.get_agent_summary('AAPL')
```

**Response Format:**
```json
{
  "symbol": "AAPL",
  "data_collection_agent": {
    "role": "observer",
    "mandate": "Collect and normalize factual market data; do not debate or vote on strategies.",
    "key_metrics": {
      "price": 175.43,
      "pe_ratio": 28.5,
      "market_cap": 3000000000000,
      "beta": 1.2
    },
    "data_sources": ["yfinance", "server_live_cache"]
  },
  "debate_agents": {
    "bullish_agent": {
      "stance": "constructive",
      "confidence": 0.81,
      "key_points": ["Trend regime reads bull...", "Model confidence 0.72..."]
    },
    "bearish_agent": {
      "stance": "skeptical", 
      "confidence": 0.60,
      "key_points": ["Volatility regime normal...", "Mean reversion risk..."]
    },
    "risk_critic": {
      "stance": "critique",
      "confidence": 0.75,
      "key_points": ["Drawdown proxy: 0.12", "Sharpe gauge: 1.45"]
    },
    "judge_verdict": {
      "action": "buy",
      "score": 0.21,
      "rationale": "Judge weighs trend/vol against model confidence...",
      "risk_flags": ["Microstructure stress: 0.25"]
    }
  },
  "final_prediction": {
    "direction": "bullish",
    "confidence": 0.72,
    "action": "buy"
  },
  "market_regime": {
    "trend": "bull",
    "volatility": "normal",
    "driver": "momentum",
    "confidence": 0.68
  }
}
```

## Other Useful Endpoints

### Basic Prediction
```javascript
const prediction = await api.predictStock('AAPL', 90, {risk_level: 'moderate'});
```

### Discover Elite Stocks
```javascript
const eliteStocks = await api.discoverStocks({
  minConfidence: 0.7,
  sector: 'Technology',
  limit: 10
});
```

### Portfolio Analysis
```javascript
const portfolioAnalysis = await api.analyzePortfolio({
  'AAPL': 100,
  'GOOGL': 50,
  'MSFT': 75
}, {risk_tolerance: 0.6});
```

### Get Decision Audit Trail
```javascript
const transparency = await api.getTransparency('AAPL', 20);
```

## Frontend Integration Examples

### React Component Example
```jsx
import React, { useState, useEffect } from 'react';
import StockPredictionAPI from './api_pipeline';

function StockAnalysis({ symbol }) {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const api = new StockPredictionAPI();

  useEffect(() => {
    const fetchAnalysis = async () => {
      setLoading(true);
      try {
        const result = await api.getAgentSummary(symbol);
        setAnalysis(result);
      } catch (error) {
        console.error('Failed to fetch analysis:', error);
      } finally {
        setLoading(false);
      }
    };

    if (symbol) fetchAnalysis();
  }, [symbol]);

  if (loading) return <div>Loading AI analysis...</div>;
  if (!analysis) return <div>No analysis available</div>;

  return (
    <div>
      <h2>AI Agent Analysis for {symbol}</h2>
      
      <div>
        <h3>Stock Data Agent</h3>
        <p>Price: ${analysis.data_collection_agent.key_metrics.price}</p>
        <p>P/E Ratio: {analysis.data_collection_agent.key_metrics.pe_ratio}</p>
      </div>

      <div>
        <h3>Debate Results</h3>
        <p><strong>Judge Verdict:</strong> {analysis.debate_agents.judge_verdict.action.toUpperCase()}</p>
        <p><strong>Confidence:</strong> {(analysis.final_prediction.confidence * 100).toFixed(1)}%</p>
        
        <div>
          <h4>Agent Arguments:</h4>
          {analysis.debate_agents.bullish_agent.key_points.map((point, i) => (
            <p key={i}>🐂 Bull: {point}</p>
          ))}
          {analysis.debate_agents.bearish_agent.key_points.map((point, i) => (
            <p key={i}>🐻 Bear: {point}</p>
          ))}
          {analysis.debate_agents.risk_critic.key_points.map((point, i) => (
            <p key={i}>⚠️ Risk: {point}</p>
          ))}
        </div>
      </div>
    </div>
  );
}

export default StockAnalysis;
```

### Python Backend Integration
```python
from flask import Flask, jsonify
from api_pipeline import StockPredictionAPI, APIConfig

app = Flask(__name__)
api = StockPredictionAPI(APIConfig(
    base_url="http://localhost:5000",
    api_key="your-api-key"
))

@app.route('/stock-summary/<symbol>')
def get_stock_summary(symbol):
    try:
        summary = api.get_agent_summary(symbol)
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/debate-only/<symbol>')  
def get_debate_only(symbol):
    try:
        debate = api.get_debate_analysis(symbol)
        return jsonify(debate)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

## Environment Setup

Create `.env` file:
```
REACT_APP_API_URL=http://localhost:5000
REACT_APP_API_KEY=your-api-key
STOCK_API_KEY=your-api-key
```

## Error Handling

All API calls return standardized responses:
```json
{
  "success": true,
  "api_version": "1.0",
  "timestamp": "2024-03-21T18:00:00Z",
  "data": { /* actual response data */ }
}
```

Error responses:
```json
{
  "success": false,
  "api_version": "1.0", 
  "error": "symbol query parameter required",
  "timestamp": "2024-03-21T18:00:00Z"
}
```

## Rate Limits & Performance

- API key required for production use
- Typical response time: 2-5 seconds for full analysis
- Cache stock intel data for 5-15 minutes
- Use simplified debate endpoint for real-time needs
