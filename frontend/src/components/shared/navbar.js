// navbar.js — Toda la lógica interactiva del Navbar
// Las traducciones se inyectan desde Navbar.astro via window.__navbarT

function toSlug(name) {
  return name.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9\s-]/g, '').trim().replace(/\s+/g, '-');
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function normalizeRows(value) {
  return Array.isArray(value?.data) ? value.data : Array.isArray(value) ? value : [];
}

function sortSubcategoriasAlphabetically(rows) {
  return [...rows].sort((a, b) => {
    const left = a?.attributes || a;
    const right = b?.attributes || b;
    return String(left?.nombre ?? '').localeCompare(String(right?.nombre ?? ''), undefined, {
      sensitivity: 'base'
    });
  });
}

function sortToursAlphabetically(rows) {
  return [...rows].sort((a, b) => {
    const left = a?.attributes || a;
    const right = b?.attributes || b;
    return String(left?.title ?? left?.nombre ?? '').localeCompare(String(right?.title ?? right?.nombre ?? ''), undefined, {
      sensitivity: 'base'
    });
  });
}

function renderDestinationToursHtml(destination, currentLang) {
  if (!destination) {
    return '<p class="text-sm text-gray-400 italic">Sin tours disponibles</p>';
  }

  const subcategorias = sortSubcategoriasAlphabetically(normalizeRows(destination.subcategorias_tour));
  const toursSubcategorizados = new Set();
  subcategorias.forEach(subcategoria => {
    const sub = subcategoria.attributes || subcategoria;
    normalizeRows(sub.tours).forEach(tour => {
      const t = tour.attributes || tour;
      const clave = t.slug || t.title || t.nombre;
      if (clave) toursSubcategorizados.add(String(clave));
    });
  });
  const toursSueltos = sortToursAlphabetically(
    normalizeRows(destination.tours).filter(tour => {
      const t = tour.attributes || tour;
      const clave = t.slug || t.title || t.nombre;
      return !clave || !toursSubcategorizados.has(String(clave));
    })
  );
  let html = '';

  subcategorias.forEach(subcategoria => {
    const sub = subcategoria.attributes || subcategoria;
    const tours = sortToursAlphabetically(normalizeRows(sub.tours));
    if (!sub?.nombre || tours.length === 0) return;

    html += `<div class="break-inside-avoid pb-3 border-b border-gray-100 last:border-0">
      <p class="mb-2 text-xs font-bold uppercase tracking-[0.2em] text-gray-500">${escapeHtml(sub.nombre)}</p>
      <div class="space-y-2">
        ${tours.map(tour => {
          const t = tour.attributes || tour;
          return `<a href="/${currentLang}/tours/${escapeHtml(t.slug || toSlug(t.title))}" class="block font-semibold text-gray-800 text-sm hover:text-[#1AA093] transition">
            ${escapeHtml(t.title || t.nombre)}
          </a>`;
        }).join('')}
      </div>
    </div>`;
  });

  html += toursSueltos.map(tour => {
    const t = tour.attributes || tour;
    return `<div class="break-inside-avoid pb-3 border-b border-gray-100 last:border-0">
      <a href="/${currentLang}/tours/${escapeHtml(t.slug || toSlug(t.title))}" class="font-semibold text-gray-800 text-sm hover:text-[#1AA093] transition">
        ${escapeHtml(t.title || t.nombre)}
      </a>
    </div>`;
  }).join('');

  return html || '<p class="text-sm text-gray-400 italic">Sin tours disponibles</p>';
}

function renderTourLinksHtml(tours, currentLang, emptyLabel = 'Sin tours disponibles') {
  const rows = sortToursAlphabetically(normalizeRows(tours));
  if (!rows.length) {
    return `<p class="text-sm text-gray-400 italic">${escapeHtml(emptyLabel)}</p>`;
  }

  return rows.map(tour => {
    const t = tour.attributes || tour;
    return `<div class="break-inside-avoid pb-3 border-b border-gray-100 last:border-0">
      <a href="/${currentLang}/tours/${escapeHtml(t.slug || toSlug(t.title || t.nombre || ''))}" class="block font-semibold text-gray-800 text-sm hover:text-[#1AA093] transition">
        ${escapeHtml(t.title || t.nombre || '')}
      </a>
    </div>`;
  }).join('');
}

function renderTransportLinksHtml(transportes, currentLang, emptyLabel = 'Sin transportes disponibles') {
  const rows = sortToursAlphabetically(normalizeRows(transportes));
  if (!rows.length) {
    return `<p class="text-sm text-gray-400 italic">${escapeHtml(emptyLabel)}</p>`;
  }

  return rows.map(transporte => {
    const item = transporte.attributes || transporte;
    return `<div class="break-inside-avoid pb-3 border-b border-gray-100 last:border-0">
      <a href="/${currentLang}/transporte/${escapeHtml(item.slug || '')}" class="block font-semibold text-gray-800 text-sm hover:text-[#1AA093] transition">
        ${escapeHtml(item.nombre || item.title || '')}
      </a>
    </div>`;
  }).join('');
}

function renderDestinationListHtml(destinations, currentLang) {
  return destinations.map(dest => `
    <a
      href="/${currentLang}/destinos/${escapeHtml(dest.slug || toSlug(dest.title || dest.name || ''))}"
      class="destination-item w-full px-4 py-3 text-left text-sm font-medium text-gray-700 hover:bg-[#e0f7f5] hover:text-[#1AA093] transition border-b border-gray-100 whitespace-normal block"
      title="${escapeHtml(dest.title || dest.name || '')}"
      data-dest="${escapeHtml(dest.slug || '')}"
    >
      ${escapeHtml(dest.title || dest.name || '')}
    </a>
  `).join('');
}

function buildLanguageUrl(languageCode) {
  const currentPath = window.location.pathname;
  const pathMatch = currentPath.match(/^\/[a-z]{2}(.*)/);
  const relativePath = pathMatch ? pathMatch[1] : '/';
  return `/${languageCode}${relativePath}`;
}

const mobileDetailCache = new Map();

async function fetchMobileDetailJson(path) {
  if (mobileDetailCache.has(path)) {
    return mobileDetailCache.get(path);
  }

  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} for ${path}`);
  }

  const json = await response.json();
  mobileDetailCache.set(path, json);
  return json;
}

document.addEventListener('DOMContentLoaded', function () {
  const t = window.__navbarT;
  if (!t) return;

  const navbar = document.getElementById('navbar');
  const mobileMenuBtn = document.getElementById('mobile-menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');
  const mobileBackdrop = document.getElementById('mobile-backdrop');

  if (!navbar) return;

  // ── Scroll: cambiar fondo del navbar ──────────────────────────────────────
  // contactBtn debe declararse ANTES del bloque navbarSolid para evitar ReferenceError
  const contactBtn = document.getElementById('contact-btn');

  // Si la página no tiene hero, el navbar arranca sólido
  const navbarSolid = document.body.hasAttribute('data-navbar-solid');
  if (navbarSolid) {
    navbar.classList.remove('bg-transparent');
    navbar.classList.add('bg-white', 'shadow-md');
    document.querySelectorAll('#navbar a:not(#lang-dropdown a), #navbar button:not(#lang-dropdown button)').forEach(el => {
      el.classList.remove('text-white', 'hover:text-gray-300');
      el.classList.add('text-gray-900', 'hover:text-gray-600');
    });
    setContactBtn(true);
  }

  function setContactBtn(scrolled) {
    if (!contactBtn) return;
    if (scrolled) {
      contactBtn.classList.remove('bg-white/10', 'hover:bg-white/20', 'border', 'border-white/30', 'text-white');
      contactBtn.classList.add('bg-white', 'hover:bg-gray-100', 'text-gray-900');
    } else {
      contactBtn.classList.remove('bg-white', 'hover:bg-gray-100', 'text-gray-900');
      contactBtn.classList.add('bg-white/10', 'hover:bg-white/20', 'border', 'border-white/30', 'text-white');
    }
  }

  function updateNavbarStyle() {
    if (!navbar) return;
    // No actualizar si hay un dropdown o el menú móvil abierto
    if (isAnyDropdownOpen() || navbar.classList.contains('menu-open')) return;
    // En páginas sin hero siempre sólido
    if (navbarSolid) return;

    if (window.scrollY > 50) {
      navbar.classList.remove('bg-transparent');
      navbar.classList.add('bg-white', 'shadow-md');
      document.querySelectorAll('#navbar a:not(#lang-dropdown a), #navbar button:not(#lang-dropdown button)').forEach(el => {
        el.classList.remove('text-white', 'hover:text-gray-300');
        el.classList.add('text-gray-900', 'hover:text-gray-600');
      });
      setContactBtn(true);
    } else {
      navbar.classList.remove('bg-white', 'shadow-md');
      navbar.classList.add('bg-transparent');
      document.querySelectorAll('#navbar a:not(#lang-dropdown a), #navbar button:not(#lang-dropdown button)').forEach(el => {
        el.classList.remove('text-gray-900', 'hover:text-gray-600');
        el.classList.add('text-white', 'hover:text-gray-300');
      });
      setContactBtn(false);
    }
  }

  window.addEventListener('scroll', updateNavbarStyle);

  // ── Mobile menu toggle ────────────────────────────────────────────────────
  mobileMenuBtn?.addEventListener('click', () => {
    mobileMenu?.classList.toggle('hidden');
    mobileBackdrop?.classList.toggle('hidden');
    if (!mobileMenu?.classList.contains('hidden')) {
      navbar?.classList.add('bg-white', 'shadow-md', 'menu-open');
      navbar?.classList.remove('bg-transparent');
      document.querySelectorAll('#navbar a:not(#lang-dropdown a), #navbar button:not(#lang-dropdown button)').forEach(el => {
        el.classList.remove('text-white', 'hover:text-gray-300');
        el.classList.add('text-gray-900', 'hover:text-gray-600');
      });
      setContactBtn(true);
    } else if (window.scrollY <= 50) {
      if (!navbarSolid) {
        navbar?.classList.remove('bg-white', 'shadow-md', 'menu-open');
        navbar?.classList.add('bg-transparent');
        document.querySelectorAll('#navbar a:not(#lang-dropdown a), #navbar button:not(#lang-dropdown button)').forEach(el => {
          el.classList.remove('text-gray-900', 'hover:text-gray-600');
          el.classList.add('text-white', 'hover:text-gray-300');
        });
        setContactBtn(false);
      } else {
        // En páginas de fondo sólido solo quitar menu-open, mantener estilos oscuros
        navbar?.classList.remove('menu-open');
      }
    }
  });

  mobileBackdrop?.addEventListener('click', () => {
    mobileMenu?.classList.add('hidden');
    mobileBackdrop?.classList.add('hidden');
    navbar?.classList.remove('menu-open');
  });

  // ── Helper: hover dropdown con timeout ───────────────────────────────────
  let activeDropdown = null; // Track which dropdown is open

  function isAnyDropdownOpen() {
    const allDropdowns = [
      document.getElementById('megamenu-dropdown'),
      document.getElementById('styles-dropdown'),
      document.getElementById('sustainability-dropdown'),
      document.getElementById('transport-dropdown')
    ];
    return allDropdowns.some(dd => dd && !dd.classList.contains('hidden'));
  }

  function makeDropdown(containerId, dropdownId) {
    const container = document.getElementById(containerId);
    const dropdown = document.getElementById(dropdownId);
    if (!container || !dropdown) return;

    let timeout;

    const open = () => {
      clearTimeout(timeout);
      activeDropdown = dropdownId;
      dropdown.classList.remove('hidden');
      dropdown.style.display = 'block';
      navbar.classList.add('bg-white', 'shadow-md');
      navbar.classList.remove('bg-transparent');
      document.querySelectorAll('#navbar a:not(#lang-dropdown a), #navbar button:not(#lang-dropdown button)').forEach(el => {
        el.classList.remove('text-white', 'hover:text-gray-300');
        el.classList.add('text-gray-900', 'hover:text-gray-600');
      });
    };

    const close = () => {
      timeout = setTimeout(() => {
        dropdown.classList.add('hidden');
        dropdown.style.display = 'none';
        // Only revert navbar if NO dropdowns are open
        if (!isAnyDropdownOpen() && window.scrollY <= 50) {
          navbar.classList.remove('bg-white', 'shadow-md');
          navbar.classList.add('bg-transparent');
          document.querySelectorAll('#navbar a:not(#lang-dropdown a), #navbar button:not(#lang-dropdown button)').forEach(el => {
            el.classList.remove('text-gray-900', 'hover:text-gray-600');
            el.classList.add('text-white', 'hover:text-gray-300');
          });
        }
        activeDropdown = null;
      }, 200);
    };

    container.addEventListener('mouseenter', open);
    container.addEventListener('mouseleave', close);
    dropdown.addEventListener('mouseenter', () => clearTimeout(timeout));
    dropdown.addEventListener('mouseleave', close);
  }

  makeDropdown('megamenu-container', 'megamenu-dropdown');
  makeDropdown('styles-container', 'styles-dropdown');
  makeDropdown('sustainability-container', 'sustainability-dropdown');
  makeDropdown('transport-container', 'transport-dropdown');

  // ── Destinations megamenu ─────────────────────────────────────────────────
  const scrollAmount = 100;

  document.getElementById('scroll-up')?.addEventListener('click', () => {
    document.getElementById('destinations-scroll')?.scrollBy({ top: -scrollAmount, behavior: 'smooth' });
  });
  document.getElementById('scroll-down')?.addEventListener('click', () => {
    document.getElementById('destinations-scroll')?.scrollBy({ top: scrollAmount, behavior: 'smooth' });
  });

  function updateMegamenu(destSlug) {
    const destinations = window.__navbarDestinations || [];
    const destination = destinations.find(d => d.slug === destSlug);
    if (!destination) return;

    const currentLang = window.__currentLang || 'es';
    document.getElementById('megamenu-tours').innerHTML = renderDestinationToursHtml(destination, currentLang);
  }

  function bindDestinationHover() {
    document.querySelectorAll('.destination-item').forEach(item => {
      item.addEventListener('mouseenter', () => {
        updateMegamenu(item.dataset.dest);
        document.querySelectorAll('.destination-item').forEach(i => i.classList.remove('bg-[#e0f7f5]', 'text-[#1AA093]'));
        item.classList.add('bg-[#e0f7f5]', 'text-[#1AA093]');
      });
    });
  }

  const destinationsList = window.__navbarDestinations || [];
  const destinationsScroll = document.getElementById('destinations-scroll');
  if (destinationsScroll && destinationsList.length > 0) {
    const currentLang = window.__currentLang || 'es';
    destinationsScroll.innerHTML = renderDestinationListHtml(destinationsList, currentLang);
  }
  if (destinationsList.length > 0) {
    updateMegamenu(destinationsList[0].slug);
    document.querySelector('[data-dest="' + destinationsList[0].slug + '"]')?.classList.add('bg-[#e0f7f5]', 'text-[#1AA093]');
  }
  bindDestinationHover();

  // ── Styles megamenu ───────────────────────────────────────────────────────
  function updateStylesMenuFooter(menu) {
    const menuItem = t.stylesMenu[menu];
    if (!menuItem) return;
    document.getElementById('styles-menu-footer').textContent = menuItem.description || '';
    const img = document.getElementById('styles-footer-image');
    img.src = menuItem.image
      ? (menuItem.image.startsWith('landing page images') ? '/' + menuItem.image : menuItem.image)
      : '';
  }

  document.querySelectorAll('.styles-menu-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const menu = btn.dataset.menu;
      document.querySelectorAll('.styles-menu-btn').forEach(b => {
        b.classList.remove('border-[#1AA093]', 'text-[#1AA093]');
        b.classList.add('border-transparent', 'text-gray-700');
      });
      btn.classList.remove('border-transparent', 'text-gray-700');
      btn.classList.add('border-[#1AA093]', 'text-[#1AA093]');

      document.querySelectorAll('.styles-menu-content').forEach(c => c.classList.add('hidden'));
      document.getElementById(`content-${menu}`)?.classList.remove('hidden');
      updateStylesMenuFooter(menu);
    });
  });

  updateStylesMenuFooter('travelStyles');

  // ── Sustainability megamenu ───────────────────────────────────────────────
  document.getElementById('scroll-up-sustainability')?.addEventListener('click', () => {
    document.getElementById('sustainability-scroll')?.scrollBy({ top: -scrollAmount, behavior: 'smooth' });
  });
  document.getElementById('scroll-down-sustainability')?.addEventListener('click', () => {
    document.getElementById('sustainability-scroll')?.scrollBy({ top: scrollAmount, behavior: 'smooth' });
  });

  function updateSustainabilityMenu(item) {
    if (!item) return;
    const description = item.getAttribute('data-description') || '';
    const sustImage = item.getAttribute('data-image') || '';
    const sustName = item.getAttribute('data-name') || '';
    document.getElementById('sustainability-description').innerHTML =
      `<p class="text-sm text-gray-600">${description}</p>`;

    const img = document.getElementById('sustainability-image');
    if (img && sustImage) {
      img.src = sustImage;
    }
    document.getElementById('sustainability-name').textContent = sustName;
  }

  const firstSustItem = document.querySelector('.sustainability-item');
  if (firstSustItem) {
    updateSustainabilityMenu(firstSustItem);
    firstSustItem.classList.add('bg-[#e0f7f5]', 'text-[#1AA093]');
  }

  document.querySelectorAll('.sustainability-item').forEach(item => {
    item.addEventListener('mouseenter', () => {
      updateSustainabilityMenu(item);
      document.querySelectorAll('.sustainability-item').forEach(i => i.classList.remove('bg-[#e0f7f5]', 'text-[#1AA093]'));
      item.classList.add('bg-[#e0f7f5]', 'text-[#1AA093]');
    });
  });

  // ── Mobile dropdowns ──────────────────────────────────────────────────────
  const mobileDestinationsMenu = document.getElementById('mobile-destinations-menu');
  const mobileDestinationsList = document.getElementById('mobile-destinations-list');
  const mobileDestinationsDetails = document.getElementById('mobile-destinations-details');
  const mobileStylesMenu = document.getElementById('mobile-styles-menu');
  const mobileStylesList = document.getElementById('mobile-styles-list');
  const mobileStylesDetails = document.getElementById('mobile-styles-details');
  const mobileSustainabilityMenu = document.getElementById('mobile-sustainability-menu');
  const mobileSustainabilityList = document.getElementById('mobile-sustainability-list');
  const mobileSustainabilityDetails = document.getElementById('mobile-sustainability-details');
  const mobileTransportMenu = document.getElementById('mobile-transport-menu');
  const mobileTransportList = document.getElementById('mobile-transport-list');
  const mobileTransportDetails = document.getElementById('mobile-transport-details');

  document.getElementById('mobile-destinations-btn')?.addEventListener('click', () => {
    mobileDestinationsMenu?.classList.toggle('hidden');
    mobileStylesMenu?.classList.add('hidden');
    mobileSustainabilityMenu?.classList.add('hidden');
    mobileTransportMenu?.classList.add('hidden');
  });

  document.getElementById('mobile-styles-btn')?.addEventListener('click', () => {
    mobileStylesMenu?.classList.toggle('hidden');
    mobileDestinationsMenu?.classList.add('hidden');
    mobileSustainabilityMenu?.classList.add('hidden');
    mobileTransportMenu?.classList.add('hidden');
  });

  document.getElementById('mobile-sustainability-btn')?.addEventListener('click', () => {
    mobileSustainabilityMenu?.classList.toggle('hidden');
    mobileDestinationsMenu?.classList.add('hidden');
    mobileStylesMenu?.classList.add('hidden');
    mobileTransportMenu?.classList.add('hidden');
  });

  document.getElementById('mobile-transport-btn')?.addEventListener('click', () => {
    mobileTransportMenu?.classList.toggle('hidden');
    mobileDestinationsMenu?.classList.add('hidden');
    mobileStylesMenu?.classList.add('hidden');
    mobileSustainabilityMenu?.classList.add('hidden');
  });

  // Ver todos destinos
  document.getElementById('mobile-destinations-show-all')?.addEventListener('click', () => {
    const extra = document.getElementById('mobile-destinations-extra');
    const btn = document.getElementById('mobile-destinations-show-all');
    if (extra && btn) {
      extra.classList.toggle('hidden');
      btn.textContent = extra.classList.contains('hidden') ? 'Ver todos los destinos ▼' : 'Ver menos ▲';
    }
  });

  // Detalle destino mobile
  document.querySelectorAll('.mobile-destination-item').forEach(item => {
    item.addEventListener('click', event => {
      event.preventDefault();
      const destinations = window.__navbarDestinations || [];
      const destination = destinations.find(d => d.slug === item.getAttribute('data-dest'));
      if (!destination) return;

      mobileDestinationsList?.classList.add('hidden');
      mobileDestinationsDetails?.classList.remove('hidden');
      document.getElementById('mobile-dest-name').textContent = destination.title || '';
      
      const currentLang = window.__currentLang || 'es';
      document.getElementById('mobile-dest-tours').innerHTML = renderDestinationToursHtml(destination, currentLang);
    });
  });

  document.getElementById('mobile-dest-back')?.addEventListener('click', () => {
    mobileDestinationsList?.classList.remove('hidden');
    mobileDestinationsDetails?.classList.add('hidden');
  });

  // Detalle estilos mobile
  document.querySelectorAll('.mobile-style-item').forEach(item => {
    item.addEventListener('click', async event => {
      event.preventDefault();
      const styleSlug = item.getAttribute('data-style');
      const styleName = item.getAttribute('data-name') || '';
      if (!styleSlug) return;

      mobileStylesList?.classList.add('hidden');
      mobileStylesDetails?.classList.remove('hidden');

      const styleNameEl = document.getElementById('mobile-style-name');
      if (styleNameEl) styleNameEl.textContent = styleName;

      const subitemsContainer = document.getElementById('mobile-style-subitems');
      if (!subitemsContainer) return;

      subitemsContainer.innerHTML = '<p class="text-sm text-gray-400 italic px-2 py-3">Cargando tours...</p>';

      try {
        const lang = window.__currentLang || 'es';
        const json = await fetchMobileDetailJson(`/incas/api/web/estilos-viaje/${encodeURIComponent(styleSlug)}?lang=${lang}`);
        const tours = json?.data?.tours ?? [];
        subitemsContainer.innerHTML = renderTourLinksHtml(tours, lang);
      } catch (error) {
        console.error('[Navbar] Error loading style trips:', error);
        subitemsContainer.innerHTML = '<p class="text-sm text-gray-400 italic px-2 py-3">No se pudieron cargar los tours.</p>';
      }
    });
  });

  document.getElementById('mobile-styles-back')?.addEventListener('click', () => {
    mobileStylesList?.classList.remove('hidden');
    mobileStylesDetails?.classList.add('hidden');
  });

  // Detalle transporte mobile
  document.querySelectorAll('.mobile-transport-item').forEach(item => {
    item.addEventListener('click', async event => {
      event.preventDefault();
      const transportSlug = item.getAttribute('data-transport-type');
      const transportName = item.getAttribute('data-name') || '';
      if (!transportSlug) return;

      mobileTransportList?.classList.add('hidden');
      mobileTransportDetails?.classList.remove('hidden');

      const transportNameEl = document.getElementById('mobile-transport-name');
      if (transportNameEl) transportNameEl.textContent = transportName;

      const subitemsContainer = document.getElementById('mobile-transport-subitems');
      if (!subitemsContainer) return;

      subitemsContainer.innerHTML = '<p class="text-sm text-gray-400 italic px-2 py-3">Cargando transportes...</p>';

      try {
        const lang = window.__currentLang || 'es';
        const json = await fetchMobileDetailJson(`/incas/api/web/tipo-transportes/${encodeURIComponent(transportSlug)}?lang=${lang}`);
        const transportes = json?.data?.transportes ?? [];
        subitemsContainer.innerHTML = renderTransportLinksHtml(transportes, lang);
      } catch (error) {
        console.error('[Navbar] Error loading transport types:', error);
        subitemsContainer.innerHTML = '<p class="text-sm text-gray-400 italic px-2 py-3">No se pudieron cargar los transportes.</p>';
      }
    });
  });

  document.getElementById('mobile-transport-back')?.addEventListener('click', () => {
    mobileTransportList?.classList.remove('hidden');
    mobileTransportDetails?.classList.add('hidden');
  });

  // Detalle sostenibilidad mobile
  document.querySelectorAll('.mobile-sustainability-item').forEach(item => {
    item.addEventListener('click', () => {
      mobileSustainabilityList?.classList.add('hidden');
      mobileSustainabilityDetails?.classList.remove('hidden');

      document.getElementById('mobile-sustainability-name').textContent = item.getAttribute('data-name');
      document.getElementById('mobile-sustainability-description').textContent = item.getAttribute('data-description');

      const sustDescEl = document.getElementById('mobile-sustainability-description');
      if (sustDescEl && !sustDescEl.parentElement?.querySelector('.back-btn')) {
        const backBtn = document.createElement('button');
        backBtn.className = 'w-full text-left px-0 py-2 text-[#1AA093] text-sm hover:text-[#0e8a7e] transition mt-4 border-t border-gray-300 pt-3 back-btn';
        backBtn.textContent = '← Volver';
        backBtn.addEventListener('click', () => {
          mobileSustainabilityList?.classList.remove('hidden');
          mobileSustainabilityDetails?.classList.add('hidden');
          backBtn.remove();
        });
        sustDescEl.parentElement?.appendChild(backBtn);
      }
    });
  });

  // Cerrar mobile menus al hacer click afuera
  document.addEventListener('click', e => {
    if (!e.target?.closest('#mobile-destinations-btn') && !e.target?.closest('#mobile-destinations-menu'))
      mobileDestinationsMenu?.classList.add('hidden');
    if (!e.target?.closest('#mobile-styles-btn') && !e.target?.closest('#mobile-styles-menu'))
      mobileStylesMenu?.classList.add('hidden');
    if (!e.target?.closest('#mobile-sustainability-btn') && !e.target?.closest('#mobile-sustainability-menu'))
      mobileSustainabilityMenu?.classList.add('hidden');
    if (!e.target?.closest('#mobile-transport-btn') && !e.target?.closest('#mobile-transport-menu'))
      mobileTransportMenu?.classList.add('hidden');
  });
});
