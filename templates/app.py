import random
import time
from flask import Flask, render_template, request, session, jsonify

app = Flask(__name__)
app.secret_key = "jili_clean_secure_v12"

users = {
    "923001234567": {"password": "123", "balance": 50000, "withdraw_pin": "1122"}
}
deposit_requests = []
withdraw_requests = []
active_bets = []
game_history = [random.randint(0, 9) for _ in range(15)]

TIMER_DURATION = 15
game_status = {
    "period": 20260522001,
    "last_number": 0,
    "end_time": time.time() + TIMER_DURATION
}

FIXED_MULTIPLIERS = {
    0: 20, 1: 4, 2: 3, 3: 1, 4: 8,
    5: 4, 6: 12, 7: 3, 8: 2, 9: 10
}

fake_bets_pool = {i: 0 for i in range(10)}
current_extra_pays = {}

def check_and_update_game():
    global active_bets, game_history, fake_bets_pool, current_extra_pays
    now = time.time()
    time_left = game_status["end_time"] - now
    
    if time_left > 5.0:
        for _ in range(3):
            fake_num = random.randint(0, 9)
            fake_bets_pool[fake_num] += random.choice([10, 20, 50, 100, 500])

    if 0.0 < time_left <= 5.0 and not current_extra_pays:
        username = "923001234567"
        player_bet_map = {i: 0 for i in range(10)}
        for b in active_bets:
            if b["user"] == username:
                player_bet_map[b["num"]] += b["amount"]

        empty_boxes = [i for i in range(10) if player_bet_map[i] == 0]
        target_boxes = empty_boxes if len(empty_boxes) <= 4 else random.sample(empty_boxes, 4)
        if not target_boxes:
            target_boxes = random.sample(range(10), 4)
            
        jili_rewards = [500, 230, 160, 80, 25]
        random.shuffle(jili_rewards)
        for idx, box in enumerate(target_boxes):
            if idx < len(jili_rewards):
                current_extra_pays[box] = jili_rewards[idx]

    if now >= game_status["end_time"]:
        username = "923001234567"
        player_bet_map = {i: 0 for i in range(10)}
        for b in active_bets:
            if b["user"] == username:
                player_bet_map[b["num"]] += b["amount"]

        empty_boxes = [i for i in range(10) if player_bet_map[i] == 0]
        
        if len(active_bets) > 0:
            is_win_round = random.random() < 0.40
            if is_win_round:
                active_player_numbers = [i for i in range(10) if player_bet_map[i] > 0]
                win_number = random.choice(active_player_numbers) if active_player_numbers else random.randint(0, 9)
            else:
                if empty_boxes:
                    extra_pay_no_bet = [b for b in current_extra_pays if b in empty_boxes]
                    win_number = random.choice(extra_pay_no_bet) if extra_pay_no_bet else random.choice(empty_boxes)
                else:
                    win_number = min(player_bet_map, key=player_bet_map.get)
        else:
            win_number = random.randint(0, 9)

        for bet in active_bets:
            user = bet["user"]
            if bet["num"] == win_number:
                payout_mult = current_extra_pays[win_number] if win_number in current_extra_pays else FIXED_MULTIPLIERS[win_number]
                users[user]["balance"] += (bet["amount"] * payout_mult)

        game_history.insert(0, win_number)
        if len(game_history) > 30: game_history = game_history[:30]

        game_status["last_number"] = win_number
        game_status["period"] += 1
        game_status["end_time"] = now + TIMER_DURATION
        active_bets = []
        fake_bets_pool = {i: 0 for i in range(10)}
        current_extra_pays = {}

@app.route('/')
def home():
    check_and_update_game()
    if "user" not in session: session["user"] = "923001234567"
    username = session["user"]
    return render_template("index.html", username=username, balance=users[username]["balance"], game=game_status, multipliers=FIXED_MULTIPLIERS, history=game_history)

@app.route('/api/game_status')
def api_status():
    check_and_update_game()
    time_left = max(0, game_status["end_time"] - time.time())
    pools = {i: fake_bets_pool[i] for i in range(10)}
    my_bets = {i: 0 for i in range(10)}
    username = session.get("user", "923001234567")
    for b in active_bets:
        pools[b["num"]] += b["amount"]
        if b["user"] == username: my_bets[b["num"]] += b["amount"]
    return jsonify({
        "period": game_status["period"], "last_number": game_status["last_number"],
        "time_left": time_left, "pools": pools, "my_bets": my_bets,
        "lightning_boxes": current_extra_pays, "user_balance": users[username]["balance"]
    })

@app.route('/bet', methods=['POST'])
def bet():
    check_and_update_game()
    if max(0, game_status["end_time"] - time.time()) <= 5.0:
        return jsonify({"status": "error", "message": "Time Over! Bets locked."})
    username = session.get("user", "923001234567")
    amount = int(request.form.get("amount"))
    target_num = int(request.form.get("target_num"))
    if amount > users[username]["balance"] or amount <= 0:
        return jsonify({"status": "error", "message": "Balance kam hai!"})
    users[username]["balance"] -= amount
    active_bets.append({"user": username, "amount": amount, "num": target_num})
    return jsonify({"status": "success", "new_balance": users[username]["balance"]})

@app.route('/panel/<string:mode>')
def transaction_panel(mode):
    return render_template("panel.html", mode=mode)

@app.route('/submit_deposit', methods=['POST'])
def submit_deposit():
    deposit_requests.append({"user": session.get("user", "923001234567"), "name": request.form.get("sender_name"), "number": request.form.get("sender_number"), "amount": request.form.get("amount")})
    return "<div style='text-align:center;color:white;margin-top:50px;'><h3>Submitted!</h3><a href='/'>Back</a></div>"

@app.route('/submit_withdrawal', methods=['POST'])
def submit_withdrawal():
    username = session.get("user", "923001234567")
    if users[username]["withdraw_pin"] != request.form.get("secure_pin"):
        return "<div style='text-align:center;color:red;margin-top:50px;'><h3>Wrong Pin!</h3><a href='/panel/withdraw'>Try Again</a></div>"
    amt = int(request.form.get("amount"))
    if amt > users[username]["balance"]:
        return "<div style='text-align:center;color:red;margin-top:50px;'><h3>Insufficient Balance!</h3><a href='/'>Back</a></div>"
    users[username]["balance"] -= amt
    withdraw_requests.append({"user": username, "name": request.form.get("acc_name"), "number": request.form.get("acc_number"), "amount": amt})
    return "<div style='text-align:center;color:green;margin-top:50px;'><h3>Request Forwarded!</h3><a href='/'>Back</a></div>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

