import React from 'react';

export const SUGGESTED_QUESTIONS = [
  {
    category: 'DarGlobal Portfolio',
    source: 'DarGlobal',
    question: 'What residential projects are available on DarGlobal?',
    description: 'Explore branded towers, beach villas & golf communities across UAE, KSA, Oman, Qatar, Spain & UK.',
  },
  {
    category: 'Wasalt Saudi Portal',
    source: 'Wasalt',
    question: 'What projects does Wasalt feature?',
    description: 'View verified Saudi residential compounds, villas, apartments & masterplans with SAR prices.',
  },
  {
    category: 'Cross-Platform Analysis',
    source: 'Both',
    question: 'Compare the projects available on both platforms.',
    description: 'Side-by-side comparison of business models, locations, pricing transparency, and Riyadh/Jeddah overlap.',
  },
  {
    category: 'Lifestyle & Amenities',
    source: 'Both',
    question: 'Which projects mention waterfront amenities?',
    description: 'Discover beachfront, Red Sea Corniche, Dubai Canal, Muscat cliffside & Wadi Hanifa projects.',
  },
  {
    category: 'Financial Terms',
    source: 'Both',
    question: 'What payment plans are publicly listed?',
    description: 'Review off-plan milestone structures, RERA escrow rules, Oman mortgages & Wasalt payment options.',
  },
  {
    category: 'Geographic Coverage',
    source: 'Both',
    question: 'What locations are mentioned across both platforms?',
    description: 'Complete directory of countries, cities, and neighborhoods indexed from DarGlobal and Wasalt.',
  },
  {
    category: 'Delivery Schedules',
    source: 'Both',
    question: 'Which projects have publicly listed completion dates?',
    description: 'Compare 2026–2031 handover timelines and ready-to-move-in developments across both sources.',
  },
];

export default function SuggestedPrompts({ onSelectQuestion, disabled }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5 mt-6">
      {SUGGESTED_QUESTIONS.map((item, idx) => (
        <button
          key={idx}
          disabled={disabled}
          onClick={() => onSelectQuestion(item.question)}
          className="text-left group p-4 rounded-xl border border-slate-800 bg-slate-900/70 hover:bg-slate-800/90 hover:border-amber-500/50 transition-all duration-200 flex flex-col justify-between shadow-sm"
        >
          <div>
            <div className="flex items-center justify-between gap-2 mb-2">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-400/90">
                {item.category}
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                {item.source}
              </span>
            </div>
            <p className="text-sm font-medium text-slate-100 group-hover:text-amber-300 transition-colors">
              {item.question}
            </p>
          </div>
          <p className="text-xs text-slate-400 mt-2 line-clamp-2">{item.description}</p>
        </button>
      ))}
    </div>
  );
}
