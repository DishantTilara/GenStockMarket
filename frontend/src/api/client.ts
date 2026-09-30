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

  public static async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
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

  public static getHistory(symbol: string, days = 90) {
    return this.request<any[]>(`/market/history/${symbol}?days=${days}`);
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
    return this.request('/watchlists', {
      method: 'POST',
      body: JSON.stringify({ name, description })
    });
  }

  public static addWatchlistItem(watchlistId: string, symbol: string) {
    return this.request(`/watchlists/${watchlistId}/items`, {
      method: 'POST',
      body: JSON.stringify({ symbol })
    });
  }

  public static removeWatchlistItem(watchlistId: string, symbol: string) {
    return this.request(`/watchlists/${watchlistId}/items/${symbol}`, {
      method: 'DELETE'
    });
  }

  // Alerts
  public static getAlerts() {
    return this.request<any[]>('/alerts');
  }

  public static createAlert(symbol: string, condition_type: string, target_value: number) {
    return this.request('/alerts', {
      method: 'POST',
      body: JSON.stringify({ symbol, condition_type, target_value })
    });
  }

  public static deleteAlert(alertId: string) {
    return this.request(`/alerts/${alertId}`, { method: 'DELETE' });
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
    return this.request('/strategies', {
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

  // Orders & Risk
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

  public static getOrders() {
    return this.request<any[]>('/orders');
  }

  // Health
  public static getMarketHealth() {
    return this.request<any>('/health/market');
  }
}
