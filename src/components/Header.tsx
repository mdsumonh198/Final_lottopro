import React from 'react';
import { Download, Globe } from 'lucide-react';
import { GuaranteeGoal } from '../types';

interface HeaderProps {
  activeTab: 'dashboard' | 'or-theory' | 'python-source' | 'colab-mip' | 'cpp-engine';
  setActiveTab: (tab: 'dashboard' | 'or-theory' | 'python-source' | 'colab-mip' | 'cpp-engine') => void;
  onExportWheel: () => void;
  onExportBudget: () => void;
  budgetCount: number;
  poolSize: number;
  pickSize: number;
  goal?: GuaranteeGoal;
  lang?: 'bn' | 'en';
  onToggleLang?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  onExportWheel,
  onExportBudget,
  budgetCount,
  poolSize,
  pickSize,
  goal,
  lang = 'bn',
  onToggleLang,
}) => {
  const isBn = lang === 'bn';

  return (
    <header className="border-b border-neutral-800 bg-[#0d1117]/95 backdrop-blur-md sticky top-0 z-30 px-4 lg:px-8 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
        {/* Zone 1: Wordmark */}
        <div className="flex items-center gap-3 shrink-0">
          <span className="text-lg sm:text-xl font-extrabold tracking-tight text-white font-mono flex items-center gap-2">
            <span>🎯</span>
            <span className="bg-gradient-to-r from-cyan-400 via-emerald-300 to-amber-300 bg-clip-text text-transparent">
              LOTTO-WHEEL
            </span>
          </span>
          <span className="hidden md:inline text-xs text-neutral-400 font-mono">
            {isBn ? `গেম ${pickSize}/${poolSize}` : `Game ${pickSize}/${poolSize}`} ·{' '}
            {goal
              ? isBn
                ? `টার্গেট: ${goal.matchTier}-ম্যাচ (${goal.targetFrequency} বার)`
                : `Target: ${goal.matchTier}-Match (${goal.targetFrequency}x)`
              : 'Priority Ranked'}
          </span>
        </div>

        {/* Zone 2: Navigation Tabs */}
        <nav className="flex items-center gap-1 sm:gap-1.5 overflow-x-auto">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
              activeTab === 'dashboard'
                ? 'bg-cyan-600 text-black shadow-md shadow-cyan-950/60'
                : 'text-neutral-300 hover:text-white hover:bg-neutral-800'
            }`}
          >
            {isBn ? 'লাইভ অ্যানালাইজার' : 'Live Analyzer'}
          </button>
          <button
            onClick={() => setActiveTab('or-theory')}
            className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
              activeTab === 'or-theory'
                ? 'bg-cyan-600 text-black shadow-md shadow-cyan-950/60'
                : 'text-neutral-300 hover:text-white hover:bg-neutral-800'
            }`}
          >
            {isBn ? 'অপারেশন্স রিসার্চ তত্ত্ব' : 'Operations Research'}
          </button>
          <button
            onClick={() => setActiveTab('python-source')}
            className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
              activeTab === 'python-source'
                ? 'bg-cyan-600 text-black shadow-md shadow-cyan-950/60'
                : 'text-neutral-300 hover:text-white hover:bg-neutral-800'
            }`}
          >
            {isBn ? 'পাইথন কোড (app.py)' : 'Python Source'}
          </button>
          <button
            onClick={() => setActiveTab('colab-mip')}
            className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
              activeTab === 'colab-mip'
                ? 'bg-emerald-500 text-black shadow-md shadow-emerald-950/60'
                : 'text-neutral-300 hover:text-white hover:bg-neutral-800'
            }`}
          >
            {isBn ? 'গুগল কোলাব (MIP)' : 'Google Colab (MIP)'}
          </button>
          <button
            onClick={() => setActiveTab('cpp-engine')}
            className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors whitespace-nowrap cursor-pointer ${
              activeTab === 'cpp-engine'
                ? 'bg-emerald-400 text-black shadow-md shadow-emerald-950/60'
                : 'text-emerald-400 hover:text-white hover:bg-emerald-950/60 border border-emerald-500/40'
            }`}
          >
            {isBn ? '⚡ C++ ইঞ্জিন (১০x ম্যাচ)' : '⚡ C++ Engine (10x Match)'}
          </button>
        </nav>

        {/* Zone 3: Language Toggle & CSV Downloads */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Language Toggle */}
          {onToggleLang && (
            <button
              onClick={onToggleLang}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-[#182235] hover:bg-[#202d45] border border-cyan-700/60 text-xs font-mono font-bold text-cyan-300 cursor-pointer shadow-sm"
              title={isBn ? 'Switch to English' : 'বাংলা মোড অন করুন'}
            >
              <Globe className="w-3.5 h-3.5 text-cyan-400" />
              <span>{isBn ? 'বাংলা' : 'English'}</span>
            </button>
          )}

          <button
            onClick={onExportBudget}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-black bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-300 hover:to-amber-400 rounded-lg transition-all shadow-md shadow-amber-950/60 cursor-pointer whitespace-nowrap"
            title={isBn ? `বাজেটের শীর্ষ ${budgetCount} টিকিট ডাউনলোড (CSV)` : `Download Top ${budgetCount} Budget CSV`}
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">
              {isBn ? `বাজেট ${budgetCount.toLocaleString()} টিকিট (CSV)` : `Budget ${budgetCount.toLocaleString()} CSV`}
            </span>
            <span className="sm:hidden">CSV</span>
          </button>

          <button
            onClick={onExportWheel}
            className="hidden xl:flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-black bg-gradient-to-r from-emerald-400 to-cyan-400 hover:from-emerald-300 hover:to-cyan-300 rounded-lg transition-all shadow-md shadow-emerald-950/60 cursor-pointer whitespace-nowrap"
            title={isBn ? 'সম্পূর্ণ কভারিং হুইল ডাউনলোড (CSV)' : 'Download Full Wheel CSV'}
          >
            <Download className="w-3.5 h-3.5" />
            <span>{isBn ? 'ফুল হুইল CSV' : 'Full Wheel CSV'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};
