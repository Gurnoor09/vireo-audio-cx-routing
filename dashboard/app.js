/**
 * Vireo Audio Support Desk Diagnostic - Dashboard Controller
 */

// Global State
let dashboardData = null;
let workloadChartInstance = null;
let monthlyChartInstance = null;
let csatTransfersChartInstance = null;
let financialChartInstance = null;
let currentWorkloadView = 'comparison';

// ─── NAVIGATION ────────────────────────────────────────────────────────────────
const TOTAL_STEPS = 6;
let currentStep = 1;

function goToStep(step) {
  if (step < 1 || step > TOTAL_STEPS) return;

  // Hide all screens
  document.querySelectorAll('.pres-screen').forEach(s => s.classList.remove('active'));
  // Show target screen
  const target = document.getElementById('screen-' + step);
  if (target) target.classList.add('active');

  // Update header step buttons
  document.querySelectorAll('.step-btn').forEach((btn, idx) => {
    btn.classList.toggle('active', idx + 1 === step);
  });

  // Update footer pill buttons
  document.querySelectorAll('.pill-btn').forEach((btn, idx) => {
    btn.classList.toggle('active', idx + 1 === step);
  });

  // Update counter label
  const counter = document.getElementById('step-counter');
  if (counter) counter.innerText = `Screen ${step} of ${TOTAL_STEPS}`;

  // Prev / Next button disabled state
  const btnPrev = document.getElementById('btn-prev');
  const btnNext = document.getElementById('btn-next');
  if (btnPrev) btnPrev.disabled = step === 1;
  if (btnNext) btnNext.disabled = step === TOTAL_STEPS;

  currentStep = step;
}

function prevStep() {
  goToStep(currentStep - 1);
}

function nextStep() {
  goToStep(currentStep + 1);
}
// ────────────────────────────────────────────────────────────────────────────────


// Embedded Fallback Data in case file:// CORS restricts fetch
const FALLBACK_DATA = {
  summary: {
    total_tickets: 11780,
    billing_intake_count: 2564,
    billing_resolved_count: 1838,
    logistics_intake_count: 1905,
    logistics_resolved_count: 2673,
    sla_breach_rate: 11.4,
    total_financial_opportunity_inr: 3198878
  },
  monthly_charts: {
    months: ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09", "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"],
    assigned_by_team: {
      "Billing": [71, 76, 104, 104, 83, 98, 97, 162, 143, 198, 219, 170, 143, 148, 159, 178, 144, 128],
      "Logistics": [43, 56, 75, 75, 75, 72, 85, 126, 120, 148, 172, 137, 122, 120, 127, 132, 115, 105],
      "Chat Frontline": [84, 95, 120, 101, 106, 102, 112, 180, 161, 207, 249, 220, 233, 198, 214, 237, 206, 205],
      "Email Frontline": [57, 58, 86, 68, 71, 67, 72, 107, 98, 127, 138, 114, 122, 128, 119, 144, 115, 116],
      "Voice Frontline": [26, 23, 37, 27, 41, 35, 38, 44, 56, 46, 72, 55, 72, 53, 53, 71, 73, 78],
      "Returns Desk": [26, 33, 46, 44, 42, 42, 37, 75, 70, 85, 82, 82, 70, 58, 71, 60, 53, 73],
      "Escalations & Warranty": [15, 14, 25, 23, 21, 23, 24, 39, 25, 34, 42, 37, 36, 33, 37, 42, 36, 19]
    },
    resolving_by_team: {
      "Billing": [53, 56, 80, 75, 66, 68, 69, 123, 94, 143, 152, 128, 115, 103, 131, 137, 108, 97],
      "Logistics": [61, 76, 99, 104, 92, 102, 113, 165, 169, 203, 239, 179, 150, 165, 155, 173, 151, 136],
      "Chat Frontline": [82, 100, 120, 98, 113, 110, 111, 175, 176, 200, 250, 227, 225, 216, 213, 237, 214, 211],
      "Email Frontline": [50, 50, 78, 62, 60, 57, 65, 96, 91, 119, 131, 106, 116, 113, 114, 133, 102, 105],
      "Voice Frontline": [24, 19, 33, 20, 35, 31, 34, 39, 42, 43, 60, 43, 63, 48, 44, 61, 65, 62],
      "Returns Desk": [28, 32, 44, 40, 40, 45, 40, 74, 82, 85, 96, 88, 75, 65, 77, 67, 60, 79],
      "Escalations & Warranty": [24, 22, 39, 43, 39, 26, 34, 61, 39, 52, 46, 44, 44, 38, 46, 56, 42, 34]
    }
  },
  csat_transfers: [
    { transfers: 0, count: 3017, avg_csat: 3.52 },
    { transfers: 1, count: 424, avg_csat: 2.75 },
    { transfers: 2, count: 101, avg_csat: 2.66 }
  ],
  financial_items: [
    { name: "Billing Headcount Avoidance", amount: 900000, type: "saving" },
    { name: "SLA Response Breach Credits", amount: 469000, type: "waste" },
    { name: "Repeat Contacts (FCR)", amount: 874820, type: "waste" },
    { name: "Inter-Team Transfer Waste", amount: 396195, type: "waste" },
    { name: "Double-Dipping (Refund+Repl)", amount: 394616, type: "waste" },
    { name: "Goodwill Cap Overages", amount: 53428, type: "waste" }
  ],
  scenarios: [
    {
      id: "sc-1",
      label: "Payment debited, order not delivered",
      message: "Paid via UPI, money was deducted from my account but no order confirmation was generated and nothing has arrived. Please help!",
      bot_category: "Billing & Payments",
      bot_assigned: "Billing",
      bot_status: "MISROUTED",
      ai_category: "Order Fulfillment & Logistics",
      ai_assigned: "Logistics",
      ai_status: "OPTIMAL ROUTING",
      explanation: "The legacy keyword bot detected 'paid/money' and dumped the ticket into Billing. However, the order was never fulfilled and requires warehouse tracking and logistics intervention. The AI router routes directly to Logistics, saving ₹305 in transfer costs and preventing a 24h triage delay.",
      cost_saved_inr: 305
    },
    {
      id: "sc-2",
      label: "GST invoice request for company",
      message: "Bought Pulse2 on vireo.in for our office. Please regenerate the invoice with my company GSTIN: 29ABCDE1234F1Z5.",
      bot_category: "Billing & Payments",
      bot_assigned: "Billing",
      bot_status: "CORRECT ROUTING",
      ai_category: "Invoicing & Tax",
      ai_assigned: "Billing",
      ai_status: "OPTIMAL ROUTING",
      explanation: "Both the bot and AI correctly identify this as a pure billing and tax invoice request. Resolvable within minutes by Billing agents.",
      cost_saved_inr: 0
    },
    {
      id: "sc-3",
      label: "Return pickup done, refund pending",
      message: "Returned my AirLite 10 days back. The courier picked it up from my house, but refund has still not been credited to my bank account.",
      bot_category: "Billing & Payments",
      bot_assigned: "Billing",
      bot_status: "MISROUTED",
      ai_category: "Returns & Reverse Logistics",
      ai_assigned: "Returns Desk",
      ai_status: "OPTIMAL ROUTING",
      explanation: "The legacy bot triggered on 'refund' and misrouted to Billing. Return reverse pickups and QC refund clearances are exclusively owned by Returns Desk (Policy §6). AI router saves ₹305 transfer overhead.",
      cost_saved_inr: 305
    },
    {
      id: "sc-4",
      label: "Right earbud buzzing / charging dead",
      message: "The right earbud of my Strata 3 has a persistent buzzing sound and stopped charging entirely after 2 weeks of use.",
      bot_category: "Other",
      bot_assigned: "Chat Frontline",
      bot_status: "INEFFICIENT TRIAGE",
      ai_category: "Hardware Fault / Warranty RMA",
      ai_assigned: "Escalations & Warranty",
      ai_status: "OPTIMAL ROUTING",
      explanation: "The legacy bot failed to classify and dumped this into Frontline as 'Other'. Because it is a hardware failure requiring Tier 2 warranty replacement certification (Policy §6), frontline agents cannot approve it and must transfer it. AI router sends directly to Tier 2.",
      cost_saved_inr: 305
    },
    {
      id: "sc-5",
      label: "Courier tracking stuck for 7 days",
      message: "Order VR902188 tracking has shown 'Out for delivery' by BlueDart for 7 days now. Delivery boy is not answering.",
      bot_category: "Other",
      bot_assigned: "Chat Frontline",
      bot_status: "INEFFICIENT TRIAGE",
      ai_category: "Courier Escalation & Tracking",
      ai_assigned: "Logistics",
      ai_status: "OPTIMAL ROUTING",
      explanation: "Another ticket dumped into 'Other' by the bot that actually belongs to Logistics delivery expediting. Direct AI routing saves re-handling time and improves CSAT.",
      cost_saved_inr: 305
    }
  ]
};

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const response = await fetch('data.json');
    if (response.ok) {
      dashboardData = await response.json();
    } else {
      dashboardData = FALLBACK_DATA;
    }
  } catch (e) {
    console.warn("Using embedded fallback data due to fetch error/CORS:", e);
    dashboardData = FALLBACK_DATA;
  }

  initWorkloadChart();
  initMonthlyChart();
  initCsatTransfersChart();
  initFinancialChart();
  initSimulator();
  goToStep(1); // set initial nav state
});


// 1. WORKLOAD COMPARISON CHART
function initWorkloadChart() {
  const ctx = document.getElementById('workloadChart').getContext('2d');
  const teams = ['Logistics', 'Billing', 'Chat Frontline', 'Email Frontline', 'Returns Desk', 'Voice Frontline', 'Escalations & Wty'];
  
  // Data points
  const assignedData = [1905, 2564, 3030, 1807, 1049, 900, 525];
  const resolvedData = [2673, 1838, 3078, 1604, 1067, 766, 754];

  workloadChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: teams,
      datasets: [
        {
          label: 'Assigned Intake (Bot Routing)',
          data: assignedData,
          backgroundColor: 'rgba(99, 102, 241, 0.7)',
          borderColor: '#6366F1',
          borderWidth: 1,
          borderRadius: 6
        },
        {
          label: 'Actually Resolved (Real Workload)',
          data: resolvedData,
          backgroundColor: 'rgba(236, 72, 153, 0.7)',
          borderColor: '#EC4899',
          borderWidth: 1,
          borderRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#9CA3AF', font: { family: 'Inter', size: 12 } }
        },
        tooltip: {
          callbacks: {
            footer: (items) => {
              const team = items[0].label;
              if (team === 'Billing') return '⚠️ 33.5% (860 tickets) misrouted away from Billing!';
              if (team === 'Logistics') return '🔥 Logistics resolved +768 tickets (+40.3%) over intake!';
              return '';
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9CA3AF', font: { family: 'Inter', size: 11 } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9CA3AF', font: { family: 'Inter', size: 11 } }
        }
      }
    }
  });
}

function switchWorkloadView(view) {
  currentWorkloadView = view;
  document.querySelectorAll('.btn-group .toggle-btn').forEach(btn => btn.classList.remove('active'));
  
  const assignedData = [1905, 2564, 3030, 1807, 1049, 900, 525];
  const resolvedData = [2673, 1838, 3078, 1604, 1067, 766, 754];
  const subtitle = document.getElementById('workload-chart-subtitle');

  if (view === 'comparison') {
    document.getElementById('btn-view-comparison').classList.add('active');
    subtitle.innerText = 'Side-by-side comparison: tickets assigned by bot vs tickets actually resolved by team agents';
    workloadChartInstance.data.datasets = [
      {
        label: 'Assigned Intake (Bot Routing)',
        data: assignedData,
        backgroundColor: 'rgba(99, 102, 241, 0.7)',
        borderColor: '#6366F1',
        borderWidth: 1,
        borderRadius: 6
      },
      {
        label: 'Actually Resolved (Real Workload)',
        data: resolvedData,
        backgroundColor: 'rgba(236, 72, 153, 0.7)',
        borderColor: '#EC4899',
        borderWidth: 1,
        borderRadius: 6
      }
    ];
  } else if (view === 'assigned') {
    document.getElementById('btn-view-assigned').classList.add('active');
    subtitle.innerText = "Priya's Assumption: Raw intake queue shows Billing as #2 biggest (22% share) and Logistics at 16%";
    workloadChartInstance.data.datasets = [
      {
        label: 'Assigned Intake (Bot Routing)',
        data: assignedData,
        backgroundColor: 'rgba(99, 102, 241, 0.85)',
        borderColor: '#6366F1',
        borderWidth: 1,
        borderRadius: 6
      }
    ];
  } else if (view === 'resolving') {
    document.getElementById('btn-view-resolving').classList.add('active');
    subtitle.innerText = "Operational Reality: Logistics resolves 2,673 tickets (535/agent), while Billing resolves only 1,838 (460/agent)";
    workloadChartInstance.data.datasets = [
      {
        label: 'Actually Resolved (Real Workload)',
        data: resolvedData,
        backgroundColor: 'rgba(236, 72, 153, 0.85)',
        borderColor: '#EC4899',
        borderWidth: 1,
        borderRadius: 6
      }
    ];
  }
  workloadChartInstance.update();
}

// 2. MONTHLY VOLUME CHART
function initMonthlyChart() {
  const ctx = document.getElementById('monthlyChart').getContext('2d');
  const months = dashboardData.monthly_charts.months;
  const resolving = dashboardData.monthly_charts.resolving_by_team;

  monthlyChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: months,
      datasets: [
        {
          label: 'Logistics (Resolved)',
          data: resolving['Logistics'],
          borderColor: '#EF4444',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          borderWidth: 3,
          tension: 0.3,
          fill: true
        },
        {
          label: 'Billing (Resolved)',
          data: resolving['Billing'],
          borderColor: '#10B981',
          backgroundColor: 'transparent',
          borderWidth: 2,
          borderDash: [5, 5],
          tension: 0.3
        },
        {
          label: 'Chat Frontline',
          data: resolving['Chat Frontline'],
          borderColor: '#6366F1',
          backgroundColor: 'transparent',
          borderWidth: 2,
          tension: 0.3
        },
        {
          label: 'Email Frontline',
          data: resolving['Email Frontline'],
          borderColor: '#3B82F6',
          backgroundColor: 'transparent',
          borderWidth: 2,
          tension: 0.3
        },
        {
          label: 'Returns Desk',
          data: resolving['Returns Desk'],
          borderColor: '#F59E0B',
          backgroundColor: 'transparent',
          borderWidth: 2,
          tension: 0.3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#9CA3AF', font: { family: 'Inter', size: 12 } }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9CA3AF', font: { family: 'Inter', size: 10 } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9CA3AF', font: { family: 'Inter', size: 11 } }
        }
      }
    }
  });
}

function updateMonthlyChart() {
  const filterType = document.getElementById('monthly-filter-type').value;
  const months = dashboardData.monthly_charts.months;

  if (filterType === 'resolving') {
    const res = dashboardData.monthly_charts.resolving_by_team;
    monthlyChartInstance.data.datasets = [
      { label: 'Logistics (Resolved)', data: res['Logistics'], borderColor: '#EF4444', backgroundColor: 'rgba(239, 68, 68, 0.15)', borderWidth: 3, tension: 0.3, fill: true },
      { label: 'Billing (Resolved)', data: res['Billing'], borderColor: '#10B981', borderWidth: 2, borderDash: [5, 5], tension: 0.3 },
      { label: 'Chat Frontline', data: res['Chat Frontline'], borderColor: '#6366F1', borderWidth: 2, tension: 0.3 },
      { label: 'Email Frontline', data: res['Email Frontline'], borderColor: '#3B82F6', borderWidth: 2, tension: 0.3 },
      { label: 'Returns Desk', data: res['Returns Desk'], borderColor: '#F59E0B', borderWidth: 2, tension: 0.3 }
    ];
  } else if (filterType === 'assigned') {
    const ass = dashboardData.monthly_charts.assigned_by_team;
    monthlyChartInstance.data.datasets = [
      { label: 'Billing (Assigned Intake)', data: ass['Billing'], borderColor: '#10B981', backgroundColor: 'rgba(16, 185, 129, 0.15)', borderWidth: 3, tension: 0.3, fill: true },
      { label: 'Logistics (Assigned Intake)', data: ass['Logistics'], borderColor: '#EF4444', borderWidth: 2, tension: 0.3 },
      { label: 'Chat Frontline', data: ass['Chat Frontline'], borderColor: '#6366F1', borderWidth: 2, tension: 0.3 },
      { label: 'Email Frontline', data: ass['Email Frontline'], borderColor: '#3B82F6', borderWidth: 2, tension: 0.3 },
      { label: 'Returns Desk', data: ass['Returns Desk'], borderColor: '#F59E0B', borderWidth: 2, tension: 0.3 }
    ];
  } else if (filterType === 'category') {
    const cats = dashboardData.monthly_charts.category_by_month;
    if (cats) {
      monthlyChartInstance.data.datasets = [
        { label: 'Billing & Payments', data: cats['Billing & Payments'], borderColor: '#10B981', borderWidth: 2, tension: 0.3 },
        { label: 'Delivery & Shipping', data: cats['Delivery & Shipping'], borderColor: '#EF4444', borderWidth: 2, tension: 0.3 },
        { label: 'Other', data: cats['Other'], borderColor: '#8B5CF6', borderWidth: 2, tension: 0.3 },
        { label: 'Returns & Refunds', data: cats['Returns & Refunds'], borderColor: '#F59E0B', borderWidth: 2, tension: 0.3 },
        { label: 'Connectivity', data: cats['Connectivity'], borderColor: '#3B82F6', borderWidth: 2, tension: 0.3 }
      ];
    }
  }
  monthlyChartInstance.update();
}

// 3. CSAT VS TRANSFERS CHART
function initCsatTransfersChart() {
  const ctx = document.getElementById('csatTransfersChart').getContext('2d');
  const data = dashboardData.csat_transfers;

  csatTransfersChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['0 Transfers (Direct)', '1 Transfer (Hand-off)', '2 Transfers (Multi-hop)'],
      datasets: [{
        label: 'Average CSAT Score (1–5)',
        data: data.map(d => d.avg_csat),
        backgroundColor: [
          'rgba(16, 185, 129, 0.7)',
          'rgba(245, 158, 11, 0.7)',
          'rgba(239, 68, 68, 0.7)'
        ],
        borderColor: ['#10B981', '#F59E0B', '#EF4444'],
        borderWidth: 1,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        y: {
          min: 2.0,
          max: 4.0,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9CA3AF' }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#9CA3AF', font: { size: 10 } }
        }
      }
    }
  });
}

// 4. FINANCIAL OPPORTUNITY CHART
function initFinancialChart() {
  const ctx = document.getElementById('financialChart').getContext('2d');
  const items = dashboardData.financial_items;

  financialChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: items.map(i => i.name.replace(' (', '\n(')),
      datasets: [{
        label: 'Addressable Value (₹)',
        data: items.map(i => i.amount),
        backgroundColor: [
          'rgba(16, 185, 129, 0.75)', // Headcount
          'rgba(99, 102, 241, 0.75)', // SLA
          'rgba(59, 130, 246, 0.75)', // Repeat
          'rgba(245, 158, 11, 0.75)', // Transfers
          'rgba(239, 68, 68, 0.75)',  // Double dip
          'rgba(236, 72, 153, 0.75)'  // Goodwill
        ],
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (item) => `₹${item.raw.toLocaleString('en-IN')}`
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: {
            color: '#9CA3AF',
            callback: (val) => `₹${(val / 100000).toFixed(1)}L`
          }
        },
        y: {
          grid: { display: false },
          ticks: { color: '#9CA3AF', font: { size: 11 } }
        }
      }
    }
  });
}

// 5. INTERACTIVE SMART ROUTER SIMULATOR
function initSimulator() {
  const container = document.getElementById('scenario-buttons');
  if (!container || !dashboardData.scenarios) return;

  dashboardData.scenarios.forEach((sc, idx) => {
    const btn = document.createElement('button');
    btn.className = `scenario-btn ${idx === 0 ? 'active' : ''}`;
    btn.innerText = `Scenario ${idx + 1}: ${sc.label}`;
    btn.onclick = () => selectScenario(sc, btn);
    container.appendChild(btn);
  });

  // Select first scenario by default
  selectScenario(dashboardData.scenarios[0]);
}

function selectScenario(sc, clickedBtn) {
  if (clickedBtn) {
    document.querySelectorAll('.scenario-btn').forEach(b => b.classList.remove('active'));
    clickedBtn.classList.add('active');
  }

  document.getElementById('custom-ticket-input').value = sc.message;
  displaySimulationResult(sc);
}

function runSimulation() {
  const text = document.getElementById('custom-ticket-input').value.toLowerCase();
  if (!text.trim()) return;

  // Simulate Legacy Bot Rule:
  // If text mentions payment/paid/debited/charged/money/upi/card/cost/price -> 'Billing & Payments' -> 'Billing'
  let botCat = 'Other';
  let botTeam = 'Chat Frontline';
  let isBotMisrouted = false;

  const paymentKeywords = ['paid', 'payment', 'money', 'deducted', 'debited', 'charged', 'upi', 'card', 'bank', 'cost', 'price', 'refund'];
  const deliveryKeywords = ['deliver', 'delivery', 'courier', 'track', 'tracking', 'dispatch', 'ship', 'transit', 'delayed', 'arrived', 'rto', 'package', 'box', 'order not'];
  const returnKeywords = ['return', 'pickup', 'pick up', 'exchange'];
  const hardwareKeywords = ['buzz', 'static', 'noise', 'defect', 'broken', 'not working', 'charging', 'left ear', 'right ear', 'bluetooth', 'pairing', 'audio'];
  const invoiceKeywords = ['gst', 'gstin', 'invoice', 'bill', 'receipt', 'tax invoice'];

  if (paymentKeywords.some(kw => text.includes(kw))) {
    botCat = 'Billing & Payments';
    botTeam = 'Billing';
  } else if (deliveryKeywords.some(kw => text.includes(kw))) {
    botCat = 'Delivery & Shipping';
    botTeam = 'Logistics';
  } else if (returnKeywords.some(kw => text.includes(kw))) {
    botCat = 'Returns & Refunds';
    botTeam = 'Returns Desk';
  } else if (hardwareKeywords.some(kw => text.includes(kw))) {
    botCat = 'Connectivity';
    botTeam = 'Chat Frontline';
  }

  // AI Router True Intent Logic:
  let aiCat = 'General Enquiry';
  let aiTeam = 'Chat Frontline';
  let explanation = '';

  if (invoiceKeywords.some(kw => text.includes(kw))) {
    aiCat = 'Billing & Invoicing';
    aiTeam = 'Billing';
    explanation = 'Explicit request for tax/GST invoice generation. Correctly owned by Billing.';
  } else if (returnKeywords.some(kw => text.includes(kw))) {
    aiCat = 'Returns & Reverse Logistics';
    aiTeam = 'Returns Desk';
    explanation = 'Return pickup and refund processing. Exclusively owned by Returns Desk per Policy §6.';
  } else if (deliveryKeywords.some(kw => text.includes(kw))) {
    aiCat = 'Delivery & Fulfillment';
    aiTeam = 'Logistics';
    explanation = 'Delivery, carrier delay, or tracking issue. Even if the customer mentions "payment" or "paid", the primary operational failure is shipping fulfillment. Belonged directly to Logistics.';
  } else if (hardwareKeywords.some(kw => text.includes(kw))) {
    aiCat = 'Hardware Fault & RMA';
    aiTeam = 'Escalations & Warranty';
    explanation = 'Hardware audio artifact or charging defect requiring Tier 2 certified warranty evaluation (Policy §6).';
  } else if (paymentKeywords.some(kw => text.includes(kw))) {
    aiCat = 'Payment Gateway & Transactions';
    aiTeam = 'Billing';
    explanation = 'Direct payment transaction dispute without fulfillment component.';
  }

  isBotMisrouted = botTeam !== aiTeam;

  const resultObj = {
    bot_category: botCat,
    bot_assigned: botTeam,
    bot_status: isBotMisrouted ? 'MISROUTED' : 'CORRECT ROUTING',
    ai_category: aiCat,
    ai_assigned: aiTeam,
    ai_status: 'OPTIMAL ROUTING',
    cost_saved_inr: isBotMisrouted ? 305 : 0,
    explanation: isBotMisrouted 
      ? `The legacy bot matched payment keywords and assigned to ${botTeam}. However, the customer's true operational intent is ${aiCat}, which belongs to ${aiTeam}. The AI router eliminates the inter-team transfer, saving ₹305 in handling fees and preventing a 24+ hour resolution delay.`
      : explanation
  };

  displaySimulationResult(resultObj);
}

function displaySimulationResult(res) {
  // Bot box
  document.getElementById('bot-category-val').innerText = res.bot_category;
  document.getElementById('bot-team-val').innerText = res.bot_assigned;
  
  const botStatusBadge = document.getElementById('bot-status-badge');
  botStatusBadge.innerText = res.bot_status;
  if (res.bot_status === 'MISROUTED') {
    botStatusBadge.className = 'sim-status-badge';
    document.getElementById('bot-action-val').innerText = 'Manual triage required; re-tagged & transferred';
    document.getElementById('bot-cost-val').innerText = '+₹305 Transfer Fee + SLA Breach Delay';
    document.getElementById('bot-cost-val').className = 'sim-val danger-text';
  } else {
    botStatusBadge.className = 'sim-status-badge success';
    document.getElementById('bot-action-val').innerText = 'Direct resolution by assigned team';
    document.getElementById('bot-cost-val').innerText = 'No transfer fee incurred';
    document.getElementById('bot-cost-val').className = 'sim-val success-text';
  }

  // AI box
  document.getElementById('ai-category-val').innerText = res.ai_category;
  document.getElementById('ai-team-val').innerText = res.ai_assigned;
  document.getElementById('ai-status-badge').innerText = res.ai_status;
  document.getElementById('ai-action-val').innerText = `Direct dispatch to ${res.ai_assigned} specialist`;
  
  if (res.cost_saved_inr > 0) {
    document.getElementById('ai-cost-val').innerText = '₹305 Transfer Saved & Zero Triage Delay';
  } else {
    document.getElementById('ai-cost-val').innerText = 'Optimally Handled (0 Transfers)';
  }

  // Explanation
  document.getElementById('sim-explanation-text').innerText = res.explanation;
}

// ─── SCREEN 4: AI ROUTER DEMO (maps to live-* IDs in HTML) ───────────────────

const DEMO_SCENARIOS = [
  {
    message: "Paid via UPI, money was deducted from my account but no order confirmation was generated and nothing has arrived. Please help!",
    botDest: "Billing",
    botStatus: "MISROUTED",
    botReason: "Triggered on \"paid / deducted\" payment keywords",
    aiDest: "Logistics",
    aiStatus: "CORRECT DISPATCH",
    aiReason: "Delivery failure — order never fulfilled despite payment. Belongs to Logistics."
  },
  {
    message: "Returned my AirLite 10 days back. The courier picked it up from my house, but refund has still not been credited to my bank account.",
    botDest: "Billing",
    botStatus: "MISROUTED",
    botReason: "Triggered on \"refund / bank account\" keywords",
    aiDest: "Returns Desk",
    aiStatus: "CORRECT DISPATCH",
    aiReason: "Reverse pickup completed — QC & refund clearance owned by Returns Desk (Policy §6)."
  },
  {
    message: "Bought Pulse2 on vireo.in for our office. Please regenerate the invoice with my company GSTIN: 29ABCDE1234F1Z5.",
    botDest: "Billing",
    botStatus: "CORRECT ROUTING",
    botReason: "Invoice / GST keywords correctly matched",
    aiDest: "Billing",
    aiStatus: "CORRECT DISPATCH",
    aiReason: "Explicit B2B GST invoice request. Correctly owned by Billing."
  }
];

function applyDemoResult(sc) {
  const botDest   = document.getElementById('live-bot-dest');
  const botStatus = document.getElementById('live-bot-status');
  const botReason = document.getElementById('live-bot-reason');
  const aiDest    = document.getElementById('live-ai-dest');
  const aiStatus  = document.getElementById('live-ai-status');
  const aiReason  = document.getElementById('live-ai-reason');

  if (botDest)   botDest.innerText   = sc.botDest;
  if (botReason) botReason.innerText = sc.botReason;
  if (aiDest)    aiDest.innerText    = sc.aiDest;
  if (aiReason)  aiReason.innerText  = sc.aiReason;

  if (botStatus) {
    botStatus.innerText = sc.botStatus;
    botStatus.className = sc.botStatus === 'MISROUTED'
      ? 'status-pill danger'
      : 'status-pill success';
  }
  if (aiStatus) {
    aiStatus.innerText  = sc.aiStatus;
    aiStatus.className  = 'status-pill success';
  }

  // colour the destination text
  if (botDest) {
    botDest.className = sc.botStatus === 'MISROUTED'
      ? 'p-v danger-text'
      : 'p-v success-text';
  }
  if (aiDest) aiDest.className = 'p-v success-text';
}

function loadDemoScenario(num) {
  const sc = DEMO_SCENARIOS[num - 1];
  if (!sc) return;

  // highlight active preset button
  document.querySelectorAll('.preset-btn').forEach((b, i) => {
    b.classList.toggle('active', i + 1 === num);
  });

  const input = document.getElementById('live-ticket-input');
  if (input) input.value = sc.message;

  applyDemoResult(sc);
}

function runLivePrediction() {
  const input = document.getElementById('live-ticket-input');
  if (!input || !input.value.trim()) return;
  const text = input.value.toLowerCase();

  const paymentKW  = ['paid', 'payment', 'money', 'deducted', 'debited', 'charged', 'upi', 'card', 'bank', 'refund'];
  const deliveryKW = ['deliver', 'courier', 'track', 'dispatch', 'ship', 'transit', 'delayed', 'arrived', 'rto', 'package', 'not arrived', 'order not'];
  const returnKW   = ['return', 'pickup', 'pick up', 'exchange', 'reverse'];
  const hardwareKW = ['buzz', 'static', 'noise', 'defect', 'broken', 'not working', 'charging', 'left ear', 'right ear', 'bluetooth', 'pairing', 'audio'];
  const invoiceKW  = ['gst', 'gstin', 'invoice', 'bill', 'receipt', 'tax'];

  // AI intent priority: invoice > return > delivery > hardware > payment > general
  let aiDest = 'Chat Frontline', aiReason = 'General enquiry routed to frontline triage.';
  if (invoiceKW.some(k => text.includes(k))) {
    aiDest = 'Billing'; aiReason = 'Explicit GST/invoice request — owned by Billing.';
  } else if (returnKW.some(k => text.includes(k))) {
    aiDest = 'Returns Desk'; aiReason = 'Return/pickup request — owned by Returns Desk (Policy §6).';
  } else if (deliveryKW.some(k => text.includes(k))) {
    aiDest = 'Logistics'; aiReason = 'Carrier tracking / delivery failure — owned by Logistics.';
  } else if (hardwareKW.some(k => text.includes(k))) {
    aiDest = 'Escalations & Warranty'; aiReason = 'Hardware fault requiring Tier 2 warranty evaluation.';
  } else if (paymentKW.some(k => text.includes(k))) {
    aiDest = 'Billing'; aiReason = 'Payment transaction dispute without delivery component.';
  }

  // Legacy bot: payment keywords win over everything else
  let botDest = 'Chat Frontline', botStatus = 'CORRECT ROUTING', botReason = 'No strong keyword match — defaulted to Frontline.';
  if (paymentKW.some(k => text.includes(k))) {
    botDest = 'Billing'; botReason = 'Payment keywords matched — routed to Billing.';
  } else if (deliveryKW.some(k => text.includes(k))) {
    botDest = 'Logistics'; botReason = 'Delivery keywords matched.';
  } else if (returnKW.some(k => text.includes(k))) {
    botDest = 'Returns Desk'; botReason = 'Return keywords matched.';
  }

  botStatus = botDest === aiDest ? 'CORRECT ROUTING' : 'MISROUTED';

  applyDemoResult({ botDest, botStatus, botReason, aiDest, aiStatus: 'CORRECT DISPATCH', aiReason });
}

// Initialise demo with scenario 1 once DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  loadDemoScenario(1);
});
