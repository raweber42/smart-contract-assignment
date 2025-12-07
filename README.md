# Decentralized Tutoring Prototype

This project demonstrates a trustless tutoring payment system using a Python-based mock Smart Contract and Oracle.

## Prerequisites

- Python 3.8+

## Setup

1.  Create a virtual environment (optional but recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Prototype

You need to run the Backend and Frontend in separate terminal windows.

### Terminal 1: Backend (Flask API)

```bash
cd backend
python3 app.py
```
*The server will start at http://127.0.0.1:5000*

### Terminal 2: Frontend (Streamlit UI)

```bash
cd frontend
streamlit run ui.py
```
*The UI will open in your browser at http://localhost:8501*

## Usage

1.  **Select Scenario:** Use the sidebar to choose "Happy Path", "Student No-Show", or "Teacher No-Show". Click "Apply Scenario".
2.  **Fund Lesson:** As the student, click "Fund Lesson" to lock 30 USDC in the contract.
3.  **Resolve:** Click "Trigger Oracle Resolution". The system will simulate fetching data from Google Meet and settling the contract based on the selected scenario.
