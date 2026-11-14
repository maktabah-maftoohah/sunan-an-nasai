/**
 * Maktabah Maftoohah Sunan an-Nasa'i - Reader Application
 * Zero-Build Vanilla ES6 Architecture & Offline PWA
 */

import { analytics } from './analytics.js';

class NasaiReader {
  constructor() {
    this.currentLang = 'ms'; // Default Nusantara Malay
    this.currentBook = 1;
    this.books = [];
    this.hadiths = [];
    this.searchQuery = '';
    this.arabicFontSize = 1.65; // in rem

    this.contentView = document.getElementById('contentView');
    this.bookSelector = document.getElementById('bookSelector');
    this.hadithSearch = document.getElementById('hadithSearch');
    this.searchClear = document.getElementById('searchClear');
    this.jumpInput = document.getElementById('jumpInput');
    this.jumpBtn = document.getElementById('jumpBtn');
    this.langToggle = document.getElementById('langToggle');
    this.themeToggle = document.getElementById('themeToggle');
    this.fontInc = document.getElementById('fontInc');
    this.fontDec = document.getElementById('fontDec');
    this.toastMsg = document.getElementById('toastMsg');
  }

  async init() {
    analytics.init();
    this.registerServiceWorker();

    // Check saved theme
    const savedTheme = localStorage.getItem('maktabah_theme') || 'light';
    document.body.setAttribute('data-theme', savedTheme);
    if (this.themeToggle) {
      this.themeToggle.textContent = savedTheme === 'dark' ? '☀️' : '🌙';
    }

    // Check URL search params e.g. ?lang=en or ?lang=ms
    if (window.location.search) {
      const sp = new URLSearchParams(window.location.search);
      const urlLang = sp.get('lang');
      if (urlLang === 'en' || urlLang === 'ms') {
        this.currentLang = urlLang;
      }
    }
    if (this.langToggle) {
      this.langToggle.textContent = this.currentLang === 'ms' ? 'MY' : 'EN';
    }

    this.setupEventListeners();
    await this.loadBooks();
    this.populateBookSelector();
    await this.handleRouting();

    window.addEventListener('hashchange', () => this.handleRouting());
    window.addEventListener('popstate', () => this.handleRouting());
  }

  parseRoute() {
    // 1. Check pathname e.g. /sunan-an-nasai/42 or /42
    const pathname = window.location.pathname;
    let sub = pathname;
    if (sub.startsWith('/sunan-an-nasai')) {
      sub = sub.slice('/sunan-an-nasai'.length);
    }
    sub = sub.replace(/^\/+|\/+$/g, '');
    if (sub && sub !== 'index.html' && sub !== '404.html') {
      const pathMatch = sub.match(/^(?:hadith\/|h\/)?(\d+(?:\.\d+)?)$/i);
      if (pathMatch) {
        return { type: 'hadith', number: parseFloat(pathMatch[1]) };
      }
    }

    // 2. Check hash e.g. #hadith/42, #42, #nasai:42, #book/2
    const hash = window.location.hash.slice(1);
    if (hash) {
      const hadithHash = hash.match(/^(?:hadith\/|h\/|nasai:)?(\d+(?:\.\d+)?)$/i);
      if (hadithHash) {
        return { type: 'hadith', number: parseFloat(hadithHash[1]) };
      }
      const bookHash = hash.match(/^book\/(\d+)(?:\/(\d+))?$/i);
      if (bookHash) {
        return { type: 'book', book: parseInt(bookHash[1], 10), inBook: bookHash[2] ? parseInt(bookHash[2], 10) : null };
      }
    }

    // 3. Check query param e.g. ?hadith=42, ?h=42
    if (window.location.search) {
      const sp = new URLSearchParams(window.location.search);
      const h = sp.get('hadith') || sp.get('h');
      if (h) {
        return { type: 'hadith', number: parseFloat(h) };
      }
      const b = sp.get('book') || sp.get('b');
      if (b) {
        return { type: 'book', book: parseInt(b, 10) };
      }
    }

    return null;
  }

  async handleRouting() {
    const route = this.parseRoute();
    if (route && route.type === 'hadith') {
      const targetHadith = route.number;
      const targetBook = this.books.find(b => targetHadith >= b.hadith_start && targetHadith <= b.hadith_end) || this.books[0];
      const bookNum = targetBook ? targetBook.book_number : 1;
      this.currentBook = bookNum;
      if (this.bookSelector) this.bookSelector.value = String(bookNum);
      await this.loadHadiths(bookNum);
      this.scrollToHadith(targetHadith);
    } else if (route && route.type === 'book') {
      this.currentBook = route.book;
      if (this.bookSelector) this.bookSelector.value = String(route.book);
      await this.loadHadiths(route.book);
    } else {
      if (this.bookSelector) this.bookSelector.value = String(this.currentBook);
      await this.loadHadiths(this.currentBook);
    }
  }

  scrollToHadith(hadithNum) {
    const normalized = Number.isInteger(hadithNum) ? hadithNum : hadithNum;
    setTimeout(() => {
      const el = document.getElementById(`hadith-${normalized}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.classList.add('highlighted');
        setTimeout(() => el.classList.remove('highlighted'), 2800);
      }
    }, 200);

    const bookObj = this.books.find(b => b.book_number === this.currentBook);
    const bookTitle = bookObj ? (this.currentLang === 'ms' ? bookObj.title_ms : bookObj.title_en) : '';
    document.title = `Sunan an-Nasa'i #${hadithNum} (${bookTitle}) — Maktabah Maftoohah`;

    analytics.trackHadithView(hadithNum, this.currentBook, bookTitle);
  }

  registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('./sw.js').then(
          (reg) => console.log('Nasai PWA ServiceWorker registered:', reg.scope),
          (err) => console.warn('Nasai PWA ServiceWorker registration failed:', err)
        );
      });
    }
  }

  setupEventListeners() {
    // Theme Toggle
    if (this.themeToggle) {
      this.themeToggle.addEventListener('click', () => {
        const isDark = document.body.getAttribute('data-theme') === 'dark';
        const newTheme = isDark ? 'light' : 'dark';
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('maktabah_theme', newTheme);
        this.themeToggle.textContent = newTheme === 'dark' ? '☀️' : '🌙';
      });
    }

    // Language Toggle
    if (this.langToggle) {
      this.langToggle.addEventListener('click', () => {
        this.currentLang = this.currentLang === 'ms' ? 'en' : 'ms';
        this.langToggle.textContent = this.currentLang === 'ms' ? 'MY' : 'EN';
        this.populateBookSelector();
        this.updateHeroText();
        this.render();
      });
    }

    // Book Selector Change
    if (this.bookSelector) {
      this.bookSelector.addEventListener('change', (e) => {
        this.currentBook = parseInt(e.target.value, 10);
        window.location.hash = `#book/${this.currentBook}`;
        this.loadHadiths(this.currentBook);
      });
    }

    // Search Input
    if (this.hadithSearch) {
      this.hadithSearch.addEventListener('input', (e) => {
        this.searchQuery = e.target.value;
        if (this.searchClear) {
          this.searchClear.style.display = this.searchQuery ? 'block' : 'none';
        }
        this.renderHadithList();
      });
    }

    if (this.searchClear) {
      this.searchClear.addEventListener('click', () => {
        this.hadithSearch.value = '';
        this.searchQuery = '';
        this.searchClear.style.display = 'none';
        this.renderHadithList();
      });
    }

    // Hadith Number Jump
    const handleJump = () => {
      const val = parseFloat(this.jumpInput.value);
      if (isNaN(val) || val < 1 || val > 5758) {
        this.showToast(this.currentLang === 'ms' ? 'Sila masukkan nombor hadis antara 1 dan 5758.' : 'Please enter a hadith number between 1 and 5758.');
        return;
      }
      window.location.hash = `#hadith/${val}`;
      this.jumpInput.value = '';
    };

    if (this.jumpBtn) {
      this.jumpBtn.addEventListener('click', handleJump);
    }
    if (this.jumpInput) {
      this.jumpInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleJump();
      });
    }

    // Font Controls
    if (this.fontInc) {
      this.fontInc.addEventListener('click', () => {
        if (this.arabicFontSize < 2.5) {
          this.arabicFontSize += 0.15;
          document.querySelectorAll('.hadith-arabic').forEach(el => {
            el.style.fontSize = `${this.arabicFontSize}rem`;
          });
        }
      });
    }
    if (this.fontDec) {
      this.fontDec.addEventListener('click', () => {
        if (this.arabicFontSize > 1.2) {
          this.arabicFontSize -= 0.15;
          document.querySelectorAll('.hadith-arabic').forEach(el => {
            el.style.fontSize = `${this.arabicFontSize}rem`;
          });
        }
      });
    }

    // Document Modal Controls
    const docsToggle = document.getElementById('docsToggle');
    const docsModal = document.getElementById('docsModal');
    const closeDocsModal = document.getElementById('closeDocsModal');

    if (docsToggle && docsModal) {
      docsToggle.addEventListener('click', () => docsModal.showModal());
    }
    if (closeDocsModal && docsModal) {
      closeDocsModal.addEventListener('click', () => docsModal.close());
      docsModal.addEventListener('click', (e) => {
        if (e.target === docsModal) docsModal.close();
      });
    }

    // Global Hadith Action Delegation (Copy / Share)
    document.addEventListener('click', async (e) => {
      const btn = e.target.closest('.btn-action');
      if (!btn) return;

      const action = btn.getAttribute('data-action');
      const card = btn.closest('.hadith-card');
      if (!card) return;

      const num = card.getAttribute('data-hadith-num');
      const inBook = card.getAttribute('data-in-book');
      const arText = card.querySelector('.hadith-arabic')?.textContent?.trim() || '';
      const transText = card.querySelector('.hadith-translation')?.textContent?.trim() || '';
      const permalink = `https://maktabah-maftoohah.github.io/sunan-an-nasai/${num}`;

      if (action === 'copy-ar') {
        await this.copyText(arText, this.currentLang === 'ms' ? 'Matan Arab berjaya disalin!' : 'Arabic text copied!');
      } else if (action === 'copy-trans') {
        await this.copyText(transText, this.currentLang === 'ms' ? 'Terjemahan berjaya disalin!' : 'Translation copied!');
      } else if (action === 'copy-full') {
        const fullText = `[Sunan an-Nasa'i #${num} (Kitab: ${inBook})]\n\n${arText}\n\nTerjemahan:\n${transText}\n\nPautan: ${permalink}`;
        await this.copyText(fullText, this.currentLang === 'ms' ? 'Hadis lengkap berjaya disalin!' : 'Full hadith text copied!');
      } else if (action === 'share') {
        if (navigator.share) {
          try {
            await navigator.share({
              title: `Sunan an-Nasa'i #${num}`,
              text: `${arText.slice(0, 120)}...\n${transText.slice(0, 150)}...`,
              url: permalink
            });
            analytics.trackShare(num, 'web_share');
          } catch {
            // User cancelled or unsupported
          }
        } else {
          await this.copyText(permalink, this.currentLang === 'ms' ? 'Pautan hadis berjaya disalin!' : 'Hadith link copied!');
          analytics.trackShare(num, 'copy_link');
        }
      }
    });
  }

  async copyText(text, successMsg) {
    try {
      await navigator.clipboard.writeText(text);
      this.showToast(successMsg);
    } catch {
      prompt('Salin teks:', text);
    }
  }

  showToast(message) {
    if (!this.toastMsg) return;
    this.toastMsg.textContent = message;
    this.toastMsg.classList.add('show');
    setTimeout(() => {
      this.toastMsg.classList.remove('show');
    }, 2500);
  }

  updateHeroText() {
    const heroTitle = document.getElementById('heroTitle');
    const heroDesc = document.getElementById('heroDesc');
    if (this.currentLang === 'ms') {
      if (heroTitle) heroTitle.textContent = "Sunan an-Nasa'i (Al-Mujtaba min as-Sunan)";
      if (heroDesc) heroDesc.textContent = "Imam Ahmad ibn Shu'ayb an-Nasa'i (214–303 H) • 51 Kitab • 5,765 Hadis • Teks Autentik & Takhrij Ulama";
      if (this.hadithSearch) this.hadithSearch.placeholder = "Cari hadis (nombor, matan Arab, atau terjemahan)...";
    } else {
      if (heroTitle) heroTitle.textContent = "Sunan an-Nasa'i (The Abridged Collection)";
      if (heroDesc) heroDesc.textContent = "Imam Ahmad ibn Shu'ayb an-Nasa'i (214–303 AH) • 51 Books • 5,765 Hadiths • Authentic Text & Critical Gradings";
      if (this.hadithSearch) this.hadithSearch.placeholder = "Search hadith (number, Arabic text, or translation)...";
    }
  }

  async loadBooks() {
    try {
      const res = await fetch('./data/books.json');
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      this.books = await res.json();
    } catch (e) {
      console.error('Failed to load books catalogue:', e);
      this.books = [];
    }
  }

  populateBookSelector() {
    if (!this.bookSelector || this.books.length === 0) return;
    this.bookSelector.innerHTML = this.books.map(b => {
      const title = this.currentLang === 'ms' ? b.title_ms : b.title_en;
      return `<option value="${b.book_number}">
        ${b.book_number}. ${title} (${b.title_ar}) [${b.hadith_count} Hadis]
      </option>`;
    }).join('');
    this.bookSelector.value = String(this.currentBook);
  }

  async loadHadiths(bookNumber) {
    this.contentView.innerHTML = '<p class="loading-state">Memuatkan hadis Sunan an-Nasa\'i...</p>';
    const padded = String(bookNumber).padStart(2, '0');
    try {
      const res = await fetch(`./data/hadiths/${padded}.json`);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      this.hadiths = await res.json();
      this.searchQuery = '';
      if (this.hadithSearch) this.hadithSearch.value = '';
      if (this.searchClear) this.searchClear.style.display = 'none';
      this.render();
    } catch (e) {
      console.warn(`Book ${bookNumber} load error:`, e);
      this.hadiths = [];
      this.contentView.innerHTML = `
        <div class="hadith-card" style="text-align: center; padding: 3rem 1rem;">
          <p style="color: var(--text-muted);">${this.currentLang === 'ms' ? 'Ralat memuatkan data hadis.' : 'Error loading hadith data.'}</p>
        </div>
      `;
    }
  }

  getFilteredHadiths() {
    if (!this.searchQuery.trim()) {
      return this.hadiths;
    }
    const q = this.searchQuery.toLowerCase().trim();
    return this.hadiths.filter(h => {
      const numMatch = String(h.hadith_number).includes(q) || String(h.in_book_number).includes(q);
      const arMatch = (h.arabic || '').includes(q);
      const msMatch = (h.translations?.ms || '').toLowerCase().includes(q);
      const enMatch = (h.translations?.en || '').toLowerCase().includes(q);
      return numMatch || arMatch || msMatch || enMatch;
    });
  }

  render() {
    const currentBookObj = this.books.find(b => b.book_number === this.currentBook) || {};
    const bookTitle = this.currentLang === 'ms' 
      ? (currentBookObj.title_ms || currentBookObj.title_ar) 
      : (currentBookObj.title_en || currentBookObj.title_ar);
    const bookTitleAr = currentBookObj.title_ar || '';

    const headerHtml = `
      <div class="book-header-banner">
        <h2 class="book-header-title">Kitab ${this.currentBook}: ${bookTitle}</h2>
        <div class="book-header-ar">${bookTitleAr}</div>
        <div class="book-header-stats">
          ${this.hadiths.length} ${this.currentLang === 'ms' ? 'Hadis' : 'Hadiths'} (No. ${currentBookObj.hadith_start} – ${currentBookObj.hadith_end})
        </div>
      </div>
    `;

    const listHtml = `<div id="hadithsContainer">${this.buildHadithListHtml()}</div>`;
    this.contentView.innerHTML = headerHtml + listHtml;

    // Apply font size
    document.querySelectorAll('.hadith-arabic').forEach(el => {
      el.style.fontSize = `${this.arabicFontSize}rem`;
    });
  }

  renderHadithList() {
    const container = document.getElementById('hadithsContainer');
    if (container) {
      container.innerHTML = this.buildHadithListHtml();
      document.querySelectorAll('.hadith-arabic').forEach(el => {
        el.style.fontSize = `${this.arabicFontSize}rem`;
      });
    }
  }

  buildHadithListHtml() {
    const filtered = this.getFilteredHadiths();
    if (filtered.length === 0) {
      return `
        <div class="hadith-card" style="text-align: center; padding: 2.5rem 1rem;">
          <p style="color: var(--text-muted); font-size: 1.05rem;">
            ${this.currentLang === 'ms' ? 'Tiada hadis sepadan dengan carian.' : 'No hadiths found matching your query.'}
          </p>
        </div>
      `;
    }
    return filtered.map(h => this.renderHadithCard(h)).join('');
  }

  renderHadithCard(hadith) {
    const hNum = hadith.hadith_number;
    const inBook = hadith.in_book_number || '';
    const arText = hadith.arabic || '';
    const trans = hadith.translations?.[this.currentLang] || hadith.translations?.ms || hadith.translations?.en || '';
    const altTrans = this.currentLang === 'ms' ? hadith.translations?.en : hadith.translations?.ms;

    // Gradings
    const gradingsHtml = (hadith.gradings || []).map(g => {
      const gLower = (g.grade || '').toLowerCase();
      let cls = 'sahih';
      if (gLower.includes('hasan')) cls = 'hasan';
      else if (gLower.includes("da'if") || gLower.includes('daif') || gLower.includes('munkar')) cls = 'daif';

      return `<span class="badge-grade ${cls}" title="${g.notes || ''}">
        ${g.scholar}: ${g.grade} (${g.grade_ar || ''})
      </span>`;
    }).join('');

    // Cross-references to Al-Quran
    const crossRefsHtml = (hadith.cross_references || []).map(cr => {
      if (cr.type === 'quran') {
        const url = cr.url || `https://maktabah-maftoohah.github.io/al-quran/${cr.surah}/${cr.ayah}`;
        const sName = cr.surah_name || `Surah ${cr.surah}`;
        return `<a href="${url}" class="crossref-pill" target="_blank" rel="noopener">
          📖 Rujuk ${sName} (${cr.surah}:${cr.ayah}) ↗
        </a>`;
      }
      return '';
    }).join('');

    return `
      <article class="hadith-card" id="hadith-${hNum}" data-hadith-num="${hNum}" data-in-book="${inBook}">
        <div class="hadith-meta-row">
          <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
            <span class="hadith-badge-num">Hadis #${hNum}</span>
            <span style="font-size: 0.85rem; color: var(--text-muted); font-weight: 600;">
              ${this.currentLang === 'ms' ? 'Nombor Kitab' : 'In-Book No.'}: ${inBook}
            </span>
          </div>
          <div class="hadith-gradings">
            ${gradingsHtml}
          </div>
        </div>

        <div class="hadith-arabic">
          ${arText}
        </div>

        <div class="hadith-translation">
          <span class="trans-tag">${this.currentLang === 'ms' ? 'Terjemahan Melayu' : 'English Translation'}:</span>
          ${trans}
        </div>

        ${altTrans ? `
          <div class="hadith-translation-en">
            <span class="trans-tag">${this.currentLang === 'ms' ? 'Darussalam English' : 'Terjemahan Melayu'}:</span>
            ${altTrans}
          </div>
        ` : ''}

        ${crossRefsHtml ? `<div class="hadith-crossrefs">${crossRefsHtml}</div>` : ''}

        <div class="hadith-actions">
          <button class="btn-action" data-action="copy-ar" title="Salin Teks Arab">📋 Salin Arab</button>
          <button class="btn-action" data-action="copy-trans" title="Salin Terjemahan">📝 Salin Terjemahan</button>
          <button class="btn-action" data-action="copy-full" title="Salin Hadis Penuh & Rujukan">📄 Salin Lengkap</button>
          <button class="btn-action" data-action="share" title="Kongsi Hadis">🔗 Kongsi</button>
        </div>
      </article>
    `;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const reader = new NasaiReader();
  reader.init();
});
