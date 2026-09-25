import React, { useState, useMemo } from 'react';
import { TicketEvaluation, GuaranteeGoal, GameCategory } from '../types';
import { Search, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import { exportEvaluationsToCSV } from '../wheelEngine';

interface DetailTableProps {
  evaluations: TicketEvaluation[];
  winningNumbers: number[];
  budgetCount: number;
  goal?: GuaranteeGoal;
  poolSize?: number;
  pickSize?: number;
  gameCategory?: GameCategory;
  orderMatters?: boolean;
  lang?: 'bn' | 'en';
}

export const DetailTable: React.FC<DetailTableProps> = ({
  evaluations,
  winningNumbers,
  budgetCount,
  goal,
  poolSize = 25,
  pickSize = 6,
  gameCategory = 'lotto',
  orderMatters = false,
  lang = 'bn',
}) => {
  const isBn = lang === 'bn';
  const isDigitGame = gameCategory === 'pick_digits' || poolSize === 10 || pickSize <= 4;
  const [scopeFilter, setScopeFilter] = useState<'budget' | 'full'>('budget');
  const [tierFilter, setTierFilter] = useState<'goal-only' | 'straight-only' | 'box-only' | 'pairs-only' | 'all-winning' | 'all'>('all-winning');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(25);

  const targetTier = goal?.matchTier || (isDigitGame ? 3 : 4);

  const filtered = useMemo(() => {
    let result = evaluations;

    // Scope filter (Active Budget vs Full Wheel)
    if (scopeFilter === 'budget') {
      result = result.filter((e) => e.inBudget);
    }

    // Match tier filter
    if (tierFilter === 'goal-only') {
      result = result.filter((e) => e.meetsGoal || e.matches >= targetTier);
    } else if (tierFilter === 'straight-only') {
      result = result.filter((e) => e.isStraightWin);
    } else if (tierFilter === 'box-only') {
      result = result.filter((e) => e.isBoxWin);
    } else if (tierFilter === 'pairs-only') {
      result = result.filter((e) => e.isFrontPair || e.isBackPair || e.isSplitPair);
    } else if (tierFilter === 'all-winning') {
      if (isDigitGame) {
        result = result.filter((e) => e.matches >= 2 || e.isStraightWin || e.isBoxWin || e.isFrontPair || e.isBackPair);
      } else {
        result = result.filter((e) => e.matches >= 3);
      }
    }

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.trim().toLowerCase();
      result = result.filter((e) => {
        const rankMatch = String(e.priorityRank).includes(q) || `#${e.priorityRank}`.includes(q);
        const idMatch = e.id.toLowerCase().includes(q);
        const numMatch = e.numbers.some((n) => String(n) === q || String(n).padStart(2, '0') === q);
        const joinedMatch = e.numbers.join('').includes(q) || e.numbers.join('-').includes(q);
        return rankMatch || idMatch || numMatch || joinedMatch;
      });
    }

    return [...result].sort((a, b) => a.priorityRank - b.priorityRank);
  }, [evaluations, scopeFilter, tierFilter, searchQuery, targetTier, isDigitGame]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const validPage = Math.min(currentPage, totalPages);
  const startIndex = (validPage - 1) * pageSize;
  const pageItems = filtered.slice(startIndex, startIndex + pageSize);

  const handleDownloadFiltered = () => {
    const csvData = exportEvaluationsToCSV(filtered);
    const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `lottery_evaluation_${gameCategory}_${scopeFilter}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="bg-[#161b22] border border-neutral-800 rounded-xl overflow-hidden shadow-xl mb-8 font-sans">
      {/* Controls Bar */}
      <div className="p-4 sm:p-5 border-b border-neutral-800 flex flex-col gap-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2 flex-wrap">
              <span>{isBn ? 'প্রায়োরিটি র‍্যাঙ্কভিত্তিক মূল্যায়ন টেবিল' : 'Priority-Ranked Match Evaluation Table'}</span>
              <span className="text-xs font-mono font-normal px-2 py-0.5 rounded bg-neutral-800 text-neutral-300 border border-neutral-700">
                {filtered.length.toLocaleString()} {isBn ? 'টি টিকিট' : 'tickets'}
              </span>
              {goal && (
                <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-700">
                  {isBn ? `টার্গেট: ${goal.matchTier}-ম্যাচ (${goal.targetFrequency} বার)` : `Target: ${goal.matchTier}-Match (${goal.targetFrequency}x)`}
                </span>
              )}
            </h3>
            <p className="text-xs text-neutral-400 mt-0.5">
              {isBn
                ? 'সর্বোচ্চ এন্ট্রপি কভারেজ র‍্যাঙ্ক (#১ থেকে শুরু করে) অনুযায়ী টিকিট এবং তাদের উইনিং স্ট্যাটাস।'
                : 'Ranked by marginal coverage entropy #1 to #N with match statuses.'}
            </p>
          </div>

          <button
            onClick={handleDownloadFiltered}
            className="self-start sm:self-auto flex items-center gap-1.5 px-3 py-1.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 hover:text-white rounded-lg text-xs font-medium transition-colors border border-neutral-700 shrink-0 cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-cyan-400" />
            <span>{isBn ? 'টেবিল এক্সপোর্ট (CSV)' : 'Export Table (CSV)'}</span>
          </button>
        </div>

        {/* Filters Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {/* Scope Filter */}
          <div>
            <label className="block text-[11px] font-semibold text-neutral-400 uppercase tracking-wider mb-1 font-mono">
              {isBn ? 'প্রদর্শনের পরিধি' : 'Display Scope'}
            </label>
            <select
              value={scopeFilter}
              onChange={(e) => {
                setScopeFilter(e.target.value as any);
                setCurrentPage(1);
              }}
              className="w-full bg-[#0d1117] border border-neutral-700 rounded-lg px-3 py-1.5 text-xs text-neutral-200 focus:outline-none focus:border-amber-500"
            >
              <option value="budget">
                {isBn ? `শীর্ষ ${budgetCount.toLocaleString()} বাজেট টিকিট` : `Top ${budgetCount.toLocaleString()} Budget Tickets`}
              </option>
              <option value="full">
                {isBn ? `সম্পূর্ণ হুইল (${evaluations.length.toLocaleString()} টিকিট)` : `Full Wheel (${evaluations.length.toLocaleString()} Tickets)`}
              </option>
            </select>
          </div>

          {/* Tier Filter */}
          <div>
            <label className="block text-[11px] font-semibold text-neutral-400 uppercase tracking-wider mb-1 font-mono">
              {isBn ? 'প্রাইজ / ম্যাচ ফিল্টার' : 'Prize / Match Filter'}
            </label>
            <select
              value={tierFilter}
              onChange={(e) => {
                setTierFilter(e.target.value as any);
                setCurrentPage(1);
              }}
              className="w-full bg-[#0d1117] border border-neutral-700 rounded-lg px-3 py-1.5 text-xs text-neutral-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="goal-only">
                {isBn ? `🎯 টার্গেট ম্যাচ শুধুমাত্র (${targetTier}+ ম্যাচ)` : `🎯 Goal Matches Only (${targetTier}+ Matches)`}
              </option>
              {isDigitGame ? (
                <>
                  <option value="straight-only">{isBn ? '👑 Straight উইন (হুবহু অর্ডার)' : '👑 Straight Wins (Exact Order)'}</option>
                  <option value="box-only">{isBn ? '📦 Box উইন (যেকোনো ক্রম)' : '📦 Box Wins (Any Order)'}</option>
                  <option value="pairs-only">{isBn ? '⚡ Pair ম্যাচ (Front/Back)' : '⚡ Pair Matches (Front/Back)'}</option>
                  <option value="all-winning">{isBn ? 'সব উইনিং টিকিট' : 'All Winning Tickets'}</option>
                </>
              ) : (
                <option value="all-winning">{isBn ? 'সব উইনিং টিকিট (৩+ ম্যাচ)' : 'All Winning Tickets (3+ Matches)'}</option>
              )}
              <option value="all">{isBn ? 'সব টিকিট' : 'All Tickets'}</option>
            </select>
          </div>

          {/* Search Box */}
          <div>
            <label className="block text-[11px] font-semibold text-neutral-400 uppercase tracking-wider mb-1 font-mono">
              {isBn ? 'অনুসন্ধান (Search)' : 'Search'}
            </label>
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-neutral-500 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                placeholder={isBn ? 'র‍্যাঙ্ক (#1) বা টিকিট নম্বর দিয়ে খুঁজুন...' : 'Search Rank, TK-ID, or Number...'}
                className="w-full bg-[#0d1117] border border-neutral-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Table Element */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-neutral-300">
          <thead className="bg-[#0d1117] border-b border-neutral-800 text-neutral-400 font-mono uppercase text-[11px]">
            <tr>
              <th className="py-3 px-4 font-semibold">{isBn ? 'প্রায়োরিটি র‍্যাঙ্ক' : 'Priority Rank'}</th>
              <th className="py-3 px-4 font-semibold">{isBn ? 'টিকিট আইডি' : 'Ticket ID'}</th>
              <th className="py-3 px-4 font-semibold">
                {isDigitGame ? (isBn ? 'ডিজিট স্লট (১, ২, ৩)' : 'Digits (1, 2, 3)') : (isBn ? 'টিকিট নম্বর' : 'Ticket Numbers')}
              </th>
              <th className="py-3 px-4 font-semibold text-center">{isBn ? 'ম্যাচ' : 'Matches'}</th>
              <th className="py-3 px-4 font-semibold">{isBn ? 'স্ট্যাটাস / প্রাইজ টায়ার' : 'Status / Prize Tier'}</th>
              <th className="py-3 px-4 font-semibold">
                {isDigitGame ? (isBn ? 'পজিশনাল মিল' : 'Positional Breakdown') : (isBn ? 'মিলে যাওয়া সংখ্যা' : 'Matched Numbers')}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-800/80 font-mono">
            {pageItems.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-neutral-500 italic">
                  {isBn ? 'এই ফিল্টারে কোনো টিকিট পাওয়া যায়নি।' : 'No tickets matched the selected criteria.'}
                </td>
              </tr>
            ) : (
              pageItems.map((item) => {
                const isStraight = item.isStraightWin;
                const isBox = item.isBoxWin;
                const isPair = item.isFrontPair || item.isBackPair || item.isSplitPair;

                return (
                  <tr
                    key={item.id}
                    className={`hover:bg-neutral-800/40 transition-colors ${
                      isStraight
                        ? 'bg-emerald-950/30'
                        : isBox
                        ? 'bg-purple-950/20'
                        : isPair
                        ? 'bg-cyan-950/20'
                        : ''
                    }`}
                  >
                    {/* Priority Rank */}
                    <td className="py-3 px-4">
                      <span className="inline-flex items-center px-2 py-0.5 rounded font-mono font-bold text-xs bg-[#21262d] text-neutral-200 border border-neutral-700">
                        #{item.priorityRank}
                      </span>
                    </td>

                    {/* Ticket ID & Budget Badge */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="font-semibold text-white">{item.id}</span>
                        {item.inBudget && (
                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-950/80 text-amber-300 border border-amber-800">
                            {isBn ? 'বাজেট' : 'Budget'}
                          </span>
                        )}
                        {item.meetsGoal && (
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-700 font-bold">
                            {isBn ? '🎯 টার্গেট পূরণ' : '🎯 Goal Met'}
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Digits Display */}
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1.5">
                        {item.numbers.map((n, idx) => {
                          const isExactPosMatch = isDigitGame && winningNumbers[idx] === n;
                          const isAnyMatch = !isDigitGame && winningNumbers.includes(n);

                          return (
                            <div key={`${n}-${idx}`} className="flex flex-col items-center">
                              <span
                                className={`inline-flex items-center justify-center ${
                                  isDigitGame ? 'w-7 h-7 text-sm' : 'w-6 h-6 text-[11px]'
                                } rounded font-extrabold ${
                                  isExactPosMatch
                                    ? 'bg-emerald-500 text-black shadow-md shadow-emerald-500/50 ring-1 ring-emerald-300'
                                    : isAnyMatch
                                    ? 'bg-cyan-600 text-white'
                                    : 'bg-[#21262d] text-neutral-400'
                                }`}
                              >
                                {isDigitGame ? n : String(n).padStart(2, '0')}
                              </span>
                              {isDigitGame && (
                                <span className="text-[8px] text-neutral-500 font-mono mt-0.5">
                                  p{idx + 1}
                                </span>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </td>

                    {/* Matches Count */}
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`inline-block px-2.5 py-1 rounded font-extrabold text-xs ${
                          isStraight
                            ? 'bg-emerald-500 text-black'
                            : isBox
                            ? 'bg-purple-500 text-white'
                            : item.matches >= 2
                            ? 'bg-cyan-500 text-black'
                            : 'bg-neutral-800 text-neutral-400'
                        }`}
                      >
                        {item.matches}
                      </span>
                    </td>

                    {/* Status / Prize Tier */}
                    <td className="py-3 px-4">
                      {isDigitGame ? (
                        isStraight ? (
                          <span className="text-emerald-400 font-bold">👑 Straight Win</span>
                        ) : isBox ? (
                          <span className="text-purple-300 font-bold">📦 Box Win</span>
                        ) : item.isFrontPair ? (
                          <span className="text-cyan-400 font-semibold">⚡ Front Pair</span>
                        ) : item.isBackPair ? (
                          <span className="text-cyan-400 font-semibold">⚡ Back Pair</span>
                        ) : item.isSplitPair ? (
                          <span className="text-cyan-400 font-semibold">⚡ Split Pair</span>
                        ) : item.exactPositionalMatches === 1 ? (
                          <span className="text-neutral-400">{isBn ? '১ পজিশন মিল' : '1 Position Match'}</span>
                        ) : (
                          <span className="text-neutral-500">{isBn ? 'কোনো মিল নেই' : 'No Match'}</span>
                        )
                      ) : item.matches === 6 ? (
                        <span className="text-yellow-400 font-bold">👑 ৬/৬ জ্যাকপট</span>
                      ) : item.matches === 5 ? (
                        <span className="text-emerald-400 font-bold">⭐ ৫-ম্যাচ</span>
                      ) : item.matches === 4 ? (
                        <span className="text-cyan-400 font-semibold">🔹 ৪-ম্যাচ</span>
                      ) : item.matches === 3 ? (
                        <span className="text-amber-400 font-medium">🔸 ৩-ম্যাচ</span>
                      ) : (
                        <span className="text-neutral-500">{item.matches}-{isBn ? 'ম্যাচ' : 'Match'}</span>
                      )}
                    </td>

                    {/* Breakdown */}
                    <td className="py-3 px-4">
                      {isDigitGame ? (
                        <div className="flex items-center gap-1.5 flex-wrap text-[11px]">
                          {item.positionMatchFlags?.map((flag, idx) => (
                            <span
                              key={idx}
                              className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                                flag
                                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                                  : 'bg-neutral-800 text-neutral-500'
                              }`}
                            >
                              p{idx + 1}: {flag ? (isBn ? 'মিল' : 'YES') : '—'}
                            </span>
                          ))}
                        </div>
                      ) : item.matchedDigits.length > 0 ? (
                        <span className="text-cyan-400">
                          {item.matchedDigits.map((n) => String(n).padStart(2, '0')).join(' · ')}
                        </span>
                      ) : (
                        <span className="text-neutral-500">—</span>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-4 border-t border-neutral-800 bg-[#0d1117] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-neutral-400">
        <div className="flex items-center gap-2">
          <span>{isBn ? 'প্রতি পেজে রো:' : 'Rows per page:'}</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="bg-[#161b22] border border-neutral-700 rounded px-2 py-1 text-xs text-neutral-200"
          >
            <option value={15}>15</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
          <span className="ml-2">
            {isBn
              ? `প্রদর্শিত ${Math.min(startIndex + 1, filtered.length)} থেকে ${Math.min(startIndex + pageSize, filtered.length)} (মোট ${filtered.length.toLocaleString()})`
              : `Showing ${Math.min(startIndex + 1, filtered.length)} to ${Math.min(startIndex + pageSize, filtered.length)} of ${filtered.length.toLocaleString()}`}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={validPage === 1}
            className="p-1.5 rounded bg-neutral-800 hover:bg-neutral-700 disabled:opacity-40 disabled:cursor-not-allowed text-neutral-200 cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="font-mono text-neutral-300">
            {isBn ? `পেজ ${validPage} এর ${totalPages}` : `Page ${validPage} of ${totalPages}`}
          </span>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={validPage === totalPages}
            className="p-1.5 rounded bg-neutral-800 hover:bg-neutral-700 disabled:opacity-40 disabled:cursor-not-allowed text-neutral-200 cursor-pointer"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
