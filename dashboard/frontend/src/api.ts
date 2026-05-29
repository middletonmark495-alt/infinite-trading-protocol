import axios from 'axios'
import { useSettingsStore } from './store'

const http = axios.create({ baseURL: '/api', timeout: 30_000 })

http.interceptors.request.use((config) => {
  const { coinbaseKey, coinbaseSecret } = useSettingsStore.getState()
  if (coinbaseKey)    config.headers['x-coinbase-key']    = coinbaseKey
  if (coinbaseSecret) config.headers['x-coinbase-secret'] = coinbaseSecret
  return config
})

// ── Coinbase ──────────────────────────────────────────────────────────────────

export const fetchCoinbaseAccounts = () =>
  http.get('/coinbase/accounts').then((r) => r.data.accounts)

export const fetchCoinbasePortfolios = () =>
  http.get('/coinbase/portfolios').then((r) => r.data.portfolios)

export const fetchPortfolioDetail = (uuid: string) =>
  http.get(`/coinbase/portfolio/${uuid}`).then((r) => r.data)

export const fetchPaymentMethods = () =>
  http.get('/coinbase/payment-methods').then((r) => r.data.payment_methods)

export const movePortfolioFunds = (data: {
  funds: string
  currency: string
  source_portfolio_uuid: string
  target_portfolio_uuid: string
}) => http.post('/coinbase/portfolio/move', data).then((r) => r.data)

export const createConvertQuote = (data: {
  from_account: string
  to_account: string
  amount: string
}) => http.post('/coinbase/convert/quote', data).then((r) => r.data)

export const commitConvert = (data: {
  trade_id: string
  from_account: string
  to_account: string
}) => http.post('/coinbase/convert/commit', data).then((r) => r.data)

export const fetchOrders = (limit = 25) =>
  http.get('/coinbase/orders', { params: { limit } }).then((r) => r.data.orders)

// ── EVM ───────────────────────────────────────────────────────────────────────

export const fetchChains = () =>
  http.get('/evm/chains').then((r) => r.data.chains)

export const fetchEVMBalance = (address: string, network: string) =>
  http.get('/evm/balance', { params: { address, network } }).then((r) => r.data)

export const sendEVMTransfer = (data: {
  from_address: string
  to_address: string
  amount: string
  network: string
  private_key: string
  rpc_url?: string
  token_address?: string
  token_decimals?: number
}) => http.post('/evm/transfer', data).then((r) => r.data)
