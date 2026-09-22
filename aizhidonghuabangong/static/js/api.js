// api.js — API 请求封装模块
// 封装 fetch 请求，自动携带 Token，统一处理错误

const API = {
    // 获取存储的 Token
    getToken() {
        return localStorage.getItem('token');
    },

    // 保存 Token
    setToken(token) {
        localStorage.setItem('token', token);
    },

    // 清除 Token（登出时使用）
    clearToken() {
        localStorage.removeItem('token');
    },

    // 构建请求头（自动携带 Token）
    headers() {
        const h = { 'Content-Type': 'application/json' };
        const token = this.getToken();
        if (token) {
            h['Authorization'] = `Bearer ${token}`;
        }
        return h;
    },

    // 通用请求方法
    async request(url, options = {}) {
        const config = {
            headers: this.headers(),
            ...options
        };

        try {
            const response = await fetch(url, config);

            // 处理 401 未授权（Token 过期或无效）
            if (response.status === 401) {
                this.clearToken();
                window.location.reload();
                throw new Error('登录已过期，请重新登录');
            }

            // 处理文件下载（blob 响应）
            if (response.headers.get('Content-Disposition')) {
                return response;
            }

            // 处理 JSON 响应
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || '请求失败');
            }

            return data;
        } catch (error) {
            console.error('API 请求错误:', error);
            throw error;
        }
    },

    // ========== 登录 ==========
    async login(username, password) {
        const data = await this.request('/api/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        this.setToken(data.access_token);
        return data;
    },

    // ========== 客户管理 ==========
    async getCustomers(keyword = '') {
        const params = keyword ? `?keyword=${encodeURIComponent(keyword)}` : '';
        return this.request(`/api/customers${params}`);
    },

    async getCustomer(id) {
        return this.request(`/api/customers/${id}`);
    },

    async createCustomer(data) {
        return this.request('/api/customers', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async updateCustomer(id, data) {
        return this.request(`/api/customers/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async deleteCustomer(id) {
        return this.request(`/api/customers/${id}`, {
            method: 'DELETE'
        });
    },

    // ========== 订单管理 ==========
    async getOrders(keyword = '', status = '') {
        const params = new URLSearchParams();
        if (keyword) params.append('keyword', keyword);
        if (status) params.append('status', status);
        const qs = params.toString();
        return this.request(`/api/orders${qs ? '?' + qs : ''}`);
    },

    async getOrder(id) {
        return this.request(`/api/orders/${id}`);
    },

    async createOrder(data) {
        return this.request('/api/orders', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async updateOrder(id, data) {
        return this.request(`/api/orders/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async deleteOrder(id) {
        return this.request(`/api/orders/${id}`, {
            method: 'DELETE'
        });
    },

    // ========== 跟进记录 ==========
    async getFollowups(customerId = '') {
        const params = customerId ? `?customer_id=${customerId}` : '';
        return this.request(`/api/followups${params}`);
    },

    async createFollowup(data) {
        return this.request('/api/followups', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async deleteFollowup(id) {
        return this.request(`/api/followups/${id}`, {
            method: 'DELETE'
        });
    },

    // ========== 文档生成 ==========
    async generateDocument(orderId) {
        const response = await fetch(`/api/documents/generate/${orderId}`, {
            headers: this.headers()
        });

        if (response.status === 401) {
            this.clearToken();
            window.location.reload();
            throw new Error('登录已过期');
        }

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || '文档生成失败');
        }

        // 下载文件
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;

        // 从 Content-Disposition 获取文件名
        const disposition = response.headers.get('Content-Disposition');
        const filenameMatch = disposition && disposition.match(/filename\*?=(?:UTF-8'')?(.+)/i);
        a.download = filenameMatch ? decodeURIComponent(filenameMatch[1]) : '订单文档.docx';

        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        return true;
    },

    // ========== 异常提醒 ==========
    async getAlerts() {
        return this.request('/api/alerts');
    }
};