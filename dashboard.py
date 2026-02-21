import sqlite3
import pandas as pd
from flask import Flask, render_template_string
from config import DB_PATH

app = Flask(__name__)

# =========================
# DATABASE HELPERS
# =========================

def get_summary(conn):
    summary = {}

    summary["open_count"] = pd.read_sql("""
        SELECT COUNT(*) as c
        FROM signals
        WHERE status = 'OPEN'
    """, conn)["c"][0]

    summary["closed_count"] = pd.read_sql("""
        SELECT COUNT(*) as c
        FROM signals
        WHERE status LIKE 'CLOSED%'
    """, conn)["c"][0]

    results_df = pd.read_sql("""
        SELECT percent_result
        FROM signals
        WHERE status LIKE 'CLOSED%'
        AND percent_result IS NOT NULL
    """, conn)

    results = results_df["percent_result"].tolist()

    if len(results) > 0:

        wins = [r for r in results if r > 0]
        losses = [r for r in results if r <= 0]

        summary["winrate"] = round(len(wins) / len(results) * 100, 2)
        summary["avg_gain"] = round(sum(wins) / len(wins), 2) if wins else 0
        summary["avg_loss"] = round(sum(losses) / len(losses), 2) if losses else 0

    else:
        summary["winrate"] = 0
        summary["avg_gain"] = 0
        summary["avg_loss"] = 0

    return summary


# =========================
# ROUTE
# =========================

@app.route("/")
def dashboard():
    conn = sqlite3.connect(DB_PATH)

    latest_df = pd.read_sql("""
        SELECT *
        FROM signals
        ORDER BY value DESC
        LIMIT 20
    """, conn)

    open_df = pd.read_sql("""
        SELECT *
        FROM signals
        WHERE status = 'OPEN'
        ORDER BY value DESC
    """, conn)

    closed_df = pd.read_sql("""
        SELECT *
        FROM signals
        WHERE status LIKE 'CLOSED%'
        ORDER BY exit_date DESC
    """, conn)

    summary = get_summary(conn)

    conn.close()

    return render_template_string(
        TEMPLATE,
        latest=latest_df.to_dict("records"),
        open_trades=open_df.to_dict("records"),
        closed=closed_df.to_dict("records"),
        summary=summary
    )


# =========================
# TEMPLATE
# =========================

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>IDX Breakout Dashboard</title>
    <meta http-equiv="refresh" content="60">
    <style>
        body { font-family: Arial; background:#f5f5f5; padding:20px; }
        h1 { margin-bottom:5px; }
        table { border-collapse: collapse; width:100%; margin-bottom:30px; }
        th, td { border:1px solid #ccc; padding:6px; font-size:12px; }
        th { background:#333; color:white; }
        tr:nth-child(even) { background:#fafafa; }
        .card { padding:15px; border-radius:8px; font-weight:bold; min-width:150px; }
        .green { color:green; }
        .red { color:red; }
        .blue { color:blue; }
    </style>
</head>

<body>

<h1>📊 IDX Breakout Dashboard</h1>

<h2>📌 System Summary</h2>
<div style="display:flex; gap:20px; margin-bottom:30px;">
    <div class="card" style="background:#e8f5e9;">
        Open Positions<br>{{ summary.open_count }}
    </div>
    <div class="card" style="background:#e3f2fd;">
        Closed Trades<br>{{ summary.closed_count }}
    </div>
    <div class="card" style="background:#fff3e0;">
        Winrate<br>{{ summary.winrate }}%
    </div>
        Total R<br>{{ summary.total_r }}
</div>
    <div class="card" style="background:#e8f5e9;">
        Avg Gain<br>
        <span class="green">{{ summary.avg_gain }}%</span>
    </div>

    <div class="card" style="background:#ffebee;">
        Avg Loss<br>
        <span class="red">{{ summary.avg_loss }}%</span>
    </div>
</div>

<h2>🚀 Latest Signals</h2>
<table>
{% if latest|length > 0 %}
<tr>
{% for key in latest[0].keys() %}
    <th>{{ key }}</th>
{% endfor %}
</tr>

{% for row in latest %}
<tr>
{% for value in row.values() %}
    <td>{{ value }}</td>
{% endfor %}
</tr>
{% endfor %}
{% else %}
<tr><td>No data</td></tr>
{% endif %}
</table>


<h2>🟢 Open Positions</h2>
<table>
{% if open_trades|length > 0 %}
<tr>
{% for key in open_trades[0].keys() %}
    <th>{{ key }}</th>
{% endfor %}
</tr>

{% for row in open_trades %}
<tr>
{% for key, value in row.items() %}
    {% if key == "status" %}
        <td class="green">{{ value }}</td>
    {% else %}
        <td>{{ value }}</td>
    {% endif %}
{% endfor %}
</tr>
{% endfor %}
{% else %}
<tr><td>No open trades</td></tr>
{% endif %}
</table>


<h2>🔴 Closed Trades</h2>
<table>
{% if closed|length > 0 %}
<tr>
{% for key in closed[0].keys() %}
    <th>{{ key }}</th>
{% endfor %}
</tr>

{% for row in closed %}
<tr>
{% for key, value in row.items() %}
    {% if key == "status" %}
        {% if "TP" in value %}
            <td class="blue">{{ value }}</td>
        {% elif "SL" in value %}
            <td class="red">{{ value }}</td>
        {% else %}
            <td>{{ value }}</td>
        {% endif %}
    {% elif key == "result_r" %}
        {% if value and value > 0 %}
            <td class="green">{{ value }}</td>
        {% elif value and value < 0 %}
            <td class="red">{{ value }}</td>
        {% else %}
            <td>{{ value }}</td>
        {% endif %}
    {% else %}
        <td>{{ value }}</td>
    {% endif %}
{% endfor %}
</tr>
{% endfor %}
{% else %}
<tr><td>No closed trades</td></tr>
{% endif %}
</table>

</body>
</html>
"""

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
