export type GameCategory = 'lotto' | 'pick_digits';

export type DigitPlayType = 'straight' | 'box' | 'pairs' | 'both';

export interface GuaranteeGoal {
  matchTier: number; // 2, 3, 4, 5, 6 etc.
  targetFrequency: number; // 1 time, 2 times, 3+ times
  playType?: DigitPlayType; // For Pick 3/4: 'straight' (exact order) or 'box' (any order)
}

export interface Ticket {
  id: string;
  numbers: number[]; // For lotto: [3, 7, 12...]. For pick_digits: [7, 7, 2] (repeats allowed, order matters)
  priorityRank: number; // 1 = highest marginal coverage
}

export interface TicketEvaluation {
  id: string;
  priorityRank: number;
  numbers: number[];
  matches: number; // Active match count based on chosen rule (Straight or Box)
  matchedDigits: number[];
  unmatchedDigits: number[];
  inBudget: boolean;
  meetsGoal?: boolean;
  // Pick 3 / Digit-specific attributes:
  exactPositionalMatches?: number; // Digits matching in identical position index (Order matters)
  boxMatches?: number; // Digits matching in any position (accounting for duplicate counts)
  isStraightWin?: boolean; // 100% Exact order match (e.g. 3/3 in Pick 3)
  isBoxWin?: boolean; // 100% Any order match (e.g. 7-2-7 matches 7-7-2)
  isFrontPair?: boolean; // Slot 0 & Slot 1 match exact
  isBackPair?: boolean; // Slot 1 & Slot 2 match exact
  isSplitPair?: boolean; // Slot 0 & Slot 2 match exact
  positionMatchFlags?: boolean[]; // [true, false, true] indicating which exact slots matched
}

export interface GameConfig {
  gameCategory: GameCategory; // 'lotto' (1..N no repeats) or 'pick_digits' (0..9 repeats allowed, order matters)
  poolSize: number; // For lotto: 20, 25, 27, 36, 42, 45, 49. For pick_digits: 10 (digits 0–9)
  pickSize: number; // 3 for Pick 3, 4 for Pick 4, 6 for Pick 6
  guarantee: number; // t: 2, 3, 4, 5
  drawnNumbers: number; // m: 3, 4, 5, 6
  allowRepeats?: boolean; // true for pick_digits (doubles/triples allowed)
  orderMatters?: boolean; // true for pick_digits Straight
  digitPlayType?: DigitPlayType; // 'straight' (exact order) vs 'box' (any order)
  goal?: GuaranteeGoal;
}

export interface GamePreset {
  id: string;
  name: string;
  shortLabel: string;
  category: GameCategory;
  poolSize: number;
  pickSize: number;
  guarantee: number;
  drawnNumbers: number;
  allowRepeats?: boolean;
  orderMatters?: boolean;
  smartStops: [number, number, number, number];
  description: string;
}

export interface TicketGeneratorOptions {
  count: number;
  includeKeyNumbers: number[];
  excludeNumbers: number[];
  balancedOddEven: boolean;
  maxConsecutive: number;
}

export interface MatchCounts {
  6: number;
  5: number;
  4: number;
  3: number;
  2: number;
  1: number;
  0: number;
}
