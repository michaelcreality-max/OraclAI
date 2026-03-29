/**
 * Stock Prediction API Pipeline
 * Simplified interface for frontend integration with the AI agents system
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const API_KEY = process.env.REACT_APP_API_KEY || '';

class StockPredictionAPI {
  constructor(baseURL = API_BASE_URL, apiKey = API_KEY) {
    this.baseURL = baseURL;
    this.apiKey = apiKey;
  }

  /**
   * Get real-time stock quote
   */
  async getQuote(symbol) {
    const response = await this.request('/api/v1/quote', 'GET', null, { symbol });
    return response.quote;
  }

  /**
   * Get stock intelligence data (data collection agent only)
   */
  async getStockIntel(symbol, historyPeriod = '3mo') {
    const response = await this.request('/api/v1/intel/stock', 'GET', null, { 
      symbol, 
      history_period: historyPeriod 
    });
    return response.stock_intel;
  }

  /**
   * Basic stock prediction
   */
  async predictStock(symbol, days = 90, clientContext = {}) {
    const response = await this.request('/api/v1/predict', 'POST', {
      symbol,
      days,
      client_context: clientContext
    });
    return response.prediction;
  }

  /**
   * Full AI agents analysis with debate system
   * This includes: Stock Data Agent + 4 Debate Agents + Full ecosystem
   */
  async analyzeWithDebate(symbol, options = {}) {
    const {
      period = '2y',
      userProfile = null,
      whatIf = null,
      includeCrossMarket = true,
      includeStockIntel = false,
      maxHypotheses = 4,
      topModels = 2
    } = options;

    const response = await this.request('/api/v1/intelligence/analyze', 'POST', {
      symbol,
      period,
      user_profile: userProfile,
      what_if: whatIf,
      include_cross_market: includeCrossMarket,
      include_stock_intel: includeStockIntel,
      max_hypotheses: maxHypotheses,
      top_models: topModels
    });
    return response.intelligence;
  }

  /**
   * Discover elite stocks with high confidence
   */
  async discoverStocks(options = {}) {
    const {
      minConfidence = 0.5,
      sector = null,
      limit = 25
    } = options;

    const response = await this.request('/api/v1/discover', 'POST', {
      min_confidence: minConfidence,
      sector,
      limit
    });
    return response.discover;
  }

  /**
   * Analyze portfolio with AI agents
   */
  async analyzePortfolio(holdings, clientContext = {}) {
    const response = await this.request('/api/v1/portfolio', 'POST', {
      holdings,
      client_context: clientContext
    });
    return response.portfolio;
  }

  /**
   * Get decision transparency/audit trail
   */
  async getTransparency(symbol = null, limit = 40) {
    const response = await this.request('/api/v1/intelligence/transparency', 'GET', null, {
      symbol,
      limit
    });
    return response.transparency_events;
  }

  /**
   * Run stress tests
   */
  async runStressTests(options = {}) {
    const { nDays = 400, seed = 42 } = options;
    const response = await this.request('/api/v1/intelligence/stress', 'POST', {
      n_days: nDays,
      seed
    });
    return response.stress_tests;
  }

  /**
   * Check API health
   */
  async healthCheck() {
    const response = await this.request('/health', 'GET');
    return response;
  }

  /**
   * Generic request method
   */
  async request(endpoint, method = 'GET', data = null, params = null) {
    const url = new URL(endpoint, this.baseURL);
    
    if (params && method === 'GET') {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
          url.searchParams.append(key, value);
        }
      });
    }

    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (this.apiKey) {
      options.headers['X-API-Key'] = this.apiKey;
    }

    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url.toString(), options);
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || `HTTP error! status: ${response.status}`);
      }

      return result;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  /**
   * Classify user input to determine pipeline type
   */
  async classifyInput(userInput) {
    const response = await this.request('/api/v1/classify', 'POST', {
      input: userInput
    });
    return response;
  }

  /**
   * Discover hidden gems (undiscovered opportunities)
   */
  async discoverHiddenGems(options = {}) {
    const {
      limit = 10,
      sector = null,
      maxAttention = 0.6
    } = options;

    const response = await this.request('/api/v1/discover/hidden-gems', 'POST', {
      limit,
      sector,
      max_attention: maxAttention
    });
    return response.hidden_gems;
  }

  /**
   * Scan for dangerous/risky stocks
   */
  async scanRisks(options = {}) {
    const {
      limit = 15,
      minRiskLevel = 'HIGH',
      sector = null
    } = options;

    const response = await this.request('/api/v1/scan/risks', 'POST', {
      limit,
      min_risk_level: minRiskLevel,
      sector
    });
    return response.dangerous_stocks;
  }

  /**
   * Generate smart alerts
   */
  async generateSmartAlerts(options = {}) {
    const {
      symbols = null,
      alertTypes = null
    } = options;

    const response = await this.request('/api/v1/alerts/smart', 'POST', {
      symbols,
      alert_types: alertTypes
    });
    return response;
  }

  /**
   * Discover unknown patterns in market data
   */
  async discoverPatterns(options = {}) {
    const {
      symbols = null,
      patternTypes = null
    } = options;

    const response = await this.request('/api/v1/discover/patterns', 'POST', {
      symbols,
      pattern_types: patternTypes
    });
    return response;
  }

  /**
   * Universal smart predict - classifies input and routes to appropriate pipeline
   */
  async smartPredict(userInput, options = {}) {
    // First classify the input
    const classification = await this.classifyInput(userInput);
    
    switch (classification.type) {
      case 'single_stock':
        return await this.analyzeWithDebate(classification.ticker, options);
      
      case 'ranking':
        return await this.discoverStocks({
          limit: classification.limit,
          ...options
        });
      
      case 'discovery':
        return await this.discoverHiddenGems(options);
      
      case 'risk_scan':
        return await this.scanRisks(options);
      
      case 'market_overview':
        // Return market regime analysis
        return await this.getMarketOverview();
      
      default:
        throw new Error(`Unknown request type: ${classification.type}`);
    }
  }

  /**
   * Get market overview/regime analysis
   */
  async getMarketOverview() {
    // Use SPY as market proxy
    const analysis = await this.analyzeWithDebate('SPY', {
      includeCrossMarket: true,
      includeStockIntel: true,
      maxHypotheses: 2,
      topModels: 1
    });

    return {
      market_regime: analysis.regime,
      overview: {
        trend: analysis.regime.trend,
        volatility: analysis.regime.volatility,
        confidence: analysis.regime.confidence,
        recommendation: analysis.debate?.judge?.action || 'hold',
        key_insights: [
          `Market in ${analysis.regime.trend} regime`,
          `Volatility: ${analysis.regime.volatility}`,
          `Regime confidence: ${(analysis.regime.confidence * 100).toFixed(1)}%`
        ]
      }
    };
  }

  /**
   * Get comprehensive agent summary (enhanced)
   */
  async getAgentSummary(symbol, options = {}) {
    const fullAnalysis = await this.analyzeWithDebate(symbol, options);
    
    // Get additional risk and gem analysis
    const [riskAnalysis, gemAnalysis] = await Promise.all([
      this.scanRisks({ limit: 1 }).then(risks => risks.find(r => r.symbol === symbol) || null),
      this.discoverHiddenGems({ limit: 1 }).then(gems => gems.find(g => g.symbol === symbol) || null)
    ]);

    return {
      symbol: fullAnalysis.symbol,
      data_collection_agent: {
        role: "observer",
        mandate: "Collect and normalize factual market data",
        key_metrics: fullAnalysis.stock_intel?.fundamentals ? {
          price: fullAnalysis.stock_intel.fundamentals.currentPrice,
          pe_ratio: fullAnalysis.stock_intel.fundamentals.trailingPE,
          market_cap: fullAnalysis.stock_intel.fundamentals.marketCap,
          beta: fullAnalysis.stock_intel.fundamentals.beta,
          volume: fullAnalysis.stock_intel.fundamentals.averageVolume
        } : null,
        data_sources: fullAnalysis.stock_intel?.data_sources || []
      },
      debate_agents: {
        bullish_agent: {
          stance: fullAnalysis.debate?.agents?.[0]?.stance || 'constructive',
          confidence: fullAnalysis.debate?.agents?.[0]?.confidence || 0,
          key_points: fullAnalysis.debate?.agents?.[0]?.points || []
        },
        bearish_agent: {
          stance: fullAnalysis.debate?.agents?.[1]?.stance || 'skeptical',
          confidence: fullAnalysis.debate?.agents?.[1]?.confidence || 0,
          key_points: fullAnalysis.debate?.agents?.[1]?.points || []
        },
        risk_critic: {
          stance: fullAnalysis.debate?.agents?.[2]?.stance || 'critique',
          confidence: fullAnalysis.debate?.agents?.[2]?.confidence || 0,
          key_points: fullAnalysis.debate?.agents?.[2]?.points || []
        },
        judge_verdict: {
          action: fullAnalysis.debate?.judge?.action || 'hold',
          score: fullAnalysis.debate?.judge?.score || 0,
          rationale: fullAnalysis.debate?.judge?.rationale || '',
          risk_flags: fullAnalysis.debate?.judge?.risk_flags || []
        }
      },
      final_prediction: {
        direction: fullAnalysis.ecosystem?.reality_reports?.[0]?.direction || 'neutral',
        confidence: fullAnalysis.ecosystem?.reality_reports?.[0]?.confidence || 0.5,
        action: fullAnalysis.debate?.judge?.action || 'hold',
        score: fullAnalysis.debate?.judge?.score || 0
      },
      market_regime: fullAnalysis.regime,
      risk_analysis: riskAnalysis ? {
        overall_risk_score: riskAnalysis.overall_risk_score,
        risk_level: riskAnalysis.risk_level,
        is_dangerous: riskAnalysis.is_dangerous,
        warnings: riskAnalysis.warnings,
        recommendation: riskAnalysis.recommendation
      } : null,
      hidden_gem_analysis: gemAnalysis ? {
        hidden_gem_score: gemAnalysis.hidden_gem_score,
        is_hidden_gem: gemAnalysis.is_hidden_gem,
        scores: gemAnalysis.scores,
        reasoning: gemAnalysis.reasoning
      } : null,
      patterns: fullAnalysis.patterns,
      ecosystem_performance: fullAnalysis.ecosystem ? {
        cycle: fullAnalysis.ecosystem.cycle,
        hypotheses_count: fullAnalysis.ecosystem.hypotheses?.length || 0,
        models_tested: fullAnalysis.ecosystem.arena?.reduce((sum, a) => sum + (a.models_trained || 0), 0) || 0,
        survivors: fullAnalysis.ecosystem.state?.survivors || []
      } : null
    };
  }

  /**
   * Simplified debate analysis - just the core agent arguments
   */
  async getDebateAnalysis(symbol, options = {}) {
    const fullAnalysis = await this.analyzeWithDebate(symbol, {
      ...options,
      includeCrossMarket: false,
      includeStockIntel: false,
      maxHypotheses: 2,
      topModels: 1
    });

    return {
      symbol: fullAnalysis.symbol,
      debate: fullAnalysis.debate,
      prediction: {
        direction: fullAnalysis.ecosystem?.reality_reports?.[0]?.direction || 'neutral',
        confidence: fullAnalysis.ecosystem?.reality_reports?.[0]?.confidence || 0.5,
        action: fullAnalysis.debate?.judge?.action || 'hold'
      },
      regime: fullAnalysis.regime,
      risk_metrics: fullAnalysis.ecosystem?.reality_reports?.[0] ? {
        sharpe: fullAnalysis.ecosystem.reality_reports[0].sharpe,
        max_drawdown: fullAnalysis.ecosystem.reality_reports[0].max_drawdown
      } : null
    };
  }
}

// Export for use in React/Vue/etc.
export default StockPredictionAPI;

// Example usage:
/*
const api = new StockPredictionAPI();

// Get stock data agent info
const stockIntel = await api.getStockIntel('AAPL');

// Get full debate analysis
const debateAnalysis = await api.getDebateAnalysis('AAPL');

// Full intelligence with all agents
const fullAnalysis = await api.analyzeWithDebate('AAPL', {
  userProfile: { risk_tolerance: 0.7, investment_horizon: 'medium' },
  whatIf: { 'fed_rate_hike': 0.5 }
});
*/
