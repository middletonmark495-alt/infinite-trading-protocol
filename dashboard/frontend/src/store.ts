import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { EVMWallet } from './types'

interface Settings {
  coinbaseKey: string
  coinbaseSecret: string
  wallets: EVMWallet[]
}

interface SettingsStore extends Settings {
  setKeys: (key: string, secret: string) => void
  addWallet: (wallet: EVMWallet) => void
  removeWallet: (id: string) => void
  updateWallet: (id: string, patch: Partial<EVMWallet>) => void
  clearAll: () => void
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      coinbaseKey: '',
      coinbaseSecret: '',
      wallets: [],
      setKeys: (coinbaseKey, coinbaseSecret) => set({ coinbaseKey, coinbaseSecret }),
      addWallet: (wallet) => set((s) => ({ wallets: [...s.wallets, wallet] })),
      removeWallet: (id) => set((s) => ({ wallets: s.wallets.filter((w) => w.id !== id) })),
      updateWallet: (id, patch) =>
        set((s) => ({ wallets: s.wallets.map((w) => (w.id === id ? { ...w, ...patch } : w)) })),
      clearAll: () => set({ coinbaseKey: '', coinbaseSecret: '', wallets: [] }),
    }),
    { name: 'btd-settings' },
  ),
)
