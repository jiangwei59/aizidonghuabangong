// app.js — 前端业务逻辑
// 处理页面交互、数据加载、表单提交等

const App = {
    // 当前客户列表（缓存，用于订单和跟进表单选择）
    customerList: [],

    // ========== 初始化 ==========
    init() {
        this.bindEvents();
        this.checkLogin();
    },

    // 检查登录状态
    checkLogin() {
        if (API.getToken()) {
            this.showMainPage();
        } else {
            this.showLoginPage();
        }
    },

    // 绑定全局事件
    bindEvents() {
        // 登录表单
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // 客户表单
        document.getElementById('customerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSaveCustomer();
        });

        // 订单表单
        document.getElementById('orderForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSaveOrder();
        });

        // 跟进表单
        document.getElementById('followupForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSaveFollowup();
        });

        // 导航切换
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchPage(link.dataset.page);
            });
        });

        // 搜索框回车
        document.getElementById('customerSearch').addEventListener('keyup', (e) => {
            if (e.key === 'Enter') this.loadCustomers();
        });

        document.getElementById('orderSearch').addEventListener('keyup', (e) => {
            if (e.key === 'Enter') this.loadOrders();
        });

        // 订单状态筛选
        document.getElementById('orderStatusFilter').addEventListener('change', () => {
            this.loadOrders();
        });

        // 跟进记录客户筛选
        document.getElementById('followupCustomerFilter').addEventListener('change', () => {
            this.loadFollowups();
        });
    },

    // ========== 页面切换 ==========
    showLoginPage() {
        document.getElementById('loginPage').style.display = 'flex';
        document.getElementById('mainPage').style.display = 'none';
    },

    showMainPage() {
        document.getElementById('loginPage').style.display = 'none';
        document.getElementById('mainPage').style.display = 'block';
        // 加载默认页面数据
        this.loadCustomers();
    },

    switchPage(pageName) {
        // 切换导航高亮
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.dataset.page === pageName);
        });

        // 切换页面显示
        document.querySelectorAll('.page').forEach(page => {
            page.classList.toggle('active', page.id === `page-${pageName}`);
        });

        // 加载对应页面数据
        switch (pageName) {
            case 'customers': this.loadCustomers(); break;
            case 'orders': this.loadOrders(); break;
            case 'followups':
                this.loadCustomerOptions('followupCustomerFilter');
                this.loadFollowups();
                break;
            case 'documents': this.loadOrdersForDoc(); break;
            case 'alerts': this.loadAlerts(); break;
        }
    },

    // ========== 登录/登出 ==========
    async handleLogin() {
        const username = document.getElementById('loginUsername').value.trim();
        const password = document.getElementById('loginPassword').value;
        const errorEl = document.getElementById('loginError');

        try {
            errorEl.textContent = '';
            await API.login(username, password);
            this.showMainPage();
            this.toast('登录成功', 'success');
        } catch (error) {
            errorEl.textContent = error.message || '登录失败';
        }
    },

    logout() {
        API.clearToken();
        this.showLoginPage();
        this.toast('已退出登录');
    },

    // ========== 客户管理 ==========
    async loadCustomers() {
        try {
            const keyword = document.getElementById('customerSearch').value.trim();
            const customers = await API.getCustomers(keyword);
            this.customerList = customers; // 缓存客户列表
            this.renderCustomerTable(customers);
        } catch (error) {
            this.toast(error.message, 'error');
        }
    },

    renderCustomerTable(customers) {
        const tbody = document.getElementById('customerTableBody');
        if (customers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:#999;">暂无客户数据</td></tr>';
            return;
        }

        tbody.innerHTML = customers.map(c => `
            <tr>
                <td>${c.id}</td>
                <td>${this.esc(c.name)}</td>
                <td>${this.esc(c.contact || '-')}</td>
                <td>${this.esc(c.phone || '-')}</td>
                <td>${this.esc(c.address || '-')}</td>
                <td>${this.formatDate(c.created_at)}</td>
                <td class="actions">
                    <button class="btn btn-sm" onclick="App.editCustomer(${c.id})">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="App.deleteCustomer(${c.id})">删除</button>
                </td>
            </tr>
        `).join('');
    },

    showCustomerForm(customer = null) {
        document.getElementById('customerModalTitle').textContent = customer ? '编辑客户' : '新增客户';
        document.getElementById('customerId').value = customer ? customer.id : '';
        document.getElementById('customerName').value = customer ? customer.name : '';
        document.getElementById('customerContact').value = customer ? (customer.contact || '') : '';
        document.getElementById('customerPhone').value = customer ? (customer.phone || '') : '';
        document.getElementById('customerAddress').value = customer ? (customer.address || '') : '';
        document.getElementById('customerNotes').value = customer ? (customer.notes || '') : '';
        this.openModal('customerModal');
    },

    async editCustomer(id) {
        try {
            const customer = await API.getCustomer(id);
            this.showCustomerForm(customer);
        } catch (error) {
            this.toast(error.message, 'error');
        }
    },

    async handleSaveCustomer() {
        const id = document.getElementById('customerId').value;
        const data = {
            name: document.getElementById('customerName').value.trim(),
            contact: document.getElementById('customerContact').value.trim() || null,
            phone: document.getElementById('customerPhone').value.trim() || null,
            address: document.getElementById('customerAddress').value.trim() || null,
            notes: document.getElementById('customerNotes').value.trim() || null,
        };

        try {
            if (id) {
                await API.updateCustomer(id, data);
                this.toast('客户信息已更新', 'success');
            } else {
                await API.createCustomer(data);
                this.toast('客户创建成功', 'success');
            }
            this.closeModal('customerModal');
            this.loadCustomers();
        } catch (error) {
            this.toast(error.message, 'error');
        }
    },

    async deleteCustomer(id) {
        if (!confirm('确定要删除该客户吗？关联的订单和跟进记录也将被删除。')) return;
        try {
            await API.deleteCustomer(id);
            this.toast('删除成功', 'success');
            this.loadCustomers();
        } catch (error) {
            this.toast(error.message, 'error');
        }
    },

    // ========== 订单管理 ==========
    async loadOrders() {
        try {
            const keyword = document.getElementById('orderSearch').value.trim();
            const status = document.getElementById('orderStatusFilter').value;
            const orders = await API.getOrders(keyword, status);
            this.renderOrderTable(orders);
        } catch (error) {
            this.toast(error.message, 'error');
        }
    },

    renderOrderTable(orders) {
        const tbody = document.getElementById('orderTableBody');
        if (orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#999;">暂无订单数据</td></tr>';
            return;
        }

        tbody.innerHTML = orders.map(o => `
            <tr>
                <td>${this.esc(o.order_no)}</td>
                <td>${this.esc(o.customer_name || '-')}</td>
                <td>¥${Number(o.amount).toLocaleString('zh-CN', {minimumFractionDigits: 2})}</td>
                <td>${this.esc(o.product_info || '-')}</td>
                <td>${o.delivery_date || '-'}</td>
                <td><span class="status-tag ${this.statusClass(o.status)}">${this.esc(o.status)}</span></td>
                <td>${this.formatDate(o.created_at)}</td>
                <td class="actions">
                    <button class="btn btn-sm" onclick="App.editOrder(${o.id})">编辑</button>
                    <button class="btn btn-sm btn-danger" onclick="App.deleteOrder(${o.id})">删除</button>
                </td>
            </tr>
        `).join('');
    },

    async showOrderForm(order = null) {
        document.getElementById('orderModalTitle').textContent = order ? '编辑订单' : '新增订单';
        document.getElementById('orderId').value = order ? order.id : '';
        document.getElementById('orderAmount').value = order ? order.amount : '0';
        document.getElementById('orderProductInfo').value = order ? (order.product_info || '') : '';
        document.getElementById('orderDeliveryDate').value = order ? (order.delivery_date || '') : '';
        document.getElementById('orderStatus').value = order ? order.status : '待处理';

        // 加载客户下拉选项
        await this.loadCustomerOptions('orderCustomerId');
        if (order) {
            document.getElementById('orderCustomerId').value = order.customer_id;
        }

        this.openModal('orderModal');
    },

    async editOrder(id) {
        try {
            const order = await API.getOrder(id);
            this.showOrderForm(order);
        } catch (error) {
            this.toast(error.message, 'error');
        }
    },

    async handleSaveOrder() {
        const id = document.getElementById('orderId').value;
        const data = {
            customer_id: parseInt(document.getElementById('orderCustomerId').value),
            amount: parseFloat(document.getElementById('orderAmount').value) || 0,
            product_info: document.getElementById('orderProductInfo').value.trim() || null,
            delivery_date: document.getElementById('orderDeliveryDate').value || null,
            status: document.getElementById('orderStatus').value,
        };

        try {
            if (id) {
                await API.updateOrder(id, data);
                this.toast('订单已更新', 'success');
            } else {
                await API.createOrder(data);
                this.toast('订单创建成功', 'success');
            }
            this.closeModal('orderModal');
            this.loadOrders();
        } catch (error) {
            this.toast(error.message, 'error');
        }
    },

    async deleteOrder(id) {
        if (!confirm('确定要删除该订单吗？')) return;
        try {
            await API.deleteOrder(id);
            this.toast('删除成功', 'success');
            this.loadOrders();
        } catch (error) {
            this.toast(error.message, 'error');
        }
    },

    // ========== 跟进记录 ==========
    async loadFollowups() {
        try {
            const customerId = document.getElementById('followupCustomerFilter').value;
            const followups = await API.getFollowups(customerId);
            this.renderFollowupTable(followups);
        } catch (error) {
            this.toast(error.message, 'error');
        }
    },

    renderFollowupTable(followups) {
        const tbody = document.getElementById('followupTableBody');
        if (followups.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#999;">暂无跟进记录</td></tr>';
            return;
        }

        tbody.innerHTML = followups.map(f => `
            <tr>
                <td>${f.id}</td>
                <td>${this.esc(f.customer_name || '-')}</td>
                <td>${this.esc(f.content)}</td>
                <td>${this.formatDate(f.follow_time)}</td>
                <td class="actions">
                    <button class="btn btn-sm btn-danger" onclick="App.deleteFollowup(${f.id})">删除</button>
                </td>
            </tr>
        `).join('');
    },

    async showFollowupForm() {
        document.getElementById('followupContent').value = '';
        await this.loadCustomerOptions('followupCustomerId');
        this.openModal('followupModal');
    },

    async handleSaveFollowup() {
        const data = {
            customer_id: parseInt(document.getElementById('followupCustomerId').value),
            content: document.getElementById('followupContent').value.trim(),
        };

        try {
            await API.createFollowup(data);
            this.toast('跟进记录创建成功', 'success');
            this.closeModal('followupModal');
            this.loadFollowups();
        } catch (error) {
            this.toast(error.message, 'error');
        }
    },

    async deleteFollowup(id) {
        if (!confirm('确定要删除该跟进记录吗？')) return;
        try {
            await API.deleteFollowup(id);
            this.toast('删除成功', 'success');
            this.loadFollowups();
        } catch (error) {
            this.toast(error.message, 'error');
        }
    },

    // ========== 文档导出 ==========
    async loadOrdersForDoc() {
        try {
            const orders = await API.getOrders();
            this.renderDocTable(orders);
        } catch (error) {
            this.toast(error.message, 'error');
        }
    },

    renderDocTable(orders) {
        const tbody = document.getElementById('documentTableBody');
        if (orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#999;">暂无订单数据</td></tr>';
            return;
        }

        tbody.innerHTML = orders.map(o => `
            <tr>
                <td>${this.esc(o.order_no)}</td>
                <td>${this.esc(o.customer_name || '-')}</td>
                <td>¥${Number(o.amount).toLocaleString('zh-CN', {minimumFractionDigits: 2})}</td>
                <td><span class="status-tag ${this.statusClass(o.status)}">${this.esc(o.status)}</span></td>
                <td class="actions">
                    <button class="btn btn-sm btn-primary" onclick="App.downloadDoc(${o.id})">下载 Word</button>
                </td>
            </tr>
        `).join('');
    },

    async downloadDoc(orderId) {
        try {
            await API.generateDocument(orderId);
            this.toast('文档下载成功', 'success');
        } catch (error) {
            this.toast(error.message, 'error');
        }
    },

    // ========== 异常提醒 ==========
    async loadAlerts() {
        try {
            const alerts = await API.getAlerts();
            this.renderAlerts(alerts);
        } catch (error) {
            this.toast(error.message, 'error');
        }
    },

    renderAlerts(alerts) {
        // 到期订单
        const dueEl = document.getElementById('dueOrdersList');
        if (alerts.due_orders.length === 0) {
            dueEl.innerHTML = '<div class="alert-empty">暂无到期订单 ✅</div>';
        } else {
            dueEl.innerHTML = alerts.due_orders.map(a => `
                <div class="alert-item">
                    <div class="alert-title">${this.esc(a.title)}</div>
                    <div class="alert-detail">${this.esc(a.detail)}</div>
                </div>
            `).join('');
        }

        // 待跟进客户
        const followEl = document.getElementById('pendingFollowupsList');
        if (alerts.pending_followups.length === 0) {
            followEl.innerHTML = '<div class="alert-empty">暂无待跟进客户 ✅</div>';
        } else {
            followEl.innerHTML = alerts.pending_followups.map(a => `
                <div class="alert-item">
                    <div class="alert-title">${this.esc(a.title)}</div>
                    <div class="alert-detail">${this.esc(a.detail)}</div>
                </div>
            `).join('');
        }
    },

    // ========== 工具函数 ==========

    // 加载客户下拉选项（用于订单和跟进表单）
    async loadCustomerOptions(selectId) {
        try {
            if (this.customerList.length === 0) {
                this.customerList = await API.getCustomers();
            }
            const select = document.getElementById(selectId);
            const currentValue = select.value;
            select.innerHTML = '<option value="">请选择客户</option>' +
                this.customerList.map(c => `<option value="${c.id}">${this.esc(c.name)}</option>`).join('');
            if (currentValue) select.value = currentValue;
        } catch (error) {
            console.error('加载客户列表失败:', error);
        }
    },

    // 打开弹窗
    openModal(id) {
        document.getElementById(id).classList.add('show');
    },

    // 关闭弹窗
    closeModal(id) {
        document.getElementById(id).classList.remove('show');
    },

    // Toast 提示
    toast(message, type = '') {
        // 移除已有的 toast
        const existing = document.querySelector('.toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        // 显示动画
        setTimeout(() => toast.classList.add('show'), 10);

        // 3 秒后自动消失
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    // HTML 转义（防 XSS）
    esc(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    // 格式化日期
    formatDate(dateStr) {
        if (!dateStr) return '-';
        const d = new Date(dateStr);
        return d.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // 订单状态样式映射
    statusClass(status) {
        const map = {
            '待处理': 'pending',
            '生产中': 'processing',
            '已发货': 'shipped',
            '已完成': 'done',
            '已取消': 'cancelled'
        };
        return map[status] || '';
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => App.init());