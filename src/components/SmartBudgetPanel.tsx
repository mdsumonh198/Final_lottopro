import React from 'react';
import { Wallet, SlidersHorizontal, Download, Target, CheckCircle2, Hash } from 'lucide-react';
import { GuaranteeGoal } from '../types';

interface SmartBudgetPanelProps {
  budgetCount: number;
  totalTickets: number;
  onChangeBudget: (budget: number) => void;
  onDownloadBudget: () => void;
  guaranteedMatchesBudget?: number;
  goal?: GuaranteeGoal;
  recommendedTickets?: number;
  poolSize?: number;
  pickSize?: number;
  lang?: 'bn' | 'en';
}

export const SmartBudgetPanel: React.FC<SmartBudgetPanelProps> = ({
  budgetCount,
  totalTickets,
  onChangeBudget,
  onDownloadBudget,
  goal,
  recommendedTickets,
  lang = 'bn',
}) => {
  const isBn = lang === 'bn';

  return (
    <div className="bg-gradient-to-r from-[#161b22] via-[#1c1810] to-[#161b22] border-2 border-amber-500/60 rounded-xl p-5 mb-6 shadow-xl shadow-amber-950/20">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-neutral-800">
        <div className="flex items-start sm:items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-950/80 border border-amber-600/70 flex items-center justify-center shrink-0 shadow-md shadow-amber-900/40">
            <Wallet className="w-5 h-5 text-amber-400" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                {isBn ? 'ধাপ ২' : 'Step 2'}
              </span>
              <h3 className="text-base font-bold text-white tracking-tight">
                {isBn ? 'স্মার্ট বাজেট ও প্রায়োরিটি টিকিট নির্বাচন' : 'Smart Budget & Priority Ticket Selection'}
              </h3>
              <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-700/80">
                {isBn
                  ? `শীর্ষ ${budgetCount.toLocaleString()} / ${totalTickets.toLocaleString()} টিকিট`
                  : `Top ${budgetCount.toLocaleString()} / ${totalTickets.toLocaleString()} Tickets`}
              </span>
              {goal && (
                <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-700">
                  {isBn
                    ? `টার্গেট: ${goal.matchTier}-ম্যাচ (${goal.targetFrequency} বার)`
                    : `Target: ${goal.matchTier}-Match (${goal.targetFrequency}x)`}
                </span>
              )}
            </div>
            <p className="text-xs text-neutral-300 mt-0.5">
              {isBn
                ? 'টিকিটগুলো সর্বোচ্চ কভারেজ এন্ট্রপি অনুসারে ১ থেকে N পর্যন্ত সাজানো। আপনার বাজেট অনুযায়ী টিকিট সংখ্যা নির্ধারণ করুন।'
                : 'Tickets are sorted by maximum marginal coverage entropy #1 to #N. Choose your ticket budget.'}
            </p>
          </div>
        </div>

        {/* Download Top N Budget Button */}
        <button
          onClick={onDownloadBudget}
          className="self-start sm:self-auto flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-amber-600 to-amber-500 hover:from-amber-500 hover:to-amber-400 text-black font-semibold rounded-lg text-xs transition-all shadow-md shadow-amber-950/50 shrink-0 cursor-pointer"
        >
          <Download className="w-4 h-4" />
          <span>
            {isBn
              ? `শীর্ষ ${budgetCount.toLocaleString()} বাজেট টিকিট ডাউনলোড (CSV)`
              : `Download Top ${budgetCount.toLocaleString()} Budget Tickets (CSV)`}
          </span>
        </button>
      </div>

      {/* Target Goal Lock Banner inside Budget */}
      {goal && recommendedTickets && (
        <div className="mt-3.5 p-3 rounded-lg bg-[#141b24] border border-cyan-800/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-cyan-400 shrink-0" />
            <span className="text-neutral-300">
              {isBn ? 'সক্রিয় গ্যারান্টি টার্গেট: ' : 'Active Guarantee Target: '}
              <strong className="text-cyan-300">
                {goal.matchTier}-{isBn ? 'ম্যাচ কমপক্ষে ' : 'Match at least '}
                {goal.targetFrequency} {isBn ? 'বার' : goal.targetFrequency > 1 ? 'times' : 'time'}
              </strong>
              <span className="text-neutral-400 text-[11px] ml-1.5">
                {isBn
                  ? `(১০০% লক করতে প্রয়োজন ~${recommendedTickets.toLocaleString()} টি টিকিট)`
                  : `(Lock requires ~${recommendedTickets.toLocaleString()} tickets)`}
              </span>
            </span>
          </div>

          <div className="flex items-center gap-2">
            {budgetCount >= recommendedTickets ? (
              <span className="text-emerald-400 font-bold flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> {isBn ? 'গ্যারান্টি সক্রিয়' : 'Guarantee Active'}
              </span>
            ) : (
              <button
                type="button"
                onClick={() => onChangeBudget(recommendedTickets)}
                className="px-3 py-1 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-extrabold text-xs transition-colors cursor-pointer shadow-sm shadow-cyan-950/50"
              >
                {isBn
                  ? `বাজেট ${recommendedTickets.toLocaleString()} টিকিটে লক করুন`
                  : `Set Budget to ${recommendedTickets.toLocaleString()} tix (Lock Goal)`}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Unified Slider & Direct Number Input */}
      <div className="mt-4 pt-1 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono">
          <span className="text-neutral-400 flex items-center gap-1.5">
            <SlidersHorizontal className="w-3.5 h-3.5 text-amber-400" />
            <span>{isBn ? 'বাজেট সাইজ স্লাইডার ও সরাসরি সংখ্যা ইনপুট:' : 'Budget Size Slider & Direct Input:'}</span>
          </span>

          <div className="flex items-center gap-2">
            <span className="text-neutral-400">{isBn ? 'নির্বাচিত টিকিট:' : 'Selected Tickets:'}</span>
            <div className="flex items-center bg-[#101726] border border-amber-500/70 rounded-lg px-2 py-1">
              <Hash className="w-3.5 h-3.5 text-amber-400 mr-1" />
              <input
                type="number"
                min={1}
                max={totalTickets}
                value={budgetCount}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  if (val >= 1 && val <= totalTickets) {
                    onChangeBudget(val);
                  }
                }}
                className="w-20 bg-transparent text-amber-300 font-mono font-extrabold text-sm focus:outline-none text-right"
              />
              <span className="text-neutral-400 text-xs ml-1">/ {totalTickets.toLocaleString()}</span>
            </div>
            <span className="text-amber-400 font-bold">
              ({((budgetCount / totalTickets) * 100).toFixed(1)}%)
            </span>
          </div>
        </div>

        {/* Range Slider */}
        <input
          type="range"
          min={1}
          max={totalTickets}
          step={totalTickets > 500 ? 5 : 1}
          value={budgetCount}
          onChange={(e) => onChangeBudget(Number(e.target.value))}
          className="w-full h-2.5 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-amber-500 focus:outline-none"
        />

        <div className="flex justify-between text-[10px] font-mono text-neutral-500">
          <span>{isBn ? '১টি টিকিট (সর্বনিম্ন)' : '1 ticket (Minimum)'}</span>
          <span>{isBn ? `${Math.round(totalTickets / 2).toLocaleString()} টিকিট (৫০%)` : `${Math.round(totalTickets / 2).toLocaleString()} tickets (50%)`}</span>
          <span>{isBn ? `${totalTickets.toLocaleString()} টিকিট (সম্পূর্ণ হুইল)` : `${totalTickets.toLocaleString()} tickets (Full Wheel)`}</span>
        </div>
      </div>
    </div>
  );
};
