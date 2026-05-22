import time, random, threading, os
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
