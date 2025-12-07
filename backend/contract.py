import time

class SmartContract:
    def __init__(self):
        self.reset()

    def reset(self):
        # Initial Balances (Mock USD)
        self.balances = {
            "student": 100,
            "teacher": 0,
            "contract": 0,
            "platform": 0
        }
        self.status = "CREATED" # CREATED, FUNDED, COMPLETED, REFUNDED
        self.lesson_price = 30
        self.platform_fee_percent = 0.02
        # TODO: Fix this hardcoded value
        self.tx_fee_percent = 0.001 
        self.logs = []
        self.last_oracle_data = None
        self.last_outcome = None
        self.transactions = []

    def log(self, message, tx_hash=None):
        self.logs.append({"message": message, "tx_hash": tx_hash})

    def topup_student(self, amount):
        self.balances["student"] += amount
        self.log(f"Student wallet topped up by {amount} USD.")
        return True, "Top-up successful."

    def fund_lesson(self, price=30, lesson_title="Lesson"):
        if self.status not in ["CREATED", "COMPLETED", "REFUNDED"]:
            return False, "Contract already funded."
        
        # Reset state for new lesson if previous was completed
        if self.status in ["COMPLETED", "REFUNDED"]:
            self.status = "CREATED"
            self.last_oracle_data = None
            self.last_outcome = None
        
        self.lesson_price = price
        tx_fee = price * self.tx_fee_percent
        total_deduction = price + tx_fee

        if self.balances["student"] < total_deduction:
            return False, f"Insufficient funds. Need {total_deduction} USD."

        self.balances["student"] -= total_deduction
        self.balances["contract"] += price
        self.status = "FUNDED"
        
        tx_hash = f"0x{abs(hash(str(time.time()) + 'fund'))}"
        self.log(f"Student funded '{lesson_title}' ({price} USD + {tx_fee:.2f} fee). Funds locked in Escrow.", tx_hash)
        return True, "Lesson funded successfully."

    def resolve_lesson(self, teacher_duration, student_duration, oracle_data=None, required_duration=60):
        if self.status != "FUNDED":
            return False, "Contract not in funded state."

        self.last_oracle_data = oracle_data

        # Logic from the prompt
        # Happy Path: Teacher >= 90% AND Student >= 90%
        # Student No-Show: Teacher >= 90% AND Student < 10%
        # Teacher No-Show: Teacher < 10% AND Student >= 90%
        
        threshold = required_duration * 0.9
        min_threshold = required_duration * 0.1

        payout_teacher = False
        refund_student = False
        
        outcome = "Unknown"

        if teacher_duration >= threshold and student_duration >= threshold:
            outcome = "Happy Path: Lesson Completed Successfully."
            payout_teacher = True
        elif teacher_duration >= threshold and student_duration < min_threshold:
            outcome = "Student No-Show: Teacher compensated."
            payout_teacher = True
        elif teacher_duration < min_threshold and student_duration >= threshold:
            outcome = "Teacher No-Show: Student refunded."
            refund_student = True
        else:
            # Fallback / Dispute / Partial - For MVP treat as refund or hold
            outcome = "Dispute/Irregular: Manual intervention required. (Refunding for MVP)"
            refund_student = True
        
        self.last_outcome = outcome
        tx_hash = f"0x{abs(hash(str(time.time()) + 'resolve'))}"

        if payout_teacher:
            contract_balance = self.balances["contract"]
            
            platform_fee = contract_balance * self.platform_fee_percent
            gross_payout = contract_balance - platform_fee
            
            tx_fee = gross_payout * self.tx_fee_percent
            net_payout = gross_payout - tx_fee
            
            self.balances["contract"] = 0
            self.balances["teacher"] += net_payout
            self.balances["platform"] += platform_fee
            
            self.status = "COMPLETED"
            self.log(f"Oracle Resolution: {outcome} -> Payout {net_payout:.2f} to Teacher (Fees: {platform_fee:.2f} Platform, {tx_fee:.2f} Tx).", tx_hash)
        
        elif refund_student:
            gross_refund = self.balances["contract"]
            tx_fee = gross_refund * self.tx_fee_percent
            net_refund = gross_refund - tx_fee
            
            self.balances["contract"] = 0
            self.balances["student"] += net_refund
            
            self.status = "REFUNDED"
            self.log(f"Oracle Resolution: {outcome} -> Refund {net_refund:.2f} to Student (Tx Fee: {tx_fee:.2f}).", tx_hash)

        return True, outcome

    def get_state(self):
        return {
            "balances": self.balances,
            "status": self.status,
            "logs": self.logs,
            "lesson_price": self.lesson_price,
            "last_oracle_data": self.last_oracle_data,
            "last_outcome": self.last_outcome
        }
