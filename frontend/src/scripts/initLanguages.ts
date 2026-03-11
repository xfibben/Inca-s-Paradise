/**
 * Initialize dynamic languages on page load
 * This script runs on the client to fetch languages from the backend
 * and update the language switcher if needed
 */

import { fetchLanguagesFromBackend } from '../i18n/index';

// Run when the page is fully loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeLanguages);
} else {
  initializeLanguages();
}

async function initializeLanguages() {
  try {
    // Fetch languages from backend
    const languages = await fetchLanguagesFromBackend();
    
    // Log for debugging (remove in production)
    console.log('Languages loaded from backend:', languages);
    
    // Store in window for client-side access
    (window as any).__availableLanguages = languages;
    
    // Update the language switcher if it exists
    updateLanguageSwitcher(languages);
  } catch (error) {
    console.warn('Failed to initialize languages:', error);
  }
}

/**
 * Update the language switcher dropdown with fresh languages from backend
 */
function updateLanguageSwitcher(languages: Record<string, string>) {
  const dropdown = document.getElementById('lang-dropdown');
  if (!dropdown) {
    console.warn('Language switcher dropdown not found');
    return;
  }

  // Get current language from the button
  const button = document.getElementById('lang-button');
  if (!button) return;

  const currentLangSpan = button.querySelector('span:nth-child(2)');
  if (!currentLangSpan) return;

  const currentLangName = currentLangSpan.textContent;

  // Find current language code
  let currentLangCode = 'es';
  for (const [code, name] of Object.entries(languages)) {
    if (name === currentLangName) {
      currentLangCode = code;
      break;
    }
  }

  // Flag emoji mapping
  const flagMap: Record<string, string> = {
    es: '🇪🇸',
    en: '🇺🇸',
    pt: '🇧🇷',
    'es-PE': '🇵🇪',
    'en-US': '🇺🇸',
    'pt-BR': '🇧🇷',
  };

  // Rebuild dropdown with new languages
  dropdown.innerHTML = '';
  
  for (const [code, name] of Object.entries(languages)) {
    if (code === currentLangCode) continue; // Skip current language

    const link = document.createElement('a');
    link.href = `/${code}/`;
    link.className = 'flex items-center space-x-3 px-4 py-3 hover:bg-white/10 transition text-white text-sm';
    
    const flag = flagMap[code] || '🌐';
    link.innerHTML = `<span>${flag}</span><span>${name}</span>`;
    
    link.addEventListener('click', () => {
      const langDropdown = document.getElementById('lang-dropdown');
      const langArrow = document.getElementById('lang-arrow');
      langDropdown?.classList.add('hidden');
      langArrow?.classList.remove('rotate-180');
    });

    dropdown.appendChild(link);
  }

  console.log('Language switcher updated with', Object.keys(languages).length, 'languages');
}
