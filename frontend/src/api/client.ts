const API_BASE = '/api/v1';

export class ApiClient {
  private static getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('access_token');
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  public static async request<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
    const headers = {
      ...this.getAuthHeaders(),
      ...(options.headers || {})
    };

    const response = await fetch(url, { ...options, headers });
    const data = await response.json();

    if (!response.ok) {
      const errorMsg = data?.error?.message || data?.detail || 'Request failed';
      throw new Error(errorMsg);
    }

    return data as T;
  }

  // Auth
  public static login(email: string, password: string) {
    return this.request<{ access_token: string; refresh_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  }

  public static register(full_name: string, email: string, password: string) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ full_name, email, password })
    });
  }

  public static getMe() {
    return this.request<{ id: string; email: string; full_name: string; role: string }>('/auth/me');
  }

  // Market
  public static getMarketStatus() {
    return this.request<{ status: string; exchange: string; trading_day: string; message: string }>('/market/status');
  }

  public static getInstruments() {
    return this.request<any[]>('/market/instruments');
  }

  public static getQuote(symbol: string) {
    return this.request<any>(`/market/quote/${symbol}`);
  }

  public static getMinuteBars(symbol: string, limit = 100) {
    return this.request<any[]>(`/market/minute/${symbol}?limit=${limit}`);
  }

  public static getCandles(symbol: string, timeframe = '1m', limit = 100) {
    return this.request<any[]>(`/market/candles/${symbol}?timeframe=${timeframe}&limit=${limit}`);
  }

  public static searchMarket(q: string) {
    return this.request<any[]>(`/market/search?q=${encodeURIComponent(q)}`);
  }

  public static getMarketDataHealth() {
    return this.request<any>('/health/market-data');
  }

  public static getHistory(symbol: string, days = 90) {
    return this.request<any[]>(`/market/history/${symbol}?days=${days}`);
  }

  public static getFundamentals(symbol: string) {
    return this.request<any>(`/market/fundamentals/${symbol}`);
  }

  public static getOptionChain(symbol: string, expiry?: string) {
    const q = expiry ? `?expiry=${expiry}` : '';
    return this.request<{
      symbol: string;
      underlying_price: number;
      expiries: string[];
      selected_expiry: string;
      chain: Array<{
        strike: number;
        call?: {
          contract_symbol: string;
          strike: number;
          last_price: number;
          bid?: number;
          ask?: number;
          change?: number;
          change_pct?: number;
          volume?: number;
          open_interest?: number;
          implied_volatility?: number;
          in_the_money: boolean;
        };
        put?: {
          contract_symbol: string;
          strike: number;
          last_price: number;
          bid?: number;
          ask?: number;
          change?: number;
          change_pct?: number;
          volume?: number;
          open_interest?: number;
          implied_volatility?: number;
          in_the_money: boolean;
        };
      }>;
      total_call_oi: number;
      total_put_oi: number;
      pcr_ratio?: number;
      max_pain?: number;
      provider: string;
      timestamp: string;
    }>(`/market/options/${symbol}${q}`);
  }

  // Technical Indicators
  public static getIndicators(symbol: string, timeframe = '1m') {
    return this.request<any>(`/technical/${symbol}?timeframe=${timeframe}`);
  }

  // Scanner
  public static getScannerPresets() {
    return this.request<any[]>('/scanner/presets');
  }

  public static runScanner(rules: any[]) {
    return this.request<any[]>('/scanner/run', {
      method: 'POST',
      body: JSON.stringify(rules)
    });
  }

  public static parseNLScanner(query: string) {
    return this.request<any>('/scanner/nl-query', {
      method: 'POST',
      body: JSON.stringify({ query })
    });
  }

  // Watchlists
  public static getWatchlists() {
    return this.request<any[]>('/watchlists');
  }

  public static createWatchlist(name: string, description?: string) {
    return this.request<any>('/watchlists', {
      method: 'POST',
      body: JSON.stringify({ name, description })
    });
  }

  public static addWatchlistItem(watchlistId: string, symbol: string) {
    return this.request<any>(`/watchlists/${watchlistId}/items`, {
      method: 'POST',
      body: JSON.stringify({ symbol })
    });
  }

  public static removeWatchlistItem(watchlistId: string, symbol: string) {
    return this.request<any>(`/watchlists/${watchlistId}/items/${symbol}`, {
      method: 'DELETE'
    });
  }

  // Alerts
  public static getAlerts() {
    return this.request<any[]>('/alerts');
  }

  public static createAlert(symbol: string, condition_type: string, target_value: number) {
    return this.request<any>('/alerts', {
      method: 'POST',
      body: JSON.stringify({ symbol, condition_type, target_value })
    });
  }

  public static deleteAlert(alertId: string) {
    return this.request<any>(`/alerts/${alertId}`, { method: 'DELETE' });
  }

  // News
  public static getNews(symbol?: string) {
    const q = symbol ? `?symbol=${symbol}` : '';
    return this.request<any[]>(`/news${q}`);
  }

  public static getAnnouncements(symbol?: string) {
    const q = symbol ? `?symbol=${symbol}` : '';
    return this.request<any[]>(`/news/announcements${q}`);
  }

  // GenAI
  public static sendAIChat(message: string, conversation_id?: string) {
    return this.request<any>('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ message, conversation_id })
    });
  }

  public static getAIStockAnalysis(symbol: string) {
    return this.request<any>(`/ai/stock/${symbol}`);
  }

  public static getAINewspaper(edition = 'INTRADAY') {
    return this.request<any>(`/ai/newspaper?edition=${edition}`);
  }

  // Strategies & Backtests
  public static getStrategies() {
    return this.request<any[]>('/strategies');
  }

  public static createStrategy(data: any) {
    return this.request<any>('/strategies', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  public static runBacktest(data: any) {
    return this.request<any>('/backtests/run', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  public static getBacktests() {
    return this.request<any[]>('/backtests');
  }

  public static getBacktestById(id: string) {
    return this.request<any>(`/backtests/${id}`);
  }

  // Portfolio
  public static getPortfolio() {
    return this.request<any>('/portfolio');
  }

  public static getPortfolioAnalysis() {
    return this.request<any>('/portfolio/analysis');
  }

  // Wallet
  public static getWallet() {
    return this.request<any>('/wallet');
  }

  public static depositFunds(amount: number, idempotency_key: string) {
    return this.request<any>('/wallet/deposit', {
      method: 'POST',
      body: JSON.stringify({ amount, idempotency_key, payment_method: 'simulated_upi' })
    });
  }

  public static withdrawFunds(amount: number, bank_account_info: string) {
    return this.request<any>('/wallet/withdraw', {
      method: 'POST',
      body: JSON.stringify({ amount, bank_account_info })
    });
  }

  public static getLedgerTransactions() {
    return this.request<any[]>('/wallet/transactions');
  }

  // Razorpay Payments (TEST MODE)
  public static createPaymentOrder(amount: number) {
    return this.request<{
      id: string;
      razorpay_order_id: string;
      amount: number;
      currency: string;
      status: string;
      key_id: string;
      mode: string;
      notes?: Record<string, any>;
    }>('/payments/create-order', {
      method: 'POST',
      body: JSON.stringify({ amount })
    });
  }

  public static verifyPayment(data: {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
  }) {
    return this.request<{
      success: boolean;
      status: string;
      payment_id: string;
      credited_amount: number;
      new_balance: number;
      message: string;
    }>('/payments/verify', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  public static getPaymentHistory() {
    return this.request<any[]>('/payments');
  }

  // Orders & Risk & Paper Trading
  public static generateTradeSetup(symbol: string) {
    return this.request<any>(`/orders/trade-setup?symbol=${symbol}`, { method: 'POST' });
  }

  public static validateRisk(data: any) {
    return this.request<any>('/orders/validate-risk', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  public static executeOrder(data: any) {
    return this.request<any>('/orders/execute', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  public static createOrder(data: any) {
    return this.request<any>('/orders', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  public static getOrders(status?: string, symbol?: string) {
    const params = new URLSearchParams();
    if (status && status !== 'ALL') params.append('status', status);
    if (symbol) params.append('symbol', symbol);
    const q = params.toString() ? `?${params.toString()}` : '';
    return this.request<any[]>(`/orders${q}`);
  }

  public static getOrderById(id: string) {
    return this.request<any>(`/orders/${id}`);
  }

  public static cancelOrder(id: string) {
    return this.request<any>(`/orders/${id}/cancel`, { method: 'POST' });
  }

  public static modifyOrder(id: string, data: any) {
    return this.request<any>(`/orders/${id}/modify`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  public static getOrderEvents(id: string) {
    return this.request<any[]>(`/orders/${id}/events`);
  }

  // Positions
  public static getPositions() {
    return this.request<{
      open_positions: any[];
      closed_positions: any[];
      total_unrealized_pnl: number;
      total_realized_pnl: number;
      total_current_value: number;
    }>('/positions');
  }

  public static closePosition(symbol: string) {
    return this.request<any>(`/positions/${symbol}/close`, { method: 'POST' });
  }

  public static modifyPositionSlTarget(symbol: string, stop_loss?: number | null, target_price?: number | null) {
    return this.request<any>(`/positions/${symbol}/modify-sl-target`, {
      method: 'POST',
      body: JSON.stringify({ stop_loss, target_price })
    });
  }

  public static resetPaperAccount(optionsOrClearHistory: any = true, confirm = true) {
    let body = { clear_history: true, confirm: true };
    if (typeof optionsOrClearHistory === 'object' && optionsOrClearHistory !== null) {
      body = {
        clear_history: optionsOrClearHistory.clear_orders ?? optionsOrClearHistory.clear_history ?? true,
        confirm: optionsOrClearHistory.confirm ?? true,
        ...optionsOrClearHistory
      };
    } else {
      body = { clear_history: Boolean(optionsOrClearHistory), confirm };
    }
    return this.request<any>('/paper/reset', {
      method: 'POST',
      body: JSON.stringify(body)
    });
  }

  // Trading Environment
  public static getTradingEnvironment() {
    return this.request<{
      trading_mode: 'PAPER' | 'SANDBOX' | 'LIVE';
      broker_provider: string;
      broker_env: string;
      is_paper: boolean;
      is_sandbox: boolean;
      is_live: boolean;
      require_explicit_confirmation: boolean;
    }>('/trading/environment');
  }

  // Risk Management & Kill Switches
  public static getRiskSettings() {
    return this.request<any>('/risk/settings');
  }

  public static updateRiskSettings(data: any) {
    return this.request<any>('/risk/settings', {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  public static getKillSwitches() {
    return this.request<any[]>('/risk/kill-switch');
  }

  public static toggleKillSwitch(scope: 'PLATFORM' | 'USER' | 'AI_TRADING', is_active: boolean, reason?: string) {
    return this.request<any>('/risk/kill-switch', {
      method: 'POST',
      body: JSON.stringify({ scope, is_active, reason })
    });
  }

  public static getRiskEvents(limit = 50) {
    return this.request<any[]>(`/risk/events?limit=${limit}`);
  }

  // Broker Gateway Integration
  public static getBrokerStatus() {
    return this.request<any>('/broker/status');
  }

  public static connectBroker(data: {
    broker_name: string;
    environment: string;
    api_key: string;
    api_secret: string;
    client_id?: string;
    access_token?: string;
  }) {
    return this.request<any>('/broker/connect', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  public static disconnectBroker() {
    return this.request<any>('/broker/disconnect', {
      method: 'POST'
    });
  }

  public static getBrokerMargins() {
    return this.request<any>('/broker/margins');
  }

  public static getBrokerPositions() {
    return this.request<any[]>('/broker/positions');
  }

  public static triggerReconciliation() {
    return this.request<any>('/broker/reconcile', {
      method: 'POST'
    });
  }

  public static getReconciliationEvents(limit = 50) {
    return this.request<any[]>(`/broker/reconcile/events?limit=${limit}`);
  }

  // AI Auto-Trading Engine
  public static getAIAutoTradingSettings() {
    return this.request<any>('/ai/auto-trading/settings');
  }

  public static updateAIAutoTradingSettings(data: any) {
    return this.request<any>('/ai/auto-trading/settings', {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  public static triggerAIEmergencyStop() {
    return this.request<any>('/ai/auto-trading/emergency-stop', {
      method: 'POST'
    });
  }

  public static evaluateAISignal(signal: any) {
    return this.request<any>('/ai/auto-trading/evaluate-signal', {
      method: 'POST',
      body: JSON.stringify(signal)
    });
  }

  // Health
  public static getMarketHealth() {
    return this.request<any>('/health/market');
  }

  public static getPaperHealth() {
    return this.request<any>('/health/paper-trading');
  }

  public static getBrokerHealth() {
    return this.request<any>('/health/broker');
  }
}

