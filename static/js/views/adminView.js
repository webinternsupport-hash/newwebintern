import { API } from '../api.js';

export async function renderAdminView() {
  const container = document.createElement('div');
  container.className = 'container';
  container.style.padding = '40px 16px';

  let overview = null;
  let submissions = [];
  let isAdmin = false;

  try {
    overview = await API.getAdminOverview();
    const subRes = await API.getPendingSubmissions();
    submissions = subRes.submissions || [];
    isAdmin = true;
  } catch (e) {
    isAdmin = false;
  }

  if (!isAdmin) {
    container.innerHTML = `
      <div style="max-width: 440px; margin: 40px auto;" class="card">
        <div style="text-align: center; margin-bottom: 20px;">
          <span class="badge badge-accent">Staff Portal</span>
          <h2 style="font-size: 1.8rem; font-weight: 800; margin-top: 8px;">Admin / Mentor Login</h2>
        </div>
        <form id="admin-login-form">
          <div class="form-group">
            <label class="form-label">Admin Email</label>
            <input type="email" id="admin-email" class="form-control" placeholder="admin@webintern.com" required/>
          </div>
          <div class="form-group">
            <label class="form-label">Password</label>
            <input type="password" id="admin-password" class="form-control" placeholder="••••••••" required/>
          </div>
          <div id="admin-login-err" style="color: var(--danger); font-size: 0.85rem; margin-bottom: 16px; display: none;"></div>
          <button type="submit" class="btn btn-primary btn-block">Log In as Admin</button>
        </form>
      </div>
    `;

    const form = container.querySelector('#admin-login-form');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = container.querySelector('#admin-email').value;
      const password = container.querySelector('#admin-password').value;
      const errDiv = container.querySelector('#admin-login-err');

      try {
        await API.adminLogin({ email, password });
        window.location.hash = '#/admin';
        window.location.reload();
      } catch (err) {
        errDiv.textContent = err.message || 'Invalid admin credentials.';
        errDiv.style.display = 'block';
      }
    });

    return container;
  }

  // Admin Dashboard UI
  container.innerHTML = `
    <div style="margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <span class="badge badge-primary">System Administration</span>
        <h1 style="font-size: 2rem; font-weight: 800; margin-top: 8px;">Mentor & Admin Dashboard</h1>
      </div>
      <button id="admin-logout-btn" class="btn btn-outline btn-sm">Log Out Admin</button>
    </div>

    <!-- Overview Stats Grid -->
    <div class="stats-grid" style="margin-bottom: 30px;">
      <div class="stat-box">
        <div class="stat-number">${overview.total_students || 0}</div>
        <div class="stat-label">Total Students</div>
      </div>
      <div class="stat-box">
        <div class="stat-number">${overview.total_applications || 0}</div>
        <div class="stat-label">Total Applications</div>
      </div>
      <div class="stat-box">
        <div class="stat-number">${overview.pending_submissions || 0}</div>
        <div class="stat-label">Pending Reviews</div>
      </div>
      <div class="stat-box">
        <div class="stat-number">${overview.paid_certificates || 0}</div>
        <div class="stat-label">Verified Certificates</div>
      </div>
    </div>

    <!-- Student Submissions Table -->
    <div class="card">
      <h3 style="font-size: 1.25rem; font-weight: 700; margin-bottom: 16px;">Student Deliverable Review Queue</h3>
      <div style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; font-size: 0.95rem;">
          <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left; color: var(--text-muted);">
              <th style="padding: 10px;">Student</th>
              <th style="padding: 10px;">Program</th>
              <th style="padding: 10px;">Week</th>
              <th style="padding: 10px;">Deliverable PDF</th>
              <th style="padding: 10px;">Current Status</th>
              <th style="padding: 10px;">Marks</th>
              <th style="padding: 10px; text-align: right;">Action</th>
            </tr>
          </thead>
          <tbody>
            ${submissions.length === 0 ? `
              <tr><td colspan="7" style="text-align: center; padding: 20px; color: var(--text-muted);">No student submissions found.</td></tr>
            ` : submissions.map(sub => `
              <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 10px;">
                  <strong>${sub.student_name}</strong><br/>
                  <font size="2" color="#64748b">${sub.student_email}</font>
                </td>
                <td style="padding: 10px;">${sub.internship_title}</td>
                <td style="padding: 10px; font-weight: 700;">Week ${sub.week_number}</td>
                <td style="padding: 10px;">
                  <a href="${sub.file_url}" target="_blank" class="btn btn-outline btn-sm">📄 View PDF</a>
                </td>
                <td style="padding: 10px;">
                  <span class="badge ${sub.status === 'graded' || sub.status === 'approved' ? 'badge-success' : 'badge-warning'}">
                    ${sub.status.toUpperCase()}
                  </span>
                </td>
                <td style="padding: 10px; font-weight: 700;">${sub.marks !== null ? `${sub.marks}/10` : '-'}</td>
                <td style="padding: 10px; text-align: right;">
                  <button class="btn btn-primary btn-sm grade-btn" data-sub-id="${sub.id}">Grade Work</button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;

  // Admin Logout
  container.querySelector('#admin-logout-btn')?.addEventListener('click', () => {
    API.clearToken();
    window.location.hash = '#/admin';
    window.location.reload();
  });

  // Grade Modal Trigger
  container.querySelectorAll('.grade-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const subId = btn.getAttribute('data-sub-id');
      const marksStr = prompt("Enter Marks (0 to 10):", "9");
      if (marksStr === null) return;
      const feedbackStr = prompt("Enter Mentor Feedback:", "Great implementation!");

      API.gradeSubmission({
        submission_id: subId,
        marks: parseFloat(marksStr),
        feedback: feedbackStr || 'Approved by mentor',
        status: 'graded'
      }).then(() => {
        alert("Submission graded successfully!");
        window.location.reload();
      }).catch(err => alert("Grading error: " + err.message));
    });
  });

  return container;
}
