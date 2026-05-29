export interface CoinbaseAccount {
  uuid: string
  name: string
  currency: string
  available_balance: { value: string; currency: string }
  hold: { value: string; currency: string }
  type: string
}

export interface CoinbasePortfolio {
  uuid: string
  name: string
  deleted: boolean
  type: string
}

export interface EVMNativeBalance {
  symbol: string
  balance: number
  balance_raw: string
  name: string
}

export interface EVMTokenBalance {
  symbol: string
  address: string
  balance: number
  decimals: number
}

export interface EVMBalanceResult {
  network: string
  address: string
  native: EVMNativeBalance
  tokens: EVMTokenBalance[]
}

export interface EVMWallet {
  id: string
  label: string
  address: string
  networks: string[]
}

export interface Chain {
  id: string
  name: string
  symbol: string
  chain_id: number
}

export type ServiceType = 'coinbase' | 'evm'

export interface TransferFormState {
  service: ServiceType
  network: string
  fromAddress: string
  toAddress: string
  amount: string
  currency: string
  tokenAddress?: string
  tokenDecimals?: number
  privateKey: string
  // Coinbase portfolio move
  sourcePortfolioUuid?: string
  targetPortfolioUuid?: string
}
