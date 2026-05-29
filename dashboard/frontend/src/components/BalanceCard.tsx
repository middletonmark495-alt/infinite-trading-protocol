import { ArrowRightLeft, ExternalLink } from 'lucide-react'
import clsx from 'clsx'

interface TokenRow {
  symbol: string
  balance: number
}

interface Props {
  platform: 'coinbase' | 'evm'
  network?: string
  label: string
  address?: string
  nativeSymbol?: string
  nativeBalance?: number
  tokens?: TokenRow[]
  onTransfer?: () => void
  isLoading?: boolean
  error?: string
}

const fmt = (n: number) =>
  n < 0.0001 ? n.toExponential(4) : n.toLocaleString('en-US', { maximumFractionDigits: 6 })

const networkColor: Record<string, string> = {
  ethereum: 'badge-blue',
  base:     'badge-blue',
  polygon:  'badge-purple',
  arbitrum: 'badge-blue',
  optimism: 'badge-amber',
}

export default function BalanceCard({ platform, network, label, address, nativeSymbol, nativeBalance, tokens = [], onTransfer, isLoading, error }: Props) {
  const badgeClass = network ? networkColor[network] ?? 'badge-blue' : 'badge-green'

  return (
    <div className="card flex flex-col gap-3 hover:border-gray-700/80 transition-colors">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={clsx(badgeClass)}>
              {platform === 'coinbase' ? 'Coinbase' : network ?? 'EVM'}
            </span>
          </div>
          <h3 className="font-semibold text-gray-100 text-sm">{label}</h3>
          {address && (
            <p className="text-xs text-gray-500 font-mono mt-0.5">
              {address.slice(0, 6)}…{address.slice(-4)}
            </p>
          )}
        </div>
        {onTransfer && (
          <button onClick={onTransfer} className="btn-secondary flex items-center gap-1.5 !py-1.5 !px-3">
            <ArrowRightLeft size={13} />
            Transfer
          </button>
        )}
      </div>

      {/* Body */}
      {isLoading && <p className="text-xs text-gray-500 animate-pulse">Loading balances…</p>}
      {error    && <p className="text-xs text-red-400">{error}</p>}

      {!isLoading && !error && (
        <div className="space-y-1.5">
          {nativeSymbol !== undefined && nativeBalance !== undefined && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-300 font-medium">{nativeSymbol}</span>
              <span className="text-sm font-mono text-gray-100">{fmt(nativeBalance)}</span>
            </div>
          )}
          {tokens.map((t) => (
            <div key={t.symbol} className="flex justify-between items-center">
              <span className="text-sm text-gray-400">{t.symbol}</span>
              <span className="text-sm font-mono text-gray-300">{fmt(t.balance)}</span>
            </div>
          ))}
          {!nativeSymbol && tokens.length === 0 && (
            <p className="text-xs text-gray-600">No balances found</p>
          )}
        </div>
      )}
    </div>
  )
}
