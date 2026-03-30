import pandas as pd

df = pd.read_csv('finance/tushare/margin_trading_sse_szse.csv')
print('Current data range:')
print('  Start date:', df['trade_date'].min())
print('  End date:', df['trade_date'].max())
print('  Total records:', len(df))
print('  SSE records:', len(df[df['exchange_id'] == 'SSE']))
print('  SZSE records:', len(df[df['exchange_id'] == 'SZSE']))
