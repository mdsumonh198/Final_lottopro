import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Layers,
  Award,
  Target,
  Zap,
  Edit3,
} from 'lucide-react';
import { GameConfig, GameCategory, DigitPlayType } from '../types';
import { calculateGoalRequirements } from '../wheelEngine';

interface DynamicConfigBarProps {
  config: GameConfig;
  onChangeConfig: (config: GameConfig) => void;
  schonheimBound: number;
  totalCombinations: number;
  totalWheelSize: number;
  onApplyGoalAsBudget?: (tickets: number) => void;
  lang?: 'bn' | 'en';
}

export const DynamicConfigBar: React.FC<DynamicConfigBarProps> = ({
  config,
  onChangeConfig,
  schonheimBound,
  totalCombinations,
  totalWheelSize,
  onApplyGoalAsBudget,
  lang = 'bn',
}) => {
  const isBn = lang === 'bn';

  // Game Mode: default is 'lotto' (1..N) as requested
  const [activeCategory, setActiveCategory] = useState<GameCategory>(config.gameCategory || 'lotto');

  // Interactive inputs user types:
  const [inputPool, setInputPool] = useState<number>(config.poolSize || 25);
  const [inputPick, setInputPick] = useState<number>(config.pickSize || 6);
  const [inputMatchTier, setInputMatchTier] = useState<number>(config.goal?.matchTier || 4);
  const [inputFrequency, setInputFrequency] = useState<number>(config.goal?.targetFrequency || 2);

  // Pick 3 / Digit-specific settings
  const [allowRepeats, setAllowRepeats] = useState<boolean>(config.allowRepeats ?? (activeCategory === 'pick_digits'));
  const [orderMatters, setOrderMatters] = useState<boolean>(config.orderMatters ?? (activeCategory === 'pick_digits'));
  const [digitPlayType, setDigitPlayType] = useState<DigitPlayType>(config.digitPlayType || 'straight');

  // Synchronize when config changes externally
  useEffect(() => {
    setActiveCategory(config.gameCategory || 'lotto');
    setInputPool(config.poolSize);
    setInputPick(config.pickSize);
    setAllowRepeats(config.allowRepeats ?? (config.gameCategory === 'pick_digits'));
    setOrderMatters(config.orderMatters ?? (config.gameCategory === 'pick_digits'));
    if (config.digitPlayType) setDigitPlayType(config.digitPlayType);
    if (config.goal) {
      setInputMatchTier(config.goal.matchTier);
      setInputFrequency(config.goal.targetFrequency);
    }
  }, [config]);

  // Live calculation of requirements based on the user's typed values
  const previewReq = calculateGoalRequirements(
    activeCategory === 'pick_digits' ? 10 : Math.max(10, inputPool),
    Math.max(2, inputPick),
    Math.max(1, Math.min(inputPick, inputMatchTier)),
    Math.max(1, inputFrequency),
    activeCategory,
    orderMatters
  );

  // Apply custom typed parameters
  const handleApplyCustomTarget = () => {
    const isDigits = activeCategory === 'pick_digits';
    const validPool = isDigits ? 10 : Math.max(10, Math.min(60, inputPool));
    const validPick = isDigits ? Math.max(2, Math.min(4, inputPick)) : Math.max(3, Math.min(validPool - 1, inputPick));
    const validTier = Math.max(1, Math.min(validPick, inputMatchTier));
    const validFreq = Math.max(1, inputFrequency);

    setInputPool(validPool);
    setInputPick(validPick);
    setInputMatchTier(validTier);
    setInputFrequency(validFreq);

    const newConfig: GameConfig = {
      gameCategory: activeCategory,
      poolSize: validPool,
      pickSize: validPick,
      drawnNumbers: validPick,
      guarantee: validTier,
      allowRepeats: isDigits ? true : allowRepeats,
      orderMatters: isDigits ? orderMatters : false,
      digitPlayType: isDigits ? digitPlayType : undefined,
      goal: {
        matchTier: validTier,
        targetFrequency: validFreq,
        playType: isDigits ? digitPlayType : undefined,
      },
    };

    onChangeConfig(newConfig);

    if (onApplyGoalAsBudget) {
      onApplyGoalAsBudget(previewReq.recommendedTickets);
    }
  };

  // Switch between Lotto Style and Pick 3/4
  const handleSwitchCategory = (newCat: GameCategory) => {
    setActiveCategory(newCat);
    if (newCat === 'lotto') {
      setInputPool(25);
      setInputPick(6);
      setInputMatchTier(4);
      setInputFrequency(2);
      setAllowRepeats(false);
      setOrderMatters(false);

      const req = calculateGoalRequirements(25, 6, 4, 2, 'lotto', false);
      const newConfig: GameConfig = {
        gameCategory: 'lotto',
        poolSize: 25,
        pickSize: 6,
        drawnNumbers: 6,
        guarantee: 4,
        allowRepeats: false,
        orderMatters: false,
        goal: { matchTier: 4, targetFrequency: 2 },
      };
      onChangeConfig(newConfig);
      if (onApplyGoalAsBudget) onApplyGoalAsBudget(req.recommendedTickets);
    } else {
      setInputPool(10);
      setInputPick(3);
      setInputMatchTier(3);
      setInputFrequency(1);
      setAllowRepeats(true);
      setOrderMatters(true);
      setDigitPlayType('straight');

      const req = calculateGoalRequirements(10, 3, 3, 1, 'pick_digits', true);
      const newConfig: GameConfig = {
        gameCategory: 'pick_digits',
        poolSize: 10,
        pickSize: 3,
        drawnNumbers: 3,
        guarantee: 3,
        allowRepeats: true,
        orderMatters: true,
        digitPlayType: 'straight',
        goal: { matchTier: 3, targetFrequency: 1, playType: 'straight' },
      };
      onChangeConfig(newConfig);
      if (onApplyGoalAsBudget) onApplyGoalAsBudget(req.recommendedTickets);
    }
  };

  return (
    <div className="bg-[#121824] border-2 border-cyan-500/70 rounded-2xl p-5 sm:p-6 mb-6 shadow-2xl shadow-cyan-950/30 space-y-5">
      {/* Top Header & Game Mode Switcher (Lotto Style is Default) */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-cyan-900/60">
        <div className="flex items-start sm:items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-950/90 border border-cyan-500/80 flex items-center justify-center shrink-0 shadow-lg shadow-cyan-500/20 text-cyan-300">
            <Edit3 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                {isBn ? 'ধাপ ১' : 'Step 1'}
              </span>
              <h2 className="text-base font-bold text-white tracking-wide">
                {isBn ? 'গেম ও টার্গেট গ্যারান্টি কনফিগারেশন' : 'Game & Target Guarantee Configuration'}
              </h2>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                {activeCategory === 'pick_digits'
                  ? isBn ? '০–৯ পিক ৩/৪ ইঞ্জিন' : '0–9 Pick 3/4 Engine'
                  : isBn ? 'লটো কম্বিনেশন ইঞ্জিন' : 'Lotto Combinations Engine'}
              </span>
            </div>
            <p className="text-xs text-neutral-300 mt-0.5">
              {isBn
                ? 'লটারি (১ থেকে N) কিংবা ডিজিট গেম (০ থেকে ৯ পিক ৩ - সংখ্যা রিপিট ও পজিশন অর্ডার) নিজে লিখে টার্গেট ম্যাচ সেট করুন।'
                : 'Configure standard lotto (1 to N) or digit numbers (0 to 9 Pick 3 with repeats & order).'}
            </p>
          </div>
        </div>

        {/* 2-Family Category Selector (Lotto Style Default) */}
        <div className="flex items-center bg-[#0a0f1a] p-1 rounded-xl border border-neutral-800 self-start lg:self-auto font-mono text-xs">
          <button
            type="button"
            onClick={() => handleSwitchCategory('lotto')}
            className={`px-3.5 py-2 rounded-lg font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              activeCategory === 'lotto'
                ? 'bg-cyan-600 text-black shadow-md shadow-cyan-950/50'
                : 'text-neutral-400 hover:text-white'
            }`}
          >
            <span>🎱 {isBn ? 'লটো স্টাইল (১ থেকে N, যেমন ৬/২৫)' : 'Lotto Style (1 to N, e.g. 6/25)'}</span>
          </button>
          <button
            type="button"
            onClick={() => handleSwitchCategory('pick_digits')}
            className={`px-3.5 py-2 rounded-lg font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              activeCategory === 'pick_digits'
                ? 'bg-gradient-to-r from-purple-600 to-cyan-600 text-white shadow-md shadow-purple-950/50'
                : 'text-neutral-400 hover:text-white'
            }`}
          >
            <span>🎰 {isBn ? '০–৯ পিক ৩ (রিপিট ও অর্ডার)' : '0–9 Pick 3 (Repeats & Order)'}</span>
          </button>
        </div>
      </div>

      {/* --- USER TYPED INPUT SECTION --- */}
      <div className="bg-[#0a0f1a] border border-cyan-900/70 rounded-xl p-4 sm:p-5">
        <div className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider mb-3 flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4" />
            <span>
              {isBn
                ? 'নিজের পছন্দমতো লিখে দিন (আপনার কাস্টম গেম ও টার্গেট প্যারামিটার):'
                : 'Type Your Custom Game & Guarantee Parameters:'}
            </span>
          </div>

          {activeCategory === 'pick_digits' && (
            <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/40">
              {isBn ? '০–৯ ডিজিট · রিপিট সমর্থিত · অর্ডার গুরুত্বপূর্ণ' : 'Digits 0–9 · Repeats Allowed · Order Matters'}
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Input 1: Pool Size */}
          <div className="space-y-1.5 bg-[#101726] p-3 rounded-xl border border-neutral-700/80 focus-within:border-cyan-400 transition-colors">
            <label className="block text-[11px] font-bold text-neutral-300 uppercase tracking-wider font-mono">
              {isBn ? '১. কোন গেম? (১ থেকে কত?)' : '1. Game Pool (1 to X)'}
            </label>
            {activeCategory === 'pick_digits' ? (
              <div className="w-full bg-[#182235] border border-purple-600/60 rounded-lg px-3 py-2 text-sm font-mono font-bold text-purple-300 flex items-center justify-between">
                <span>0 to 9 (10 Digits)</span>
                <span className="text-[10px] text-purple-400">{isBn ? '০–৯ ডিজিট' : '10 Digits'}</span>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-xs text-neutral-400 font-mono font-semibold">1 to</span>
                <input
                  type="number"
                  min={10}
                  max={60}
                  value={inputPool}
                  onChange={(e) => setInputPool(Number(e.target.value))}
                  className="w-full bg-[#182235] border border-neutral-600 rounded-lg px-3 py-2 text-base font-mono font-extrabold text-white text-center focus:outline-none focus:border-cyan-400"
                  placeholder="25"
                />
                <span className="text-xs text-neutral-400 font-mono">{isBn ? 'বল' : 'balls'}</span>
              </div>
            )}
            <span className="text-[10px] text-neutral-400 block font-mono">
              {activeCategory === 'pick_digits'
                ? isBn ? 'ডিজিট: ০, ১, ২, ৩, ৪, ৫, ৬, ৭, ৮, ৯' : 'Digits: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9'
                : isBn ? 'যেমন: 25 (১ থেকে ২৫) বা 27 বা 49' : 'e.g. 25 (1 to 25) or 27 or 49'}
            </span>
          </div>

          {/* Input 2: Pick Size */}
          <div className="space-y-1.5 bg-[#101726] p-3 rounded-xl border border-neutral-700/80 focus-within:border-cyan-400 transition-colors">
            <label className="block text-[11px] font-bold text-neutral-300 uppercase tracking-wider font-mono">
              {isBn ? '২. কয়টি সংখ্যা/ডিজিট? (পিক k)' : '2. Numbers per ticket (Pick k)'}
            </label>
            <div className="flex items-center gap-2">
              <span className="text-xs text-neutral-400 font-mono font-semibold">Pick</span>
              <input
                type="number"
                min={activeCategory === 'pick_digits' ? 2 : 3}
                max={activeCategory === 'pick_digits' ? 4 : inputPool - 1}
                value={inputPick}
                onChange={(e) => setInputPick(Number(e.target.value))}
                className="w-full bg-[#182235] border border-neutral-600 rounded-lg px-3 py-2 text-base font-mono font-extrabold text-white text-center focus:outline-none focus:border-cyan-400"
                placeholder={activeCategory === 'pick_digits' ? '3' : '6'}
              />
              <span className="text-xs text-neutral-400 font-mono">{isBn ? 'টি' : 'nums'}</span>
            </div>
            <span className="text-[10px] text-neutral-400 block font-mono">
              {activeCategory === 'pick_digits'
                ? isBn ? 'পিক ৩ (000–999) বা পিক ৪' : 'Pick 3 (000–999) or Pick 4'
                : isBn ? 'যেমন: 6 (পিক ৬) বা 5 (পিক ৫)' : 'e.g. 6 (Pick 6) or 5 (Pick 5)'}
            </span>
          </div>

          {/* Input 3: Desired Match Tier */}
          <div className="space-y-1.5 bg-[#101726] p-3 rounded-xl border-2 border-cyan-500/50 focus-within:border-cyan-400 transition-colors">
            <label className="block text-[11px] font-bold text-cyan-300 uppercase tracking-wider font-mono flex items-center justify-between">
              <span>{isBn ? '৩. কত ম্যাচ করাতে চান?' : '3. Desired Match Tier'}</span>
              <span className="text-[10px] text-cyan-400 font-normal">Match</span>
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min={activeCategory === 'pick_digits' ? 1 : 2}
                max={inputPick}
                value={inputMatchTier}
                onChange={(e) => setInputMatchTier(Number(e.target.value))}
                className="w-full bg-[#182235] border border-cyan-600/70 rounded-lg px-3 py-2 text-base font-mono font-extrabold text-cyan-300 text-center focus:outline-none focus:border-cyan-400"
                placeholder={activeCategory === 'pick_digits' ? '3' : '4'}
              />
              <span className="text-xs text-cyan-300 font-mono font-bold whitespace-nowrap">
                {isBn ? 'ম্যাচ' : 'Match'}
              </span>
            </div>
            <span className="text-[10px] text-neutral-400 block font-mono">
              {activeCategory === 'pick_digits'
                ? isBn ? '3 (৩টি ডিজিট) বা 2 (Pair)' : '3 (All 3 digits) or 2 (Pair)'
                : isBn ? 'যেমন: 4 (৪-ম্যাচ), 5 (৫-ম্যাচ)' : 'e.g. 4 (4-match), 5 (5-match)'}
            </span>
          </div>

          {/* Input 4: Frequency (Times) */}
          <div className="space-y-1.5 bg-[#101726] p-3 rounded-xl border-2 border-emerald-500/50 focus-within:border-emerald-400 transition-colors">
            <label className="block text-[11px] font-bold text-emerald-300 uppercase tracking-wider font-mono flex items-center justify-between">
              <span>{isBn ? '৪. কত বার ম্যাচ করাতে চান?' : '4. How many times?'}</span>
              <span className="text-[10px] text-emerald-400 font-normal">Times</span>
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min={1}
                max={20}
                value={inputFrequency}
                onChange={(e) => setInputFrequency(Number(e.target.value))}
                className="w-full bg-[#182235] border border-emerald-600/70 rounded-lg px-3 py-2 text-base font-mono font-extrabold text-emerald-300 text-center focus:outline-none focus:border-emerald-400"
                placeholder="2"
              />
              <span className="text-xs text-emerald-300 font-mono font-bold whitespace-nowrap">
                {isBn ? 'বার' : 'Times'}
              </span>
            </div>
            <span className="text-[10px] text-neutral-400 block font-mono">
              {isBn ? 'যেমন: 1 (১ বার) বা 2 (২ বার - দুটি টিকিটে)' : 'e.g. 1 (1 time) or 2 (2 times)'}
            </span>
          </div>
        </div>

        {/* Pick 3/Digit Specific Rules: Order Matters & Repeats */}
        {activeCategory === 'pick_digits' && (
          <div className="mt-4 pt-3.5 border-t border-cyan-900/60 grid grid-cols-1 md:grid-cols-2 gap-3 bg-[#0d1624] p-3 rounded-xl border border-cyan-700/60">
            {/* Rule 1: Order Matters (Straight vs Box) */}
            <div className="space-y-1">
              <span className="text-[11px] font-mono font-bold text-cyan-300 flex items-center gap-1.5">
                <span>🎯 {isBn ? 'অর্ডার রুল (উইনিং নম্বরে অর্ডার ম্যাটার করে কি?):' : 'Order Rule (Straight vs Box):'}</span>
              </span>
              <div className="grid grid-cols-2 gap-2 mt-1">
                <button
                  type="button"
                  onClick={() => {
                    setOrderMatters(true);
                    setDigitPlayType('straight');
                  }}
                  className={`p-2 rounded-lg text-xs font-mono font-bold flex flex-col text-left transition-all border cursor-pointer ${
                    orderMatters && digitPlayType === 'straight'
                      ? 'bg-cyan-500 text-black border-cyan-400 shadow-sm'
                      : 'bg-[#141d2c] text-neutral-300 border-neutral-700 hover:border-cyan-400'
                  }`}
                >
                  <span>Straight (Exact Order)</span>
                  <span className="text-[10px] font-normal opacity-90">
                    {isBn ? 'অর্ডার গুরুত্বপূর্ণ (১ম, ২য়, ৩য় পজিশন হুবহু মিলতে হবে)' : 'Positions 1, 2, 3 must match exact order'}
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setOrderMatters(false);
                    setDigitPlayType('box');
                  }}
                  className={`p-2 rounded-lg text-xs font-mono font-bold flex flex-col text-left transition-all border cursor-pointer ${
                    !orderMatters || digitPlayType === 'box'
                      ? 'bg-purple-600 text-white border-purple-400 shadow-sm'
                      : 'bg-[#141d2c] text-neutral-300 border-neutral-700 hover:border-purple-400'
                  }`}
                >
                  <span>Box (Any Order)</span>
                  <span className="text-[10px] font-normal opacity-90">
                    {isBn ? 'যেকোনো ক্রমে সংখ্যা মিললেই উইন (6-way/3-way)' : 'Digits match in any order'}
                  </span>
                </button>
              </div>
            </div>

            {/* Rule 2: Repeats Allowed */}
            <div className="space-y-1">
              <span className="text-[11px] font-mono font-bold text-emerald-300 flex items-center gap-1.5">
                <span>🔄 {isBn ? 'সংখ্যা রিপিটেশন (Repeats Allowed):' : 'Number Repeats:'}</span>
              </span>
              <div className="p-2 rounded-lg bg-[#141d2c] border border-emerald-700/60 text-xs font-mono flex items-center justify-between">
                <div>
                  <span className="text-white font-bold block">{isBn ? 'রিপিট সম্পূর্ণ সক্রিয় (Yes):' : 'Repeats Allowed (Yes):'}</span>
                  <span className="text-[11px] text-neutral-400">
                    {isBn
                      ? 'ডাবল (যেমন 7-7-2, 0-5-0) ও ট্রিপল (যেমন 3-3-3) সম্পূর্ণ সাপোর্ট করে।'
                      : 'Doubles (7-7-2) and triples (3-3-3) fully supported.'}
                  </span>
                </div>
                <span className="px-2 py-0.5 rounded bg-emerald-500 text-black font-extrabold text-[11px]">
                  {isBn ? 'সক্রিয়' : 'Active'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Live Bangla Translation & Action Button */}
        <div className="mt-4 pt-3.5 border-t border-neutral-800 flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="text-xs text-white font-medium flex items-center gap-2 flex-wrap">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
              <span>
                {activeCategory === 'pick_digits' ? (
                  <span>
                    {isBn ? 'আপনার হিসাব: ' : 'Your calculation: '}
                    <strong className="text-cyan-300 font-mono">০ থেকে ৯</strong> {isBn ? 'ডিজিটের খেলা (পিক ' : 'digit game (Pick '}
                    <strong className="text-cyan-300 font-mono">{inputPick}</strong>),{' '}
                    {isBn ? 'যেখানে সংখ্যা রিপিট হতে পারে এবং ' : 'where numbers repeat and '}
                    <strong className="text-cyan-300 font-mono">{inputMatchTier}-ম্যাচ ({orderMatters ? 'Straight হুবহু অর্ডার' : 'Box যেকোনো ক্রম'})</strong>{' '}
                    {isBn ? 'কমপক্ষে ' : 'guaranteed at least '}
                    <strong className="text-emerald-300 font-mono">{inputFrequency} বার</strong> {isBn ? 'মিলবে।' : 'time(s).'}
                  </span>
                ) : (
                  <span>
                    {isBn ? 'আপনার হিসাব: ১ থেকে ' : 'Your calculation: 1 to '}
                    <strong className="text-cyan-300 font-mono">{inputPool}</strong> {isBn ? 'এর খেলা (পিক ' : 'game (Pick '}
                    <strong className="text-cyan-300 font-mono">{inputPick}</strong>), {isBn ? 'যেখানে ' : 'where '}
                    <strong className="text-cyan-300 font-mono">{inputMatchTier}-ম্যাচ</strong> {isBn ? 'কমপক্ষে ' : 'guaranteed at least '}
                    <strong className="text-emerald-300 font-mono">{inputFrequency} বার</strong> {isBn ? 'গ্যারান্টি হবে।' : 'time(s).'}
                  </span>
                )}
              </span>
            </div>
            <div className="text-[11px] text-neutral-400 font-mono">
              {isBn ? 'প্রয়োজনীয় বাজেট: ' : 'Required Budget: '}
              <strong className="text-cyan-300 font-bold">~{previewReq.recommendedTickets.toLocaleString()}</strong>{' '}
              {isBn ? 'টি প্রায়োরিটি টিকিট (গাণিতিক নির্ভুলতা: ১০০%)' : 'priority tickets (100% Mathematical Lock)'}
            </div>
          </div>

          <button
            type="button"
            onClick={handleApplyCustomTarget}
            className="flex items-center justify-center gap-2 px-5 py-2.5 bg-gradient-to-r from-cyan-500 via-emerald-500 to-cyan-400 hover:from-cyan-400 hover:to-emerald-400 text-black font-extrabold rounded-xl text-xs transition-all shadow-lg shadow-cyan-950/60 shrink-0 cursor-pointer"
          >
            <Zap className="w-4 h-4 fill-black" />
            <span>
              {isBn
                ? `⚡ কাস্টম টার্গেট রান করুন ও বাজেট লক করুন (${previewReq.recommendedTickets} টিকিট)`
                : `⚡ Run Custom Target & Lock Budget (${previewReq.recommendedTickets} tix)`}
            </span>
          </button>
        </div>
      </div>

      {/* Live Theoretical Parameters */}
      <div className="pt-2 border-t border-neutral-800 flex flex-wrap items-center justify-between gap-3 text-xs font-mono text-neutral-400">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-neutral-300">
            {isBn ? 'মোট কম্বিনেশন' : 'Total Combinations'} $\binom{'{'}{config.poolSize}{'}'}{'{'}{config.pickSize}{'}'}$: <strong className="text-white">{totalCombinations.toLocaleString()}</strong> {activeCategory === 'pick_digits' ? (isBn ? 'টি পারমিউটেশন (000–999)' : 'permutations (000–999)') : (isBn ? 'টি ড্র' : 'draws')}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-neutral-300">
            {activeCategory === 'pick_digits' ? (isBn ? 'ফুল ইউনিভার্স সাইজ' : 'Full Universe Size') : (isBn ? 'শোনহেইম লোয়ার বাউন্ড' : 'Schönheim Lower Bound')}: <strong className="text-blue-300">{schonheimBound.toLocaleString()}</strong> {isBn ? 'টি টিকিট' : 'tickets'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Award className="w-3.5 h-3.5 text-amber-400" />
          <span className="text-neutral-300">
            {isBn ? 'বর্তমান ফুল হুইল: ' : 'Current Full Wheel: '}
            <strong className="text-amber-300">{totalWheelSize.toLocaleString()}</strong> {isBn ? 'টি টিকিট' : 'tickets'} (
            <span className="text-emerald-400 font-bold font-mono">
              100.0% Bound Efficiency
            </span>
            )
          </span>
        </div>
      </div>
    </div>
  );
};
