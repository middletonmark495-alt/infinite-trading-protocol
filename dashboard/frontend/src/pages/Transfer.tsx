import { useState } from 'react'
import { useLocation } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle2, Loader2, Eye, EyeOff } from 'lucide-react'
import { useSettingsStore } from '../store'
import { fetchCoinbasePortfolios, movePortfolioFunds, sendEVMTransfer, fetchEVMBalance } from '../api'
import { CoinbasePortfolio, EVMBalanceResult } from '../types'
import clsx from 'clsx'

type Tab = 'evm' | 'coinbase-portfolio'

const NETWORKS = ['ethereum', 'base', 'polygon', 'arbitrum', 'optimism']

export default function Transfer() {
  const location = useLocation()
  const locationState = location.state as { service?: string; network?: string; fromAddress?: string } | null

  const { wallets, coinbaseKey, coinbaseSecret } = useSettingsStore()
  const hasCoinbase = Boolean(coinbaseKey && coinbaseSecret)

  const [tab, setTab] = useState<Tab>(
    locationState?.service === 'coinbase' ? 'coinbase-portfolio' : 'evm',
  )

  // ── EVM form ────────────────────────────────────────────────────────────────
  const [evmNetwork, setEvmNetwork] = useState(locationState?.network ?? 'ethereum')
  const [fromAddr, setFromAddr] = useState(locationState?.fromAddress ?? (wallets[0]?.address ?? ''))
  const [toAddr, setToAddr] = useState('')
  const [amount, setAmount] = useState('')
  const [privateKey, setPrivateKey] = useState('')
  const [showKey, setShowKey] = useState(false)
  const [tokenAddr, setTokenAddr] = useState('')
  const [tokenDec, setTokenDec] = useState('')

  const evmBalanceQuery = useQuery<EVMBalanceResult>({
    queryKey: ['evm-balance-transfer', fromAddr, evmNetwork],
    queryFn: () => fetchEVMBalance(fromAddr, evmNetwork),
    enabled: Boolean(fromAddr && evmNetwork),
  })

  const evmMutation = useMutation({
    mutationFn: () =>
      sendEVMTransfer({
        from_address: fromAddr,
        to_address: toAddr,
        amount,
        network: evmNetwork,
        private_key: privateKey,
        token_address: tokenAddr || undefined,
        token_decimals: tokenDec ? parseInt(tokenDec) : undefined,
      }),
  })

  // ── Coinbase portfolio form ──────────────────────────────────────────────────
  const portfoliosQuery = useQuery<CoinbasePortfolio[]>({
    queryKey: ['coinbase-portfolios'],
    queryFn: fetchCoinbasePortfolios,
    enabled: hasCoinbase && tab === 'coinbase-portfolio',
  })

  const [srcPortfolio, setSrcPortfolio] = useState('')
  const [dstPortfolio, setDstPortfolio] = useState('')
  const [cbFunds, setCbFunds] = useState('')
  const [cbCurrency, setCbCurrency] = useState('USDC')

  const cbMutation = useMutation({
    mutationFn: () =>
      movePortfolioFunds({
        funds: cbFunds,
        currency: cbCurrency,
        source_portfolio_uuid: srcPortfolio,
        target_portfolio_uuid: dstPortfolio,
      }),
  })

  const portfolios: CoinbasePortfolio[] = portfoliosQuery.data ?? []

  return (
    <div className="p-6 max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-100">Transfer</h1>
        <p className="text-sm text-gray-500">Send funds between accounts or to external addresses</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-navy-700 rounded-lg p-1 w-fit">
        {(['evm', 'coinbase-portfolio'] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={clsx(
              'px-4 py-1.5 rounded-md text-sm font-medium transition-colors',
              tab === t ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-gray-200',
            )}
          >
            {t === 'evm' ? 'EVM / Blockchain' : 'Coinbase Portfolios'}
          </button>
        ))}
      </div>

      {/* ── EVM Transfer ─────────────────────────────────────────────────────── */}
      {tab === 'evm' && (
        <div className="card space-y-4">
          <h2 className="font-semibold text-gray-200">Send on-chain</h2>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Network</label>
              <select className="input" value={evmNetwork} onChange={(e) => setEvmNetwork(e.target.value)}>
                {NETWORKS.map((n) => (
                  <option key={n} value={n}>{n.charAt(0).toUpperCase() + n.slice(1)}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">From wallet</label>
              {wallets.length > 0 ? (
                <select className="input" value={fromAddr} onChange={(e) => setFromAddr(e.target.value)}>
                  {wallets.map((w) => (
                    <option key={w.id} value={w.address}>{w.label} ({w.address.slice(0, 6)}…)</option>
                  ))}
                </select>
              ) : (
                <input className="input" placeholder="0x… your address" value={fromAddr} onChange={(e) => setFromAddr(e.target.value)} />
              )}
            </div>
          </div>

          {/* Live balance */}
          {evmBalanceQuery.data && (
            <div className="bg-navy-700 rounded-lg px-3 py-2 text-xs text-gray-400 font-mono space-y-0.5">
              <div className="flex justify-between">
                <span>{evmBalanceQuery.data.native.symbol} balance</span>
                <span className="text-gray-200">{evmBalanceQuery.data.native.balance.toLocaleString('en-US', { maximumFractionDigits: 6 })}</span>
              </div>
              {evmBalanceQuery.data.tokens.map((t) => (
                <div key={t.symbol} className="flex justify-between">
                  <span>{t.symbol}</span>
                  <span className="text-gray-300">{t.balance.toLocaleString('en-US', { maximumFractionDigits: 6 })}</span>
                </div>
              ))}
            </div>
          )}

          <div>
            <label className="label">To address</label>
            <input className="input font-mono" placeholder="0x…" value={toAddr} onChange={(e) => setToAddr(e.target.value)} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Amount</label>
              <input className="input" type="number" placeholder="0.0" value={amount} onChange={(e) => setAmount(e.target.value)} />
            </div>
            <div>
              <label className="label">Token contract (leave blank for native)</label>
              <input className="input font-mono text-xs" placeholder="0x… or blank for ETH/POL" value={tokenAddr} onChange={(e) => setTokenAddr(e.target.value)} />
            </div>
          </div>

          {tokenAddr && (
            <div>
              <label className="label">Token decimals</label>
              <input className="input" type="number" placeholder="18" value={tokenDec} onChange={(e) => setTokenDec(e.target.value)} />
            </div>
          )}

          <div>
            <label className="label flex items-center gap-1">
              <AlertTriangle size={11} className="text-amber-400" />
              Private key (used only for signing — never stored)
            </label>
            <div className="relative">
              <input
                className="input font-mono text-xs pr-10"
                type={showKey ? 'text' : 'password'}
                placeholder="0x…"
                value={privateKey}
                onChange={(e) => setPrivateKey(e.target.value)}
              />
              <button
                type="button"
                onClick={() => setShowKey((v) => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
              >
                {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
          </div>

          {evmMutation.isSuccess && (
            <div className="flex items-start gap-2 bg-emerald-900/20 border border-emerald-800/40 rounded-lg px-3 py-2.5">
              <CheckCircle2 size={15} className="text-emerald-400 mt-0.5 shrink-0" />
              <div className="text-xs">
                <p className="text-emerald-400 font-medium">Transaction sent!</p>
                <p className="text-gray-400 font-mono break-all">{(evmMutation.data as { tx_hash: string }).tx_hash}</p>
              </div>
            </div>
          )}
          {evmMutation.isError && (
            <div className="flex items-start gap-2 bg-red-900/20 border border-red-800/40 rounded-lg px-3 py-2.5">
              <AlertTriangle size={15} className="text-red-400 mt-0.5 shrink-0" />
              <p className="text-xs text-red-400">{String((evmMutation.error as Error)?.message ?? 'Transfer failed')}</p>
            </div>
          )}

          <button
            className="btn-primary w-full flex items-center justify-center gap-2"
            onClick={() => evmMutation.mutate()}
            disabled={evmMutation.isPending || !fromAddr || !toAddr || !amount || !privateKey}
          >
            {evmMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : null}
            {evmMutation.isPending ? 'Signing & Broadcasting…' : 'Send Transaction'}
          </button>
        </div>
      )}

      {/* ── Coinbase Portfolio Move ───────────────────────────────────────────── */}
      {tab === 'coinbase-portfolio' && (
        <div className="card space-y-4">
          {!hasCoinbase && (
            <p className="text-amber-400 text-sm">Add your Coinbase API keys in Settings first.</p>
          )}
          {hasCoinbase && (
            <>
              <h2 className="font-semibold text-gray-200">Move between Coinbase portfolios</h2>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Source portfolio</label>
                  <select className="input" value={srcPortfolio} onChange={(e) => setSrcPortfolio(e.target.value)}>
                    <option value="">Select…</option>
                    {portfolios.map((p) => (
                      <option key={p.uuid} value={p.uuid}>{p.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">Destination portfolio</label>
                  <select className="input" value={dstPortfolio} onChange={(e) => setDstPortfolio(e.target.value)}>
                    <option value="">Select…</option>
                    {portfolios.filter((p) => p.uuid !== srcPortfolio).map((p) => (
                      <option key={p.uuid} value={p.uuid}>{p.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Amount</label>
                  <input className="input" type="number" placeholder="0.0" value={cbFunds} onChange={(e) => setCbFunds(e.target.value)} />
                </div>
                <div>
                  <label className="label">Currency</label>
                  <input className="input" placeholder="USDC" value={cbCurrency} onChange={(e) => setCbCurrency(e.target.value.toUpperCase())} />
                </div>
              </div>

              {cbMutation.isSuccess && (
                <div className="flex items-center gap-2 bg-emerald-900/20 border border-emerald-800/40 rounded-lg px-3 py-2.5">
                  <CheckCircle2 size={15} className="text-emerald-400 shrink-0" />
                  <p className="text-xs text-emerald-400 font-medium">Funds moved successfully!</p>
                </div>
              )}
              {cbMutation.isError && (
                <div className="flex items-start gap-2 bg-red-900/20 border border-red-800/40 rounded-lg px-3 py-2.5">
                  <AlertTriangle size={15} className="text-red-400 mt-0.5 shrink-0" />
                  <p className="text-xs text-red-400">{String((cbMutation.error as Error)?.message ?? 'Move failed')}</p>
                </div>
              )}

              <button
                className="btn-primary w-full flex items-center justify-center gap-2"
                onClick={() => cbMutation.mutate()}
                disabled={cbMutation.isPending || !srcPortfolio || !dstPortfolio || !cbFunds}
              >
                {cbMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : null}
                {cbMutation.isPending ? 'Moving funds…' : 'Move Funds'}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  )
}
