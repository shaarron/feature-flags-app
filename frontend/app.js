const list = document.getElementById('featureList');
const searchBox = document.getElementById('searchBox');

// Theme toggle functionality
const themeToggleBtn = document.getElementById('themeToggleBtn');
const body = document.body;
const sunIcon = document.getElementById('sunIcon');
const moonIcon = document.getElementById('moonIcon');

// Check for saved theme preference or default to dark
const savedTheme = localStorage.getItem('theme') || 'dark';
body.classList.toggle('light', savedTheme === 'light');
updateThemeUI();

themeToggleBtn.addEventListener('click', () => {
  body.classList.toggle('light');
  const currentTheme = body.classList.contains('light') ? 'light' : 'dark';
  localStorage.setItem('theme', currentTheme);
  updateThemeUI();
});

function updateThemeUI() {
  const isLight = body.classList.contains('light');
  sunIcon.style.opacity = isLight ? '1' : '0.5';
  moonIcon.style.opacity = isLight ? '0.5' : '1';
  
  // Update toggle switch state
  const toggleSwitch = themeToggleBtn.querySelector('.toggle-ui');
  toggleSwitch.classList.toggle('active', isLight);
}

// Environment tabs functionality
const envTabs = document.querySelectorAll('.env-tabs .tab');
const currentEnvDisplay = document.getElementById('currentEnv');
let currentEnv = 'staging'; // Default environment

function updateEnvironmentDisplay() {
  const envName = currentEnv.charAt(0).toUpperCase() + currentEnv.slice(1);
  currentEnvDisplay.textContent = `(${envName})`;
}

envTabs.forEach(tab => {
  tab.addEventListener('click', () => {
    // Remove active class from all tabs
    envTabs.forEach(t => t.classList.remove('active'));
    // Add active class to clicked tab
    tab.classList.add('active');
    
    // Update current environment
    currentEnv = tab.textContent.toLowerCase();
    
    // Update environment display
    updateEnvironmentDisplay();
    
    // Reload flags for the new environment
    loadFlags();
  });
});

// Initialize environment display
updateEnvironmentDisplay();

function featureCard(flag) {
  const el = document.createElement('article');
  el.className = 'feature';
  el.dataset.id = flag._id;

  el.innerHTML = `
    <div class="meta">
      <div class="title">${flag.name}</div>
      <p class="desc">${flag.description || ''}</p>
      <small style="color: var(--muted);">Environment: ${currentEnv}</small>
    </div>
    <div style="display: flex; align-items: center;">
      <label class="switch" aria-label="Toggle ${flag.name}">
        <input type="checkbox" ${flag.enabled ? 'checked' : ''}/>
        <span class="slider"></span>
      </label>
      <button class="delete-btn" aria-label="Delete ${flag.name}" title="Delete feature flag">
        <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
        </svg>
      </button>
    </div>
  `;

  // Gray-out off state via CSS and keep hover cues:
  // .feature:not(:has(input:checked)) { opacity: .5 }

  const checkbox = el.querySelector('input[type="checkbox"]');
  checkbox.addEventListener('change', async () => {
    // POST /flags/:id/toggle with environment
    try {
      const res = await fetch(`/flags/${flag._id}/toggle`, { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ environment: currentEnv })
      });
      if (!res.ok) throw new Error('Toggle failed');
      const updated = await res.json();
      // sync DOM in case server logic flips it back/forward
      checkbox.checked = !!updated.enabled;
    } catch (e) {
      // revert UI on error
      checkbox.checked = !checkbox.checked;
      alert('Failed to toggle flag.');
    }
  });

  // Delete functionality
  const deleteBtn = el.querySelector('.delete-btn');
  deleteBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    
    if (!confirm(`Are you sure you want to delete "${flag.name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      const res = await fetch(`/flags/${flag._id}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (!res.ok) throw new Error('Delete failed');
      
      // Remove the card from the DOM
      el.remove();
    } catch (error) {
      console.error('Error deleting flag:', error);
      alert('Failed to delete feature flag.');
    }
  });

  return el;
}

async function loadFlags() {
  list.innerHTML = '';
  try {
    const res = await fetch(`/flags?environment=${currentEnv}`);
    if (!res.ok) throw new Error('Failed to fetch flags');
    const flags = await res.json();
    flags.forEach(f => list.appendChild(featureCard(f)));
  } catch (error) {
    console.error('Error loading flags:', error);
    list.innerHTML = '<p style="color: var(--muted);">Failed to load feature flags</p>';
  }
}

searchBox.addEventListener('input', () => {
  const q = searchBox.value.toLowerCase();
  list.querySelectorAll('.feature').forEach(card => {
    const text = card.innerText.toLowerCase();
    card.style.display = text.includes(q) ? 'flex' : 'none';
  });
});

window.addEventListener('DOMContentLoaded', loadFlags);

