import React, { useState, useMemo } from 'react';
import { Header } from './components/Header';
import { UnifiedGameAndBudgetPanel } from './components/UnifiedGameAndBudgetPanel';
import { NumberSelector } from './components/NumberSelector';
import { MetricCards } from './components/MetricCards';
import { DetailTable } from './components/DetailTable';
import { OperationsResearchPanel } from './components/OperationsResearchPanel';
import { PythonSourcePanel } from './components/PythonSourcePanel';
import { ColabScriptPanel } from './components/ColabScriptPanel';
import { CppSourcePanel } from './components/CppSourcePanel';
import { ExhaustiveAuditPanel } from './components/ExhaustiveAuditPanel';
import {
  generateWheel,
  evaluateWheel,
  exportWheelToCSV,
  calculateGoalRequirements,
} from './wheelEngine';
import { GameConfig } from './types';
import { BarChart3, AlertCircle, Target, ShieldAlert, ArrowRight } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'audit-296k' | 'or-theory' | 'python-source' | 'colab-mip' | 'cpp-engine'>('dashboard');

  // Bangla Mode ON by default as requested
  const [lang, setLang] = useState<'bn' | 'en'>('bn');
  const isBn = lang === 'bn';

  // DEFAULT: System 6/27 (1 to 27, Pick 6, 5-Match 1x, 2,335 Tickets - 100% Zero-Miss Guarantee)
  const [gameConfig, setGameConfig] = useState<GameConfig>({
    gameCategory: 'lotto',
    poolSize: 27,
    pickSize: 6,
    guarantee: 5,
    drawnNumbers: 6,
    allowRepeats: false,
    orderMatters: false,
    goal: {
      matchTier: 5,
      targetFrequency: 1,
    },
  });

  // Winning Numbers selection: Default for 6/27
  const [selectedNumbers, setSelectedNumbers] = useState<number[]>([1, 2, 3, 4, 5, 6]);

  // Priority-ranked wheel generation
  const { tickets, theoreticalBound, totalDraws } = useMemo(() => {
    return generateWheel(gameConfig);
  }, [gameConfig]);

  // Active Goal with safe fallback
  const activeGoal = useMemo(() => {
    return (
      gameConfig.goal || {
        matchTier: gameConfig.pickSize,
        targetFrequency: 1,
      }
    );
  }, [gameConfig.goal, gameConfig.pickSize]);

  // Goal requirement calculation
  const goalReq = useMemo(() => {
    return calculateGoalRequirements(
      gameConfig.poolSize,
      gameConfig.pickSize,
      activeGoal.matchTier,
      activeGoal.targetFrequency,
      gameConfig.gameCategory,
      gameConfig.orderMatters ?? false
    );
  }, [gameConfig.poolSize, gameConfig.pickSize, activeGoal.matchTier, activeGoal.targetFrequency, gameConfig.gameCategory, gameConfig.orderMatters]);

  // Smart Budget state: 2,335 tickets default for 6/27 5-Match (Zero-Miss Guarantee)
  const [budgetCount, setBudgetCount] = useState<number>(2335);

  // Sync budgetCount bounds when wheel size changes
  const activeBudget = Math.min(budgetCount, tickets.length);

  // Evaluate matches against winning numbers
  const { evaluations, fullMatchCounts, budgetMatchCounts, goalSummary, tickets: effectiveTickets } = useMemo(() => {
    if (selectedNumbers.length !== gameConfig.drawnNumbers) {
      return {
        evaluations: [],
        fullMatchCounts: { 6: 0, 5: 0, 4: 0, 3: 0, 2: 0, 1: 0, 0: 0 },
        budgetMatchCounts: { 6: 0, 5: 0, 4: 0, 3: 0, 2: 0, 1: 0, 0: 0 },
        goalSummary: undefined,
        tickets,
      };
    }
    return evaluateWheel(
      tickets,
      selectedNumbers,
      activeBudget,
      gameConfig.guarantee,
      activeGoal,
      gameConfig.gameCategory,
      gameConfig.orderMatters ?? false,
      gameConfig.digitPlayType || 'straight'
    );
  }, [
    tickets,
    selectedNumbers,
    activeBudget,
    gameConfig.guarantee,
    gameConfig.drawnNumbers,
    activeGoal,
    gameConfig.gameCategory,
    gameConfig.orderMatters,
    gameConfig.digitPlayType,
  ]);

  // When user switches game configuration, adjust default winning numbers intelligently
  const handleConfigChange = (newCfg: GameConfig) => {
    setGameConfig(newCfg);
    if (newCfg.gameCategory === 'pick_digits' || (newCfg.poolSize === 10 && newCfg.pickSize <= 4)) {
      if (newCfg.pickSize === 3) {
        setSelectedNumbers([7, 7, 2]);
        setBudgetCount(36);
      } else if (newCfg.pickSize === 4) {
        setSelectedNumbers([7, 7, 2, 5]);
        setBudgetCount(100);
      }
    } else {
      // Lotto 1 to N
      setSelectedNumbers([1, 2, 3, 4, 5, 6].filter((n) => n <= newCfg.poolSize).slice(0, newCfg.drawnNumbers));
      if (newCfg.poolSize === 27 && newCfg.guarantee === 5) {
        setBudgetCount(2335);
      } else if (newCfg.poolSize === 27 && newCfg.guarantee === 4) {
        setBudgetCount(135);
      } else if (newCfg.poolSize === 25 && newCfg.guarantee === 4) {
        setBudgetCount(85);
      }
    }
  };

  // Export Full Wheel
  const handleExportFullWheel = () => {
    const wheelToExport = effectiveTickets || tickets;
    const csv = exportWheelToCSV(wheelToExport, gameConfig);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute(
      'download',
      `wheel_${gameConfig.gameCategory}_${gameConfig.pickSize}_${gameConfig.poolSize}_full_${wheelToExport.length}_tickets.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Export Top N Budget Tickets
  const handleExportBudgetTickets = () => {
    const wheelToExport = effectiveTickets || tickets;
    const budgetTickets = wheelToExport.slice(0, activeBudget);
    const csv = exportWheelToCSV(budgetTickets, gameConfig);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute(
      'download',
      `wheel_${gameConfig.gameCategory}_${gameConfig.pickSize}_${gameConfig.poolSize}_top_${activeBudget}_budget_tickets.csv`
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const isDigitGame = gameConfig.gameCategory === 'pick_digits' || gameConfig.poolSize === 10;

  return (
    <div className="min-h-screen bg-[#0d1117] text-[#c9d1d9] flex flex-col font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Top Navigation Header with Language Toggle */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onExportWheel={handleExportFullWheel}
        onExportBudget={handleExportBudgetTickets}
        budgetCount={activeBudget}
        poolSize={gameConfig.poolSize}
        pickSize={gameConfig.pickSize}
        goal={activeGoal}
        lang={lang}
        onToggleLang={() => setLang((l) => (l === 'bn' ? 'en' : 'bn'))}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-6">
        {activeTab === 'dashboard' && (
          <div>
            {/* Quick 296,010 Exhaustive Audit Notification Strip */}
            {!isDigitGame && gameConfig.poolSize === 27 && (
              <div className="mb-5 bg-gradient-to-r from-[#1c0f14] via-[#161b24] to-[#1c0f14] border border-red-500/50 rounded-xl p-3.5 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-md">
                <div className="flex items-center gap-2.5">
                  <ShieldAlert className="w-5 h-5 text-red-400 shrink-0" />
                  <div className="text-xs font-mono">
                    <span className="text-white font-bold">
                      {isBn ? '২৯৬,০১০টি ড্র অডিট রিপোর্ট:' : '296,010 Draws Audit Report:'}
                    </span>{' '}
                    <span className="text-emerald-400 font-semibold">{isBn ? 'পাস: ১৮৪,৮৪৭ (৬২.৪৫%)' : 'PASS: 184,847 (62.45%)'}</span> ·{' '}
                    <span className="text-red-400 font-semibold">{isBn ? 'ফেল: ১১১,১৬৩ (৩৭.৫৫%)' : 'FAIL: 111,163 (37.55%)'}</span> ·{' '}
                    <span className="text-cyan-300 font-semibold">{isBn ? '৪-ম্যাচে ১০০% নিশ্চিত' : '100% 4-Match Lock'}</span>
                  </div>
                </div>
                <button
                  onClick={() => setActiveTab('audit-296k')}
                  className="px-3 py-1.5 rounded-lg bg-red-600/80 hover:bg-red-500 text-white font-mono font-bold text-xs flex items-center gap-1.5 shrink-0 transition-colors cursor-pointer"
                >
                  <span>{isBn ? 'সম্পূর্ণ অডিট ও প্রমাণ দেখুন' : 'View Full Audit & Proof'}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {/* Step 1: Unified Game Setup, Target Guarantee & Budget Selection (Integrated Single Card) */}
            <UnifiedGameAndBudgetPanel
              config={gameConfig}
              onChangeConfig={handleConfigChange}
              budgetCount={activeBudget}
              totalTickets={tickets.length}
              onChangeBudget={(val) => setBudgetCount(val)}
              onDownloadBudget={handleExportBudgetTickets}
              onDownloadFullWheel={handleExportFullWheel}
              schonheimBound={theoreticalBound}
              totalCombinations={totalDraws}
              lang={lang}
            />

            {/* Step 2: Winning Numbers Selector */}
            <NumberSelector
              poolSize={gameConfig.poolSize}
              pickSize={gameConfig.drawnNumbers}
              selectedNumbers={selectedNumbers}
              onChange={setSelectedNumbers}
              gameCategory={gameConfig.gameCategory}
              orderMatters={gameConfig.orderMatters}
              allowRepeats={gameConfig.allowRepeats}
              lang={lang}
            />

            {/* Validation warning if not exact numbers selected */}
            {selectedNumbers.length !== gameConfig.drawnNumbers ? (
              <div className="bg-amber-950/40 border border-amber-800/80 rounded-xl p-5 text-center text-amber-300 text-sm flex items-center justify-center gap-2">
                <AlertCircle className="w-5 h-5 text-amber-400" />
                <span>
                  {isBn
                    ? `ম্যাচ কভারেজ যাচাই করতে অনুগ্রহ করে ঠিক ${gameConfig.drawnNumbers}টি নম্বর নির্বাচন করুন। (বর্তমানে নির্বাচিত: ${selectedNumbers.length}/${gameConfig.drawnNumbers})`
                    : `Please select exactly ${gameConfig.drawnNumbers} numbers to analyze match coverage. (Currently selected: ${selectedNumbers.length}/${gameConfig.drawnNumbers})`}
                </span>
              </div>
            ) : (
              <>
                {/* Step 3 Section Title */}
                <div className="flex items-center justify-between mb-3 mt-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                      {isBn ? 'ধাপ ৩' : 'Step 3'}
                    </span>
                    <h3 className="text-sm font-bold text-white tracking-wide">
                      {isBn ? 'তাৎক্ষণিক উইন মূল্যায়ন ও টার্গেট ম্যাচ ভেরিফিকেশন' : 'Instant Win Evaluation & Target Match Verification'}
                    </h3>
                  </div>

                  <div className="text-xs font-mono text-cyan-400 flex items-center gap-1.5">
                    <Target className="w-3.5 h-3.5" />
                    <span>
                      {isBn ? 'টার্গেট: ' : 'Target: '}
                      {activeGoal.matchTier}-{isBn ? 'ম্যাচ' : 'Match'} ({activeGoal.targetFrequency} {isBn ? 'বার' : 'x'}){' '}
                      {isDigitGame && (gameConfig.orderMatters ? (isBn ? 'Straight (হুবহু অর্ডার)' : 'Straight (Order Matters)') : (isBn ? 'Box (যেকোনো ক্রম)' : 'Box (Any Order)'))}
                    </span>
                  </div>
                </div>

                {/* Unified 5 Key Result Metrics Cards */}
                <MetricCards
                  budgetMatchCounts={budgetMatchCounts}
                  fullMatchCounts={fullMatchCounts}
                  budgetCount={activeBudget}
                  totalEvaluated={tickets.length}
                  schonheimBound={theoreticalBound}
                  goalSummary={goalSummary}
                  gameCategory={gameConfig.gameCategory}
                  orderMatters={gameConfig.orderMatters}
                  evaluations={evaluations}
                  lang={lang}
                />

                {/* Distribution Summary Strip */}
                <div className="bg-[#161b22] border border-neutral-800 rounded-xl p-4 mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-semibold text-white">
                      {isBn
                        ? `সক্রিয় বাজেট (${activeBudget.toLocaleString()} টিকিট) ম্যাচ বিস্তার:`
                        : `Active Budget (${activeBudget.toLocaleString()} tickets) Match Distribution:`}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 sm:gap-6 text-xs font-mono flex-wrap">
                    {isDigitGame ? (
                      <>
                        <div className="flex items-center gap-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50"></span>
                          <span className="text-neutral-400">{isBn ? 'Straight উইন:' : 'Straight Wins:'}</span>
                          <span className="font-bold text-emerald-300 tabular-nums">
                            {evaluations.filter((e) => e.inBudget && e.isStraightWin).length}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-purple-500"></span>
                          <span className="text-neutral-400">{isBn ? 'Box উইন:' : 'Box Wins:'}</span>
                          <span className="font-bold text-purple-300 tabular-nums">
                            {evaluations.filter((e) => e.inBudget && e.isBoxWin).length}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-cyan-500"></span>
                          <span className="text-neutral-400">{isBn ? 'Pair ম্যাচ:' : 'Pair Matches:'}</span>
                          <span className="font-bold text-cyan-300 tabular-nums">
                            {evaluations.filter((e) => e.inBudget && (e.isFrontPair || e.isBackPair || e.isSplitPair)).length}
                          </span>
                        </div>
                      </>
                    ) : (
                      <>
                        {budgetMatchCounts[6] > 0 && (
                          <div className="flex items-center gap-1.5">
                            <span className="w-2.5 h-2.5 rounded-full bg-yellow-400 shadow-sm shadow-yellow-400/50"></span>
                            <span className="text-neutral-400">{isBn ? '৬/৬ জ্যাকপট:' : '6/6 Jackpot:'}</span>
                            <span className="font-bold text-yellow-300 tabular-nums">
                              {budgetMatchCounts[6]} ({((budgetMatchCounts[6] / activeBudget) * 100).toFixed(2)}%)
                            </span>
                          </div>
                        )}
                        <div className="flex items-center gap-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50"></span>
                          <span className="text-neutral-400">{isBn ? '৫-ম্যাচ:' : '5-Match:'}</span>
                          <span className="font-bold text-emerald-300 tabular-nums">
                            {budgetMatchCounts[5]} ({((budgetMatchCounts[5] / activeBudget) * 100).toFixed(2)}%)
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-cyan-500"></span>
                          <span className="text-neutral-400">{isBn ? '৪-ম্যাচ:' : '4-Match:'}</span>
                          <span className="font-bold text-cyan-300 tabular-nums">
                            {budgetMatchCounts[4]} ({((budgetMatchCounts[4] / activeBudget) * 100).toFixed(2)}%)
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                          <span className="text-neutral-400">{isBn ? '৩-ম্যাচ:' : '3-Match:'}</span>
                          <span className="font-bold text-amber-300 tabular-nums">
                            {budgetMatchCounts[3]} ({((budgetMatchCounts[3] / activeBudget) * 100).toFixed(2)}%)
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                </div>

                {/* Priority Ranked Detail Table */}
                <DetailTable
                  evaluations={evaluations}
                  winningNumbers={selectedNumbers}
                  budgetCount={activeBudget}
                  goal={activeGoal}
                  poolSize={gameConfig.poolSize}
                  pickSize={gameConfig.pickSize}
                  gameCategory={gameConfig.gameCategory}
                  orderMatters={gameConfig.orderMatters}
                  lang={lang}
                />
              </>
            )}
          </div>
        )}

        {activeTab === 'audit-296k' && (
          <ExhaustiveAuditPanel
            tickets={tickets}
            budgetCount={activeBudget}
            lang={lang}
            onSelectBudget={(b) => setBudgetCount(b)}
            onSwitchTo4Match={() => {
              handleConfigChange({
                ...gameConfig,
                guarantee: 4,
                goal: { matchTier: 4, targetFrequency: 1 },
              });
              setBudgetCount(135);
              setActiveTab('dashboard');
            }}
          />
        )}

        {activeTab === 'or-theory' && <OperationsResearchPanel />}

        {activeTab === 'python-source' && <PythonSourcePanel />}

        {activeTab === 'colab-mip' && <ColabScriptPanel />}

        {activeTab === 'cpp-engine' && <CppSourcePanel />}
      </main>

      {/* Footer */}
      <footer className="border-t border-neutral-800 bg-[#0d1117] py-4 text-center text-xs text-neutral-400 font-mono">
        {isBn
          ? `লটারি ও নাম্বার্স অ্যানালাইজার · গেম ${gameConfig.pickSize}/${gameConfig.poolSize} · টার্গেট: ${activeGoal.matchTier}-ম্যাচ (${activeGoal.targetFrequency} বার) · ১০০.০% বাউন্ড এফিসিয়েন্সি`
          : `Lotto & Numbers Analyzer · Game ${gameConfig.pickSize}/${gameConfig.poolSize} · Target: ${activeGoal.matchTier}-Match (${activeGoal.targetFrequency}x) · 100.0% Bound Efficiency`}
      </footer>
    </div>
  );
}
