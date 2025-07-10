from flask import Flask, request, jsonify
import pandas as pd
from datetime import datetime, timedelta
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/suggestions', methods=['POST'])
def get_suggestions():
    try:
        data = request.json.get("expenses", [])
        df = pd.DataFrame(data)
        print("DataFrame columns:", df.columns.tolist())
        df.columns = [str(col).lower() for col in df.columns]

        if 'date' not in df.columns:
            return jsonify({"error": f"Expected 'date' but got: {df.columns.tolist()}"}), 400

        df['date'] = pd.to_datetime(df['date'], utc=True)


        now=pd.Timestamp.utcnow()
        last_30_days = now - timedelta(days=30)
        
        recent = df[df['date'] >= last_30_days]

        if recent.empty:
            return jsonify({"message": "No recent expenses found."})

        totals = recent.groupby("category")["amount"].sum().sort_values(ascending=False)
        suggestions = []

        for category, total in totals.items():
            if total > 1000:
                suggestions.append(f"You're spending a lot on {category}. Try to reduce it by 15%.")

        df['month'] = df['date'].dt.to_period('M')
        monthly = df.groupby(['month', 'category'])['amount'].sum().reset_index()

        for category in monthly['category'].unique():
            cat_data = monthly[monthly['category'] == category].sort_values('month')
            if len(cat_data) >= 2:
                diff = cat_data.iloc[-1]['amount'] - cat_data.iloc[-2]['amount']
                if diff > 0.3 * cat_data.iloc[-2]['amount']:
                    suggestions.append(f"Your {category} expenses increased a lot this month.")

        return jsonify({"suggestions": suggestions})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
