import React, { useState } from 'react';
import { Dices, RotateCcw, Sparkles } from 'lucide-react';
import { GameCategory } from '../types';

interface NumberSelectorProps {
  poolSize: number;
  pickSize: number;
  selectedNumbers: number[];
  onChange: (numbers: number[]) => void;
  gameCategory?: GameCategory;
  orderMatters?: boolean;
  allowRepeats?: boolean;
  lang?: 'bn' | 'en';
}

export const NumberSelector: React.FC<NumberSelectorProps> = ({
  poolSize,
  pickSize,
  selectedNumbers,
  onChange,
  gameCategory = 'lotto',
  orderMatters = false,
  allowRepeats = false,
  lang = 'bn',
}) => {
  const isBn = lang === 'bn';
  const isDigitGame = gameCategory === 'pick_digits' || allowRepeats || (poolSize === 10 && pickSize <= 4);
  const [activeSlot, setActiveSlot] = useState<number>(0);

  // --- LOTTO TOGGLE (Unique balls 1 to N) ---
  const toggleLottoNumber = (n: number) => {
    if (selectedNumbers.includes(n)) {
      onChange(selectedNumbers.filter((x) => x !== n).sort((a, b) => a - b));
    } else {
      if (selectedNumbers.length < pickSize) {
        onChange([...selectedNumbers, n].sort((a, b) => a - b));
      }
    }
  };

  // --- DIGIT PICK 3/4 SELECTION (0 to 9, repeats allowed, order matters) ---
  const handleDigitSelect = (digit: number) => {
    const current = [...selectedNumbers];
    if (current.length < pickSize) {
      current.push(digit);
      onChange(current);
      setActiveSlot(Math.min(pickSize - 1, current.length));
    } else {
      current[activeSlot] = digit;
      onChange(current);
      setActiveSlot((prev) => (prev + 1) % pickSize);
    }
  };

  const handleRandomDraw = () => {
    if (isDigitGame) {
      const digits: number[] = [];
      for (let i = 0; i < pickSize; i++) {
        digits.push(Math.floor(Math.random() * 10));
      }
      onChange(digits);
      setActiveSlot(0);
    } else {
      const pool = Array.from({ length: poolSize }, (_, i) => i + 1);
      const picked: number[] = [];
      for (let i = 0; i < pickSize; i++) {
        const idx = Math.floor(Math.random() * pool.length);
        picked.push(pool.splice(idx, 1)[0]);
      }
      onChange(picked.sort((a, b) => a - b));
    }
  };

  const digitPresets = [
    {
      label: isBn
        ? (pickSize === 4 ? 'ডাবল: 7-7-2-5 (রিপিট)' : 'ডাবল: 7-7-2 (রিপিট)')
        : (pickSize === 4 ? 'Double: 7-7-2-5' : 'Double: 7-7-2'),
      numbers: pickSize === 4 ? [7, 7, 2, 5] : [7, 7, 2],
    },
    {
      label: isBn
        ? (pickSize === 4 ? 'ডাবল: 0-5-0-9 (রিপিট)' : 'ডাবল: 0-5-0 (রিপিট)')
        : (pickSize === 4 ? 'Double: 0-5-0-9' : 'Double: 0-5-0'),
      numbers: pickSize === 4 ? [0, 5, 0, 9] : [0, 5, 0],
    },
    {
      label: isBn
        ? (pickSize === 4 ? 'কোয়াড: 3-3-3-3 (সব রিপিট)' : 'ট্রিপল: 3-3-3 (সব রিপিট)')
        : (pickSize === 4 ? 'Quad: 3-3-3-3' : 'Triple: 3-3-3'),
      numbers: pickSize === 4 ? [3, 3, 3, 3] : [3, 3, 3],
    },
    {
      label: isBn
        ? (pickSize === 4 ? 'সিঙ্গেল: 3-7-2-8' : 'সিঙ্গেল: 3-7-2')
        : (pickSize === 4 ? 'Single: 3-7-2-8' : 'Single: 3-7-2'),
      numbers: pickSize === 4 ? [3, 7, 2, 8] : [3, 7, 2],
    },
  ];

  const getClassicLottoNumbers = () => {
    const base = [3, 7, 12, 16, 21, 25].filter((n) => n <= poolSize);
    for (let p = 1; p <= poolSize && base.length < pickSize; p++) {
      if (!base.includes(p)) base.push(p);
    }
    return base.slice(0, pickSize).sort((a, b) => a - b);
  };

  const lottoPresets = [
    { label: isBn ? 'ক্লাসিক ড্র' : 'Classic Draw', numbers: getClassicLottoNumbers() },
    { label: isBn ? 'লো রেঞ্জ' : 'Low Range', numbers: Array.from({ length: pickSize }, (_, i) => i + 1) },
    { label: isBn ? 'হাই রেঞ্জ' : 'High Range', numbers: Array.from({ length: pickSize }, (_, i) => poolSize - pickSize + i + 1) },
  ];

  return (
    <div className="bg-[#161b22] border border-neutral-800 rounded-xl p-5 mb-6 shadow-xl font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-neutral-800">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              {isBn ? 'ধাপ ২' : 'Step 2'}
            </span>
            <h2 className="text-base font-semibold text-white">
              {isBn ? 'উইনিং ড্র নম্বর নির্বাচন' : 'Winning Numbers Selection'}
            </h2>
            <span
              className={`text-xs font-mono font-medium px-2 py-0.5 rounded ${
                selectedNumbers.length === pickSize
                  ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                  : 'bg-amber-950/70 text-amber-300 border border-amber-800/60'
              }`}
            >
              {isBn
                ? `${selectedNumbers.length}/${pickSize} টি নির্বাচিত`
                : `${selectedNumbers.length}/${pickSize} Selected`}
            </span>
            {isDigitGame && (
              <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-purple-950/80 text-purple-300 border border-purple-700/80">
                {isBn ? '⭐ ০–৯ ডিজিট · রিপিট সমর্থিত · অর্ডার গুরুত্বপূর্ণ' : '⭐ 0–9 Digits · Repeats Allowed · Order Matters!'}
              </span>
            )}
          </div>
          <p className="text-xs text-neutral-300 mt-1">
            {isDigitGame
              ? isBn
                ? 'পিক ৩ (০–৯) এর ড্র নম্বর সেট করুন। সংখ্যা রিপিট হতে পারে (যেমন 7-7-2 বা 3-3-3) এবং পজিশনের অর্ডার অত্যন্ত গুরুত্বপূর্ণ (Straight vs Box)।'
                : 'Set winning numbers for Pick 3 (0–9). Numbers repeat and position order matters.'
              : isBn
              ? `আপনার টিকিটের ম্যাচ কভারেজ পরীক্ষা করতে ১ থেকে ${poolSize} এর মধ্যে ঠিক ${pickSize}টি সংখ্যা নির্বাচন করুন।`
              : `Pick exactly ${pickSize} numbers (1 to ${poolSize}) to test match coverage across your tickets.`}
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            onClick={handleRandomDraw}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 hover:text-white rounded-lg text-xs font-medium transition-colors border border-neutral-700 cursor-pointer"
          >
            <Dices className="w-3.5 h-3.5 text-cyan-400" />
            <span>{isBn ? 'র‍্যান্ডম ড্র' : 'Random Draw'} {isDigitGame && (isBn ? '(রিপিট সমর্থিত)' : '(Repeats)')}</span>
          </button>
          <button
            type="button"
            onClick={() => onChange([])}
            disabled={selectedNumbers.length === 0}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
              selectedNumbers.length === 0
                ? 'bg-neutral-900/60 text-neutral-600 border-neutral-800/80 cursor-not-allowed opacity-60'
                : 'bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 hover:text-white border-rose-800/60 cursor-pointer'
            }`}
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>{isBn ? 'ক্লিয়ার' : 'Clear'}</span>
          </button>
        </div>
      </div>

      {/* DIGIT PICK 3/4 POSITIONAL CONTROLLER */}
      {isDigitGame ? (
        <div className="mt-4 space-y-4">
          <div className="bg-[#0b121e] border-2 border-cyan-500/60 rounded-xl p-4">
            <div className="flex items-center justify-between gap-2 mb-3">
              <span className="text-xs font-mono font-bold text-cyan-300 uppercase tracking-wider">
                {isBn ? 'পজিশনাল স্লট (অর্ডার অনুযায়ী প্রতিটি স্লটের ডিজিট):' : 'Position Slots (Order Matters):'}
              </span>
              <span className="text-[11px] text-neutral-400 font-mono">
                {isBn ? 'ক্লিক করে স্লট বেছে নিন বা নিচের ০–৯ কীপ্যাড চাপুন' : 'Click slot or press digit keypad below'}
              </span>
            </div>

            <div className="grid grid-cols-3 sm:grid-cols-4 gap-3 max-w-xl mx-auto">
              {Array.from({ length: pickSize }, (_, slotIdx) => {
                const hasVal = slotIdx < selectedNumbers.length;
                const digit = hasVal ? selectedNumbers[slotIdx] : null;
                const isActive = activeSlot === slotIdx;

                return (
                  <button
                    key={slotIdx}
                    type="button"
                    onClick={() => setActiveSlot(slotIdx)}
                    className={`relative p-3 rounded-xl border-2 transition-all flex flex-col items-center justify-center text-center cursor-pointer ${
                      isActive
                        ? 'bg-cyan-950/90 border-cyan-400 ring-2 ring-cyan-400/50 shadow-lg shadow-cyan-950/60'
                        : 'bg-[#141d2c] border-neutral-700 hover:border-cyan-500/50'
                    }`}
                  >
                    <span className="text-[10px] font-mono text-neutral-400 uppercase tracking-wider mb-1">
                      {isBn ? `পজিশন ${slotIdx + 1}` : `Position ${slotIdx + 1}`}
                    </span>
                    <span className="text-3xl font-extrabold font-mono text-white tabular-nums">
                      {digit !== null ? digit : '—'}
                    </span>
                    <span className="text-[9px] font-mono text-cyan-400 mt-1">
                      {slotIdx === 0
                        ? isBn ? '১ম ডিজিট' : '1st Digit'
                        : slotIdx === 1
                        ? isBn ? '২য় ডিজিট' : '2nd Digit'
                        : isBn ? '৩য় ডিজিট' : '3rd Digit'}
                    </span>
                    {isActive && (
                      <span className="absolute -top-2 -right-1 px-1.5 py-0.2 rounded-full bg-cyan-500 text-black text-[9px] font-bold">
                        {isBn ? 'সম্পাদনা' : 'Active'}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            <div className="mt-3 pt-3 border-t border-cyan-950 flex items-center justify-between text-xs text-neutral-300 font-mono flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span>
                  {isBn ? 'বর্তমান ড্র: ' : 'Current Draw: '}
                  <strong className="text-white text-sm tracking-widest">
                    {selectedNumbers.length === pickSize ? selectedNumbers.join(' - ') : (isBn ? 'অসম্পূর্ণ' : 'Incomplete')}
                  </strong>
                </span>
                {selectedNumbers.length === pickSize && (
                  <span className="text-[11px] text-cyan-300">
                    {new Set(selectedNumbers).size === 1
                      ? isBn ? '⭐ ট্রিপল রিপিট (সব সমান)' : '⭐ Triple Repeat'
                      : new Set(selectedNumbers).size < pickSize
                      ? isBn ? '⭐ ডাবল রিপিট (সংখ্যা রিপিট হয়েছে)' : '⭐ Double Repeat'
                      : isBn ? 'সিঙ্গেলস (সব আলাদা)' : 'Singles'}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* 0 to 9 Digit Keypad */}
          <div>
            <span className="block text-xs font-mono font-bold text-neutral-300 uppercase tracking-wider mb-2">
              {isBn ? `পজিশন ${activeSlot + 1} এর জন্য ০ থেকে ৯ ডিজিট চাপুন:` : `Select Digit 0 to 9 for Position ${activeSlot + 1}:`}
            </span>
            <div className="grid grid-cols-5 sm:grid-cols-10 gap-2">
              {Array.from({ length: 10 }, (_, i) => i).map((digit) => {
                const countInSelected = selectedNumbers.filter((n) => n === digit).length;
                return (
                  <button
                    key={digit}
                    type="button"
                    onClick={() => handleDigitSelect(digit)}
                    className="h-12 rounded-xl font-mono text-lg font-extrabold bg-[#21262d] hover:bg-cyan-600 hover:text-black text-white border border-neutral-700/80 transition-all flex flex-col items-center justify-center cursor-pointer active:scale-95 shadow-md relative"
                  >
                    <span>{digit}</span>
                    {countInSelected > 0 && (
                      <span className="text-[9px] font-bold text-cyan-300 absolute bottom-1 right-1 px-1 rounded bg-black/60">
                        {countInSelected}x
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        /* STANDARD LOTTO 1 TO N GRID */
        <div className="mt-4">
          <div className="grid grid-cols-6 sm:grid-cols-9 md:grid-cols-12 lg:grid-cols-14 gap-2">
            {Array.from({ length: poolSize }, (_, i) => i + 1).map((n) => {
              const isSelected = selectedNumbers.includes(n);
              return (
                <button
                  key={n}
                  onClick={() => toggleLottoNumber(n)}
                  className={`h-10 rounded-lg font-mono text-sm font-bold transition-all flex items-center justify-center cursor-pointer ${
                    isSelected
                      ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-900/50 scale-105 border border-cyan-400'
                      : 'bg-[#21262d] hover:bg-neutral-700 text-neutral-300 border border-neutral-700/80 hover:border-neutral-500'
                  }`}
                >
                  {String(n).padStart(2, '0')}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Selected Numbers Summary & Quick Presets Strip */}
      <div className="mt-4 pt-4 border-t border-neutral-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs text-neutral-400 font-medium">
            {isBn ? 'নির্বাচিত উইনিং নম্বর:' : 'Selected Winning Numbers:'}
          </span>
          {selectedNumbers.length === 0 ? (
            <span className="text-xs text-neutral-500 italic">{isBn ? 'এখনো কোনো নম্বর নির্বাচন করা হয়নি' : 'No numbers selected yet'}</span>
          ) : (
            <div className="flex items-center gap-1.5 flex-wrap">
              {selectedNumbers.map((n, idx) => (
                <span
                  key={`${n}-${idx}`}
                  className="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-600 font-mono text-sm font-extrabold shadow-sm"
                >
                  {isDigitGame ? n : String(n).padStart(2, '0')}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Quick Presets */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <Sparkles className="w-3.5 h-3.5 text-neutral-400 shrink-0" />
          <span className="text-[11px] text-neutral-400 mr-1 font-mono">
            {isBn ? 'প্রিসেট ড্র:' : 'Presets:'}
          </span>
          {(isDigitGame ? digitPresets : lottoPresets).map((p) => (
            <button
              key={p.label}
              onClick={() => {
                onChange(p.numbers);
                setActiveSlot(0);
              }}
              className="text-[11px] px-2 py-0.5 rounded bg-neutral-800 hover:bg-neutral-700 text-neutral-200 hover:text-white transition-colors border border-neutral-700 cursor-pointer font-mono"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
