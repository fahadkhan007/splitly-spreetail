export interface User {
  id: string;
  email: string;
  display_name: string;
  is_verified: boolean;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  token_type: string;
}

export type GroupStatus = 'ACTIVE' | 'ARCHIVED';

export type MemberRole = 'ADMIN' | 'MEMBER';

export interface GroupMember {
  group_id: string;
  user_id: string;
  role: MemberRole;
  joined_at: string;
  left_at: string | null;
}

export interface MemberOut {
  user_id: string;
  display_name: string;
  email: string;
  role: MemberRole;
  joined_at: string;
  left_at: string | null;
}

export interface InvitationOut {
  id: string;
  group_id: string;
  invited_email: string;
  token: string;
  expires_at: string;
  is_accepted: boolean;
  created_at: string;
}

export interface Group {
  id: string;
  name: string;
  description: string | null;
  base_currency: string;
  currency_locked: boolean;
  status: GroupStatus;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
}

export interface GroupDetailOut extends Group {
  members: MemberOut[];
}

export type SplitType = 'EQUAL' | 'UNEQUAL' | 'PERCENTAGE' | 'SHARE';

export interface SplitInput {
  user_id: string;
  value: number;
}

export interface ExpenseSplit {
  user_id: string;
  amount_owed_base: number;
}

export interface ExpenseSplitOut extends ExpenseSplit {
  display_name: string;
}

export interface ExpenseOut {
  id: string;
  group_id: string;
  paid_by_user_id: string;
  paid_by_name: string;
  description: string;
  notes: string | null;
  amount_original: number;
  currency_original: string;
  amount_base: number;
  fx_rate_used: number | null;
  expense_date: string;
  split_type: SplitType;
  is_deleted: boolean;
  created_at: string;
  splits: ExpenseSplitOut[];
}

export interface ExpenseCreate {
  paid_by_user_id: string;
  description: string;
  notes?: string | null;
  amount: number;
  currency: string;
  expense_date: string;
  split_type: SplitType;
  splits: SplitInput[];
}

export type SettlementStatus = 'ACTIVE' | 'VOIDED';

export interface SettlementOut {
  id: string;
  group_id: string;
  payer_user_id: string;
  payer_name: string;
  payee_user_id: string;
  payee_name: string;
  amount_original: number;
  currency_original: string;
  amount_base: number;
  fx_rate_used: number | null;
  settlement_date: string;
  status: SettlementStatus;
  notes: string | null;
  created_at: string;
}

export interface SettlementCreate {
  payer_user_id: string;
  payee_user_id: string;
  amount: number;
  currency: string;
  settlement_date: string;
  notes?: string | null;
}

export interface MemberBalance {
  user_id: string;
  display_name: string;
  total_paid: number;
  total_owed: number;
  net_balance: number;
}

export interface PaymentAction {
  payer_user_id: string;
  payer_name: string;
  payee_user_id: string;
  payee_name: string;
  amount: number;
}

export interface GroupBalanceReport {
  group_id: string;
  currency: string;
  balances: MemberBalance[];
  suggested_payments: PaymentAction[];
}

export interface ImportRowResult {
  row_number: number;
  outcome: string;
  anomalies: string[];
  raw_data: Record<string, string>;
}

export interface ImportReportOut {
  import_id: string;
  group_id: string;
  filename: string;
  total_rows: number;
  imported: number;
  skipped: number;
  converted: number;
  warning_count: number;
  error_count: number;
  rows: ImportRowResult[];
  created_at: string;
}

export interface ImportSummaryOut {
  import_id: string;
  filename: string;
  total_rows: number;
  imported: number;
  skipped: number;
  warning_count: number;
  error_count: number;
  created_at: string;
}

export interface CategoryBreakdown {
  category: string;
  expense_count: number;
  total_amount: number;
}

export interface MemberSummary {
  user_id: string;
  display_name: string;
  total_paid: number;
  total_owed: number;
  net_balance: number;
}

export interface GroupSummaryReport {
  group_id: string;
  base_currency: string;
  total_expenses: number;
  total_amount: number;
  total_settlements: number;
  total_settled_amount: number;
  by_category: CategoryBreakdown[];
  by_member: MemberSummary[];
}

export interface MonthlyEntry {
  year: number;
  month: number;
  month_label: string;
  expense_count: number;
  total_amount: number;
}

export interface MonthlyReport {
  group_id: string;
  base_currency: string;
  monthly_data: MonthlyEntry[];
}
