"use strict";
/* ── ITP Dashboard — app.js ─────────────────────────────────────────────────
   Requires: ethers (UMD, global `ethers`), Chart.js (global `Chart`),
             config.js (global `ITP_CONFIG`), served by server.py
   ────────────────────────────────────────────────────────────────────────── */

const DAO = "0xfbC61F8A651622B82829046afb3f10AF666c19e1";

// ── State ──────────────────────────────────────────────────────────────────
const S = {
  walletAddr:  null,
  provider:    null,
  signer:      null,
  priceChart:  null,
  gasInterval: null,
};

// ── ABIs (minimal) ─────────────────────────────────────────────────────────
const ABI = {
  InfiniteBoost: [
    "function owner() view returns (address)",
    "function paused() view returns (bool)",
    "function feePercentage() view returns (uint256)",
    "function totalAssignedBoostRewards() view returns (uint256)",
    "function balanceOf(address,address) view returns (uint256)",
    "function pause()",
    "function unPause()",
    "function setFeePercentage(uint256)",
    "function setBoostPercentage(address,uint256)",
    "function addGauge(address,address,uint256,uint256)",
    "function removeGauge(address)",
    "function depositBoostReward(uint256)",
    "function withdrawBoostRewardToken(uint256)",
    "function emergencyWithdraw(address)",
    "function claimBaseRewardTokenOwner(address)",
  ],
  AutoCompoundVault: [
    "function totalShares() view returns (uint256)",
    "function userShares(address) view returns (uint256)",
    "function chainlinkKeeper() view returns (address)",
    "function deposit(uint256)",
    "function withdraw(uint256)",
  ],
  UniV3AutoCompounder: [
    "function owner() view returns (address)",
    "function dao() view returns (address)",
    "function DAO_FEE_BPS() view returns (uint256)",
    "function EXECUTOR_FEE_BPS() view returns (uint256)",
    "function compound()",
    "function rescueTokens(address,address,uint256)",
  ],
  ERC20: [
    "function balanceOf(address) view returns (uint256)",
    "function decimals() view returns (uint8)",
    "function approve(address,uint256)",
  ],
};

// ── Toast ──────────────────────────────────────────────────────────────────
function toast(msg, type = "info", ms = 4000) {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = msg;
  document.getElementById("toast-container").appendChild(el);
  setTimeout(() => el.remove(), ms);
}

// ── RPC helper (no wallet needed) ─────────────────────────────────────────
async function rpcCall(url, method, params = []) {
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }),
  });
  const data = await r.json();
  if (data.error) throw new Error(data.error.message);
  return data.result;
}

function hexToGwei(hex) {
  return (parseInt(hex, 16) / 1e9).toFixed(2);
}

function hexToEther(hex) {
  return (parseInt(hex, 16) / 1e18).toFixed(4);
}

function shortAddr(addr) {
  return addr ? `${addr.slice(0, 6)}…${addr.slice(-4)}` : "—";
}

// ── Navigation ─────────────────────────────────────────────────────────────
function showSection(id) {
  document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  document.getElementById(`sec-${id}`)?.classList.add("active");
  document.querySelector(`[data-section="${id}"]`)?.classList.add("active");
  if (id === "gas")     loadGas();
  if (id === "vault")   loadVault();
  if (id === "trading") loadTrading();
  if (id === "admin")   loadAdmin();
  if (id === "overview") loadOverview();
}

// ── Wallet connect ─────────────────────────────────────────────────────────
async function connectWallet() {
  if (!window.ethereum) { toast("MetaMask not detected", "error"); return; }
  try {
    const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
    S.walletAddr = accounts[0];
    S.provider   = new ethers.providers.Web3Provider(window.ethereum);
    S.signer     = S.provider.getSigner();
    document.getElementById("wallet-addr").textContent = shortAddr(S.walletAddr);
    document.getElementById("wallet-dot").className = "dot green";
    document.getElementById("wallet-btn").textContent = "Connected";
    toast("Wallet connected", "success");
    window.ethereum.on("accountsChanged", accs => { S.walletAddr = accs[0]; location.reload(); });
  } catch (e) {
    toast(e.message, "error");
  }
}

// ── Gas & Wallet Monitor ───────────────────────────────────────────────────
const NETWORKS = {
  ethereum: { name: "Ethereum",  rpc: "https://cloudflare-eth.com",      color: "#627eea" },
  base:     { name: "Base",      rpc: "https://mainnet.base.org",         color: "#0052ff" },
  optimism: { name: "Optimism",  rpc: "https://mainnet.optimism.io",      color: "#ff0420" },
};

async function fetchGas(rpc) {
  try {
    const hex = await rpcCall(rpc, "eth_gasPrice");
    return parseFloat(hexToGwei(hex));
  } catch { return null; }
}

async function fetchBalance(rpc, addr) {
  try {
    const hex = await rpcCall(rpc, "eth_getBalance", [addr, "latest"]);
    return parseFloat(hexToEther(hex));
  } catch { return null; }
}

async function loadGas() {
  const container = document.getElementById("gas-cards");
  container.innerHTML = Object.entries(NETWORKS).map(([k, n]) => `
    <div class="gas-card">
      <div class="gas-network" style="color:${n.color}">${n.name}</div>
      <div class="gas-row"><span class="gas-label">Gas Price</span><span class="gas-val" id="gas-${k}"><span class="spinner"></span></span></div>
      <div class="gas-row"><span class="gas-label">DAO Balance</span><span class="gas-val" id="bal-${k}"><span class="spinner"></span></span></div>
    </div>
  `).join("");

  await Promise.all(Object.entries(NETWORKS).map(async ([k, n]) => {
    const [gas, bal] = await Promise.all([fetchGas(n.rpc), fetchBalance(n.rpc, DAO)]);
    const gasEl = document.getElementById(`gas-${k}`);
    const balEl = document.getElementById(`bal-${k}`);
    if (gasEl) gasEl.innerHTML = gas !== null
      ? `<span class="${gas < 5 ? "text-green" : gas < 30 ? "" : "text-red"}">${gas} gwei</span>` : "—";
    if (balEl) balEl.textContent = bal !== null ? `${bal} ETH` : "—";
  }));
}

// ── Overview ───────────────────────────────────────────────────────────────
async function loadOverview() {
  const balEl = document.getElementById("ov-balance");
  const gasEl = document.getElementById("ov-gas");
  if (balEl) {
    const bal = await fetchBalance(NETWORKS.ethereum.rpc, DAO);
    balEl.textContent = bal !== null ? `${bal} ETH` : "—";
  }
  if (gasEl) {
    const gas = await fetchGas(NETWORKS.ethereum.rpc);
    gasEl.textContent = gas !== null ? `${gas} gwei` : "—";
  }
}

// ── Vault ──────────────────────────────────────────────────────────────────
async function loadVault() {
  const cfg = ITP_CONFIG.contracts.AutoCompoundVault;
  const el  = document.getElementById("vault-status");
  if (!cfg.address) {
    el.innerHTML = `<p class="text-muted">AutoCompoundVault not deployed yet. Run <code>forge script DeployAutoCompoundVault.s.sol</code> then add the address to <code>config.js</code>.</p>`;
    return;
  }
  try {
    const provider = new ethers.providers.JsonRpcProvider(cfg.rpc);
    const vault    = new ethers.Contract(cfg.address, ABI.AutoCompoundVault, provider);
    const [total, keeper] = await Promise.all([vault.totalShares(), vault.chainlinkKeeper()]);
    const userShares = S.walletAddr ? await vault.userShares(S.walletAddr) : null;
    el.innerHTML = `
      <div class="grid-3">
        <div class="card"><div class="card-title">Total Shares</div><div class="card-value">${ethers.utils.formatEther(total)}</div></div>
        <div class="card"><div class="card-title">Your Shares</div><div class="card-value">${userShares ? ethers.utils.formatEther(userShares) : "—"}</div><div class="card-sub">${S.walletAddr ? "" : "Connect wallet to view"}</div></div>
        <div class="card"><div class="card-title">Keeper</div><div class="card-value" style="font-size:14px" class="mono">${shortAddr(keeper)}</div></div>
      </div>`;
  } catch (e) {
    el.innerHTML = `<p class="text-red">Error loading vault: ${e.message}</p>`;
  }
}

async function vaultDeposit() {
  if (!S.signer) { toast("Connect wallet first", "error"); return; }
  const amt = document.getElementById("vault-deposit-amt").value;
  if (!amt || parseFloat(amt) <= 0) { toast("Enter an amount", "error"); return; }
  const cfg = ITP_CONFIG.contracts.AutoCompoundVault;
  if (!cfg.address) { toast("Vault address not configured", "error"); return; }
  try {
    const vault = new ethers.Contract(cfg.address, ABI.AutoCompoundVault, S.signer);
    const tx = await vault.deposit(ethers.utils.parseUnits(amt, 6)); // USDC = 6 decimals
    toast(`Deposit submitted: ${tx.hash.slice(0, 12)}…`, "info");
    await tx.wait();
    toast("Deposit confirmed!", "success");
    loadVault();
  } catch (e) {
    toast(e.reason || e.message, "error");
  }
}

async function vaultWithdraw() {
  if (!S.signer) { toast("Connect wallet first", "error"); return; }
  const shares = document.getElementById("vault-withdraw-shares").value;
  if (!shares || parseFloat(shares) <= 0) { toast("Enter share amount", "error"); return; }
  const cfg = ITP_CONFIG.contracts.AutoCompoundVault;
  if (!cfg.address) { toast("Vault address not configured", "error"); return; }
  try {
    const vault = new ethers.Contract(cfg.address, ABI.AutoCompoundVault, S.signer);
    const tx = await vault.withdraw(ethers.utils.parseEther(shares));
    toast(`Withdraw submitted: ${tx.hash.slice(0, 12)}…`, "info");
    await tx.wait();
    toast("Withdraw confirmed!", "success");
    loadVault();
  } catch (e) {
    toast(e.reason || e.message, "error");
  }
}

// ── Trading (Coinbase) ─────────────────────────────────────────────────────
const PAIRS = ["BTC-USD", "ETH-USD", "POL-USD", "SOL-USD", "LINK-USD"];
const TIMEFRAMES = { "1m": 60, "5m": 300, "15m": 900, "1h": 3600, "6h": 21600, "1d": 86400 };

async function fetchCandles(pair, tf) {
  const gran = TIMEFRAMES[tf] || 3600;
  const url  = `https://api.exchange.coinbase.com/products/${pair}/candles?granularity=${gran}`;
  const r    = await fetch(url);
  if (!r.ok) throw new Error(`${r.status}`);
  const raw = await r.json();
  // [timestamp, low, high, open, close, volume]
  return raw.slice(0, 200).reverse();
}

function renderChart(candles) {
  const ctx = document.getElementById("price-chart").getContext("2d");
  if (S.priceChart) S.priceChart.destroy();
  S.priceChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: candles.map(c => new Date(c[0] * 1000).toLocaleTimeString()),
      datasets: [{
        label: "Close",
        data:  candles.map(c => c[4]),
        borderColor: "#3b82f6",
        borderWidth: 1.5,
        pointRadius: 0,
        tension: 0.1,
        fill: { target: "origin", above: "rgba(59,130,246,.06)" },
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: { ticks: { color: "#64748b", maxTicksLimit: 8 }, grid: { color: "rgba(255,255,255,.04)" } },
        y: { ticks: { color: "#64748b" }, grid: { color: "rgba(255,255,255,.04)" } },
      },
      plugins: { legend: { display: false }, tooltip: { backgroundColor: "#1e2435", titleColor: "#e2e8f0", bodyColor: "#94a3b8" } },
    },
  });
}

async function loadTrading() {
  const pair = document.getElementById("chart-pair")?.value || "BTC-USD";
  const tf   = document.getElementById("chart-tf")?.value   || "1h";
  document.getElementById("chart-status").textContent = "Loading…";
  try {
    const candles = await fetchCandles(pair, tf);
    renderChart(candles);
    const last = candles[candles.length - 1];
    const prev = candles[candles.length - 2];
    const chg  = ((last[4] - prev[4]) / prev[4] * 100).toFixed(2);
    document.getElementById("chart-status").innerHTML =
      `<strong>$${last[4].toLocaleString()}</strong> &nbsp;<span class="${chg >= 0 ? "text-green" : "text-red"}">${chg >= 0 ? "+" : ""}${chg}%</span>`;
  } catch (e) {
    document.getElementById("chart-status").textContent = `Error: ${e.message}`;
  }
  loadAccounts();
}

async function loadAccounts() {
  const el = document.getElementById("accounts-list");
  if (!el) return;
  try {
    const r = await fetch("/api/coinbase/api/v3/brokerage/accounts");
    if (!r.ok) { el.innerHTML = `<p class="text-muted">Add COINBASE_API_KEY to .env to see balances.</p>`; return; }
    const data = await r.json();
    const accs = (data.accounts || []).filter(a => parseFloat(a.available_balance?.value || 0) > 0);
    if (!accs.length) { el.innerHTML = `<p class="text-muted">No balances or API key not set.</p>`; return; }
    el.innerHTML = `<table class="tbl"><thead><tr><th>Asset</th><th>Available</th><th>Hold</th></tr></thead><tbody>
      ${accs.map(a => `<tr>
        <td><strong>${a.currency}</strong></td>
        <td>${parseFloat(a.available_balance?.value || 0).toFixed(6)}</td>
        <td>${parseFloat(a.hold?.value || 0).toFixed(6)}</td>
      </tr>`).join("")}
    </tbody></table>`;
  } catch {
    el.innerHTML = `<p class="text-muted">Could not load accounts.</p>`;
  }
}

async function placeOrder() {
  const pair = document.getElementById("order-pair").value;
  const side = document.getElementById("order-side").value;
  const type = document.getElementById("order-type").value;
  const size = document.getElementById("order-size").value;
  const price = document.getElementById("order-price").value;

  if (!size) { toast("Enter a size", "error"); return; }

  let cfg;
  if (type === "market") {
    cfg = { market_market_ioc: { base_size: size } };
  } else {
    if (!price) { toast("Enter a limit price", "error"); return; }
    cfg = { limit_limit_gtc: { base_size: size, limit_price: price, post_only: false } };
  }

  const payload = {
    client_order_id: crypto.randomUUID(),
    product_id: pair,
    side,
    order_configuration: cfg,
  };

  try {
    const r = await fetch("/api/coinbase/api/v3/brokerage/orders", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(payload),
    });
    const data = await r.json();
    if (data.success) {
      toast(`Order placed: ${data.order_id}`, "success");
      loadOpenOrders();
    } else {
      toast(data.error_response?.message || "Order failed", "error");
    }
  } catch (e) {
    toast(e.message, "error");
  }
}

async function loadOpenOrders() {
  const el = document.getElementById("orders-list");
  if (!el) return;
  try {
    const r = await fetch("/api/coinbase/api/v3/brokerage/orders/historical/batch?order_status=OPEN");
    if (!r.ok) { el.innerHTML = `<p class="text-muted">—</p>`; return; }
    const data = await r.json();
    const orders = data.orders || [];
    if (!orders.length) { el.innerHTML = `<p class="text-muted">No open orders.</p>`; return; }
    el.innerHTML = `<table class="tbl"><thead><tr><th>Pair</th><th>Side</th><th>Type</th><th>Size</th><th>Price</th><th>Status</th><th></th></tr></thead><tbody>
      ${orders.map(o => {
        const cfg = o.order_configuration;
        const lim = cfg?.limit_limit_gtc || cfg?.limit_limit_gtd || {};
        return `<tr>
          <td>${o.product_id}</td>
          <td><span class="badge ${o.side === "BUY" ? "green" : "red"}">${o.side}</span></td>
          <td class="text-muted">${Object.keys(cfg || {})[0] || "—"}</td>
          <td>${lim.base_size || "—"}</td>
          <td>${lim.limit_price || "—"}</td>
          <td><span class="badge blue">${o.status}</span></td>
          <td><button class="btn btn-danger" style="padding:3px 10px;font-size:11px" onclick="cancelOrder('${o.order_id}')">✕</button></td>
        </tr>`;
      }).join("")}
    </tbody></table>`;
  } catch {
    el.innerHTML = `<p class="text-muted">Could not load orders.</p>`;
  }
}

async function cancelOrder(orderId) {
  try {
    const r = await fetch("/api/coinbase/api/v3/brokerage/orders/batch_cancel", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ order_ids: [orderId] }),
    });
    const data = await r.json();
    toast("Order cancelled", "success");
    loadOpenOrders();
  } catch (e) {
    toast(e.message, "error");
  }
}

// ── Admin — InfiniteBoost ──────────────────────────────────────────────────
async function loadAdmin() {
  const cfg = ITP_CONFIG.contracts.InfiniteBoost;
  const el  = document.getElementById("boost-status");
  if (!cfg.address) {
    el.innerHTML = `<p class="text-muted">InfiniteBoost not deployed. Run <code>forge script DeployInfiniteBoost.s.sol</code> then add the address to <code>config.js</code>.</p>`;
    return;
  }
  try {
    const provider = new ethers.providers.JsonRpcProvider(cfg.rpc);
    const boost    = new ethers.Contract(cfg.address, ABI.InfiniteBoost, provider);
    const [owner, paused, fee] = await Promise.all([boost.owner(), boost.paused(), boost.feePercentage()]);
    el.innerHTML = `
      <div class="grid-3">
        <div class="card"><div class="card-title">Status</div><div class="card-value"><span class="badge ${paused ? "red" : "green"}">${paused ? "PAUSED" : "ACTIVE"}</span></div></div>
        <div class="card"><div class="card-title">Fee</div><div class="card-value">${fee.toString()}%</div></div>
        <div class="card"><div class="card-title">Owner</div><div class="card-value" style="font-size:12px" class="mono">${shortAddr(owner)}</div></div>
      </div>`;
  } catch (e) {
    el.innerHTML = `<p class="text-red">Error: ${e.message}</p>`;
  }

  // UniV3AutoCompounder
  const cfgV3 = ITP_CONFIG.contracts.UniV3AutoCompounder;
  const elV3  = document.getElementById("v3-status");
  if (cfgV3.address) {
    try {
      const provider = new ethers.providers.JsonRpcProvider(cfgV3.rpc);
      const v3       = new ethers.Contract(cfgV3.address, ABI.UniV3AutoCompounder, provider);
      const [owner, dao, daoFee, execFee] = await Promise.all([
        v3.owner(), v3.dao(), v3.DAO_FEE_BPS(), v3.EXECUTOR_FEE_BPS()
      ]);
      elV3.innerHTML = `
        <div class="grid-3">
          <div class="card"><div class="card-title">Owner</div><div class="card-value" style="font-size:12px">${shortAddr(owner)}</div></div>
          <div class="card"><div class="card-title">DAO Fee</div><div class="card-value">${(daoFee/100).toFixed(1)}%</div></div>
          <div class="card"><div class="card-title">Executor Fee</div><div class="card-value">${(execFee/100).toFixed(1)}%</div></div>
        </div>`;
    } catch (e) {
      elV3.innerHTML = `<p class="text-red">Error: ${e.message}</p>`;
    }
  } else {
    elV3.innerHTML = `<p class="text-muted">UniV3AutoCompounder not deployed yet.</p>`;
  }
}

async function adminCall(contractKey, method, args = [], label = method) {
  if (!S.signer) { toast("Connect wallet first", "error"); return; }
  const cfg = ITP_CONFIG.contracts[contractKey];
  if (!cfg?.address) { toast("Contract address not configured", "error"); return; }
  const abi = ABI[contractKey];
  try {
    const contract = new ethers.Contract(cfg.address, abi, S.signer);
    await window.ethereum.request({ method: "wallet_switchEthereumChain", params: [{ chainId: `0x${cfg.chainId.toString(16)}` }] });
    const tx = await contract[method](...args);
    toast(`${label} submitted…`, "info");
    await tx.wait();
    toast(`${label} confirmed!`, "success");
    loadAdmin();
  } catch (e) {
    toast(e.reason || e.message, "error");
  }
}

function boostPause()   { adminCall("InfiniteBoost", "pause",   [], "Pause"); }
function boostUnpause() { adminCall("InfiniteBoost", "unPause", [], "Unpause"); }

function boostSetFee() {
  const val = document.getElementById("boost-fee-val").value;
  if (!val) { toast("Enter fee %", "error"); return; }
  adminCall("InfiniteBoost", "setFeePercentage", [parseInt(val)], "Set Fee");
}

function boostAddGauge() {
  const lp    = document.getElementById("gauge-lp").value;
  const gauge = document.getElementById("gauge-addr").value;
  const boost = document.getElementById("gauge-boost").value;
  const min   = document.getElementById("gauge-min").value;
  if (!lp || !gauge || !boost || !min) { toast("Fill all gauge fields", "error"); return; }
  adminCall("InfiniteBoost", "addGauge", [lp, gauge, parseInt(boost), ethers.utils.parseEther(min)], "Add Gauge");
}

function boostRemoveGauge() {
  const lp = document.getElementById("remove-gauge-lp").value;
  if (!lp) { toast("Enter LP address", "error"); return; }
  adminCall("InfiniteBoost", "removeGauge", [lp], "Remove Gauge");
}

function v3Compound() {
  adminCall("UniV3AutoCompounder", "compound", [], "Compound");
}

// ── Init ───────────────────────────────────────────────────────────────────
function init() {
  document.querySelectorAll(".nav-item").forEach(el => {
    el.addEventListener("click", () => showSection(el.dataset.section));
  });
  document.getElementById("wallet-btn").addEventListener("click", connectWallet);
  document.getElementById("loading-overlay").style.display = "none";
  showSection("overview");

  // Chart controls
  ["chart-pair", "chart-tf"].forEach(id => {
    document.getElementById(id)?.addEventListener("change", loadTrading);
  });
}

window.addEventListener("DOMContentLoaded", init);

// Expose globals for inline onclick handlers
Object.assign(window, {
  vaultDeposit, vaultWithdraw, placeOrder, loadOpenOrders,
  cancelOrder, boostPause, boostUnpause, boostSetFee,
  boostAddGauge, boostRemoveGauge, v3Compound,
});
