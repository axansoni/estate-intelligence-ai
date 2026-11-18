import React, { useState } from 'react';
import { marked } from 'marked';

export default function MessageBubble({ message }) {
  const [showAllSources, setShowAllSources] = useState(false);
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end mb-5">
        <div className="max-w-2xl bg-gradient-to-br from-amber-500 to-amber-600 text-slate-950 font-medium px-5 py-3.5 rounded-2xl rounded-br-xs shadow-md">
          <p className="text-sm md:text-base whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  }

  const htmlContent = marked.parse(message.content || '');
  const sources = message.sources || [];
  const visibleSources = showAllSources ? sources : sources.slice(0, 4);

  return (
    <div className="flex justify-start mb-6">
      <div className="w-full max-w-4xl bg-slate-900/95 border border-slate-800 rounded-2xl p-5 shadow-lg">
        <div className="flex flex-wrap items-center justify-between gap-2 pb-3 mb-3 border-b border-slate-800/80">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
            <span className="text-xs font-semibold tracking-wide uppercase text-slate-300">
              Estate Intelligence AI
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
            {message.model_used && (
              <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-amber-300">
                Model: {message.model_used}
              </span>
            )}
            {typeof message.retrieved_chunks_count === 'number' && (
              <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                {message.retrieved_chunks_count} RAG Chunks
              </span>
            )}
            {typeof message.latency_ms === 'number' && (
              <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                {message.latency_ms} ms
              </span>
            )}
          </div>
        </div>

        <div
          className="prose prose-invert max-w-none text-sm md:text-base leading-relaxed"
          dangerouslySetInnerHTML={{ __html: htmlContent }}
        />

        {sources.length > 0 && (
          <div className="mt-5 pt-4 border-t border-slate-800">
            <div className="flex items-center justify-between mb-2.5">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Verified Source Citations ({sources.length})
              </span>
              {sources.length > 4 && (
                <button
                  onClick={() => setShowAllSources(!showAllSources)}
                  className="text-xs text-amber-400 hover:underline"
                >
                  {showAllSources ? 'Show fewer' : `Show all ${sources.length} sources`}
                </button>
              )}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {visibleSources.map((src, i) => (
                <a
                  key={i}
                  href={src.page_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block p-3 rounded-xl bg-slate-950/70 border border-slate-800 hover:border-amber-500/60 transition-all"
                >
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span
                      className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                        src.source_website === 'DarGlobal'
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      }`}
                    >
                      {src.source_website}
                    </span>
                    <span className="text-[11px] text-slate-400 truncate">{src.location}</span>
                  </div>
                  <p className="text-xs font-semibold text-slate-100 truncate">{src.project_name}</p>
                  <p className="text-[11px] text-amber-400/90 truncate mt-0.5">{src.page_url}</p>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
