from flask import Flask, jsonify, request
from contract import SmartContract
from oracle import Oracle

app = Flask(__name__)

# Initialize Singletons
contract = SmartContract()
oracle = Oracle()

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(contract.get_state())

@app.route('/api/reset', methods=['POST'])
def reset():
    contract.reset()
    return jsonify({"message": "System reset successfully", "state": contract.get_state()})

@app.route('/api/fund', methods=['POST'])
def fund():
    data = request.json or {}
    price = data.get('price', 30)
    lesson_title = data.get('lesson_title', 'Lesson')
    success, message = contract.fund_lesson(price, lesson_title)
    if success:
        return jsonify({"status": "success", "message": message, "state": contract.get_state()})
    else:
        return jsonify({"status": "error", "message": message}), 400

@app.route('/api/topup', methods=['POST'])
def topup():
    data = request.json or {}
    amount = data.get('amount', 100)
    success, message = contract.topup_student(amount)
    return jsonify({"status": "success", "message": message, "state": contract.get_state()})

@app.route('/api/scenario', methods=['POST'])
def set_scenario():
    data = request.json
    scenario = data.get('scenario', 'happy_path')
    oracle.set_scenario(scenario)
    return jsonify({"message": f"Scenario set to {scenario}"})

@app.route('/api/resolve', methods=['POST'])
def resolve():
    # Optional: Set scenario if provided
    data_req = request.json or {}
    if 'scenario' in data_req:
        oracle.set_scenario(data_req['scenario'])

    # 1. Oracle fetches data (Simulated)
    data = oracle.get_meeting_data()
    
    # 2. Oracle calls Smart Contract
    success, outcome = contract.resolve_lesson(
        teacher_duration=data['teacher_duration'],
        student_duration=data['student_duration'],
        oracle_data=data
    )
    
    response = {
        "oracle_data": data,
        "contract_outcome": outcome,
        "state": contract.get_state()
    }
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
