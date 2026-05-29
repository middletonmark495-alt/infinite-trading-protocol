import { useQuery } from '@tanstack/react-query'
import { useSettingsStore } from '../store'
import { fetchOrders } from '../api'
import { RefreshCw, Package } from 'lucide-react'
import clsx from 'clsx'

const statusColor: Record<string, string> = {
  FILLED:    'badge-green',
  CANCELLED: 'badge-amber',
  PENDING:   'badge-blue',
  OPEN:      'badge-blue',
  FAILED:    'text-red-400',
}

export default function History() {
  const { coinbaseKey, coinbaseSecret } = useSettingsStore()
  const hasCoinbase = Boolean(coinbaseKey && coinbaseSecret)

  const ordersQuery = useQuery({
    queryKey: ['coinbase-orders'],
    queryFn: () => fetchOrders(50),
    enabled: hasCoinbase,
  })

  const orders: any[] = ordersQuery.data ?? []

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-100">Order History</h1>
          <p className="text-sm text-gray-500">Recent Coinbase Advanced Trade orders</p>
        </div>
        <button onClick={() => ordersQuery.refetch()} className="btn-secondary flex items-center gap-2">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {!hasCoinbase && (
        <div className="card flex flex-col items-center gap-3 py-12 text-center">
          <Package size={32} className="text-gray-600" />
          <p className="text-gray-400 text-sm">Add your Coinbase API keys in Settings to view order history.</p>
        </div>
      )}

      {hasCoinbase && ordersQuery.isLoading && (
        <div className="space-y-2">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="card animate-pulse h-14" />
          ))}
        </div>
      )}

      {hasCoinbase && !ordersQuery.isLoading && orders.length === 0 && (
        <div className="card flex flex-col items-center gap-3 py-12 text-center">
          <Package size={32} className="text-gray-600" />
          <p className="text-gray-400 text-sm">No orders found.</p>
        </div>
      )}

      {orders.length > 0 && (
        <div className="card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wide">
                <th className="px-4 py-3 text-left">Product</th>
                <th className="px-4 py-3 text-left">Side</th>
                <th className="px-4 py-3 text-left">Type</th>
                <th className="px-4 py-3 text-right">Size</th>
                <th className="px-4 py-3 text-right">Filled</th>
                <th className="px-4 py-3 text-left">Status</th>
                <th className="px-4 py-3 text-left">Created</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o: any, i: number) => (
                <tr
                  key={o.order_id ?? i}
                  className={clsx('border-b border-gray-800/40 hover:bg-gray-800/20 transition-colors', i === orders.length - 1 && 'border-0')}
                >
                  <td className="px-4 py-3 font-medium text-gray-200">{o.product_id}</td>
                  <td className="px-4 py-3">
                    <span className={o.side === 'BUY' ? 'text-emerald-400' : 'text-red-400'}>{o.side}</span>
                  </td>
                  <td className="px-4 py-3 text-gray-400">{o.order_type}</td>
                  <td className="px-4 py-3 text-right font-mono text-gray-300">{o.base_size ?? '—'}</td>
                  <td className="px-4 py-3 text-right font-mono text-gray-300">{o.filled_size ?? '—'}</td>
                  <td className="px-4 py-3">
                    <span className={statusColor[o.status] ?? 'text-gray-400'}>{o.status}</span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {o.created_time ? new Date(o.created_time).toLocaleDateString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
