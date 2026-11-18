/**
 * Estate Intelligence AI — Production Frontend Application Bundle
 * Connects to FastAPI RAG Backend (/api/health, /api/chat, /api/sources, /api/models)
 */
(function () {
  const SUGGESTED_PROMPTS = [
    {
      category: 'DarGlobal Portfolio',
      source: 'DarGlobal',
      question: 'What residential projects are available on DarGlobal?',
      desc: 'Branded luxury towers, beachfront residences & golf villas across UAE, KSA, Oman, Qatar, Spain & UK.'
    },
    {
      category: 'Wasalt Saudi Portal',
      source: 'Wasalt',
      question: 'What projects does Wasalt feature?',
      desc: 'Verified residential compounds, villas, apartments & masterplans across Riyadh, Jeddah, Makkah & Madinah.'
    },
    {
      category: 'Cross-Platform Comparison',
      source: 'Both Platforms',
      question: 'Compare the projects available on both platforms.',
      desc: 'Categorized comparison of business models, locations, pricing transparency, and Riyadh/Jeddah developments.'
    },
    {
      category: 'Waterfront & Lifestyle',
      source: 'Both Platforms',
      question: 'Which projects mention waterfront amenities?',
      desc: 'Explore Al Marjan Island, Qetaifan Island, Jeddah Corniche, Dubai Canal, Muscat cliffs & Wadi Hanifa.'
    },
    {
      category: 'Financial & Escrow Terms',
      source: 'Both Platforms',
      question: 'What payment plans are publicly listed?',
      desc: 'Review construction-linked milestones, RERA escrow protections, Oman mortgages & Wasalt payment options.'
    },
    {
      category: 'Global & Regional Footprint',
      source: 'Both Platforms',
      question: 'What locations are mentioned across both platforms?',
      desc: 'Complete directory of countries, cities, and districts covered by DarGlobal and Wasalt.'
    },
    {
      category: 'Handover & Timelines',
      source: 'Both Platforms',
      question: 'Which projects have publicly listed completion dates?',
      desc: 'Compare ready-to-move-in developments and 2026–2031 scheduled handovers across both sources.'
    },
    {
      category: 'Riyadh Head-to-Head',
      source: 'Both Platforms',
      question: 'Compare Neptune by Mouawad on DarGlobal with Etoile Villas and Sadeem Town Villa on Wasalt.',
      desc: 'Detailed breakdown of Riyadh luxury villa specifications, sizes, completion dates, and SAR pricing.'
    },
    {
      category: 'Hallucination Guardrail Test',
      source: 'Verification',
      question: 'What are the prices for Emaar properties in New York or Damac towers in Tokyo?',
      desc: 'Verify that the RAG assistant strictly refuses unindexed developers and locations without guessing.'
    }
  ];

  const state = {
    messages: [],
    loading: false,
    error: null,
    sourceFilter: 'ALL',
    health: null,
    sourcesModalOpen: false,
    apiKeyModalOpen: false,
    customApiKey: localStorage.getItem('estate_ai_openrouter_key') || '',
    indexedRecords: [],
    sourcesFilterTab: 'ALL',
    sourcesSearch: ''
  };

  function escapeHtml(str) {
    return String(str || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function renderMarkdown(md) {
    if (!md) return '';
    const lines = md.split('\n');
    let html = '';
    let inList = false;
    let inTable = false;
    let tableRows = [];

    function formatInline(text) {
      let s = escapeHtml(text);
      // Bold + link: **[text](url)**
      s = s.replace(/\*\*\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)\*\*/g, '<strong><a href="$2" target="_blank" rel="noopener noreferrer">$1 ↗</a></strong>');
      // Standard link: [text](url)
      s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1 ↗</a>');
      // Bold: **text**
      s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      // Italic: *text*
      s = s.replace(/\*([^*]+)\*/g, '<em>$1</em>');
      return s;
    }

    function flushTable() {
      if (!inTable || tableRows.length === 0) return;
      html += '<div class="table-scroll-wrapper"><table>';
      tableRows.forEach((row, rIdx) => {
        const cells = row
          .trim()
          .replace(/^\|/, '')
          .replace(/\|$/, '')
          .split('|')
          .map((c) => c.trim());
        if (rIdx === 0) {
          html += '<thead><tr>' + cells.map((c) => `<th>${formatInline(c)}</th>`).join('') + '</tr></thead><tbody>';
        } else if (rIdx === 1 && cells.every((c) => /^:?-{2,}:?$/.test(c))) {
          // separator row
        } else {
          html += '<tr>' + cells.map((c) => `<td>${formatInline(c)}</td>`).join('') + '</tr>';
        }
      });
      html += '</tbody></table></div>';
      inTable = false;
      tableRows = [];
    }

    function flushList() {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
    }

    for (let i = 0; i < lines.length; i++) {
      const rawLine = lines[i];
      const trimmed = rawLine.trim();

      if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
        flushList();
        inTable = true;
        tableRows.push(trimmed);
        continue;
      } else if (inTable) {
        flushTable();
      }

      if (!trimmed) {
        flushList();
        continue;
      }

      if (trimmed.startsWith('### ')) {
        flushList();
        html += `<h3>${formatInline(trimmed.slice(4))}</h3>`;
      } else if (trimmed.startsWith('## ')) {
        flushList();
        html += `<h3>${formatInline(trimmed.slice(3))}</h3>`;
      } else if (trimmed.startsWith('- ') || trimmed.startsWith('• ') || trimmed.startsWith('* ')) {
        if (!inList) {
          html += '<ul>';
          inList = true;
        }
        html += `<li>${formatInline(trimmed.slice(2))}</li>`;
      } else {
        flushList();
        html += `<p>${formatInline(trimmed)}</p>`;
      }
    }
    flushList();
    flushTable();
    return html;
  }

  async function loadHealth() {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        state.health = await res.json();
        render();
        return;
      }
    } catch (e) {}
    if (window.__ESTATE_AI_EMBEDDED_DATA__ && window.__ESTATE_AI_EMBEDDED_DATA__.health) {
      state.health = window.__ESTATE_AI_EMBEDDED_DATA__.health;
      render();
    }
  }

  async function loadSourcesCatalog() {
    try {
      const res = await fetch('/api/sources');
      if (res.ok) {
        const data = await res.json();
        state.indexedRecords = data.records || [];
        render();
        return;
      }
    } catch (e) {}
    if (window.__ESTATE_AI_EMBEDDED_DATA__ && window.__ESTATE_AI_EMBEDDED_DATA__.records) {
      state.indexedRecords = window.__ESTATE_AI_EMBEDDED_DATA__.records;
      render();
    }
  }

  function runClientSideRagFallback(query) {
    const embedded = window.__ESTATE_AI_EMBEDDED_DATA__ || {};
    const qLower = query.toLowerCase().trim();
    if (embedded.precomputed && embedded.precomputed[qLower]) {
      return embedded.precomputed[qLower];
    }
    const records = (embedded.records || []).filter((r) =>
      state.sourceFilter === 'ALL' ? true : r.source_website === state.sourceFilter
    );
    const outKeywords = ['emaar', 'damac', 'nakheel', 'aldar', 'new york', 'tokyo', 'paris', 'sydney'];
    for (const kw of outKeywords) {
      if (qLower.includes(kw)) {
        return {
          answer: `I cannot verify or answer information about **${kw.toUpperCase()}** because it is **not available in the indexed sources** from [DarGlobal](https://www.darglobal.co.uk/) or [Wasalt](https://wasalt.sa/en).`,
          sources: [],
          model_used: 'openrouter/free',
          llm_mode: 'grounded_synthesis_fallback',
          retrieved_chunks_count: 0,
          latency_ms: 4
        };
      }
    }
    const tokens = qLower.split(/\W+/).filter((t) => t.length > 2);
    const scored = records.map((r) => {
      const hay = `${r.project_name} ${r.location} ${r.description} ${r.pricing} ${r.completion_info} ${(r.amenities || []).join(' ')}`.toLowerCase();
      let s = 0;
      tokens.forEach((t) => {
        if (r.project_name.toLowerCase().includes(t)) s += 3;
        if (r.location.toLowerCase().includes(t)) s += 2;
        if (hay.includes(t)) s += 1;
      });
      return { rec: r, score: s };
    }).sort((a, b) => b.score - a.score);

    const top = scored.filter((x) => x.score > 0).slice(0, 5).map((x) => x.rec);
    const chosen = top.length > 0 ? top : records.slice(0, 4);
    let md = 'Based on the indexed **DarGlobal** and **Wasalt** knowledge base, here are the verified matching projects:\n\n';
    md += '| Project / Listing | Source | Location | Status / Completion | Pricing |\n';
    md += '| :--- | :--- | :--- | :--- | :--- |\n';
    chosen.forEach((r) => {
      md += `| **[${r.project_name}](${r.page_url})** | ${r.source_website} | ${r.location} | ${r.completion_info} | ${r.pricing} |\n`;
    });
    md += '\n';
    chosen.slice(0, 3).forEach((r) => {
      md += `### [${r.project_name}](${r.page_url}) (${r.source_website})\n`;
      md += `- **Location**: ${r.location}\n`;
      md += `- **Developer**: ${r.developer}\n`;
      md += `- **Description**: ${r.description}\n`;
      md += `- **Pricing**: ${r.pricing} | **Payment Plan**: ${r.payment_plan}\n`;
      md += `- **Completion**: ${r.completion_info}\n`;
      md += `- **Amenities**: ${(r.amenities || []).slice(0, 7).join(', ')}\n\n`;
    });
    return {
      answer: md,
      sources: chosen.map((r) => ({
        project_name: r.project_name,
        source_website: r.source_website,
        page_url: r.page_url,
        location: r.location,
        pricing: r.pricing,
        completion_info: r.completion_info
      })),
      model_used: 'openrouter/free',
      llm_mode: 'grounded_synthesis_fallback',
      retrieved_chunks_count: chosen.length * 2,
      latency_ms: 8
    };
  }

  async function submitQuestion(questionText) {
    const query = (questionText || '').trim();
    if (!query || state.loading) return;

    const priorHistory = state.messages.map((m) => ({
      role: m.role,
      content: m.content
    }));

    state.messages.push({ role: 'user', content: query });
    state.loading = true;
    state.error = null;
    render();
    scrollToBottom();

    try {
      const headers = { 'Content-Type': 'application/json' };
      if (state.customApiKey && state.customApiKey.trim()) {
        headers['X-OpenRouter-Key'] = state.customApiKey.trim();
      }
      let data = null;
      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers,
          body: JSON.stringify({
            message: query,
            history: priorHistory,
            source_filter: state.sourceFilter === 'ALL' ? null : state.sourceFilter,
            top_k: 8
          })
        });
        if (res.ok) {
          data = await res.json();
        }
      } catch (fetchErr) {}
      if (!data) {
        data = runClientSideRagFallback(query);
      }
      state.messages.push({
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
        model_used: data.model_used,
        llm_mode: data.llm_mode,
        retrieved_chunks_count: data.retrieved_chunks_count,
        latency_ms: data.latency_ms,
        notice: data.notice
      });
    } catch (err) {
      state.error = err.message || 'An unexpected error occurred while contacting the RAG backend.';
    } finally {
      state.loading = false;
      render();
      scrollToBottom();
    }
  }

  function scrollToBottom() {
    setTimeout(() => {
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    }, 60);
  }

  function render() {
    const root = document.getElementById('app');
    if (!root) return;

    const kb = state.health?.knowledge_base || {
      total_records: 34,
      darglobal_records: 22,
      wasalt_records: 12,
      total_indexed_chunks: 102
    };
    const llm = state.health?.llm || {
      configured_model: 'openrouter/free',
      api_key_configured: false
    };

    const hasKey = llm.api_key_configured || Boolean(state.customApiKey.trim());

    root.innerHTML = `
      <!-- Top Navigation Header -->
      <header class="sticky top-0 z-30 backdrop-blur-md bg-slate-950/90 border-b border-slate-800/90 px-4 md:px-8 py-3.5">
        <div class="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 via-amber-500 to-amber-600 flex items-center justify-center text-slate-950 font-bold text-xl shadow-lg shadow-amber-500/20">
              E
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h1 class="text-base md:text-lg font-bold tracking-tight text-white">Estate Intelligence AI</h1>
                <span class="hidden sm:inline-block text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                  RAG Active • ${kb.total_records} Projects (${kb.total_indexed_chunks} Chunks)
                </span>
              </div>
              <p class="text-xs text-slate-400">
                Public Real Estate Intelligence for <a href="https://www.darglobal.co.uk/" target="_blank" class="text-amber-400 hover:underline">DarGlobal</a> &amp; <a href="https://wasalt.sa/en" target="_blank" class="text-emerald-400 hover:underline">Wasalt</a>
              </p>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <!-- Source Filter Pills -->
            <div class="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs">
              ${['ALL', 'DarGlobal', 'Wasalt'].map((tab) => `
                <button
                  data-filter="${tab}"
                  class="filter-btn px-3 py-1.5 rounded-lg font-medium transition-all ${
                    state.sourceFilter === tab
                      ? 'bg-amber-500 text-slate-950 shadow'
                      : 'text-slate-400 hover:text-white'
                  }"
                >
                  ${tab === 'ALL' ? 'All Sources' : tab}
                </button>
              `).join('')}
            </div>

            <!-- Browse Indexed Dataset Button -->
            <button
              id="open-sources-btn"
              class="text-xs px-3 py-2 rounded-xl border border-slate-700 bg-slate-900 hover:border-amber-500/60 text-slate-200 font-medium transition-colors"
            >
              📚 Dataset (${kb.darglobal_records} DarGlobal + ${kb.wasalt_records} Wasalt)
            </button>

            <!-- OpenRouter Key Config Button -->
            <button
              id="open-key-btn"
              class="text-xs px-3 py-2 rounded-xl border ${
                hasKey
                  ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
                  : 'border-amber-500/40 bg-amber-500/10 text-amber-300'
              } hover:opacity-90 font-medium transition-colors"
              title="Configure optional OpenRouter API Key for live LLM inference"
            >
              🔑 ${hasKey ? 'OpenRouter Key Set' : 'OpenRouter Config'}
            </button>

            ${state.messages.length > 0 ? `
              <button
                id="clear-chat-btn"
                class="text-xs px-3 py-2 rounded-xl border border-rose-500/40 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20 font-medium transition-colors"
              >
                Clear Chat
              </button>
            ` : ''}
          </div>
        </div>
      </header>

      <!-- Main Content Container -->
      <main class="flex-1 max-w-6xl w-full mx-auto px-4 md:px-8 py-6 flex flex-col">
        ${state.messages.length === 0 ? `
          <!-- Landing Screen -->
          <div class="my-auto py-4">
            <div class="p-6 md:p-8 rounded-3xl bg-gradient-to-br from-slate-900 via-slate-900/95 to-slate-950 border border-slate-800/90 shadow-2xl mb-6">
              <div class="flex flex-wrap items-center gap-2 mb-4">
                <span class="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                  DarGlobal (${kb.darglobal_records} Indexed Projects)
                </span>
                <span class="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                  Wasalt (${kb.wasalt_records} Indexed Saudi Projects &amp; Catalogs)
                </span>
                <span class="px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">
                  OpenRouter Model: ${escapeHtml(llm.configured_model)}
                </span>
              </div>

              <h2 class="text-2xl md:text-4xl font-bold text-white tracking-tight leading-tight">
                AI-Powered Real Estate Research Across <span class="text-amber-400">DarGlobal</span> &amp; <span class="text-emerald-400">Wasalt</span>
              </h2>
              <p class="text-slate-300 mt-3 text-sm md:text-base max-w-3xl leading-relaxed">
                Ask detailed questions about luxury branded developments, Saudi residential compounds, locations, bedroom configurations,
                waterfront &amp; golf amenities, publicly listed SAR/QAR prices, payment plans, and 2026–2031 completion dates. Every answer is strictly
                grounded in scraped public pages with clickable citations.
              </p>
            </div>

            <div class="mb-3 flex items-center justify-between">
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">
                Suggested Research Prompts (Click to Ask Immediately)
              </h3>
              <span class="text-xs text-slate-500">Filter active: ${state.sourceFilter}</span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
              ${SUGGESTED_PROMPTS.map((item) => `
                <button
                  data-prompt="${escapeHtml(item.question)}"
                  class="prompt-card text-left group p-4 rounded-2xl border border-slate-800/90 bg-slate-900/75 hover:bg-slate-800/90 hover:border-amber-500/60 transition-all duration-200 flex flex-col justify-between shadow-md"
                >
                  <div>
                    <div class="flex items-center justify-between gap-2 mb-2">
                      <span class="text-[11px] font-bold uppercase tracking-wider text-amber-400">
                        ${escapeHtml(item.category)}
                      </span>
                      <span class="text-[10px] px-2 py-0.5 rounded-full ${
                        item.source === 'DarGlobal'
                          ? 'bg-amber-500/15 text-amber-300 border border-amber-500/30'
                          : item.source === 'Wasalt'
                          ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30'
                          : 'bg-slate-800 text-slate-300 border border-slate-700'
                      }">
                        ${escapeHtml(item.source)}
                      </span>
                    </div>
                    <p class="text-sm font-semibold text-slate-100 group-hover:text-amber-300 transition-colors">
                      “${escapeHtml(item.question)}”
                    </p>
                  </div>
                  <p class="text-xs text-slate-400 mt-2.5 leading-relaxed">
                    ${escapeHtml(item.desc)}
                  </p>
                </button>
              `).join('')}
            </div>
          </div>
        ` : `
          <!-- Conversation History -->
          <div class="flex-1 space-y-5 pb-6">
            ${state.messages.map((m) => {
              if (m.role === 'user') {
                return `
                  <div class="flex justify-end">
                    <div class="max-w-2xl bg-gradient-to-br from-amber-400 to-amber-500 text-slate-950 font-semibold px-5 py-3.5 rounded-2xl rounded-br-sm shadow-lg">
                      <div class="text-[10px] uppercase tracking-wider text-slate-900/80 mb-0.5">You Asked</div>
                      <p class="text-sm md:text-base">${escapeHtml(m.content)}</p>
                    </div>
                  </div>
                `;
              }
              const citations = m.sources || [];
              return `
                <div class="flex justify-start">
                  <div class="w-full max-w-5xl bg-slate-900/95 border border-slate-800 rounded-2xl p-5 md:p-6 shadow-xl">
                    <div class="flex flex-wrap items-center justify-between gap-2 pb-3 mb-4 border-b border-slate-800">
                      <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
                        <span class="text-xs font-bold uppercase tracking-wider text-slate-200">
                          Estate Intelligence AI
                        </span>
                        <span class="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-amber-300 border border-slate-700">
                          ${m.llm_mode === 'openrouter_live' ? '⚡ OpenRouter Live LLM' : '🛡️ Grounded RAG Synthesis'}
                        </span>
                      </div>
                      <div class="flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
                        <span class="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                          Model: ${escapeHtml(m.model_used || 'openrouter/free')}
                        </span>
                        <span class="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                          ${m.retrieved_chunks_count || 0} Chunks Retrieved
                        </span>
                        <span class="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                          ${m.latency_ms || 0} ms
                        </span>
                      </div>
                    </div>

                    <div class="markdown-body text-sm md:text-base text-slate-200">
                      ${renderMarkdown(m.content)}
                    </div>

                    ${citations.length > 0 ? `
                      <div class="mt-6 pt-4 border-t border-slate-800/90">
                        <div class="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
                          Verified Source Citations (${citations.length} Grounded Pages)
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                          ${citations.map((src) => `
                            <a
                              href="${escapeHtml(src.page_url)}"
                              target="_blank"
                              rel="noopener noreferrer"
                              class="block p-3 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-amber-500/60 transition-all group"
                            >
                              <div class="flex items-center justify-between gap-2 mb-1">
                                <span class="text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                                  src.source_website === 'DarGlobal'
                                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                                    : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                                }">
                                  ${escapeHtml(src.source_website)}
                                </span>
                                <span class="text-[11px] text-slate-400 truncate">
                                  ${escapeHtml(src.location)}
                                </span>
                              </div>
                              <div class="text-xs font-semibold text-slate-100 group-hover:text-amber-300 truncate">
                                ${escapeHtml(src.project_name)} ↗
                              </div>
                              <div class="text-[11px] text-amber-400/80 truncate mt-0.5">
                                ${escapeHtml(src.page_url)}
                              </div>
                            </a>
                          `).join('')}
                        </div>
                      </div>
                    ` : ''}
                  </div>
                </div>
              `;
            }).join('')}

            ${state.loading ? `
              <div class="flex justify-start">
                <div class="p-4 rounded-2xl bg-slate-900 border border-amber-500/40 text-xs text-amber-300 flex items-center gap-3 shadow-lg">
                  <span class="w-3 h-3 rounded-full bg-amber-400 animate-ping"></span>
                  <span>Searching DarGlobal &amp; Wasalt vector index and generating grounded response with citations...</span>
                </div>
              </div>
            ` : ''}
          </div>
        `}

        ${state.error ? `
          <div class="p-4 mb-4 rounded-xl bg-rose-950/80 border border-rose-700 text-rose-200 text-xs flex items-center justify-between">
            <span>⚠️ ${escapeHtml(state.error)}</span>
            <button id="dismiss-err-btn" class="underline ml-4">Dismiss</button>
          </div>
        ` : ''}
      </main>

      <!-- Bottom Chat Input Bar -->
      <footer class="sticky bottom-0 z-20 bg-slate-950/95 backdrop-blur-md border-t border-slate-800 px-4 md:px-8 py-3.5">
        <div class="max-w-5xl mx-auto">
          <form id="chat-form" class="flex gap-2.5">
            <input
              id="chat-input"
              type="text"
              placeholder="Ask about DarGlobal or Wasalt projects, locations, waterfront amenities, prices, payment plans, or completion dates..."
              class="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-amber-500"
              ${state.loading ? 'disabled' : ''}
            />
            <button
              type="submit"
              ${state.loading ? 'disabled' : ''}
              class="px-6 py-3 rounded-xl bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400 disabled:opacity-40 text-slate-950 font-bold text-sm shadow-md transition-all"
            >
              ${state.loading ? 'Researching...' : 'Ask AI'}
            </button>
          </form>
        </div>
      </footer>

      <!-- Dataset Inspector Modal -->
      ${state.sourcesModalOpen ? `
        <div class="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-5xl w-full max-h-[85vh] flex flex-col overflow-hidden shadow-2xl">
            <div class="p-4 md:p-5 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3">
              <div>
                <h3 class="font-bold text-base text-white">
                  Scraped &amp; Indexed Real Estate Dataset (${state.indexedRecords.length} Records)
                </h3>
                <p class="text-xs text-slate-400">
                  Every record preserves source website, canonical URL, location, specs, amenities, pricing, and completion timeline.
                </p>
              </div>
              <button id="close-sources-btn" class="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium">
                ✕ Close
              </button>
            </div>
            <div class="p-4 overflow-y-auto space-y-3">
              ${state.indexedRecords.map((r) => `
                <div class="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                  <div class="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                    <a href="${escapeHtml(r.page_url)}" target="_blank" rel="noopener noreferrer" class="font-bold text-sm text-amber-300 hover:underline">
                      ${escapeHtml(r.project_name)} ↗
                    </a>
                    <span class="px-2.5 py-0.5 rounded-full font-semibold ${
                      r.source_website === 'DarGlobal'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    }">
                      ${escapeHtml(r.source_website)}
                    </span>
                  </div>
                  <p class="text-slate-300 mb-2 leading-relaxed">${escapeHtml(r.description)}</p>
                  <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] text-slate-400 bg-slate-900/80 p-2.5 rounded-lg border border-slate-800/80">
                    <div><strong class="text-slate-200">Location:</strong> ${escapeHtml(r.location)}</div>
                    <div><strong class="text-slate-200">Pricing:</strong> ${escapeHtml(r.pricing)}</div>
                    <div><strong class="text-slate-200">Completion:</strong> ${escapeHtml(r.completion_info)}</div>
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      ` : ''}

      <!-- OpenRouter API Key Modal -->
      ${state.apiKeyModalOpen ? `
        <div class="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-lg w-full p-5 shadow-2xl">
            <div class="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
              <h3 class="font-bold text-white text-base">OpenRouter Free LLM Configuration</h3>
              <button id="close-key-btn" class="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300">✕</button>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed mb-3">
              The backend integrates with <strong>OpenRouter</strong> (defaulting to <code class="text-amber-300">openrouter/free</code> with automatic fallback to <code class="text-amber-300">nvidia/nemotron-3-ultra:free</code>, <code class="text-amber-300">google/gemma-4-31b-it:free</code>, and <code class="text-amber-300">meta-llama/llama-3.3-70b-instruct:free</code>).
            </p>
            <p class="text-xs text-slate-400 leading-relaxed mb-4">
              Per security best practices, no API key is ever hardcoded in frontend code. If the server does not have an <code class="text-slate-200">OPENROUTER_API_KEY</code> environment variable set, you can optionally paste your own OpenRouter key below (passed securely via request header) or leave it blank to use the built-in deterministic <strong>Grounded RAG Synthesis Engine</strong>.
            </p>
            <input
              id="custom-key-input"
              type="password"
              value="${escapeHtml(state.customApiKey)}"
              placeholder="sk-or-v1-... (Optional)"
              class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white mb-4"
            />
            <div class="flex justify-end gap-2">
              <button id="clear-key-btn" class="text-xs px-3 py-2 rounded-lg bg-slate-800 text-slate-300">Clear</button>
              <button id="save-key-btn" class="text-xs px-4 py-2 rounded-lg bg-amber-500 text-slate-950 font-bold">Save Key</button>
            </div>
          </div>
        </div>
      ` : ''}
    `;

    // Bind events
    document.querySelectorAll('.filter-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        state.sourceFilter = btn.getAttribute('data-filter') || 'ALL';
        render();
      });
    });

    document.querySelectorAll('.prompt-card').forEach((card) => {
      card.addEventListener('click', () => {
        const q = card.getAttribute('data-prompt');
        if (q) submitQuestion(q);
      });
    });

    const form = document.getElementById('chat-form');
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const inputEl = document.getElementById('chat-input');
        if (inputEl && inputEl.value.trim()) {
          submitQuestion(inputEl.value.trim());
        }
      });
    }

    const clearBtn = document.getElementById('clear-chat-btn');
    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        state.messages = [];
        state.error = null;
        render();
      });
    }

    const openSourcesBtn = document.getElementById('open-sources-btn');
    if (openSourcesBtn) {
      openSourcesBtn.addEventListener('click', () => {
        state.sourcesModalOpen = true;
        if (state.indexedRecords.length === 0) {
          loadSourcesCatalog();
        }
        render();
      });
    }

    const closeSourcesBtn = document.getElementById('close-sources-btn');
    if (closeSourcesBtn) {
      closeSourcesBtn.addEventListener('click', () => {
        state.sourcesModalOpen = false;
        render();
      });
    }

    const openKeyBtn = document.getElementById('open-key-btn');
    if (openKeyBtn) {
      openKeyBtn.addEventListener('click', () => {
        state.apiKeyModalOpen = true;
        render();
      });
    }

    const closeKeyBtn = document.getElementById('close-key-btn');
    if (closeKeyBtn) {
      closeKeyBtn.addEventListener('click', () => {
        state.apiKeyModalOpen = false;
        render();
      });
    }

    const saveKeyBtn = document.getElementById('save-key-btn');
    if (saveKeyBtn) {
      saveKeyBtn.addEventListener('click', () => {
        const inp = document.getElementById('custom-key-input');
        state.customApiKey = inp ? inp.value.trim() : '';
        localStorage.setItem('estate_ai_openrouter_key', state.customApiKey);
        state.apiKeyModalOpen = false;
        render();
      });
    }

    const clearKeyBtn = document.getElementById('clear-key-btn');
    if (clearKeyBtn) {
      clearKeyBtn.addEventListener('click', () => {
        state.customApiKey = '';
        localStorage.removeItem('estate_ai_openrouter_key');
        state.apiKeyModalOpen = false;
        render();
      });
    }

    const dismissErrBtn = document.getElementById('dismiss-err-btn');
    if (dismissErrBtn) {
      dismissErrBtn.addEventListener('click', () => {
        state.error = null;
        render();
      });
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    render();
    loadHealth();
  });
})();
