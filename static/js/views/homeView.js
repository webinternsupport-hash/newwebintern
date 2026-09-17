import { API } from '../api.js';

export async function renderHomeView() {
  const container = document.createElement('div');
  
  // Fetch featured internships & sectors
  let featuredInternships = [];
  let sectors = [];
  try {
    const iRes = await API.getInternships({ featured: 'true', limit: 4 });
    featuredInternships = iRes.internships || [];
    const sRes = await API.getSectors();
    sectors = sRes.sectors || [];
  } catch (e) {
    console.error('Error fetching home data:', e);
  }

  container.innerHTML = `
    <!-- Hero Banner -->
    <section class="hero-section">
      <div class="container">
        <span class="badge badge-primary mb-3">🚀 India's #1 Virtual Internship Platform</span>
        <h1 class="hero-title">Launch Your Career with Guaranteed <br/> Virtual Internships & Official Certificates</h1>
        <p class="hero-subtitle">
          Gain hands-on industry capstone experience across 20+ domains. Apply instantly for free, receive automated PDF Offer Letters, submit weekly projects, and earn verified credentials.
        </p>
        <div style="display: flex; gap: 12px; justify-content: center; flex-wrap: wrap;">
          <a href="#/explore" class="btn btn-primary btn-lg">Explore 200+ Programs</a>
          <a href="#/register" class="btn btn-outline btn-lg">Student Registration</a>
        </div>

        <!-- 2x2 Stats Grid -->
        <div class="stats-grid">
          <div class="stat-box">
            <div class="stat-number">1 Lakh+</div>
            <div class="stat-label">Active Interns</div>
          </div>
          <div class="stat-box">
            <div class="stat-number">97%</div>
            <div class="stat-label">Role Match Rate</div>
          </div>
          <div class="stat-box">
            <div class="stat-number">98%</div>
            <div class="stat-label">Skill Improvement</div>
          </div>
          <div class="stat-box">
            <div class="stat-number">MSME</div>
            <div class="stat-label">ISO Recognized</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Marquee Ticker -->
    <div class="ticker-wrap">
      <div class="ticker">
        <span>💼 Full Stack Web Development</span>
        <span>🤖 AI & Machine Learning</span>
        <span>⚡ C Algorithms</span>
        <span>📊 Data Science Analytics</span>
        <span>📈 Financial Valuation</span>
        <span>🎨 UI/UX Design</span>
        <span>⚖️ Corporate Law</span>
        <span>🏥 Health Informatics</span>
        <span>💼 Full Stack Web Development</span>
        <span>🤖 AI & Machine Learning</span>
      </div>
    </div>

    <!-- Sectors Section -->
    <section style="padding: 50px 0;">
      <div class="container">
        <div style="text-align: center; margin-bottom: 36px;">
          <span class="badge badge-accent">8 Domain Tracks</span>
          <h2 style="font-size: 2rem; font-weight: 800; margin-top: 8px;">Explore Specialized Sectors</h2>
          <p style="color: var(--text-muted);">Choose your discipline and start building real-world projects today</p>
        </div>

        <div class="grid grid-cols-4">
          ${sectors.slice(0, 8).map(sec => `
            <a href="#/sector/${sec.slug}" class="card card-hover" style="text-decoration: none; text-align: center;">
              <div style="font-size: 2.5rem; margin-bottom: 12px;">${sec.icon_url || '💼'}</div>
              <h3 style="font-size: 1.1rem; font-weight: 700; color: var(--secondary); margin-bottom: 4px;">${sec.name}</h3>
              <p style="font-size: 0.85rem; color: var(--text-muted);">${sec.internship_count || 0} Programs Available</p>
            </a>
          `).join('')}
        </div>
      </div>
    </section>

    <!-- Featured Internships -->
    <section style="padding: 50px 0; background-color: white; border-top: 1px solid var(--border-color); border-bottom: 1px solid var(--border-color);">
      <div class="container">
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 36px; flex-wrap: wrap; gap: 16px;">
          <div>
            <span class="badge badge-success">Top Rated</span>
            <h2 style="font-size: 2rem; font-weight: 800; margin-top: 8px;">Featured 4-Week Programs</h2>
          </div>
          <a href="#/explore" class="btn btn-outline">View All Programs &rarr;</a>
        </div>

        <div class="grid grid-cols-3">
          ${featuredInternships.map(intern => `
            <div class="card card-hover internship-card">
              <div>
                <div class="internship-header">
                  <div class="emoji-bubble">${intern.internship_emoji || '💼'}</div>
                  <span class="badge badge-primary">Virtual / 4 Weeks</span>
                </div>
                <h3 class="internship-title">${intern.title}</h3>
                <p class="internship-desc">${intern.short_description || ''}</p>
              </div>
              <div>
                <div class="internship-meta">
                  <span>🛠️ ${intern.skills_tools ? intern.skills_tools.split(',').slice(0, 2).join(', ') : 'Tech'}</span>
                  <span>🏆 Official Certificate</span>
                </div>
                <a href="#/internship/${intern.slug}" class="btn btn-primary btn-block">View Program Details</a>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    </section>

    <!-- 4-Step Process -->
    <section style="padding: 60px 0;">
      <div class="container">
        <div style="text-align: center; margin-bottom: 40px;">
          <h2 style="font-size: 2rem; font-weight: 800;">How Web Intern Works</h2>
          <p style="color: var(--text-muted);">Simple 4-step path from application to verified certification</p>
        </div>

        <div class="grid grid-cols-4">
          <div class="card" style="text-align: center;">
            <div style="font-size: 2rem; font-weight: 900; color: var(--primary); margin-bottom: 12px;">01</div>
            <h4 style="font-weight: 700; margin-bottom: 8px;">Select Domain</h4>
            <p style="font-size: 0.9rem; color: var(--text-muted);">Browse 20+ sector internships and choose your specialization.</p>
          </div>
          <div class="card" style="text-align: center;">
            <div style="font-size: 2rem; font-weight: 900; color: var(--primary); margin-bottom: 12px;">02</div>
            <h4 style="font-weight: 700; margin-bottom: 8px;">Instant Offer Letter</h4>
            <p style="font-size: 0.9rem; color: var(--text-muted);">Apply for free and receive your official PDF Offer Letter immediately.</p>
          </div>
          <div class="card" style="text-align: center;">
            <div style="font-size: 2rem; font-weight: 900; color: var(--primary); margin-bottom: 12px;">03</div>
            <h4 style="font-weight: 700; margin-bottom: 8px;">Submit Weekly Tasks</h4>
            <p style="font-size: 0.9rem; color: var(--text-muted);">Upload 4 weekly project deliverables (PDF format) for mentor evaluation.</p>
          </div>
          <div class="card" style="text-align: center;">
            <div style="font-size: 2rem; font-weight: 900; color: var(--primary); margin-bottom: 12px;">04</div>
            <h4 style="font-weight: 700; margin-bottom: 8px;">Verified Credential</h4>
            <p style="font-size: 0.9rem; color: var(--text-muted);">Unlock your MSME recognized certificate with online QR verification.</p>
          </div>
        </div>
      </div>
    </section>
  `;

  return container;
}
