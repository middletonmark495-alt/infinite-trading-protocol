import { useQueries, useQuery } from '@tanstack/react-query'
import { RefreshCw, AlertCircle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useSettingsStore } from '../store'
import { fetchCoinbaseAccounts, fetchEVMBalance } from '../api'
import { CoinbaseAccount, EVMBalanceResult } from '../types'
import BalanceCard from '../components/BalanceCard'

export default function Dashboard() {
  const navigate = useNavigate()
  const { coinbaseKey, coinbaseSecret, wallets } = useSettingsStore()
  const hasCoinbase = Boolean(coinbaseKey && coinbaseSecret)
  const hasWallets  = wallets.length > 0

  // Coinbase accounts
  const cbQuery = useQuery<CoinbaseAccount[]>({
    queryKey: ['coinbase-accounts', coinbaseKey],
    queryFn: fetchCoinbaseAccounts,
    enabled: hasCoinbase,
  })

  // EVM balances — one query per (wallet × network) combination
  const evmQueries = useQueries({
    queries: wallets.flatMap((w) =>
      w.networks.map((net) => ({
        queryKey: ['evm-balance', w.address, net],
        queryFn: () => fetchEVMBalance(w.address, net),
        staleTime: 30_000,
      })),
    ),
  })

  const refetchAll = () => {
    cbQuery.refetch()
    evmQueries.forEach((q) => q.refetch())
  }

  const noConfig = !hasCoinbase && !hasWallets

  if (noConfig) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-center gap-4">
        <AlertCircle size={40} className="text-gray-600" />
        <div>
          <h2 className="text-lg font-semibold text-gray-200">No accounts configured</h2>
          <p className="text-sm text-gray-500 mt-1">Add your API keys or wallet addresses in Settings to get started.</p>
        </div>
        <button onClick={() => navigate('/settings')} className="btn-primary">Go to Settings</button>
      </div>
    )
  }

  // Summarise total across non-zero Coinbase accounts
  const cbAccounts: CoinbaseAccount[] = cbQuery.data ?? []
  const nonZeroCB = cbAccounts.filter((a) => parseFloat(a.available_balance.value) > 0)

  // Map EVM query results back to wallet/network pairs
  const evmResults: Array<{ wallet: typeof wallets[0]; network: string; result: EVMBalanceResult | undefined; isLoading: boolean; error: string | undefined }> = wallets.flatMap((w) =>
    w.networks.map((net, ni) => {
      const idx = wallets.slice(0, wallets.indexOf(w)).reduce((acc, prev) => acc + prev.networks.length, 0) + ni
      const q = evmQueries[idx]
      return {
        wallet: w,
        network: net,
        result: q?.data as EVMBalanceResult | undefined,
        isLoading: q?.isLoading ?? false,
        error: q?.isError ? String((q.error as Error)?.message ?? 'Error') : undefined,
      }
    }),
  )

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-100">Dashboard</h1>
          <p className="text-sm text-gray-500">Live balances across all connected accounts</p>
        </div>
        <button onClick={refetchAll} className="btn-secondary flex items-center gap-2">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Coinbase Section */}
      {hasCoinbase && (
        <section>
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Coinbase Advanced Trade</h2>
          {cbQuery.isLoading && (
            <div className="card animate-pulse h-28" />
          )}
          {cbQuery.isError && (
            <div className="card border-red-900/40">
              <p className="text-red-400 text-sm">Failed to load Coinbase accounts — verify your API keys in Settings.</p>
            </div>
          )}
          {!cbQuery.isLoading && !cbQuery.isError && nonZeroCB.length === 0 && (
            <div className="card">
              <p className="text-gray-500 text-sm">No accounts with a positive balance found.</p>
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {nonZeroCB.map((acc) => (
              <BalanceCard
                key={acc.uuid}
                platform="coinbase"
                label={acc.name}
                nativeSymbol={acc.currency}
                nativeBalance={parseFloat(acc.available_balance.value)}
                tokens={[]}
                onTransfer={() => navigate('/transfer', { state: { service: 'coinbase', accountUuid: acc.uuid, currency: acc.currency } })}
              />
            ))}
          </div>
        </section>
      )}

      {/* EVM Section */}
      {hasWallets && (
        <section>
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">EVM Wallets</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
            {evmResults.map(({ wallet, network, result, isLoading, error }) => (
              <BalanceCard
                key={`${wallet.id}-${network}`}
                platform="evm"
                network={network}
                label={wallet.label}
                address={wallet.address}
                nativeSymbol={result?.native.symbol}
                nativeBalance={result?.native.balance}
                tokens={result?.tokens ?? []}
                isLoading={isLoading}
                error={error}
                onTransfer={() =>
                  navigate('/transfer', {
                    state: { service: 'evm', network, fromAddress: wallet.address },
                  })
                }
              />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
