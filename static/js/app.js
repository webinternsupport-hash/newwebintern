/**
 * Web Intern Platform - SPA Router & App Manager
 */

import { API } from './api.js';
import { localDB } from './storage.js';
import { renderHomeView } from './views/homeView.js';
import { renderExploreView } from './views/exploreView.js';
import { renderDetailView } from './views/detailView.js';
import { renderDashboardView } from './views/dashboardView.js';
import { renderLoginView, renderRegisterView } from './views/authViews.js';
import { renderAdminView } from './views/adminView.js';
import { renderVerifyView } from './views/verifyView.js';
import { renderSectorsView } from './views/sectorsView.js';

class App {
  constructor() {
    this.appContainer = document.getElementById('app');
    this.currentUser = null;
    this.init();
  }

  async init() {
    // 1. Initialize IndexedDB cache
    await localDB.init();

    // 2. Check current user session via API
    await this.checkAuthSession();

    // 3. Setup Navigation & Hash Listener
    window.addEventListener('hashchange', () => this.handleRoute());
    this.setupNavigationUI();

    // 4. Initial Route rendering
    this.handleRoute();
  }

  async checkAuthSession() {
    const token = API.getToken();
    if (!token) {
      this.updateHeaderAuthUI(null);
      return;
    }

    try {
      const data = await API.getMe();
      this.currentUser = data.profile;
      // Cache in IndexedDB
      localDB.save('profiles', data.profile);
      this.updateHeaderAuthUI(data.profile);
    } catch (err) {
      console.warn('Auth session recovery failed, clearing token');
      API.clearToken();
      this.updateHeaderAuthUI(null);
    }
  }

  logout() {
    API.clearToken();
    try { localDB.save('profiles', null); } catch (e) {}
    this.currentUser = null;
    this.updateHeaderAuthUI(null);
    showToast('You have been logged out successfully', 'success');
    window.location.hash = '#/login';
  }

  updateHeaderAuthUI(user) {
    const authBtn = document.getElementById('auth-header-btn');
    const headerLogoutBtn = document.getElementById('header-logout-btn');
    const drawerLoginLink = document.getElementById('drawer-login-link');
    const drawerLogoutBtn = document.getElementById('drawer-logout-btn');
    const sheetLoginBtn = document.getElementById('sheet-login-btn');
    const sheetLogoutBtn = document.getElementById('sheet-logout-btn');

    if (user) {
      if (authBtn) {
        authBtn.textContent = 'Dashboard';
        authBtn.href = '#/dashboard';
        authBtn.className = 'btn btn-primary btn-sm';
      }
      if (headerLogoutBtn) {
        headerLogoutBtn.style.display = 'inline-flex';
        headerLogoutBtn.onclick = () => this.logout();
      }
      if (drawerLoginLink) {
        drawerLoginLink.textContent = `👤 ${user.full_name} (Dashboard)`;
        drawerLoginLink.href = '#/dashboard';
      }
      if (drawerLogoutBtn) {
        drawerLogoutBtn.style.display = 'block';
        drawerLogoutBtn.onclick = () => {
          document.getElementById('mobile-drawer')?.classList.remove('active');
          document.getElementById('drawer-backdrop')?.classList.remove('active');
          this.logout();
        };
      }
      if (sheetLoginBtn) {
        sheetLoginBtn.textContent = 'Go to Student Dashboard';
        sheetLoginBtn.href = '#/dashboard';
      }
      if (sheetLogoutBtn) {
        sheetLogoutBtn.style.display = 'block';
        sheetLogoutBtn.onclick = () => {
          document.getElementById('bottom-sheet-modal')?.classList.remove('active');
          document.getElementById('bottom-sheet-backdrop')?.classList.remove('active');
          this.logout();
        };
      }
    } else {
      if (authBtn) {
        authBtn.textContent = 'Sign In';
        authBtn.href = '#/login';
        authBtn.className = 'btn btn-outline btn-sm';
      }
      if (headerLogoutBtn) {
        headerLogoutBtn.style.display = 'none';
      }
      if (drawerLoginLink) {
        drawerLoginLink.textContent = '🔑 Sign In / Register';
        drawerLoginLink.href = '#/login';
      }
      if (drawerLogoutBtn) {
        drawerLogoutBtn.style.display = 'none';
      }
      if (sheetLoginBtn) {
        sheetLoginBtn.textContent = 'Sign In / Register';
        sheetLoginBtn.href = '#/login';
      }
      if (sheetLogoutBtn) {
        sheetLogoutBtn.style.display = 'none';
      }
    }
  }

  setupNavigationUI() {
    // Drawer elements
    const drawerToggle = document.getElementById('drawer-toggle-btn');
    const drawerClose = document.getElementById('drawer-close-btn');
    const drawer = document.getElementById('mobile-drawer');
    const backdrop = document.getElementById('drawer-backdrop');

    const toggleDrawer = (open) => {
      if (open) {
        drawer?.classList.add('active');
        backdrop?.classList.add('active');
      } else {
        drawer?.classList.remove('active');
        backdrop?.classList.remove('active');
      }
    };

    drawerToggle?.addEventListener('click', () => toggleDrawer(true));
    drawerClose?.addEventListener('click', () => toggleDrawer(false));
    backdrop?.addEventListener('click', () => toggleDrawer(false));

    // Close drawer when clicking any link
    drawer?.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => toggleDrawer(false));
    });

    // Bottom Sheet elements
    const moreBtn = document.getElementById('bar-tab-more');
    const sheetModal = document.getElementById('bottom-sheet-modal');
    const sheetBackdrop = document.getElementById('bottom-sheet-backdrop');

    const toggleSheet = (open) => {
      if (open) {
        sheetModal?.classList.add('active');
        sheetBackdrop?.classList.add('active');
      } else {
        sheetModal?.classList.remove('active');
        sheetBackdrop?.classList.remove('active');
      }
    };

    moreBtn?.addEventListener('click', () => toggleSheet(true));
    sheetBackdrop?.addEventListener('click', () => toggleSheet(false));
    sheetModal?.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => toggleSheet(false));
    });
  }

  async handleRoute() {
    const hash = window.location.hash || '#/';
    window.scrollTo(0, 0);

    // Active bottom bar tab highlighting
    const tabs = ['home', 'explore', 'referrals', 'profile'];
    tabs.forEach(t => {
      const el = document.getElementById(`bar-tab-${t}`);
      if (el) el.classList.remove('active');
    });

    this.appContainer.innerHTML = `
      <div style="text-align: center; padding: 100px 0;">
        <div style="font-size: 2rem; margin-bottom: 12px;">⏳</div>
        <p style="color: var(--text-muted);">Loading Web Intern...</p>
      </div>
    `;

    let view = null;

    if (hash === '#/' || hash === '#') {
      document.getElementById('bar-tab-home')?.classList.add('active');
      view = await renderHomeView();
    } else if (hash === '#/explore' || hash.startsWith('#/internships')) {
      document.getElementById('bar-tab-explore')?.classList.add('active');
      view = await renderExploreView();
    } else if (hash.startsWith('#/internship/')) {
      const slug = hash.replace('#/internship/', '');
      view = await renderDetailView(slug);
    } else if (hash === '#/sectors') {
      view = await renderSectorsView();
    } else if (hash.startsWith('#/sector/')) {
      const slug = hash.replace('#/sector/', '');
      view = await renderExploreView(); // Explore view with sector pre-selected
    } else if (hash === '#/dashboard') {
      document.getElementById('bar-tab-profile')?.classList.add('active');
      view = await renderDashboardView('internships');
    } else if (hash === '#/referrals' || hash.startsWith('#/refer')) {
      document.getElementById('bar-tab-referrals')?.classList.add('active');
      view = await renderDashboardView('referrals');
    } else if (hash === '#/login') {
      view = renderLoginView();
    } else if (hash === '#/register') {
      view = renderRegisterView();
    } else if (hash === '#/admin') {
      view = await renderAdminView();
    } else if (hash.startsWith('#/verify/')) {
      const certId = hash.replace('#/verify/', '');
      view = await renderVerifyView(certId);
    } else {
      view = await renderHomeView();
    }

    this.appContainer.innerHTML = '';
    if (view) {
      this.appContainer.appendChild(view);
    }
  }
}

// Global Toast Helper
export function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type === 'success' ? 'badge-success' : type === 'error' ? 'badge-danger' : ''}`;
  toast.style.cssText = 'background: #1e293b; color: white; padding: 12px 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: flex; align-items: center; gap: 8px; font-weight: 500; font-size: 0.9rem; border-left: 4px solid var(--primary, #3b82f6);';
  
  if (type === 'success') toast.style.borderLeftColor = '#22c55e';
  if (type === 'error') toast.style.borderLeftColor = '#ef4444';

  const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

window.showToast = showToast;

// Initialize Application & PWA Service Worker
document.addEventListener('DOMContentLoaded', () => {
  window.app = new App();

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(err => {
      console.log('PWA ServiceWorker registration info:', err);
    });
  }
});
