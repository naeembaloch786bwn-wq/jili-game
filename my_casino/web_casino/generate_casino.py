import os

os.makedirs('templates', exist_ok=True)

py_code = """import time, random, threading, os
from flask import Flask, render_template, jsonify, request

base_dir = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'))

wallet_balance = 5000
deposit_requests, withdraw_requests = [], []

crash_status, crash_time, multiplier = 'betting', 15, 1.00
crash_history = ['1.20x', '3.50x', '1.02x'] * 10
dt_status, dt_time, dt_card_d, dt_card_t, dt_msg = 'betting', 15, '?', '?', 'Place bets!'
dt_history = ['D', 'T', 'D'] * 10
slots_status, slots_time = 'betting', 15
slots_grid = [['🍎', '🍉', '🍋'], ['🍉', '🍋', '🍎'], ['🍋', '🍎', '🍉']]
slots_history = ['🍎 Win', '🪙 Loss'] * 15
chicken_status, chicken_time, chicken_outcome = 'betting', 15, 'Safe'
chicken_history = ['Safe', 'Wasted'] * 15
balloon_status, balloon_time, balloon_scale, balloon_burst = 'betting', 15, 1.0, False
balloon_history = ['1.5x', '💥 Pop'] * 15
tower_status, tower_time, tower_layers = 'betting', 15, 0
tower_history = ['3 Layers', 'Collapse'] * 15

@app.route('/')
def home(): return render_template('index.html')

def run_crash_clock():
    global crash_status, crash_time, multiplier, crash_history
    while True:
        if crash_status == 'betting':
            for i in range(15, 0, -1):
                crash_time = i; time.sleep(1)
            crash_status, multiplier = 'flying', 1.00
            crash_point = round(random.uniform(1.01, 5.50), 2)
        elif crash_status == 'flying':
            while multiplier < crash_point:
                time.sleep(0.25)
                multiplier = round(multiplier + 0.05, 2)
            crash_status = 'crashed'
            crash_history.insert(0, f'{multiplier}x')
            time.sleep(4); crash_status = 'betting'

def run_dt_clock():
    global dt_status, dt_time, dt_card_d, dt_card_t, dt_msg, dt_history
    deck = ['A','2','3','4','5','6','7','8','9','10','J','Q','K']
    while True:
        for i in range(15, 0, -1): dt_time = i; time.sleep(1)
        dt_status, dt_msg = 'dealing', 'Shuffling...'
        time.sleep(2)
        dt_card_d, dt_card_t = random.choice(deck), random.choice(deck)
        res = 'D' if random.random() > 0.5 else 'T'
        dt_history.insert(0, res); dt_status, dt_msg = 'betting', 'Round Finished!'
        time.sleep(4)

threading.Thread(target=run_crash_clock, daemon=True).start()
threading.Thread(target=run_dt_clock, daemon=True).start()

@app.route('/status')
def get_status():
    return jsonify({
        'balance': wallet_balance, 'crash_status': crash_status, 'crash_time': crash_time, 'multiplier': multiplier, 'crash_history': crash_history,
        'dt_status': dt_status, 'dt_time': dt_time, 'dt_msg': dt_msg, 'dt_card_d': dt_card_d, 'dt_card_t': dt_card_t, 'dt_history': dt_history,
        'slots_status': slots_status, 'slots_time': slots_time, 'slots_grid': slots_grid, 'slots_history': slots_history,
        'chicken_status': chicken_status, 'chicken_time': chicken_time, 'chicken_outcome': chicken_outcome, 'chicken_history': chicken_history,
        'balloon_status': balloon_status, 'balloon_time': balloon_time, 'balloon_scale': balloon_scale, 'balloon_burst': balloon_burst, 'balloon_history': balloon_history,
        'tower_status': tower_status, 'tower_time': tower_time, 'tower_layers': tower_layers, 'tower_history': tower_history
    })

@app.route('/action', methods=['POST'])
def game_action():
    global wallet_balance
    t = request.form.get('type')
    amt = int(request.form.get('amount', 0))
    if t == 'bet' and wallet_balance >= amt:
        wallet_balance -= amt; return jsonify({'success': True})
    elif t == 'cashout':
        wallet_balance += int(amt * multiplier); return jsonify({'success': True})
    elif t == 'win_payout':
        wallet_balance += amt; return jsonify({'success': True})
    return jsonify({'success': False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
"""

html_code = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Remix Casino</title>
    <style>
        body { background: #0a0f14; color: white; font-family: sans-serif; text-align: center; padding: 10px; }
        .header { background: #12181f; padding: 15px; border-radius: 10px; border-bottom: 3px solid #f1c40f; }
        .tabs { display: grid; grid-template-columns: repeat(2, 1fr); gap: 5px; margin: 10px 0; }
        .tab-btn { padding: 12px; background: #1c232d; color: white; border: 1px solid #2b3542; border-radius: 6px; font-weight: bold; }
        .tab-btn.active { background: #e74c3c; }
        .game-panel { display: none; background: #12181f; padding: 20px; border-radius: 12px; }
        .game-panel.active { display: block; }
        .arena { background: #020617; height: 150px; border-radius: 8px; position: relative; margin-bottom: 10px; line-height: 150px; font-size: 24px; }
        input { width: 80%; padding: 10px; margin: 10px 0; background: #090d12; color: white; border: 1px solid #2b3542; text-align: center; }
        .btn { width: 85%; padding: 12px; font-weight: bold; color: white; border: none; border-radius: 6px; font-size: 16px; background: #2ecc71; }
    </style>
</head>
<body>
    <div class="header">
        <h2>🎰 REMIX LIVE SYSTEMS 🎰</h2>
        <h3>Wallet: <span id="balance" style="color:#2ecc71;">5000</span> PKR</h3>
    </div>
    
    <div class="tabs">
        <button class="tab-btn active" id="tb-crash" onclick="switchTab('crash')">🚀 Crash</button>
        <button class="tab-btn" id="tb-dt" onclick="switchTab('dt')">🐉 D-Tiger</button>
    </div>

    <div id="p-crash" class="game-panel active">
        <div class="arena" id="crash-banner">1.00x</div>
        <input type="number" id="crash-amount" value="100">
        <button class="btn" id="btn-crash" onclick="runCrashBet()">Place Order</button>
    </div>

    <div id="p-dt" class="game-panel">
        <div id="dt-timer" style="color:#e74c3c; font-weight:bold;">Timer: --</div>
        <div id="dt-msg" style="color:#f1c40f; margin: 10px 0;">Waiting...</div>
        <div style="font-size: 28px; margin: 15px 0;">🐉 <span id="card-d">?</span> VS <span id="card-t">?</span> 🐅</div>
        <input type="number" id="dt-amount" value="100">
        <div style="display:flex; gap:6px;"><button class="btn" style="background:#e74c3c;" onclick="lockLiveBet('dt','D')">Dragon</button><button class="btn" style="background:#3498db;" onclick="lockLiveBet('dt','T')">Tiger</button></div>
    </div>

<script>
    let activeTab = "crash", state = {}, currentBet = { game: null, side: null, amount: 0, active: false };
    
    function switchTab(t) {
        activeTab = t;
        document.querySelectorAll('.game-panel').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.getElementById('p-' + t).classList.add('active');
        document.getElementById('tb-' + t).classList.add('active');
    }

    function sync() {
        fetch('/status').then(r => r.json()).then(d => {
            state = d; document.getElementById('balance').innerText = d.balance;
            
            if(activeTab === "crash") {
                let b = document.getElementById("crash-banner");
                let btn = document.getElementById("btn-crash");
                if(d.crash_status === "betting") {
                    b.innerText = "Next in " + d.crash_time + "s";
                    if(!currentBet.active) btn.innerText = "Place Order";
                } else if(d.crash_status === "flying") {
                    b.innerText = d.multiplier + "x";
                    if(currentBet.active && currentBet.game === 'crash') btn.innerText = "Cashout: Rs." + Math.floor(currentBet.amount * d.multiplier);
                } else {
                    b.innerText = "💥 CRASHED (" + d.crash_history[0] + ")";
                    currentBet.active = false; btn.innerText = "Crashed";
                }
            }

            if(activeTab === "dt") {
                document.getElementById("dt-timer").innerText = d.dt_status === "betting" ? "Timer: " + d.dt_time + "s" : "Dealing Phase";
                document.getElementById("dt-msg").innerText = d.dt_msg;
                document.getElementById("card-d").innerText = d.dt_card_d;
                document.getElementById("card-t").innerText = d.dt_card_t;
                
                if(d.dt_status === "dealing" && currentBet.active && currentBet.game === 'dt') {
                    if(currentBet.side === d.dt_history[0]) fetch('/action', {method:'POST', body:new URLSearchParams({'type':'win_payout','amount':currentBet.amount*2})});
                    currentBet.active = false;
                }
            }
        });
    }

    function lockLiveBet(gameType, sideCode) {
        if(currentBet.active) return;
        let amt = document.getElementById('dt-amount').value;
        fetch("/action", {method:"POST", body:new URLSearchParams({'type':'bet','amount':amt})}).then(r=>r.json()).then(res => {
            if(res.success) currentBet = { game: gameType, side: sideCode, amount: parseInt(amt), active: true };
        });
    }

    function runCrashBet() {
        let amt = document.getElementById("crash-amount").value;
        if(!currentBet.active && state.crash_status === "betting") {
            fetch("/action", {method:"POST", body:new URLSearchParams({'type':'bet','amount':amt})}).then(r=>r.json()).then(d=>{ if(d.success) currentBet={game:'crash', active:True, amount:parseInt(amt)}; });
        } else if(currentBet.active && state.crash_status === "flying" && currentBet.game === 'crash') {
            fetch("/action", {method:"POST", body:new URLSearchParams({'type':'cashout','amount':currentBet.amount})}).then(r=>r.json()).then(d=> { if(d.success) currentBet.active=false; });
        }
    }

    setInterval(sync, 1000);
</script>
</body>
</html>
"""

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(py_code)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html_code)

print("--- FILES GENERATED SUCCESSFULLY IN LOCALS ---")
