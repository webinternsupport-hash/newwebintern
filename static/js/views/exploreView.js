import { API } from '../api.js';

export async function renderExploreView() {
  const container = document.createElement('div');
  container.className = 'container';
  container.style.padding = '40px 16px';

  let currentSector = '';
  let currentSearch = '';
  let debounceTimer = null;

  async function loadData() {
    try {
      const sectorsRes = await API.getSectors();
      const sectors = sectorsRes.sectors || [];

      const params = {};
      if (currentSector) params.sector = currentSector;
      if (currentSearch) params.q = currentSearch;

      const internshipsRes = await API.getInternships(params);
      const internships = internshipsRes.internships || [];

      renderUI(sectors, internships);
    } catch (e) {
      console.error('Explore view error:', e);
    }
  }

  function renderUI(sectors, internships) {
    container.innerHTML = `
      <div style="margin-bottom: 30px;">
        <span class="badge badge-primary">Catalog</span>
        <h1 style="font-size: 2.2rem; font-weight: 800; margin-top: 8px;">Explore Virtual Internships</h1>
        <p style="color: var(--text-muted);">Choose from 20+ sector-based 4-week virtual programs with industry capstones</p>
      </div>

      <!-- Controls: Search & Sector Filters -->
      <div style="background-color: white; padding: 20px; border-radius: var(--radius-lg); border: 1px solid var(--border-color); margin-bottom: 30px;">
        <div style="margin-bottom: 16px;">
          <input type="text" id="search-input" class="form-control" placeholder="🔍 Search programs by keyword, title, or skills..." value="${currentSearch}" style="font-size: 1rem; padding: 12px 16px;"/>
        </div>

        <div style="display: flex; gap: 8px; flex-wrap: wrap;" id="sector-filters">
          <button class="btn btn-sm ${currentSector === '' ? 'btn-primary' : 'btn-outline'}" data-sector="">All Sectors</button>
          ${sectors.map(sec => `
            <button class="btn btn-sm ${currentSector === sec.slug ? 'btn-primary' : 'btn-outline'}" data-sector="${sec.slug}">
              ${sec.icon_url || ''} ${sec.name}
            </button>
          `).join('')}
        </div>
      </div>

      <!-- Programs Grid -->
      ${internships.length === 0 ? `
        <div style="text-align: center; padding: 60px 0; background-color: white; border-radius: var(--radius-lg); border: 1px solid var(--border-color);">
          <div style="font-size: 3rem; margin-bottom: 12px;">🔍</div>
          <h3>No internships found</h3>
          <p style="color: var(--text-muted);">Try adjusting your search query or domain filter</p>
        </div>
      ` : `
        <div class="grid grid-cols-3">
          ${internships.map(intern => `
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
                <div style="margin-bottom: 12px; font-size: 0.85rem; color: var(--text-muted);">
                  <strong>Domain:</strong> ${intern.sector_name || 'Technology'}<br/>
                  <strong>Skills:</strong> ${intern.skills_tools || 'Python, Analytics'}
                </div>
                <a href="#/internship/${intern.slug}" class="btn btn-primary btn-block">View Program Details</a>
              </div>
            </div>
          `).join('')}
        </div>
      `}
    `;

    // Event listeners
    const searchInput = container.querySelector('#search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        currentSearch = e.target.value;
        debounceTimer = setTimeout(() => {
          loadData();
        }, 300); // 300ms debounce
      });
    }

    const filterBtns = container.querySelectorAll('#sector-filters button');
    filterBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        currentSector = btn.getAttribute('data-sector');
        loadData();
      });
    });
  }

  await loadData();
  return container;
}
