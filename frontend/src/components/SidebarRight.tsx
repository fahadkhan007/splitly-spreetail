import type { GroupBalanceReport, MemberBalance } from '../api';

interface SidebarRightProps {
  balances: GroupBalanceReport | null;
  isLoading: boolean;
}

export function SidebarRight({ balances, isLoading }: SidebarRightProps) {
  if (isLoading) {
    return <div style={{ padding: '1rem', color: 'var(--color-text-muted)' }}>Loading balances...</div>;
  }

  if (!balances || balances.balances.length === 0) {
    return null;
  }

  return (
    <div style={{ padding: '1rem' }}>
      <div style={{ 
        color: 'var(--color-text-muted)',
        fontSize: '0.75rem',
        fontWeight: 600,
        letterSpacing: '0.5px',
        marginBottom: '1rem'
      }}>
        GROUP BALANCES
      </div>

      <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {balances.balances.map((b: MemberBalance) => {
          let statusText = 'settled up';
          let statusColor = 'var(--color-text-muted)';
          
          if (b.net_balance > 0) {
            statusText = `gets back ${balances.currency} ${b.net_balance.toFixed(2)}`;
            statusColor = 'var(--color-owe-me)';
          } else if (b.net_balance < 0) {
            statusText = `owes ${balances.currency} ${Math.abs(b.net_balance).toFixed(2)}`;
            statusColor = 'var(--color-i-owe)';
          }

          return (
            <li key={b.user_id} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{ 
                width: '36px', 
                height: '36px', 
                borderRadius: '50%', 
                backgroundColor: '#e0e0e0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: 'bold'
              }}>
                {b.display_name.charAt(0).toUpperCase()}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>
                  {b.display_name}
                </span>
                <span style={{ fontSize: '0.75rem', color: statusColor, fontWeight: b.net_balance !== 0 ? 600 : 400 }}>
                  {statusText}
                </span>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
