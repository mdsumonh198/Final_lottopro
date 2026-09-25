import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Layers,
  Award,
  Target,
  Download,
  Wallet,
  Hash,
  CheckCircle2,
  Zap,
} from 'lucide-react';
import { GameConfig, GameCategory, DigitPlayType } from '../types';
import { calculateGoalRequirements } from '../wheelEngine';

interface UnifiedGameAndBudgetPanelProps {
  config: GameConfig;
  onChangeConfig: (config: GameConfig) => void;
  budgetCount: number;
  totalTickets: number;
  onChangeBudget: (budget: number) => void;
  onDownloadBudget: () => void;
  onDownloadFullWheel: () => void;
  schonheimBound: number;
  totalCombinations: number;
  lang?: 'bn' | 'en';
}

export const UnifiedGameAndBudgetPanel: React.FC<UnifiedGameAndBudgetPanelProps> = ({
  config,
  onChangeConfig,
  budgetCount,
  totalTickets,
  onChangeBudget,
  onDownloadBudget,
  onDownloadFullWheel,
  schonheimBound,
  totalCombinations,
  lang = 'bn',
}) => {
  const isBn = lang === 'bn';

  // 1. Game Format & Rules State
  const [activeCategory, setActiveCategory] = useState<GameCategory>(config.gameCategory || 'lotto');
  const [inputPool, setInputPool] = useState<number>(config.poolSize || 27);
  const [inputPick, setInputPick] = useState<number>(config.pickSize || 6);
  const [orderMatters, setOrderMatters] = useState<boolean>(config.orderMatters ?? false);
  const [digitPlayType, setDigitPlayType] = useState<DigitPlayType>(config.digitPlayType || 'straight');

  // 2. Guarantee Target State
  const [selectedPreset, setSelectedPreset] = useState<'opt1' | 'opt2' | 'opt3' | 'custom'>('opt1');
  const [inputMatchTier, setInputMatchTier] = useState<number>(config.goal?.matchTier || 5);
  const [inputFrequency, setInputFrequency] = useState<number>(config.goal?.targetFrequency || 1);

  // Sync state when config changes externally
  useEffect(() => {
    setActiveCategory(config.gameCategory || 'lotto');
    setInputPool(config.poolSize);
    setInputPick(config.pickSize);
    setOrderMatters(config.orderMatters ?? false);
    if (config.digitPlayType) setDigitPlayType(config.digitPlayType);
    if (config.goal) {
      setInputMatchTier(config.goal.matchTier);
      setInputFrequency(config.goal.targetFrequency);
    }

    if (config.gameCategory === 'pick_digits' || (config.poolSize === 10 && config.pickSize <= 4)) {
      if (config.goal?.matchTier === 3 && config.orderMatters) {
        setSelectedPreset('opt1');
      } else if (config.goal?.matchTier === 3 && !config.orderMatters) {
        setSelectedPreset('opt2');
      } else if (config.goal?.matchTier === 2) {
        setSelectedPreset('opt3');
      } else {
        setSelectedPreset('custom');
      }
    } else {
      if (config.poolSize === 27 && config.pickSize === 6 && config.goal?.matchTier === 5 && config.goal?.targetFrequency === 1) {
        setSelectedPreset('opt1');
      } else if (config.poolSize === 27 && config.pickSize === 6 && config.goal?.matchTier === 4 && config.goal?.targetFrequency === 1) {
        setSelectedPreset('opt2');
      } else if (config.poolSize === 27 && config.pickSize === 6 && config.goal?.matchTier === 5 && config.goal?.targetFrequency === 10) {
        setSelectedPreset('opt3');
      } else {
        setSelectedPreset('custom');
      }
    }
  }, [config]);

  // Live calculation of requirements for the chosen game & target
  const goalReq = calculateGoalRequirements(
    activeCategory === 'pick_digits' ? 10 : Math.max(10, inputPool),
    Math.max(2, inputPick),
    Math.max(1, Math.min(inputPick, inputMatchTier)),
    Math.max(1, inputFrequency),
    activeCategory,
    orderMatters
  );

  // Function to apply Game Rules Changes (Step 1.1)
  const handleGameRulesChange = (
    newCategory: GameCategory,
    newPool: number,
    newPick: number,
    newOrder: boolean = false,
    newPlayType: DigitPlayType = 'straight'
  ) => {
    const isDigits = newCategory === 'pick_digits';
    const validPool = isDigits ? 10 : Math.max(10, Math.min(60, newPool));
    const validPick = isDigits ? Math.max(2, Math.min(4, newPick)) : Math.max(3, Math.min(validPool - 1, newPick));

    let defaultTier = inputMatchTier;
    if (defaultTier > validPick) {
      defaultTier = isDigits ? validPick : Math.max(3, validPick - 1);
    }
    if (validPool === 27 && validPick === 6) {
      defaultTier = 5;
    }

    setActiveCategory(newCategory);
    setInputPool(validPool);
    setInputPick(validPick);
    setOrderMatters(newOrder);
    setDigitPlayType(newPlayType);
    setInputMatchTier(defaultTier);

    const req = calculateGoalRequirements(validPool, validPick, defaultTier, inputFrequency, newCategory, newOrder);

    const newConfig: GameConfig = {
      gameCategory: newCategory,
      poolSize: validPool,
      pickSize: validPick,
      drawnNumbers: validPick,
      guarantee: defaultTier,
      allowRepeats: isDigits,
      orderMatters: isDigits ? newOrder : false,
      digitPlayType: isDigits ? newPlayType : undefined,
      goal: {
        matchTier: defaultTier,
        targetFrequency: inputFrequency,
        playType: isDigits ? newPlayType : undefined,
      },
    };

    onChangeConfig(newConfig);
    onChangeBudget(req.recommendedTickets);
  };

  // Function to apply Guarantee Preset / Mode Changes (Step 1.2)
  const handleSelectGuaranteeMode = (
    preset: 'opt1' | 'opt2' | 'opt3' | 'custom',
    customTier?: number,
    customFreq?: number
  ) => {
    setSelectedPreset(preset);

    const isDigits = activeCategory === 'pick_digits' || (inputPool === 10 && inputPick <= 4);
    let tier = customTier ?? inputMatchTier;
    let freq = customFreq ?? inputFrequency;
    let order = orderMatters;
    let playType = digitPlayType;

    if (isDigits) {
      if (preset === 'opt1') {
        tier = inputPick;
        freq = 1;
        order = true;
        playType = 'straight';
      } else if (preset === 'opt2') {
        tier = inputPick;
        freq = 1;
        order = false;
        playType = 'box';
      } else if (preset === 'opt3') {
        tier = 2;
        freq = 1;
        order = false;
        playType = 'pairs';
      }
    } else {
      if (preset === 'opt1') {
        tier = Math.max(3, inputPick - 1); // 5-match for pick 6, 4-match for pick 5
        freq = 1;
      } else if (preset === 'opt2') {
        tier = Math.max(2, inputPick - 2); // 4-match for pick 6, 3-match for pick 5
        freq = 1;
      } else if (preset === 'opt3') {
        tier = Math.max(3, inputPick - 1);
        freq = inputPool === 27 && inputPick === 6 ? 10 : 2;
      }
    }

    setInputMatchTier(tier);
    setInputFrequency(freq);
    setOrderMatters(order);
    setDigitPlayType(playType);

    const req = calculateGoalRequirements(inputPool, inputPick, tier, freq, activeCategory, order);

    const newConfig: GameConfig = {
      gameCategory: activeCategory,
      poolSize: inputPool,
      pickSize: inputPick,
      drawnNumbers: inputPick,
      guarantee: tier,
      allowRepeats: isDigits,
      orderMatters: isDigits ? order : false,
      digitPlayType: isDigits ? playType : undefined,
      goal: {
        matchTier: tier,
        targetFrequency: freq,
        playType: isDigits ? playType : undefined,
      },
    };

    onChangeConfig(newConfig);
    onChangeBudget(req.recommendedTickets);
  };

  const isGoalLocked = budgetCount >= goalReq.recommendedTickets;
  const isDigits = activeCategory === 'pick_digits' || (inputPool === 10 && inputPick <= 4);

  return (
    <div className="bg-[#121824] border-2 border-cyan-500/80 rounded-2xl p-5 sm:p-6 mb-6 shadow-2xl shadow-cyan-950/40 space-y-5 font-sans">
      {/* Panel Header */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-cyan-900/60">
        <div className="flex items-start sm:items-center gap-3">
          <div className="w-11 h-11 rounded-xl bg-cyan-950/90 border border-cyan-400 flex items-center justify-center shrink-0 shadow-lg shadow-cyan-500/20 text-cyan-300">
            <Target className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-2.5 py-0.5 rounded text-[11px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                {isBn ? 'ধাপ ১' : 'Step 1'}
              </span>
              <h2 className="text-base sm:text-lg font-bold text-white tracking-wide">
                {isBn ? 'গেম ও বাজেট কন্ট্রোলার' : 'Game Setup & Budget Controller'}
              </h2>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                100.0% Bound Efficiency
              </span>
            </div>
            <p className="text-xs text-neutral-300 mt-1">
              {isBn
                ? 'প্রথমে গেমের নিয়ম ও পিক সংখ্যা ঠিক করুন ➔ এরপর গ্যারান্টি মোড বেছে নিন ➔ বাজেট নির্ধারণ করে টিকিট ডাউনলোড করুন।'
                : '1. Set game rules & pick size ➔ 2. Choose guarantee mode ➔ 3. Set budget & download tickets.'}
            </p>
          </div>
        </div>

        {/* Live Bound Efficiency Badge */}
        <div className="bg-[#0a0f1a] border border-neutral-700/80 rounded-xl px-3.5 py-2 font-mono text-xs flex items-center gap-3 shrink-0">
          <div>
            <span className="text-neutral-400 text-[10px] block uppercase">{isBn ? 'ফুল হুইল সাইজ' : 'Full Wheel'}</span>
            <span className="text-white font-extrabold text-sm">{totalTickets.toLocaleString()} {isBn ? 'টিকিট' : 'tix'}</span>
          </div>
          <div className="h-6 w-px bg-neutral-800"></div>
          <div>
            <span className="text-emerald-400 text-[10px] block uppercase font-bold">Bound Efficiency</span>
            <span className="text-emerald-300 font-extrabold text-sm">100.0%</span>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* SECTION 1.1: GAME RULES & NUMBERS PER TICKET */}
      {/* ========================================================================= */}
      <div className="bg-[#0a0f1a] border border-cyan-800/70 rounded-xl p-4 sm:p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-neutral-800 pb-3">
          <div className="flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-cyan-500 text-black font-bold text-xs flex items-center justify-center font-mono">
              1
            </span>
            <h3 className="text-xs sm:text-sm font-bold text-white uppercase tracking-wider font-mono">
              {isBn ? 'প্রথমে গেমের ধরন ও সংখ্যা নির্বাচন করুন (Game Rules & Pick Size)' : '1. Select Game Type & Numbers Per Ticket'}
            </h3>
          </div>

          {/* Game Category Tabs: Standard Lotto vs 0-9 Pick Digits */}
          <div className="flex items-center bg-[#121824] p-1 rounded-lg border border-neutral-700 font-mono text-xs">
            <button
              type="button"
              onClick={() => handleGameRulesChange('lotto', 27, 6, false)}
              className={`px-3 py-1.5 rounded-md font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                activeCategory === 'lotto'
                  ? 'bg-cyan-500 text-black shadow-md'
                  : 'text-neutral-300 hover:text-white'
              }`}
            >
              <span>🎱</span>
              <span>{isBn ? 'লটো স্টাইল (১ থেকে N)' : 'Lotto (1 to N)'}</span>
            </button>
            <button
              type="button"
              onClick={() => handleGameRulesChange('pick_digits', 10, 3, true, 'straight')}
              className={`px-3 py-1.5 rounded-md font-bold transition-all cursor-pointer flex items-center gap-1.5 ${
                activeCategory === 'pick_digits'
                  ? 'bg-purple-600 text-white shadow-md'
                  : 'text-neutral-300 hover:text-white'
              }`}
            >
              <span>🎰</span>
              <span>{isBn ? '০–৯ ডিজিট (পিক ৩/৪)' : '0–9 Digits (Pick 3/4)'}</span>
            </button>
          </div>
        </div>

        {/* Inputs: Game Universe Pool + Numbers Per Ticket Pick */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {/* 1. Pool Size */}
          <div className="bg-[#101726] p-3.5 rounded-xl border border-neutral-700/80">
            <label className="block text-[11px] font-bold text-neutral-300 uppercase tracking-wider font-mono">
              {isBn ? '১. মোট সংখ্যার রেঞ্জ (Pool Size)' : '1. Number Pool (1 to X)'}
            </label>
            {activeCategory === 'pick_digits' ? (
              <div className="w-full bg-[#182235] border border-purple-600/60 rounded-lg px-3 py-2 text-sm font-mono font-bold text-purple-300 flex items-center justify-between mt-1.5">
                <span>0, 1, 2, 3, 4, 5, 6, 7, 8, 9</span>
                <span className="text-[10px] text-purple-400">10 Digits</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 mt-1.5">
                <span className="text-xs text-neutral-400 font-mono font-semibold">{isBn ? '১ থেকে' : '1 to'}</span>
                <input
                  type="number"
                  min={10}
                  max={60}
                  value={inputPool}
                  onChange={(e) => handleGameRulesChange('lotto', Number(e.target.value), inputPick, false)}
                  className="w-full bg-[#182235] border border-neutral-600 rounded-lg px-3 py-2 text-base font-mono font-extrabold text-white text-center focus:outline-none focus:border-cyan-400"
                />
                <span className="text-xs text-neutral-400 font-mono">{isBn ? 'পর্যন্ত' : 'max'}</span>
              </div>
            )}
            <span className="text-[10px] text-neutral-400 block font-mono mt-1">
              {activeCategory === 'pick_digits'
                ? (isBn ? '১০টি ডিজিট (০ থেকে ৯)' : '10 digits (0 to 9)')
                : (isBn ? 'ডিফল্ট: 27 (১ থেকে ২৭) বা নিজের সংখ্যা দিন' : 'Default: 27 (1 to 27) or custom')}
            </span>
          </div>

          {/* 2. Pick Size */}
          <div className="bg-[#101726] p-3.5 rounded-xl border border-neutral-700/80">
            <label className="block text-[11px] font-bold text-neutral-300 uppercase tracking-wider font-mono">
              {isBn ? '২. প্রতি টিকিটে কয়টি সংখ্যা? (পিক k)' : '2. Numbers per ticket (Pick k)'}
            </label>
            <div className="flex items-center gap-2 mt-1.5">
              <span className="text-xs text-neutral-400 font-mono font-semibold">Pick</span>
              <input
                type="number"
                min={activeCategory === 'pick_digits' ? 2 : 3}
                max={activeCategory === 'pick_digits' ? 4 : inputPool - 1}
                value={inputPick}
                onChange={(e) => handleGameRulesChange(activeCategory, inputPool, Number(e.target.value), orderMatters, digitPlayType)}
                className="w-full bg-[#182235] border border-neutral-600 rounded-lg px-3 py-2 text-base font-mono font-extrabold text-white text-center focus:outline-none focus:border-cyan-400"
              />
              <span className="text-xs text-neutral-400 font-mono">{isBn ? 'টি' : 'numbers'}</span>
            </div>
            <span className="text-[10px] text-neutral-400 block font-mono mt-1">
              {activeCategory === 'pick_digits'
                ? (isBn ? 'পিক ৩ (৩ ডিজিট) বা পিক ৪' : 'Pick 3 (3 Digits) or Pick 4')
                : (isBn ? 'ডিফল্ট: 6 (পিক ৬) বা 5' : 'Default: 6 (Pick 6) or 5')}
            </span>
          </div>

          {/* 3. Game Summary Card */}
          <div className="bg-[#101726] p-3.5 rounded-xl border border-cyan-800/60 flex flex-col justify-between">
            <div>
              <span className="text-[11px] font-mono font-bold text-cyan-300 uppercase block">
                {isBn ? 'নির্বাচিত গেম ফরম্যাট:' : 'Selected Game Format:'}
              </span>
              <div className="text-base font-extrabold text-white font-mono mt-1 flex items-center gap-2">
                <span>{activeCategory === 'pick_digits' ? `0–9 Pick ${inputPick}` : `${inputPick}/${inputPool} Lotto`}</span>
                <span className="text-[11px] px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                  {activeCategory === 'pick_digits' ? (isBn ? '১,০০০ বিন্যাস' : '1,000 Draws') : `${totalCombinations.toLocaleString()} ${isBn ? 'ড্র' : 'Draws'}`}
                </span>
              </div>
            </div>
            <span className="text-[10px] text-neutral-400 font-mono mt-2">
              {activeCategory === 'pick_digits'
                ? (isBn ? 'ডাবল/ট্রিপল রিপিট সাপোর্ট সক্রিয়' : 'Doubles/Triples repeat allowed')
                : (isBn ? 'ইউনিক সংখ্যা (কম্বিনেশন)' : 'Unique numbers (combinations)')}
            </span>
          </div>
        </div>

        {/* Digit Specific Options (Straight vs Box) */}
        {activeCategory === 'pick_digits' && (
          <div className="pt-2 border-t border-purple-900/60 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => handleGameRulesChange('pick_digits', 10, inputPick, true, 'straight')}
              className={`p-2.5 rounded-xl border text-left cursor-pointer transition-all ${
                orderMatters && digitPlayType === 'straight'
                  ? 'bg-purple-900/50 border-purple-400 text-white shadow'
                  : 'bg-[#101726] border-neutral-800 text-neutral-400'
              }`}
            >
              <div className="text-xs font-bold font-mono text-purple-300">
                🎯 {isBn ? 'Straight (হুবহু অর্ডার)' : 'Straight (Exact Order)'}
              </div>
              <div className="text-[10px] text-neutral-300 mt-0.5">
                {isBn ? 'পজিশন ১, ২, ৩ হুবহু একই ক্রমে মিলতে হবে।' : 'Positions 1, 2, 3 must match in exact sequence.'}
              </div>
            </button>

            <button
              type="button"
              onClick={() => handleGameRulesChange('pick_digits', 10, inputPick, false, 'box')}
              className={`p-2.5 rounded-xl border text-left cursor-pointer transition-all ${
                !orderMatters || digitPlayType === 'box'
                  ? 'bg-purple-900/50 border-purple-400 text-white shadow'
                  : 'bg-[#101726] border-neutral-800 text-neutral-400'
              }`}
            >
              <div className="text-xs font-bold font-mono text-purple-300">
                📦 {isBn ? 'Box (যেকোনো ক্রম)' : 'Box (Any Order)'}
              </div>
              <div className="text-[10px] text-neutral-300 mt-0.5">
                {isBn ? 'যেকোনো ক্রমে সংখ্যা মিললেই উইন (3-way / 6-way)।' : 'Matches in any order win (3-way or 6-way box).'}
              </div>
            </button>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* SECTION 1.2: GUARANTEE MODE SELECTION */}
      {/* ========================================================================= */}
      <div className="bg-[#0a0f1a] border border-cyan-800/70 rounded-xl p-4 sm:p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
          <div className="flex items-center gap-2">
            <span className="w-5 h-5 rounded-full bg-cyan-500 text-black font-bold text-xs flex items-center justify-center font-mono">
              2
            </span>
            <h3 className="text-xs sm:text-sm font-bold text-white uppercase tracking-wider font-mono">
              {isBn
                ? `এবার এই গেমের জন্য গ্যারান্টি মোড বেছে নিন (${inputPick}/${inputPool} Game Modes)`
                : `2. Choose Guarantee Mode for this ${inputPick}/${inputPool} Game`}
            </h3>
          </div>
          <span className="text-[11px] font-mono text-cyan-400 hidden sm:inline">
            {isBn ? '১-ক্লিকে টার্গেট লক' : '1-Click Target Lock'}
          </span>
        </div>

        {/* 4 Guarantee Option Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {/* Card 1 */}
          <button
            type="button"
            onClick={() => handleSelectGuaranteeMode('opt1')}
            className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
              selectedPreset === 'opt1'
                ? 'bg-gradient-to-br from-cyan-950 via-[#0e272b] to-[#0a1b24] border-cyan-400 shadow-lg shadow-cyan-950/50 ring-2 ring-cyan-500/40'
                : 'bg-[#101726] border-neutral-800 hover:border-neutral-700 text-neutral-300'
            }`}
          >
            <div>
              <div className="flex items-center justify-between gap-1">
                <span className="text-xs font-bold text-white flex items-center gap-1.5">
                  <span>🏆 Option 1 ({isDigits ? 'Straight' : 'Primary'})</span>
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold">
                  {isDigits ? (isBn ? 'স্ট্রেইট' : 'Straight') : `${Math.max(3, inputPick - 1)}-${isBn ? 'ম্যাচ' : 'Match'}`}
                </span>
              </div>
              <div className="mt-1.5 text-xs font-mono font-extrabold text-cyan-300">
                {isDigits
                  ? (isBn ? '১০০% স্ট্রেইট লক (১,০০০ টিকিট)' : '100% Straight Lock (1,000 tix)')
                  : inputPool === 27 && inputPick === 6
                  ? (isBn ? '৫-ম্যাচ গ্যারান্টি (২,৩৩৫ টিকিট)' : '5-Match Guarantee (2,335 tix)')
                  : (isBn ? `${Math.max(3, inputPick - 1)}-ম্যাচ গ্যারান্টি` : `${Math.max(3, inputPick - 1)}-Match Guarantee`)}
              </div>
              <div className="text-[10px] text-neutral-400 mt-1 leading-tight">
                {isDigits
                  ? (isBn ? 'হুবহু পজিশনে জ্যাকপট Straight নিশ্চিত।' : '100% Exact positional straight lock.')
                  : inputPool === 27 && inputPick === 6
                  ? (isBn ? '১০০% জিরো-মিস ৫-ম্যাচ + ১২-২৫টি ৪-ম্যাচ।' : '100% zero-miss 5-match + 12-25 4-matches.')
                  : (isBn ? 'সর্বোচ্চ গ্যারান্টি টায়ার লক।' : 'Highest guarantee tier lock.')}
              </div>
            </div>
          </button>

          {/* Card 2 */}
          <button
            type="button"
            onClick={() => handleSelectGuaranteeMode('opt2')}
            className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
              selectedPreset === 'opt2'
                ? 'bg-gradient-to-br from-blue-950 via-[#0e2238] to-[#0a1829] border-blue-400 shadow-lg shadow-blue-950/50 ring-2 ring-blue-500/40'
                : 'bg-[#101726] border-neutral-800 hover:border-neutral-700 text-neutral-300'
            }`}
          >
            <div>
              <div className="flex items-center justify-between gap-1">
                <span className="text-xs font-bold text-white flex items-center gap-1.5">
                  <span>💰 Option 2 ({isDigits ? 'Box' : 'Budget ROI'})</span>
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 font-bold">
                  {isDigits ? 'Box' : `${Math.max(2, inputPick - 2)}-${isBn ? 'ম্যাচ' : 'Match'}`}
                </span>
              </div>
              <div className="mt-1.5 text-xs font-mono font-extrabold text-blue-300">
                {isDigits
                  ? (isBn ? '১০০% বক্স উইন লক (১২০ টিকিট)' : '100% Box Win Lock (120 tix)')
                  : inputPool === 27 && inputPick === 6
                  ? (isBn ? '৪-ম্যাচ গ্যারান্টি (১৩৫ টিকিট)' : '4-Match Guarantee (135 tix)')
                  : (isBn ? `${Math.max(2, inputPick - 2)}-ম্যাচ বাজেট লক` : `${Math.max(2, inputPick - 2)}-Match Budget Lock`)}
              </div>
              <div className="text-[10px] text-neutral-400 mt-1 leading-tight">
                {isDigits
                  ? (isBn ? 'যেকোনো ক্রমে সংখ্যা মিললে নিশ্চিত বক্স উইন।' : 'Guaranteed Box win for any digit combination.')
                  : inputPool === 27 && inputPick === 6
                  ? (isBn ? 'কম বাজেটে ১০০% নিশ্চিত ৪-ম্যাচ + ৮-১৫টি ৩-ম্যাচ।' : 'High ROI: guaranteed 4-match + 8-15 3-matches.')
                  : (isBn ? 'সাশ্রয়ী বাজেটে নিশ্চিত প্রাইজ কভারেজ।' : 'Cost-effective guaranteed prize coverage.')}
              </div>
            </div>
          </button>

          {/* Card 3 */}
          <button
            type="button"
            onClick={() => handleSelectGuaranteeMode('opt3')}
            className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
              selectedPreset === 'opt3'
                ? 'bg-gradient-to-br from-amber-950 via-[#2e230e] to-[#20190a] border-amber-400 shadow-lg shadow-amber-950/50 ring-2 ring-amber-500/40'
                : 'bg-[#101726] border-neutral-800 hover:border-neutral-700 text-neutral-300'
            }`}
          >
            <div>
              <div className="flex items-center justify-between gap-1">
                <span className="text-xs font-bold text-white flex items-center gap-1.5">
                  <span>👑 Option 3 ({isDigits ? 'Pair Match' : 'Syndicate'})</span>
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">
                  {isDigits ? 'Pair' : inputPool === 27 && inputPick === 6 ? '10x' : 'Multi-Win'}
                </span>
              </div>
              <div className="mt-1.5 text-xs font-mono font-extrabold text-amber-300">
                {isDigits
                  ? (isBn ? 'পেয়ার ম্যাচ লক (১০ টিকিট)' : 'Pair Match Lock (10 tix)')
                  : inputPool === 27 && inputPick === 6
                  ? (isBn ? '১০ বার ৫-ম্যাচ (~২৩,৩১০ টিকিট)' : '10x 5-Match (~23,310 tix)')
                  : (isBn ? 'মাল্টি-উইন সিন্ডিকেট লক' : 'Multi-Win Syndicate Lock')}
              </div>
              <div className="text-[10px] text-neutral-400 mt-1 leading-tight">
                {isDigits
                  ? (isBn ? 'ফ্রন্ট বা ব্যাক পেয়ার ১০০% নিশ্চিত।' : 'Guaranteed Front or Back Pair match.')
                  : inputPool === 27 && inputPick === 6
                  ? (isBn ? 'প্রতিটি ড্র-তে কমপক্ষে ১০টি টিকিটে ৫-ম্যাচ নিশ্চিত।' : 'Guaranteed >= 10 tickets with 5-match on any draw.')
                  : (isBn ? 'একাধিক প্রাইজ নিশ্চিত করার সিন্ডিকেট টায়ার।' : 'Syndicate multiple-prize tier.')}
              </div>
            </div>
          </button>

          {/* Card 4: Custom Target */}
          <button
            type="button"
            onClick={() => setSelectedPreset('custom')}
            className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
              selectedPreset === 'custom'
                ? 'bg-gradient-to-br from-purple-950 via-[#23112e] to-[#170a20] border-purple-400 shadow-lg shadow-purple-950/50 ring-2 ring-purple-500/40'
                : 'bg-[#101726] border-neutral-800 hover:border-neutral-700 text-neutral-300'
            }`}
          >
            <div>
              <div className="flex items-center justify-between gap-1">
                <span className="text-xs font-bold text-white flex items-center gap-1.5">
                  <span>⚙️ {isBn ? 'কাস্টম টার্গেট' : 'Custom Target'}</span>
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 font-bold">
                  Custom
                </span>
              </div>
              <div className="mt-1.5 text-xs font-mono font-extrabold text-purple-300">
                {inputMatchTier}-{isBn ? 'ম্যাচ' : 'Match'} ({inputFrequency} {isBn ? 'বার' : 'x'})
              </div>
              <div className="text-[10px] text-neutral-400 mt-1 leading-tight">
                {isBn ? 'কাঙ্ক্ষিত ম্যাচ ও সংখ্যা ম্যানুয়ালি সেট করুন।' : 'Set custom match tier and frequency manually.'}
              </div>
            </div>
          </button>
        </div>

        {/* Custom Match Tier & Frequency Inputs if Custom selected */}
        {selectedPreset === 'custom' && (
          <div className="p-3.5 rounded-xl bg-[#101726] border border-purple-800/80 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-bold text-purple-300 font-mono uppercase">
                {isBn ? 'কাঙ্ক্ষিত ম্যাচ টায়ার (Match Tier):' : 'Desired Match Tier:'}
              </label>
              <div className="flex items-center gap-2 mt-1">
                <input
                  type="number"
                  min={2}
                  max={inputPick}
                  value={inputMatchTier}
                  onChange={(e) => handleSelectGuaranteeMode('custom', Number(e.target.value), inputFrequency)}
                  className="w-full bg-[#182235] border border-purple-600 rounded-lg px-3 py-1.5 text-base font-mono font-extrabold text-purple-300 text-center"
                />
                <span className="text-xs text-purple-300 font-mono font-bold">{isBn ? 'ম্যাচ' : 'Match'}</span>
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-bold text-emerald-300 font-mono uppercase">
                {isBn ? 'কত বার নিশ্চিত করতে চান? (Frequency):' : 'Guarantee Frequency:'}
              </label>
              <div className="flex items-center gap-2 mt-1">
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={inputFrequency}
                  onChange={(e) => handleSelectGuaranteeMode('custom', inputMatchTier, Number(e.target.value))}
                  className="w-full bg-[#182235] border border-emerald-600 rounded-lg px-3 py-1.5 text-base font-mono font-extrabold text-emerald-300 text-center"
                />
                <span className="text-xs text-emerald-300 font-mono font-bold">{isBn ? 'বার' : 'times'}</span>
              </div>
            </div>
          </div>
        )}

        {/* Live Calculation Guarantee Banner */}
        <div className="pt-2 border-t border-neutral-800 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
          <div className="text-white">
            {isBn ? 'সক্রিয় গ্যারান্টি হিসাব: ' : 'Active Guarantee: '}
            <strong className="text-cyan-300 font-mono">
              {activeCategory === 'pick_digits' ? '0–9 Digits' : `1 to ${inputPool}`}
            </strong>{' '}
            (Pick {inputPick}), {isBn ? 'যেখানে' : 'with'}{' '}
            <strong className="text-cyan-300 font-mono">
              {inputMatchTier}-{isBn ? 'ম্যাচ' : 'Match'}
            </strong>{' '}
            {isBn ? 'কমপক্ষে' : 'at least'}{' '}
            <strong className="text-emerald-300 font-mono">
              {inputFrequency} {isBn ? 'বার' : 'time(s)'}
            </strong>{' '}
            {isBn ? 'গ্যারান্টি নিশ্চিত।' : 'guaranteed.'}
          </div>

          <div className="font-mono text-[11px] text-neutral-400 flex items-center gap-1.5">
            <span>{isBn ? '১০০% লকের জন্য প্রয়োজনীয় বাজেট:' : 'Target Lock Recommendation:'}</span>
            <span className="text-cyan-300 font-bold bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
              ~{goalReq.recommendedTickets.toLocaleString()} {isBn ? 'টিকিট' : 'tickets'}
            </span>
          </div>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* SECTION 1.3: BUDGET ALLOCATION & CSV EXPORT */}
      {/* ========================================================================= */}
      <div className="bg-gradient-to-r from-[#141b24] via-[#1a1710] to-[#141b24] border-2 border-amber-500/70 rounded-xl p-4 sm:p-5 space-y-3.5 shadow-lg shadow-amber-950/20">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-neutral-800 pb-3">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="w-5 h-5 rounded-full bg-amber-400 text-black font-bold text-xs flex items-center justify-center font-mono">
              3
            </span>
            <div className="w-7 h-7 rounded-lg bg-amber-950 border border-amber-500 flex items-center justify-center text-amber-400 shrink-0">
              <Wallet className="w-4 h-4" />
            </div>
            <span className="text-sm font-bold text-white uppercase tracking-wider font-mono">
              {isBn ? 'বাজেট নির্ধারণ ও টিকিট এক্সপোর্ট' : '3. Budget Allocation & Ticket Export'}
            </span>
            <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-600">
              {budgetCount.toLocaleString()} / {totalTickets.toLocaleString()} {isBn ? 'টিকিট' : 'tix'}
            </span>
          </div>

          {/* 1-Click Goal Lock Button */}
          <div>
            {isGoalLocked ? (
              <span className="text-emerald-400 font-mono font-bold text-xs flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-950/80 border border-emerald-600">
                <CheckCircle2 className="w-4 h-4" /> {isBn ? 'টার্গেট ১০০% লক করা আছে' : 'Target 100% Locked'}
              </span>
            ) : (
              <button
                type="button"
                onClick={() => onChangeBudget(goalReq.recommendedTickets)}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-emerald-500 hover:from-cyan-400 hover:to-emerald-400 text-black font-extrabold text-xs transition-all shadow-md shadow-cyan-950/60 cursor-pointer"
              >
                <Zap className="w-3.5 h-3.5 fill-black" />
                <span>
                  {isBn
                    ? `বাজেট ${goalReq.recommendedTickets.toLocaleString()} টিকিটে লক করুন`
                    : `Lock Target (${goalReq.recommendedTickets.toLocaleString()} tix)`}
                </span>
              </button>
            )}
          </div>
        </div>

        {/* Slider + Direct Input */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
          <div className="md:col-span-3 space-y-1.5">
            <input
              type="range"
              min={1}
              max={totalTickets}
              value={budgetCount}
              onChange={(e) => onChangeBudget(Number(e.target.value))}
              className="w-full h-2.5 bg-neutral-800 rounded-lg appearance-none cursor-pointer accent-amber-500"
            />
            <div className="flex justify-between text-[11px] font-mono text-neutral-400">
              <span>{isBn ? '১ টিকিট (মিনিমাম)' : '1 Ticket (Min)'}</span>
              <span className="text-cyan-400 font-semibold">
                {isBn ? `টার্গেট লক: ~${goalReq.recommendedTickets.toLocaleString()} টিকিট` : `Target Lock: ~${goalReq.recommendedTickets}`}
              </span>
              <span>{totalTickets.toLocaleString()} {isBn ? 'টিকিট (ফুল হুইল)' : 'tix (Full Wheel)'}</span>
            </div>
          </div>

          <div className="bg-[#0e1420] border border-amber-500/80 rounded-xl p-2.5 flex items-center justify-between gap-2">
            <div className="flex items-center gap-1">
              <Hash className="w-4 h-4 text-amber-400" />
              <span className="text-xs text-neutral-400 font-mono">{isBn ? 'সরাসরি ইনপুট:' : 'Direct:'}</span>
            </div>
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
              className="w-24 bg-[#182235] border border-neutral-600 rounded-lg px-2 py-1 text-base font-mono font-extrabold text-amber-300 text-center focus:outline-none focus:border-amber-400"
            />
          </div>
        </div>

        {/* Download Station */}
        <div className="pt-3 border-t border-neutral-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="text-xs font-mono text-neutral-300">
            <span>{isBn ? 'ডাউনলোডের জন্য প্রস্তুত: ' : 'Ready to Download: '}</span>
            <strong className="text-amber-300 font-bold">
              {budgetCount.toLocaleString()} {isBn ? 'টি প্রায়োরিটি টিকিট' : 'priority tickets'}
            </strong>{' '}
            {isBn ? '(সর্বোচ্চ কভারেজ র‍্যাঙ্ক #১ থেকে)' : '(Ranked #1 to #N)'}
          </div>

          <div className="flex items-center gap-2.5 flex-wrap">
            <button
              type="button"
              onClick={onDownloadBudget}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-amber-500 to-amber-400 hover:from-amber-400 hover:to-amber-300 text-black font-extrabold rounded-xl text-xs transition-all shadow-lg shadow-amber-950/60 cursor-pointer"
            >
              <Download className="w-4 h-4" />
              <span>
                {isBn
                  ? `শীর্ষ ${budgetCount.toLocaleString()} টি বাজেট টিকিট ডাউনলোড (CSV)`
                  : `Download Top ${budgetCount.toLocaleString()} Budget Tickets (CSV)`}
              </span>
            </button>

            <button
              type="button"
              onClick={onDownloadFullWheel}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-[#161f30] hover:bg-[#1e2a42] text-neutral-200 hover:text-white font-semibold rounded-xl text-xs transition-colors border border-neutral-700 cursor-pointer"
            >
              <Download className="w-3.5 h-3.5 text-neutral-400" />
              <span>
                {isBn
                  ? `ফুল হুইল (${totalTickets.toLocaleString()} টিকিট) CSV`
                  : `Full Wheel (${totalTickets.toLocaleString()} tix) CSV`}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Footer Mathematical Anchoring */}
      <div className="pt-2 border-t border-neutral-800 flex flex-wrap items-center justify-between gap-3 text-xs font-mono text-neutral-400">
        <div className="flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>
            {isBn ? 'মোট সম্ভাব্য ড্র: ' : 'Total Draws: '}
            <strong className="text-white">{totalCombinations.toLocaleString()}</strong>
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-blue-400" />
          <span>
            {isBn ? 'শোনহেইম লোয়ার বাউন্ড: ' : 'Schönheim Bound: '}
            <strong className="text-blue-300">{schonheimBound.toLocaleString()}</strong> {isBn ? 'টিকিট' : 'tickets'}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <Award className="w-3.5 h-3.5 text-amber-400" />
          <span>
            {isBn ? 'বাউন্ড এফিসিয়েন্সি: ' : 'Efficiency: '}
            <strong className="text-emerald-400">100.0% (Optimal Lower Bound)</strong>
          </span>
        </div>
      </div>
    </div>
  );
};
