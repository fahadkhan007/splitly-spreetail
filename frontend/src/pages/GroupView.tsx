import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Settings } from 'lucide-react';
import { groups, expenses, settlements, balances as balancesApi } from '../api';
import type { GroupDetailOut, ExpenseOut, SettlementOut, GroupBalanceReport } from '../api';
import { SidebarRight } from '../components/SidebarRight';
import { AddExpenseModal } from '../components/expenses/AddExpenseModal';
import { EditExpenseModal } from '../components/expenses/EditExpenseModal';
import { SettleUpModal } from '../components/settlements/SettleUpModal';
import { Edit3, Trash2, Ban } from 'lucide-react';

export function GroupView() {
  const { groupId } = useParams<{ groupId: string }>();
  
  const [group, setGroup] = useState<GroupDetailOut | null>(null);
  const [expenseList, setExpenseList] = useState<ExpenseOut[]>([]);
  const [settlementList, setSettlementList] = useState<SettlementOut[]>([]);
  const [balances, setBalances] = useState<GroupBalanceReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  const [isAddExpenseOpen, setIsAddExpenseOpen] = useState(false);
  const [isSettleUpOpen, setIsSettleUpOpen] = useState(false);
  
  const [editingExpense, setEditingExpense] = useState<ExpenseOut | null>(null);

  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const triggerRefresh = () => setRefreshTrigger(prev => prev + 1);

  useEffect(() => {
    if (!groupId) return;

    setIsLoading(true);
    Promise.all([
      groups.getGroupById(groupId),
      expenses.getExpenses(groupId),
      settlements.getSettlements(groupId),
      balancesApi.getGroupBalances(groupId)
    ])
      .then(([g, e, s, b]) => {
        setGroup(g);
        setExpenseList(e);
        setSettlementList(s);
        setBalances(b);
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [groupId, refreshTrigger]);

  if (isLoading) {
    return <div style={{ padding: '2rem' }}>Loading group data...</div>;
  }

  if (!group) {
    return <div style={{ padding: '2rem' }}>Group not found.</div>;
  }

  const handleDeleteExpense = async (expenseId: string) => {
    if (!window.confirm('Are you sure you want to delete this expense?')) return;
    try {
      await expenses.deleteExpense(group.id, expenseId);
      triggerRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete expense');
    }
  };

  const handleVoidSettlement = async (settlementId: string) => {
    if (!window.confirm('Are you sure you want to void this settlement?')) return;
    try {
      await settlements.voidSettlement(group.id, settlementId);
      triggerRefresh();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to void settlement');
    }
  };

  // Combine and sort activities
  type Activity = 
    | { type: 'expense'; date: string; data: ExpenseOut }
    | { type: 'settlement'; date: string; data: SettlementOut };

  const activities: Activity[] = [
    ...expenseList.map(e => ({ type: 'expense' as const, date: e.expense_date, data: e })),
    ...settlementList.map(s => ({ type: 'settlement' as const, date: s.settlement_date, data: s }))
  ].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  return (
    <div style={{ display: 'flex', minHeight: '100%' }}>
      {/* Center Main Content */}
      <div style={{ flex: 1, borderRight: '1px solid var(--color-border)' }}>
        
        {/* Top Header inside center content */}
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          padding: '1.5rem',
          backgroundColor: '#eeeeee',
          borderBottom: '1px solid var(--color-border)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ 
              width: '40px', 
              height: '40px', 
              borderRadius: '8px', 
              backgroundColor: '#333',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: '18px'
            }}>
              {group.name.charAt(0).toUpperCase()}
            </div>
            <div>
              <h1 style={{ fontSize: '1.5rem', fontWeight: 600, color: 'var(--color-text-main)', margin: 0, lineHeight: 1.2 }}>
                {group.name}
              </h1>
              <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                {group.members.length} people
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <Link to={`/groups/${groupId}/settings`} className="btn btn-secondary" style={{ padding: '0.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }} title="Group Settings">
              <Settings size={18} />
            </Link>
            <button className="btn btn-primary" onClick={() => setIsAddExpenseOpen(true)}>Add an expense</button>
            <button className="btn btn-secondary" onClick={() => setIsSettleUpOpen(true)}>Settle up</button>
          </div>
        </div>

        {/* Activity Feed */}
        <div style={{ padding: '2rem' }}>
          {activities.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '4rem 0' }}>
              <h2 style={{ fontSize: '1.25rem', color: 'var(--color-text-main)', marginBottom: '0.5rem' }}>
                No activity yet
              </h2>
              <p style={{ color: 'var(--color-text-muted)' }}>
                Add an expense or settle up to see activity here.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {activities.map(act => {
                if (act.type === 'expense') {
                  const exp = act.data as ExpenseOut;
                  return (
                    <div key={`exp-${exp.id}`} style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      padding: '1rem 0',
                      borderBottom: '1px solid #eee'
                    }}>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{new Date(exp.expense_date).toLocaleDateString()}</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontWeight: 500 }}>{exp.description}</span>
                          {exp.is_deleted && <span style={{ fontSize: '0.7rem', backgroundColor: '#fee2e2', color: '#991b1b', padding: '2px 6px', borderRadius: '12px' }}>Deleted</span>}
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                        <div style={{ textAlign: 'right' }}>
                          <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{exp.paid_by_name} paid</span>
                          <div style={{ fontWeight: 600 }}>{group.base_currency} {exp.amount_base.toFixed(2)}</div>
                        </div>
                        {!exp.is_deleted && (
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button onClick={() => setEditingExpense(exp)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)' }} title="Edit">
                              <Edit3 size={16} />
                            </button>
                            <button onClick={() => handleDeleteExpense(exp.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444' }} title="Delete">
                              <Trash2 size={16} />
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                } else {
                  const stl = act.data as SettlementOut;
                  return (
                    <div key={`stl-${stl.id}`} style={{ 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      padding: '1rem 0',
                      borderBottom: '1px solid #eee'
                    }}>
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{new Date(stl.settlement_date).toLocaleDateString()}</span>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                          <span style={{ fontWeight: 500, color: 'var(--color-brand)' }}>{stl.payer_name} paid {stl.payee_name}</span>
                          {stl.status === 'VOIDED' && <span style={{ fontSize: '0.7rem', backgroundColor: '#fee2e2', color: '#991b1b', padding: '2px 6px', borderRadius: '12px' }}>Voided</span>}
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontWeight: 600, color: 'var(--color-brand)' }}>{group.base_currency} {stl.amount_base.toFixed(2)}</div>
                        </div>
                        {stl.status === 'ACTIVE' && (
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button onClick={() => handleVoidSettlement(stl.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444' }} title="Void Settlement">
                              <Ban size={16} />
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                }
              })}
            </div>
          )}
        </div>
      </div>

      {/* Right Sidebar (Balances) */}
      <div style={{ width: '280px', flexShrink: 0 }}>
        <SidebarRight balances={balances} isLoading={isLoading} />
      </div>

      {/* Modals */}
      <AddExpenseModal 
        isOpen={isAddExpenseOpen} 
        onClose={() => setIsAddExpenseOpen(false)} 
        group={group} 
        onSuccess={triggerRefresh} 
      />
      
      <SettleUpModal 
        isOpen={isSettleUpOpen} 
        onClose={() => setIsSettleUpOpen(false)} 
        group={group} 
        onSuccess={triggerRefresh} 
      />

      <EditExpenseModal
        isOpen={!!editingExpense}
        onClose={() => setEditingExpense(null)}
        group={group}
        expense={editingExpense}
        onSuccess={triggerRefresh}
      />
    </div>
  );
}
