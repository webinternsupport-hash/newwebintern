import { API } from '../api.js';

export async function renderDetailView(slug) {
  const container = document.createElement('div');
  container.className = 'container';
  container.style.padding = '40px 16px';

  let internship = null;
  try {
    const res = await API.getInternship(slug);
    internship = res.internship;
  } catch (e) {
    container.innerHTML = `
      <div style="text-align: center; padding: 60px 0;">
        <h2>Program Not Found</h2>
        <a href="#/explore" class="btn btn-primary mt-3">Back to Explore</a>
      </div>
    `;
    return container;
  }

  container.innerHTML = `
    <!-- Header Banner -->
    <div style="background-color: white; border-radius: var(--radius-lg); border: 1px solid var(--border-color); padding: 32px; margin-bottom: 30px;">
      <div style="display: flex; gap: 20px; align-items: flex-start; flex-wrap: wrap;">
        <div class="emoji-bubble" style="width: 64px; height: 64px; font-size: 2.2rem;">${internship.internship_emoji || '💼'}</div>
        <div style="flex: 1;">
          <span class="badge badge-primary">${internship.sector_name || 'Virtual Track'}</span>
          <h1 style="font-size: 2rem; font-weight: 800; margin: 8px 0;">${internship.title}</h1>
          <p style="color: var(--text-muted); font-size: 1.05rem; margin-bottom: 16px;">${internship.short_description || ''}</p>
          
          <div style="display: flex; gap: 24px; flex-wrap: wrap; font-size: 0.9rem; color: var(--text-muted);">
            <span>⏱️ <strong>Duration:</strong> 4 Weeks</span>
            <span>📍 <strong>Location:</strong> ${internship.location || 'Virtual / Remote'}</span>
            <span>🏢 <strong>Company:</strong> ${internship.company_name || 'Web Intern'}</span>
            <span>👨‍🏫 <strong>Supervisor:</strong> ${internship.guide_name}</span>
          </div>
        </div>
      </div>
    </div>

    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 30px;">
      <!-- Main Content & Weekly Syllabus Accordion -->
      <div>
        <div class="card" style="margin-bottom: 30px;">
          <h3 style="font-size: 1.3rem; font-weight: 700; margin-bottom: 12px;">Program Overview</h3>
          <p style="color: var(--text-muted); line-height: 1.6; margin-bottom: 16px;">${internship.full_description || internship.short_description}</p>
          
          <h4 style="font-weight: 700; margin-bottom: 8px;">Skills & Tools Covered:</h4>
          <p style="color: var(--primary); font-weight: 600;">${internship.skills_tools || 'Python, Analytics, Web'}</p>
        </div>

        <h3 style="font-size: 1.4rem; font-weight: 800; margin-bottom: 16px;">Weekly Task Syllabus (4 Modules)</h3>
        
        <div class="accordion" id="task-accordion">
          ${(internship.tasks || []).map((t, idx) => `
            <div class="accordion-item ${idx === 0 ? 'active' : ''}">
              <div class="accordion-header">
                <span>Week ${t.week_number}: ${t.title}</span>
                <span>▼</span>
              </div>
              <div class="accordion-content">
                <p style="margin-bottom: 10px;"><strong>🎯 Objective:</strong> ${t.objective || ''}</p>
                <p style="margin-bottom: 10px;"><strong>📦 Deliverables:</strong> ${t.deliverables || ''}</p>
                <p style="margin-bottom: 10px;"><strong>🔹 Key Steps:</strong> ${t.key_steps || ''}</p>
                <p><strong>📊 Evaluation Criteria:</strong> ${t.evaluation_criteria || ''}</p>
              </div>
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Sticky Summary Card & Apply Button -->
      <div>
        <div class="card" style="position: sticky; top: 80px;">
          <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 16px;">Enrollment Summary</h3>
          
          <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; font-size: 0.95rem;">
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-muted);">Application Fee:</span>
              <span style="font-weight: 700; color: var(--success);">FREE (₹0)</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-muted);">Offer Letter:</span>
              <span style="font-weight: 600;">Instant PDF Download</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-muted);">Duration:</span>
              <span style="font-weight: 600;">4 Weeks</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
              <span style="color: var(--text-muted);">Certificate:</span>
              <span style="font-weight: 600;">MSME Recognized</span>
            </div>
          </div>

          <button id="apply-now-btn" class="btn btn-primary btn-lg btn-block">Apply for Internship Now</button>
          <div id="apply-status-msg" style="margin-top: 12px; font-size: 0.85rem; text-align: center;"></div>
        </div>
      </div>
    </div>
  `;

  // Accordion toggle behavior
  const headers = container.querySelectorAll('.accordion-header');
  headers.forEach(h => {
    h.addEventListener('click', () => {
      const item = h.parentElement;
      item.classList.toggle('active');
    });
  });

  // Apply button listener
  const applyBtn = container.querySelector('#apply-now-btn');
  const statusMsg = container.querySelector('#apply-status-msg');

  applyBtn.addEventListener('click', async () => {
    const token = API.getToken();
    if (!token) {
      window.location.hash = '#/login';
      return;
    }

    applyBtn.disabled = true;
    applyBtn.textContent = 'Submitting Application...';
    statusMsg.innerHTML = `<span style="color: var(--primary);">Processing registration & generating Offer Letter PDF...</span>`;

    try {
      const res = await API.applyInternship(internship.id);
      statusMsg.innerHTML = `<span style="color: var(--success);">✅ Enrolled! Redirecting to dashboard...</span>`;
      setTimeout(() => {
        window.location.hash = '#/dashboard';
      }, 1000);
    } catch (err) {
      applyBtn.disabled = false;
      applyBtn.textContent = 'Apply for Internship Now';
      statusMsg.innerHTML = `<span style="color: var(--danger);">${err.message || 'Application failed'}</span>`;
    }
  });

  return container;
}
