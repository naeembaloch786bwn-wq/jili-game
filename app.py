import random
import time
import os
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "jili_clean_secure_v16"

# 🌍 MongoDB Cloud Database Connection
# Agar cloud par connection string na mile to backup local system chalega
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://jiligame:jiligame122@cluster0.v9abc.mongodb.net/?retryWrites=True&w=majority")

try:
    client = MongoClient(MONGO_URI)
    db = client['jili_database']
    users_col = db['users']
    tx_col = db['transactions']
    # Check connection
    client.admin.command('ping')
    print("🎯 Connected Successfully to MongoDB Cloud!")
except Exception as e:
    print(f"⚠️ MongoDB Connection Error: {e}. Using Local memory backup.")
    # Fallback to local memory dictionary structures if cloud crashes
    class FakeCol:
        def __init__(self): self.data = {}
        def find_one(self, q): return self.data.get(q.get("username"))
        def update_one(self, q, u, upsert=False):
            uname = q.get("username")
            if uname:
                if uname not in self.data: self.data[uname] = {}
                if "$set" in u: self.data[uname].update(u["$set"])
        def insert_one(self, d): self.data[d["username"]] = d
        def find(self): return self.data.values()
    users_col = FakeCol()
    class FakeTx:
        def __init__(self): self.d = {"deposits": [], "withdrawals": []}
        def find_one(self, q): return self.d
        def update_one(self, q, u, upsert=True): self.d.update(u["$set"])
    tx_col = FakeTx()

# Setup Admin account if missing
if not users_col.find_one({"username": "923001234567"}):
    users_col.insert_one({
        "username": "923001234567", "password": "123", "balance": 50000,
        "withdraw_pin": "1122", "referred_by": None, "referrals": []
    })

active_bets = []
game_history = [random.randint(0, 9) for _ in range(15)]
TIMER_DURATION = 15
game_status = {"period": 20260522001, "last_number": 0, "end_time": time.time() + TIMER_DURATION}
FIXED_MULTIPLIERS = {0: 20, 1: 4, 2: 3, 3: 1, 4: 8, 5: 4, 6: 12, 7: 3, 8: 2, 9: 10}
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
        username = session.get("user")
        player_bet_map = {i: 0 for i in range(10)}
        if username:
            for b in active_bets:
                if b["user"] == username: player_bet_map[b["num"]] += b["amount"]
        empty_boxes = [i for i in range(10) if player_bet_map[i] == 0]
        target_boxes = empty_boxes if len(empty_boxes) <= 4 else random.sample(empty_boxes, 4)
        if not target_boxes: target_boxes = random.sample(range(10), 4)
        jili_rewards = [random.choice([200, 300, 500, 800, 1000]), random.choice([50, 100, 150, 250, 400]), random.choice([30, 60, 90, 120, 180]), random.choice([15, 25, 35, 45, 75])]
        random.shuffle(jili_rewards)
        for idx, box in enumerate(target_boxes):
            if idx < len(jili_rewards): current_extra_pays[box] = jili_rewards[idx]
    if now >= game_status["end_time"]:
        username = session.get("user")
        player_bet_map = {i: 0 for i in range(10)}
        if username:
            for b in active_bets:
                if b["user"] == username: player_bet_map[b["num"]] += b["amount"]
        empty_boxes = [i for i in range(10) if player_bet_map[i] == 0]
        if len(active_bets) > 0:
            if random.random() < 0.40:
                active_player_numbers = [i for i in range(10) if player_bet_map[i] > 0]
                win_number = random.choice(active_player_numbers) if active_player_numbers else random.randint(0, 9)
            else:
                if empty_boxes:
                    extra_pay_no_bet = [b for b in current_extra_pays if b in empty_boxes]
                    win_number = random.choice(extra_pay_no_bet) if extra_pay_no_bet else random.choice(empty_boxes)
                else: win_number = min(player_bet_map, key=player_bet_map.get)
        else: win_number = random.randint(0, 9)

        for bet in active_bets:
            user = bet["user"]
            if bet["num"] == win_number:
                u_data = users_col.find_one({"username": user})
                if u_data:
                    payout_mult = current_extra_pays[win_number] if win_number in current_extra_pays else FIXED_MULTIPLIERS[win_number]
                    winnings = bet["amount"] * payout_mult
                    users_col.update_one({"username": user}, {"$set": {"balance": u_data["balance"] + winnings}})

        game_history.insert(0, win_number)
        if len(game_history) > 30: game_history = game_history[:30]
        game_status["last_number"] = win_number
        game_status["period"] += 1
        game_status["end_time"] = now + TIMER_DURATION
        active_bets = []
        fake_bets_pool = {i: 0 for i in range(10)}
        current_extra_pays = {}

def get_tx_lists():
    doc = tx_col.find_one({"doc_id": "master"})
    if not doc: return [], []
    return doc.get("deposits", []), doc.get("withdrawals", [])

def save_tx_lists(deps, withs):
    tx_col.update_one({"doc_id": "master"}, {"$set": {"deposits": deps, "withdrawals": withs}}, upsert=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    ref_code = request.args.get("ref", "")
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        u_data = users_col.find_one({"username": username})
        if u_data and u_data["password"] == password:
            session["user"] = username
            return redirect(url_for('home'))
        return "<div style='text-align:center;color:red;margin-top:50px;'><h3>Galat Number ya Password!</h3><a href='/login'>Try Again</a></div>"
    return render_template("login.html", ref_code=ref_code)

@app.route('/register', methods=['GET', 'POST'])
def register():
    ref_code = request.args.get("ref", request.form.get("ref_by", ""))
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        pin = request.form.get("withdraw_pin", "1122")
        if users_col.find_one({"username": username}):
            return "<div style='text-align:center;color:red;margin-top:50px;'><h3>Yeh number pehle se register hai!</h3><a href='/register'>Try Again</a></div>"
        parent_inviter = ref_code if (ref_code and users_col.find_one({"username": ref_code})) else None
        users_col.insert_one({
            "username": username, "password": password, "balance": 88,
            "withdraw_pin": pin, "referred_by": parent_inviter, "referrals": []
        })
        if parent_inviter:
            p_data = users_col.find_one({"username": parent_inviter})
            if p_data:
                refs = p_data.get("referrals", [])
                refs.append(username)
                users_col.update_one({"username": parent_inviter}, {"$set": {"referrals": refs}})
        session["user"] = username
        return redirect(url_for('home'))
    return render_template("register.html", ref_code=ref_code)

@app.route('/logout')
def logout():
    session.pop("user", None)
    return redirect(url_for('login'))

@app.route('/')
def home():
    if "user" not in session: return redirect(url_for('login'))
    username = session["user"]
    u_data = users_col.find_one({"username": username})
    if not u_data:
        session.pop("user", None)
        return redirect(url_for('login'))
    check_and_update_game()
    ref_link = f"{request.host_url}register?ref={username}"
    return render_template("index.html", username=username, balance=u_data["balance"], game=game_status, multipliers=FIXED_MULTIPLIERS, history=game_history, ref_link=ref_link, joined_players=u_data.get("referrals", []))

@app.route('/api/game_status')
def api_status():
    if "user" not in session: return jsonify({"status": "unauthorized"})
    username = session["user"]
    u_data = users_col.find_one({"username": username})
    if not u_data: return jsonify({"status": "unauthorized"})
    check_and_update_game()
    time_left = max(0, game_status["end_time"] - time.time())
    pools = {i: fake_bets_pool[i] for i in range(10)}
    my_bets = {i: 0 for i in range(10)}
    for b in active_bets:
        pools[b["num"]] += b["amount"]
        if b["user"] == username: my_bets[b["num"]] += b["amount"]
    return jsonify({
        "period": game_status["period"], "last_number": game_status["last_number"],
        "time_left": time_left, "pools": pools, "my_bets": my_bets,
        "lightning_boxes": current_extra_pays, "user_balance": u_data["balance"]
    })

@app.route('/bet', methods=['POST'])
def bet():
    if "user" not in session: return jsonify({"status": "error", "message": "Session expired"})
    username = session["user"]
    u_data = users_col.find_one({"username": username})
    if not u_data: return jsonify({"status": "error", "message": "User not found"})
    check_and_update_game()
    if max(0, game_status["end_time"] - time.time()) <= 5.0:
        return jsonify({"status": "error", "message": "Time Over! Bets locked."})
    amount = int(request.form.get("amount"))
    target_num = int(request.form.get("target_num"))
    if amount > u_data["balance"] or amount <= 0:
        return jsonify({"status": "error", "message": "Balance kam hai!"})
    users_col.update_one({"username": username}, {"$set": {"balance": u_data["balance"] - amount}})
    active_bets.append({"user": username, "amount": amount, "num": target_num})
    return jsonify({"status": "success", "new_balance": u_data["balance"] - amount})

@app.route('/panel/<string:mode>')
def transaction_panel(mode):
    if "user" not in session: return redirect(url_for('login'))
    username = session["user"]
    deps, withs = get_tx_lists()
    user_withdrawals = [w for w in withs if w["user"] == username]
    return render_template("panel.html", mode=mode, withdrawals=user_withdrawals)

@app.route('/submit_deposit', methods=['POST'])
def submit_deposit():
    if "user" not in session: return redirect(url_for('login'))
    deps, withs = get_tx_lists()
    dep_id = len(deps) + 1
    deps.append({
        "id": dep_id, "user": session["user"], "name": request.form.get("sender_name"),
        "number": request.form.get("sender_number"), "amount": int(request.form.get("amount")), "status": "Pending"
    })
    save_tx_lists(deps, withs)
    return "<div style='text-align:center;color:white;margin-top:50px;'><h3>Deposit Request Submitted Successfully!</h3><a href='/'>Back to Game</a></div>"

@app.route('/submit_withdrawal', methods=['POST'])
def submit_withdrawal():
    if "user" not in session: return redirect(url_for('login'))
    username = session["user"]
    u_data = users_col.find_one({"username": username})
    if u_data["withdraw_pin"] != request.form.get("secure_pin"):
        return "<div style='text-align:center;color:red;margin-top:50px;'><h3>Wrong Pin!</h3><a href='/panel/withdraw'>Try Again</a></div>"
    amt = int(request.form.get("amount"))
    if amt > u_data["balance"]:
        return "<div style='text-align:center;color:red;margin-top:50px;'><h3>Insufficient Balance!</h3><a href='/'>Back</a></div>"
    users_col.update_one({"username": username}, {"$set": {"balance": u_data["balance"] - amt}})
    deps, withs = get_tx_lists()
    w_id = len(withs) + 1
    withs.append({
        "id": w_id, "user": username, "name": request.form.get("acc_name"),
        "number": request.form.get("acc_number"), "amount": amt, "status": "Pending"
    })
    save_tx_lists(deps, withs)
    return "<div style='text-align:center;color:green;margin-top:50px;'><h3>Withdrawal Request Placed (Pending)!</h3><a href='/'>Back</a></div>"

@app.route('/admin/dashboard')
def admin_dashboard():
    raw_users = users_col.find()
    all_users_dict = {u["username"]: u for u in raw_users}
    deps, withs = get_tx_lists()
    return render_template("admin.html", withdrawals=withs, deposits=deps, all_users=all_users_dict)

@app.route('/admin/update_balance', methods=['POST'])
def admin_update_balance():
    target = request.form.get("target_user")
    action = request.form.get("action_type")
    amount = int(request.form.get("amount"))
    u_data = users_col.find_one({"username": target})
    if u_data:
        new_bal = u_data["balance"] + amount if action == "add" else max(0, u_data["balance"] - amount)
        users_col.update_one({"username": target}, {"$set": {"balance": new_bal}})
    return "<script>alert('Balance Updated Successfully!'); window.location='/admin/dashboard';</script>"

@app.route('/admin/approve_deposit/<int:d_id>')
def admin_approve_deposit(d_id):
    deps, withs = get_tx_lists()
    for d in deps:
        if d["id"] == d_id and d["status"] == "Pending":
            user = d["user"]
            amount = d["amount"]
            u_data = users_col.find_one({"username": user})
            if u_data:
                users_col.update_one({"username": user}, {"$set": {"balance": u_data["balance"] + amount}})
                d["status"] = "Approved"
                inviter = u_data.get("referred_by")
                if inviter and amount >= 1500:
                    p_data = users_col.find_one({"username": inviter})
                    if p_data: users_col.update_one({"username": inviter}, {"$set": {"balance": p_data["balance"] + 320}})
    save_tx_lists(deps, withs)
    return "<script>alert('Deposit Request Approved!'); window.location='/admin/dashboard';</script>"

@app.route('/admin/approve_withdraw/<int:w_id>')
def approve_withdraw(w_id):
    deps, withs = get_tx_lists()
    for w in withs:
        if w["id"] == w_id: w["status"] = "Successful"
    save_tx_lists(deps, withs)
    return "<script>alert('Marked Successful!'); window.location='/admin/dashboard';</script>"

@app.route('/admin/reject_withdraw/<int:w_id>')
def reject_withdraw(w_id):
    deps, withs = get_tx_lists()
    for w in withs:
        if w["id"] == w_id and w["status"] == "Pending":
            w["status"] = "Rejected"
            user = w["user"]
            u_data = users_col.find_one({"username": user})
            if u_data: users_col.update_one({"username": user}, {"$set": {"balance": u_data["balance"] + w["amount"]}})
    save_tx_lists(deps, withs)
    return "<script>alert('Withdrawal Request Rejected and Refunded!'); window.location='/admin/dashboard';</script>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


# Vercel serverless variable mapping
app = app
