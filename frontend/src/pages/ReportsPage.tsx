import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { PieChart, TrendingUp, Users, DollarSign, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { reports } from '../api';
import type { GroupSummaryReport, MonthlyReport } from '../api';

export function ReportsPage() {
  const { groupId } = useParams<{ groupId: string }>();
  const [summary, setSummary] = useState<GroupSummaryReport | null>(null);
  const [monthly, setMonthly] = useState<MonthlyReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!groupId) return;

    const fetchReports = async () => {
      setIsLoading(true);
      try {
        const [sumData, monthData] = await Promise.all([
          reports.getSummary(groupId),
          reports.getMonthly(groupId)
        ]);
        setSummary(sumData);
        setMonthly(monthData);
      } catch (err) {
        setError('Failed to load reports.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchReports();
  }, [groupId]);

  const formatCurrency = (amount: number, currency: string = summary?.base_currency || 'USD') => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount);
  };

  if (isLoading) {
    return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading reports...</div>;
  }

  if (error || !summary || !monthly) {
    return <div style={{ padding: '2rem', color: '#ef4444' }}>{error || 'No data available'}</div>;
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '2rem',
        borderBottom: '1px solid var(--color-border)',
        paddingBottom: '1rem'
      }}>
        <div>
          <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '0.25rem' }}>
            <Link to={`/groups/${groupId}`} style={{ color: 'var(--color-brand)' }}>&larr; Back to group</Link>
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Group Reports</h1>
        </div>
      </div>

      {/* Top Metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div style={{ backgroundColor: 'white', padding: '1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>
            <TrendingUp size={16} /> Total Expenses
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 600 }}>
            {formatCurrency(summary.total_amount)}
          </div>
          <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
            Across {summary.total_expenses} transactions
          </div>
        </div>

        <div style={{ backgroundColor: 'white', padding: '1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', boxShadow: 'var(--shadow-sm)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>
            <DollarSign size={16} /> Total Settled
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 600 }}>
            {formatCurrency(summary.total_settled_amount)}
          </div>
          <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
            Across {summary.total_settlements} payments
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        {/* Left Column: Member Balances */}
        <div>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>
            <Users size={20} /> Member Summary
          </h3>
          <div style={{ backgroundColor: 'white', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead style={{ backgroundColor: 'var(--color-bg-surface)', borderBottom: '1px solid var(--color-border)' }}>
                <tr>
                  <th style={{ padding: '0.75rem 1rem', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Member</th>
                  <th style={{ padding: '0.75rem 1rem', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Total Paid</th>
                  <th style={{ padding: '0.75rem 1rem', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>Net Balance</th>
                </tr>
              </thead>
              <tbody>
                {summary.by_member.map(member => (
                  <tr key={member.user_id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                    <td style={{ padding: '1rem', fontWeight: 500 }}>{member.display_name}</td>
                    <td style={{ padding: '1rem' }}>{formatCurrency(member.total_paid)}</td>
                    <td style={{ padding: '1rem', fontWeight: 600, color: member.net_balance > 0 ? 'var(--color-brand)' : member.net_balance < 0 ? '#ef4444' : 'var(--color-text-muted)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        {member.net_balance > 0 ? <ArrowUpRight size={14} /> : member.net_balance < 0 ? <ArrowDownRight size={14} /> : null}
                        {formatCurrency(Math.abs(member.net_balance))}
                        {member.net_balance === 0 && 'Settled'}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Monthly & Categories */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          {/* Monthly Spending */}
          <div>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>
              <TrendingUp size={20} /> Monthly Trend
            </h3>
            <div style={{ backgroundColor: 'white', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', padding: '1.5rem' }}>
              {monthly.monthly_data.length === 0 ? (
                <p style={{ color: 'var(--color-text-muted)' }}>No monthly data available.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {monthly.monthly_data.map(month => {
                    const maxAmount = Math.max(...monthly.monthly_data.map(m => m.total_amount));
                    const widthPercent = maxAmount > 0 ? Math.max((month.total_amount / maxAmount) * 100, 5) : 0;
                    
                    return (
                      <div key={month.month_label}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem', fontSize: '0.875rem' }}>
                          <span style={{ fontWeight: 500 }}>{month.month_label}</span>
                          <span>{formatCurrency(month.total_amount)}</span>
                        </div>
                        <div style={{ width: '100%', height: '12px', backgroundColor: 'var(--color-bg-body)', borderRadius: '6px', overflow: 'hidden' }}>
                          <div style={{ 
                            width: `${widthPercent}%`, 
                            height: '100%', 
                            backgroundColor: 'var(--color-brand)',
                            transition: 'width 0.5s ease-out'
                          }} />
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
                          {month.expense_count} expenses
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Categories */}
          <div>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.25rem', fontWeight: 600, marginBottom: '1rem' }}>
              <PieChart size={20} /> Categories
            </h3>
            <div style={{ backgroundColor: 'white', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', padding: '1rem' }}>
               {summary.by_category.length === 0 ? (
                 <p style={{ color: 'var(--color-text-muted)', padding: '0.5rem' }}>No categorized data.</p>
               ) : (
                 <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                   {summary.by_category.map(cat => (
                     <li key={cat.category} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid var(--color-bg-body)' }}>
                       <span style={{ fontWeight: 500 }}>{cat.category || 'Uncategorized'}</span>
                       <span>{formatCurrency(cat.total_amount)}</span>
                     </li>
                   ))}
                 </ul>
               )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
