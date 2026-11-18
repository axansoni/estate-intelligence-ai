import React, { useState, useEffect } from 'react';
import MessageBubble from './components/MessageBubble';
import SuggestedPrompts from './components/SuggestedPrompts';
import { fetchHealth, fetchSources, sendChatMessage } from './api/client';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sourceFilter, setSourceFilter] = useState('ALL');
  const [health, setHealth] = useState(null);
  const [sourcesModalOpen, setSourcesModalOpen] = useState(false);
  const [indexedRecords, setIndexedRecords] = useState([]);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(() => {});
  }, []);

  const handleOpenSources = async () => {
    setSourcesModalOpen(true);
    if (indexedRecords.length === 0) {
      try {
        const data = await fetchSources();
        setIndexedRecords(data.records || []);
      } catch (e) {
        console.error(e);
      }
    }
  };

  const handleSend = async (questionText) => {
    const query = (questionText ?? input).trim();
    if (!query || loading) return;

    setInput('');
    setError(null);
    const nextHistory = [...messages, { role: 'user', content: query }];
    setMessages(nextHistory);
    setLoading(true);

    try {
      const priorHistory = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await sendChatMessage({
        message: query,
        history: priorHistory,
        sourceFilter,
      });
      setMessages([
        ...nextHistory,
        {
          role: 'assistant',
          content: res.answer,
          sources: res.sources,
          model_used: res.model_used,
          llm_mode: res.llm_mode,
          retrieved_chunks_count: res.retrieved_chunks_count,
          latency_ms: res.latency_ms,
          notice: res.notice,
        },
      ]);
    } catch (err) {
      setError(err.message || 'Failed to communicate with the backend API.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <header className="sticky top-0 z-20 backdrop-blur-md bg-slate-950/90 border-b border-slate-800 px-4 md:px-8 py-3.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center text-slate-950 font-bold text-lg shadow">
            E
          </div>
          <div>
            <h1 className="text-base md:text-lg font-bold tracking-tight text-white">
              Estate Intelligence AI
            </h1>
            <p className="text-xs text-slate-400">
              DarGlobal &amp; Wasalt Real Estate RAG Research Assistant
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-xs">
            {['ALL', 'DarGlobal', 'Wasalt'].map((tab) => (
              <button
                key={tab}
                onClick={() => setSourceFilter(tab)}
                className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                  sourceFilter === tab
                    ? 'bg-amber-500 text-slate-950'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {tab === 'ALL' ? 'All Sources' : tab}
              </button>
            ))}
          </div>

          <button
            onClick={handleOpenSources}
            className="text-xs px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900 hover:border-amber-500/60 text-slate-200"
          >
            Indexed Sources ({health?.knowledge_base?.total_records || 34})
          </button>

          {messages.length > 0 && (
            <button
              onClick={() => {
                setMessages([]);
                setError(null);
              }}
              className="text-xs px-3 py-1.5 rounded-lg border border-rose-500/40 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20"
            >
              Clear Chat
            </button>
          )}
        </div>
      </header>

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 md:px-8 py-6 flex flex-col">
        {messages.length === 0 ? (
          <div className="my-auto py-6">
            <div className="max-w-3xl">
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20 mb-4">
                Grounded Retrieval-Augmented Generation • Zero Hallucination Policy
              </span>
              <h2 className="text-2xl md:text-4xl font-bold text-white tracking-tight leading-tight">
                Research Luxury Developments &amp; Saudi Property Markets with Verified Citations
              </h2>
              <p className="text-slate-400 mt-3 text-sm md:text-base leading-relaxed">
                Ask questions about publicly available projects, locations, unit configurations, waterfront
                amenities, pricing, payment plans, and completion dates across{' '}
                <a
                  href="https://www.darglobal.co.uk/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-amber-400 underline"
                >
                  DarGlobal
                </a>{' '}
                and{' '}
                <a
                  href="https://wasalt.sa/en"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-emerald-400 underline"
                >
                  Wasalt
                </a>
                .
              </p>
            </div>

            <SuggestedPrompts onSelectQuestion={handleSend} disabled={loading} />
          </div>
        ) : (
          <div className="flex-1 space-y-4 pb-6">
            {messages.map((m, idx) => (
              <MessageBubble key={idx} message={m} />
            ))}
            {loading && (
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs text-amber-300 animate-pulse max-w-md">
                Retrieving relevant vector chunks &amp; synthesizing grounded answer...
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="p-3.5 mb-4 rounded-xl bg-rose-950/70 border border-rose-700 text-rose-200 text-xs">
            {error}
          </div>
        )}
      </main>

      <footer className="sticky bottom-0 bg-slate-950/95 backdrop-blur border-t border-slate-800 px-4 md:px-8 py-3.5">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="max-w-5xl mx-auto flex gap-2.5"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about DarGlobal or Wasalt projects, locations, amenities, prices, payment plans, or timelines..."
            className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-5 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-slate-950 font-semibold text-sm transition-colors"
          >
            {loading ? 'Researching...' : 'Ask AI'}
          </button>
        </form>
      </footer>

      {sourcesModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-4xl w-full max-h-[82vh] flex flex-col overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="font-bold text-white">
                Indexed Knowledge Base ({indexedRecords.length} Verified Records)
              </h3>
              <button
                onClick={() => setSourcesModalOpen(false)}
                className="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300"
              >
                Close
              </button>
            </div>
            <div className="p-4 overflow-y-auto space-y-2.5">
              {indexedRecords.map((r) => (
                <div key={r.id} className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold text-amber-300">{r.project_name}</span>
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                      {r.source_website}
                    </span>
                  </div>
                  <p className="text-slate-400 mt-1">
                    {r.location} • Status: {r.completion_info} • Pricing: {r.pricing}
                  </p>
                  <a
                    href={r.page_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-emerald-400 hover:underline inline-block mt-1"
                  >
                    {r.page_url}
                  </a>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
