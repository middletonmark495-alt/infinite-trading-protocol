import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Plus, Trash2, CheckCircle2, Eye, EyeOff, Network } from 'lucide-react'
import { useSettingsStore } from '../store'
import { fetchCoinbaseAccounts } from '../api'
import { EVMWallet } from '../types'

const ALL_NETWORKS = ['ethereum', 'base', 'polygon', 'arbitrum', 'optimism']

function id() { return Math.random().toString(36).slice(2) }

export default function Settings() {
  const { coinbaseKey, coinbaseSecret, wallets, setKeys, addWallet, removeWallet, updateWallet, clearAll } = useSettingsStore()

  // Coinbase form
  const [cbKey, setCbKey] = useState(coinbaseKey)
  const [cbSecret, setCbSecret] = useState(coinbaseSecret)
  const [showSecret, setShowSecret] = useState(false)

  // Test connection
  const testMutation = useMutation({ mutationFn: fetchCoinbaseAccounts })

  const saveCoinbase = () => setKeys(cbKey.trim(), cbSecret.trim())

  // New wallet form
  const [newLabel, setNewLabel] = useState('')
  const [newAddr, setNewAddr] = useState('')
  const [newNetworks, setNewNetworks] = useState<string[]>(['ethereum'])

  const addNewWallet = () => {
    if (!newAddr.trim()) return
    const wallet: EVMWallet = {
      id: id(),
      label: newLabel.trim() || `Wallet ${wallets.length + 1}`,
      address: newAddr.trim(),
      networks: newNetworks,
    }
    addWallet(wallet)
    setNewLabel('')
    setNewAddr('')
    setNewNetworks(['ethereum'])
  }

  const toggleNetwork = (net: string) =>
    setNewNetworks((prev) => prev.includes(net) ? prev.filter((n) => n !== net) : [...prev, net])

  const toggleWalletNetwork = (walletId: string, net: string, currentNets: string[]) => {
    const updated = currentNets.includes(net)
      ? currentNets.filter((n) => n !== net)
      : [...currentNets, net]
    updateWallet(walletId, { networks: updated })
  }

  return (
    <div className="p-6 max-w-2xl space-y-8">
      <div>
        <h1 className="text-xl font-bold text-gray-100">Settings</h1>
        <p className="text-sm text-gray-500">API keys are stored only in your browser's local storage and never sent to any server other than the intended API.</p>
      </div>

      {/* ── Coinbase ─────────────────────────────────────────────────────────── */}
      <section className="card space-y-4">
        <h2 className="font-semibold text-gray-200 flex items-center gap-2">
          Coinbase Advanced Trade API
        </h2>
        <p className="text-xs text-gray-500">Create your keys at <span className="text-blue-400 font-mono">coinbase.com → Settings → API</span>. Enable <em>View</em> and <em>Trade</em> permissions.</p>

        <div>
          <label className="label">API Key</label>
          <input className="input font-mono text-xs" placeholder="Paste your Coinbase API key" value={cbKey} onChange={(e) => setCbKey(e.target.value)} />
        </div>
        <div>
          <label className="label">API Secret</label>
          <div className="relative">
            <input
              className="input font-mono text-xs pr-10"
              type={showSecret ? 'text' : 'password'}
              placeholder="Paste your Coinbase API secret"
              value={cbSecret}
              onChange={(e) => setCbSecret(e.target.value)}
            />
            <button type="button" onClick={() => setShowSecret((v) => !v)} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300">
              {showSecret ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button onClick={saveCoinbase} className="btn-primary">Save Keys</button>
          <button
            onClick={() => { saveCoinbase(); testMutation.mutate() }}
            className="btn-secondary"
            disabled={testMutation.isPending}
          >
            {testMutation.isPending ? 'Testing…' : 'Test Connection'}
          </button>
        </div>

        {testMutation.isSuccess && (
          <div className="flex items-center gap-2 text-emerald-400 text-sm">
            <CheckCircle2 size={15} />
            Connected — found {(testMutation.data as unknown[]).length} account(s)
          </div>
        )}
        {testMutation.isError && (
          <p className="text-red-400 text-sm">{String((testMutation.error as Error)?.message ?? 'Connection failed')}</p>
        )}
      </section>

      {/* ── EVM Wallets ──────────────────────────────────────────────────────── */}
      <section className="card space-y-4">
        <h2 className="font-semibold text-gray-200 flex items-center gap-2">
          <Network size={16} />
          EVM Wallets
        </h2>
        <p className="text-xs text-gray-500">Add wallet addresses to view balances. Private keys are only needed when initiating a transfer.</p>

        {/* Existing wallets */}
        {wallets.length > 0 && (
          <div className="space-y-3">
            {wallets.map((w) => (
              <div key={w.id} className="bg-navy-700 rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-200">{w.label}</p>
                    <p className="text-xs font-mono text-gray-500">{w.address}</p>
                  </div>
                  <button onClick={() => removeWallet(w.id)} className="btn-danger !py-1 !px-2">
                    <Trash2 size={13} />
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {ALL_NETWORKS.map((net) => (
                    <button
                      key={net}
                      onClick={() => toggleWalletNetwork(w.id, net, w.networks)}
                      className={`text-xs px-2 py-0.5 rounded-full border transition-colors ${
                        w.networks.includes(net)
                          ? 'bg-blue-600/20 text-blue-400 border-blue-500/40'
                          : 'bg-gray-800 text-gray-600 border-gray-700 hover:text-gray-400'
                      }`}
                    >
                      {net}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Add new wallet */}
        <div className="border border-dashed border-gray-700 rounded-lg p-4 space-y-3">
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Add wallet</p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Label (optional)</label>
              <input className="input" placeholder="My Business Wallet" value={newLabel} onChange={(e) => setNewLabel(e.target.value)} />
            </div>
            <div>
              <label className="label">Address</label>
              <input className="input font-mono text-xs" placeholder="0x…" value={newAddr} onChange={(e) => setNewAddr(e.target.value)} />
            </div>
          </div>
          <div>
            <label className="label">Networks to track</label>
            <div className="flex flex-wrap gap-1.5">
              {ALL_NETWORKS.map((net) => (
                <button
                  key={net}
                  onClick={() => toggleNetwork(net)}
                  className={`text-xs px-2 py-0.5 rounded-full border transition-colors ${
                    newNetworks.includes(net)
                      ? 'bg-blue-600/20 text-blue-400 border-blue-500/40'
                      : 'bg-gray-800 text-gray-600 border-gray-700 hover:text-gray-400'
                  }`}
                >
                  {net}
                </button>
              ))}
            </div>
          </div>
          <button onClick={addNewWallet} disabled={!newAddr.trim()} className="btn-primary flex items-center gap-2">
            <Plus size={14} /> Add Wallet
          </button>
        </div>
      </section>

      {/* ── Danger Zone ──────────────────────────────────────────────────────── */}
      <section className="card border-red-900/30 space-y-3">
        <h2 className="font-semibold text-red-400">Danger Zone</h2>
        <p className="text-xs text-gray-500">This will remove all saved API keys and wallet addresses from this browser.</p>
        <button onClick={() => { if (confirm('Clear all saved settings?')) clearAll() }} className="btn-danger">
          Clear All Settings
        </button>
      </section>
    </div>
  )
}
