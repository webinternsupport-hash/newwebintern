/**
 * Web Intern Platform - API Client
 */

export const API = {
  getToken() {
    return localStorage.getItem('webintern_jwt') || '';
  },

  setToken(token) {
    if (token) {
      localStorage.setItem('webintern_jwt', token);
      document.cookie = `token=${token}; path=/; max-age=${7 * 24 * 3600}`;
    }
  },

  clearToken() {
    localStorage.removeItem('webintern_jwt');
    document.cookie = 'token=; path=/; max-age=0';
  },

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : endpoint;
    const token = this.getToken();
    
    const headers = {
      ...options.headers
    };

    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || `HTTP error ${response.status}`);
      }
      return data;
    } catch (err) {
      console.error(`[API Error] ${endpoint}:`, err);
      throw err;
    }
  },

  // Auth Endpoints
  async register(formData) {
    const res = await this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(formData)
    });
    if (res.token) this.setToken(res.token);
    return res;
  },

  async login(credentials) {
    const res = await this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
    if (res.token) this.setToken(res.token);
    return res;
  },

  async getMe() {
    return await this.request('/api/auth/me');
  },

  async googleSync(payload) {
    const res = await this.request('/api/auth/google-sync', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    if (res.token) this.setToken(res.token);
    return res;
  },

  // Sectors & Internships
  async getSectors() {
    return await this.request('/api/sectors');
  },

  async getSector(slug) {
    return await this.request(`/api/sectors/${slug}`);
  },

  async getInternships(params = {}) {
    const query = new URLSearchParams(params).toString();
    return await this.request(`/api/internships?${query}`);
  },

  async getInternship(slug) {
    return await this.request(`/api/internships/${slug}`);
  },

  // Applications
  async applyInternship(internshipId) {
    return await this.request('/api/applications', {
      method: 'POST',
      body: JSON.stringify({ internship_id: internshipId })
    });
  },

  async getMyApplications() {
    return await this.request('/api/applications/me');
  },

  // Submissions
  async uploadSubmission(formData) {
    return await this.request('/api/submissions/upload', {
      method: 'POST',
      body: formData
    });
  },

  async getSubmissions(appId) {
    return await this.request(`/api/submissions/${appId}`);
  },

  // Certificates & Payments
  async verifyCertificate(certId) {
    return await this.request(`/api/certificates/verify/${certId}`);
  },

  async createPaymentOrder(certId, appId) {
    return await this.request('/api/payments/create-order', {
      method: 'POST',
      body: JSON.stringify({ certificate_id: certId, application_id: appId })
    });
  },

  async verifyPayment(payload) {
    return await this.request('/api/payments/verify', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // Referrals
  async getReferralStats() {
    return await this.request('/api/referrals/my-stats');
  },

  async claimReferralReward(payload) {
    return await this.request('/api/referrals/claim-reward', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // Admin
  async adminLogin(credentials) {
    const res = await this.request('/api/admin/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
    if (res.token) this.setToken(res.token);
    return res;
  },

  async getAdminOverview() {
    return await this.request('/api/admin/overview');
  },

  async getPendingSubmissions() {
    return await this.request('/api/admin/submissions');
  },

  async gradeSubmission(payload) {
    return await this.request('/api/admin/grade-submission', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }
};
