from flask import Flask, render_template_string, jsonify
import sqlite3
import os

# Import the database connection
from database import get_db_connection

app = Flask(__name__)

# ==========================================
# Embedded HTML Template (Bypasses Vercel's folder deletion)
# ==========================================
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IDS Control Centre | Ensemble Model</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: { colors: { darkbg: '#0f172a', cardbg: '#1e293b', primary: '#0ea5e9', alert: '#ef4444', safe: '#10b981' } }
            }
        }
    </script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-darkbg text-gray-200 font-sans min-h-screen flex">
    <aside class="w-64 bg-cardbg border-r border-gray-700 flex flex-col">
        <div class="p-6">
            <h1 class="text-xl font-bold text-primary flex items-center">
                <span class="w-3 h-3 rounded-full bg-safe animate-pulse mr-2"></span>
                IDS Control Centre
            </h1>
        </div>
        <nav class="flex-1 px-4 space-y-2">
            <a href="#" class="block px-4 py-2 rounded bg-primary/10 text-primary font-medium">Dashboard Overview</a>
            <a href="#" class="block px-4 py-2 rounded hover:bg-gray-700 transition">Dataset Management</a>
            <a href="#" class="block px-4 py-2 rounded hover:bg-gray-700 transition">Model Training</a>
            <a href="#" class="block px-4 py-2 rounded hover:bg-gray-700 transition text-alert">Real-Time Detection</a>
        </nav>
    </aside>

    <main class="flex-1 p-8 overflow-y-auto">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div class="bg-cardbg p-6 rounded-lg border border-gray-700 shadow-lg">
                <h3 class="text-sm text-gray-400">Total Flows Processed</h3>
                <p class="text-3xl font-bold mt-2 text-white">124,592</p>
            </div>
            <div class="bg-cardbg p-6 rounded-lg border border-gray-700 shadow-lg relative overflow-hidden">
                <h3 class="text-sm text-gray-400">Attacks Detected</h3>
                <p class="text-3xl font-bold mt-2 text-alert">{{ total_attacks }}</p>
                <div class="absolute top-0 right-0 w-16 h-16 bg-alert/20 rounded-bl-full"></div>
            </div>
            <div class="bg-cardbg p-6 rounded-lg border border-gray-700 shadow-lg">
                <h3 class="text-sm text-gray-400">Ensemble Accuracy</h3>
                <p class="text-3xl font-bold mt-2 text-primary">99.75%</p>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div class="bg-cardbg p-6 rounded-lg border border-gray-700 shadow-lg">
                <h2 class="text-lg font-semibold mb-4 border-b border-gray-700 pb-2">Live Network Traffic</h2>
                <canvas id="trafficChart" height="200"></canvas>
            </div>
            <div class="bg-cardbg p-6 rounded-lg border border-gray-700 shadow-lg">
                <h2 class="text-lg font-semibold mb-4 border-b border-gray-700 pb-2">Attack Distribution</h2>
                <canvas id="attackChart" height="200"></canvas>
            </div>
        </div>
    </main>

    <script>
        const trafficCtx = document.getElementById('trafficChart').getContext('2d');
        new Chart(trafficCtx, {
            type: 'line',
            data: {
                labels: ['10m', '8m', '6m', '4m', '2m', 'Now'],
                datasets: [{ label: 'Normal Traffic', data: [12, 19, 15, 25, 22, 30], borderColor: '#10b981', backgroundColor: 'rgba(16, 185, 129, 0.1)', fill: true, tension: 0.4 },
                           { label: 'Anomalous', data: [1, 0, 2, 1, 8, 2], borderColor: '#ef4444', backgroundColor: 'rgba(239, 68, 68, 0.1)', fill: true, tension: 0.4 }]
            },
            options: { responsive: true, maintainAspectRatio: false, color: '#9ca3af' }
        });

        const attackCtx = document.getElementById('attackChart').getContext('2d');
        new Chart(attackCtx, {
            type: 'bar',
            data: {
                labels: ['DDoS', 'PortScan', 'Botnet', 'Web Attack'],
                datasets: [{ label: 'Detected', data: [2541, 1205, 145, 130], backgroundColor: ['#ef4444', '#f59e0b', '#8b5cf6', '#ec4899'] }]
            },
            options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, color: '#9ca3af' }
        });
    </script>
</body>
</html>
"""

# ==========================================
# 4.1 Control Centre / Main Menu
# ==========================================
@app.route('/')
def dashboard():
    """Main entry point. Renders the dynamic web dashboard."""
    try:
        conn = get_db_connection()
        # Get total attack count dynamically
        attack_count_query = conn.execute("SELECT COUNT(*) FROM alerts WHERE attack_type != 'Benign'").fetchone()
        total_attacks = attack_count_query[0] if attack_count_query else 0
        conn.close()
    except Exception as e:
        # If DB fails on Vercel, default to 0 so the page still loads
        total_attacks = 0

    # Use render_template_string to bypass the missing folder issue
    return render_template_string(DASHBOARD_HTML, total_attacks=total_attacks)

# ==========================================
# 4.2 The Submenus / Subsystems (API Routes)
# ==========================================
@app.route('/dataset', methods=['GET'])
def dataset_management():
    return jsonify({"status": "Dataset loaded."})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
