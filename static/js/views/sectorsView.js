import { API } from '../api.js';

export async function renderSectorsView() {
  const container = document.createElement('div');
  container.className = 'container';
  container.style.padding = '40px 16px';

  let sectors = [];
  try {
    const res = await API.getSectors();
    sectors = res.sectors || [];
  } catch (e) {
    console.error(e);
  }

  container.innerHTML = `
    <div style="margin-bottom: 30px; text-align: center;">
      <span class="badge badge-primary">Domains</span>
      <h1 style="font-size: 2.2rem; font-weight: 800; margin-top: 8px;">Explore Academic Sectors</h1>
      <p style="color: var(--text-muted);">Choose your discipline to view specialized 4-week virtual internships</p>
    </div>

    <div class="grid grid-cols-3">
      ${sectors.map(sec => `
        <a href="#/sector/${sec.slug}" class="card card-hover" style="text-decoration: none; display: flex; flex-direction: column; justify-content: space-between;">
          <div>
            <div style="font-size: 3rem; margin-bottom: 12px;">${sec.icon_url || '💼'}</div>
            <h3 style="font-size: 1.25rem; font-weight: 700; color: var(--secondary); margin-bottom: 8px;">${sec.name}</h3>
            <p style="font-size: 0.9rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 16px;">${sec.description || ''}</p>
          </div>
          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-color); padding-top: 12px;">
            <span style="font-size: 0.85rem; font-weight: 600; color: var(--primary);">${sec.internship_count || 0} Programs</span>
            <span class="btn btn-outline btn-sm">Explore Track &rarr;</span>
          </div>
        </a>
      `).join('')}
    </div>
  `;

  return container;
}
