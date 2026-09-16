import { API } from '../api.js';

export async function renderVerifyView(certId) {
  const container = document.createElement('div');
  container.className = 'container';
  container.style.padding = '60px 16px';
  container.style.maxWidth = '680px';

  let certData = null;
  try {
    certData = await API.verifyCertificate(certId);
  } catch (e) {
    container.innerHTML = `
      <div class="card" style="text-align: center; padding: 40px 20px;">
        <div style="font-size: 3rem; color: var(--danger); margin-bottom: 12px;">❌</div>
        <h2 style="color: var(--danger);">Invalid or Unverified Credential</h2>
        <p style="color: var(--text-muted); margin-top: 8px;">No official certificate found matching ID: <strong>${certId}</strong></p>
        <a href="#/" class="btn btn-outline mt-4">Go to Homepage</a>
      </div>
    `;
    return container;
  }

  container.innerHTML = `
    <div class="card" style="border: 2px solid var(--primary); box-shadow: var(--shadow-lg);">
      <!-- Verified Badge Header -->
      <div style="text-align: center; margin-bottom: 24px; padding-bottom: 20px; border-bottom: 1px solid var(--border-color);">
        <div style="font-size: 3.5rem; margin-bottom: 8px;">🛡️</div>
        <span class="badge ${certData.is_verified_paid ? 'badge-success' : 'badge-warning'}" style="font-size: 0.9rem; padding: 6px 14px;">
          ${certData.status || 'VERIFIED CREDENTIAL'}
        </span>
        <h1 style="font-size: 1.8rem; font-weight: 800; margin-top: 12px;">Official Credential Verification</h1>
        <p style="color: var(--text-muted); font-size: 0.9rem;">Issued by Web Intern Academic Board & MSME ISO Standard</p>
      </div>

      <!-- Credential Details Grid -->
      <div style="display: flex; flex-direction: column; gap: 16px; font-size: 0.95rem;">
        <div style="display: flex; justify-content: space-between; padding: 10px; background-color: var(--bg-main); border-radius: var(--radius-sm);">
          <span style="color: var(--text-muted);">Certificate Reference ID:</span>
          <span style="font-family: monospace; font-weight: 700;">${certData.certificate_id}</span>
        </div>

        <div style="display: flex; justify-content: space-between; padding: 10px; background-color: var(--bg-main); border-radius: var(--radius-sm);">
          <span style="color: var(--text-muted);">Candidate Full Name:</span>
          <span style="font-weight: 700; color: var(--secondary);">${certData.student_name}</span>
        </div>

        <div style="display: flex; justify-content: space-between; padding: 10px; background-color: var(--bg-main); border-radius: var(--radius-sm);">
          <span style="color: var(--text-muted);">Academic Institution:</span>
          <span style="font-weight: 600;">${certData.college_name || 'University Student'}</span>
        </div>

        <div style="display: flex; justify-content: space-between; padding: 10px; background-color: var(--bg-main); border-radius: var(--radius-sm);">
          <span style="color: var(--text-muted);">Internship Track:</span>
          <span style="font-weight: 700; color: var(--primary);">${certData.internship_title}</span>
        </div>

        <div style="display: flex; justify-content: space-between; padding: 10px; background-color: var(--bg-main); border-radius: var(--radius-sm);">
          <span style="color: var(--text-muted);">Program Duration:</span>
          <span style="font-weight: 600;">4 Weeks (${certData.start_date} - ${certData.end_date})</span>
        </div>

        <div style="display: flex; justify-content: space-between; padding: 10px; background-color: var(--bg-main); border-radius: var(--radius-sm);">
          <span style="color: var(--text-muted);">Program Director:</span>
          <span style="font-weight: 600;">${certData.guide_name}</span>
        </div>
      </div>

      <!-- Action Button -->
      <div style="margin-top: 28px; text-align: center;">
        <a href="/api/certificates/${certData.certificate_id}/pdf" target="_blank" class="btn btn-primary btn-block">
          📄 Download Verified Certificate PDF
        </a>
      </div>
    </div>
  `;

  return container;
}
