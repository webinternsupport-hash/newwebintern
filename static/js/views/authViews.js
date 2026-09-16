import { API } from '../api.js';

export function renderLoginView() {
  const container = document.createElement('div');
  container.className = 'container';
  container.style.padding = '60px 16px';
  container.style.maxWidth = '460px';

  container.innerHTML = `
    <div class="card">
      <div style="text-align: center; margin-bottom: 24px;">
        <span class="badge badge-primary">Student & Mentor Portal</span>
        <h2 style="font-size: 1.8rem; font-weight: 800; margin-top: 8px;">Sign In to Web Intern</h2>
        <p style="color: var(--text-muted); font-size: 0.9rem;">Access your virtual internships, deliverables, and certificates</p>
      </div>

      <form id="login-form">
        <div class="form-group">
          <label class="form-label">Email Address</label>
          <input type="email" id="login-email" class="form-control" placeholder="name@college.edu" required/>
        </div>

        <div class="form-group">
          <label class="form-label">Password</label>
          <input type="password" id="login-password" class="form-control" placeholder="••••••••" required/>
        </div>

        <div id="login-error" style="color: var(--danger); font-size: 0.85rem; margin-bottom: 16px; display: none;"></div>

        <button type="submit" class="btn btn-primary btn-lg btn-block" id="login-btn">Sign In</button>
      </form>

      <div style="margin-top: 20px; text-align: center; font-size: 0.9rem; color: var(--text-muted);">
        Don't have an account? <a href="#/register" style="font-weight: 600;">Register Free</a>
      </div>

      <!-- Google OAuth Trigger Stub -->
      <div style="margin-top: 20px; border-top: 1px solid var(--border-color); padding-top: 16px; text-align: center;">
        <button id="google-signin-btn" class="btn btn-outline btn-block" style="display: flex; gap: 8px; justify-content: center;">
          <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" width="18" height="18" alt="Google"/>
          Sign in with Google
        </button>
      </div>
    </div>
  `;

  const form = container.querySelector('#login-form');
  const errorDiv = container.querySelector('#login-error');
  const submitBtn = container.querySelector('#login-btn');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorDiv.style.display = 'none';
    submitBtn.disabled = true;
    submitBtn.textContent = 'Signing in...';

    const email = container.querySelector('#login-email').value;
    const password = container.querySelector('#login-password').value;

    try {
      await API.login({ email, password });
      window.location.hash = '#/dashboard';
    } catch (err) {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Sign In';
      errorDiv.textContent = err.message || 'Invalid email or password.';
      errorDiv.style.display = 'block';
    }
  });

  // Google OAuth Stub Listener
  const googleBtn = container.querySelector('#google-signin-btn');
  googleBtn.addEventListener('click', async () => {
    const mockEmail = prompt("Enter your Google Account email for GIS login:", "student@gmail.com");
    if (!mockEmail) return;

    try {
      await API.googleSync({
        email: mockEmail,
        google_account_id: `g_${Date.now()}`,
        full_name: mockEmail.split('@')[0]
      });
      window.location.hash = '#/dashboard';
    } catch (err) {
      alert('Google Sign-In failed: ' + err.message);
    }
  });

  return container;
}

export function renderRegisterView() {
  const container = document.createElement('div');
  container.className = 'container';
  container.style.padding = '50px 16px';
  container.style.maxWidth = '540px';

  container.innerHTML = `
    <div class="card">
      <div style="text-align: center; margin-bottom: 24px;">
        <span class="badge badge-accent">Free Student Registration</span>
        <h2 style="font-size: 1.8rem; font-weight: 800; margin-top: 8px;">Create Student Account</h2>
        <p style="color: var(--text-muted); font-size: 0.9rem;">Join 1 Lakh+ students building real-world skills</p>
      </div>

      <form id="register-form">
        <div class="form-group">
          <label class="form-label">Full Name *</label>
          <input type="text" id="reg-name" class="form-control" placeholder="John Doe" required/>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div class="form-group">
            <label class="form-label">Email Address *</label>
            <input type="email" id="reg-email" class="form-control" placeholder="john@college.edu" required/>
          </div>
          <div class="form-group">
            <label class="form-label">Mobile Number</label>
            <input type="tel" id="reg-phone" class="form-control" placeholder="+91 9876543210"/>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div class="form-group">
            <label class="form-label">College / University</label>
            <input type="text" id="reg-college" class="form-control" placeholder="IIT Bombay / Delhi Univ"/>
          </div>
          <div class="form-group">
            <label class="form-label">Degree / Department</label>
            <input type="text" id="reg-department" class="form-control" placeholder="B.Tech Computer Science"/>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Password *</label>
          <input type="password" id="reg-password" class="form-control" placeholder="At least 6 characters" required/>
        </div>

        <div class="form-group" style="font-size: 0.85rem;">
          <label style="display: flex; gap: 8px; align-items: center; cursor: pointer;">
            <input type="checkbox" id="reg-terms" required/>
            I accept the Terms of Service & Privacy Policy
          </label>
        </div>

        <div id="reg-error" style="color: var(--danger); font-size: 0.85rem; margin-bottom: 16px; display: none;"></div>

        <button type="submit" class="btn btn-primary btn-lg btn-block" id="reg-btn">Create Free Account</button>
      </form>

      <div style="margin-top: 20px; text-align: center; font-size: 0.9rem; color: var(--text-muted);">
        Already have an account? <a href="#/login" style="font-weight: 600;">Sign In</a>
      </div>
    </div>
  `;

  const form = container.querySelector('#register-form');
  const errorDiv = container.querySelector('#reg-error');
  const submitBtn = container.querySelector('#reg-btn');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorDiv.style.display = 'none';
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating Account...';

    const full_name = container.querySelector('#reg-name').value;
    const email = container.querySelector('#reg-email').value;
    const phone = container.querySelector('#reg-phone').value;
    const college = container.querySelector('#reg-college').value;
    const department = container.querySelector('#reg-department').value;
    const password = container.querySelector('#reg-password').value;
    const terms_accepted = container.querySelector('#reg-terms').checked;

    try {
      await API.register({
        full_name, email, phone, college, department, password, terms_accepted
      });
      window.location.hash = '#/dashboard';
    } catch (err) {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Create Free Account';
      errorDiv.textContent = err.message || 'Registration failed.';
      errorDiv.style.display = 'block';
    }
  });

  return container;
}
