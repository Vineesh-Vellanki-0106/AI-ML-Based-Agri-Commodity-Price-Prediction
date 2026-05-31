from flask import Flask, request, jsonify, render_template
import joblib
import numpy as np
import pandas as pd
import pickle
import math

# Load market label encoder classes
with open("Label_encoder_2.pkl", "rb") as f:
    classes = pickle.load(f)

app = Flask(__name__)

# Load historical data
df_hist = pd.read_csv("merged_agri_prices.csv", parse_dates=["t"])

# Load ML assets
model = joblib.load("../model/price_model.pkl")
scaler = joblib.load("../model/scaler.pkl")
le = joblib.load("../model/label_encoder.pkl")


# -----------------------------
# Home Route
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# Feature Engineering
# -----------------------------
def compute_features(commodity, date):

    df = df_hist[
        (df_hist["commodity"] == commodity) &
        (df_hist["t"] < date)
    ].sort_values("t")

    if len(df) < 90:
        raise ValueError(
            f"Not enough historical data for {commodity}"
        )

    return {
        "lag_1": df.iloc[-1]["p_modal"],
        "lag_7": df.iloc[-7]["p_modal"],
        "lag_30": df.iloc[-30]["p_modal"],
        "lag_90": df.iloc[-90]["p_modal"],

        "rolling_mean_7": df.tail(7)["p_modal"].mean(),
        "rolling_mean_30": df.tail(30)["p_modal"].mean(),
        "rolling_mean_90": df.tail(90)["p_modal"].mean(),

        "rolling_std_7": df.tail(7)["p_modal"].std(),
        "rolling_std_30": df.tail(30)["p_modal"].std(),
        "rolling_std_90": df.tail(90)["p_modal"].std()
    }


# -----------------------------
# Prediction Route
# -----------------------------
@app.route("/predict", methods=["POST"])
def predict():

    try:

        data = request.json

        commodity = data["commodity"]
        date = pd.to_datetime(data["date"])
        p_min = float(data["p_min"])
        p_max = float(data["p_max"])

        # Validate commodity
        if commodity not in le.classes_:
            return jsonify({
                "error": f"Commodity '{commodity}' not found"
            }), 400

        # Compute lag & rolling features ONCE
        feats = compute_features(commodity, date)

        commodity_encoded = le.transform([commodity])[0]

        min_cost = math.inf
        min_cost_market = -1

        # Try all markets
        for market_id in range(len(classes)):

            X = np.array([[

                commodity_encoded,

                date.year,
                date.month,
                date.day,
                date.dayofweek,
                date.quarter,

                feats["lag_1"],
                feats["lag_7"],
                feats["lag_30"],
                feats["lag_90"],

                feats["rolling_mean_7"],
                feats["rolling_mean_30"],
                feats["rolling_mean_90"],

                feats["rolling_std_7"],
                feats["rolling_std_30"],
                feats["rolling_std_90"],

                p_min,
                p_max,

                market_id

            ]])

            X_scaled = scaler.transform(X)

            prediction = model.predict(X_scaled)[0]

            # -----------------------------------
            # Logical Constraint
            # -----------------------------------
            prediction = max(
                p_min,
                min(prediction, p_max)
            )

            if prediction < min_cost:
                min_cost = prediction
                min_cost_market = market_id

        return jsonify({
            "predicted_modal_price": round(float(min_cost), 2),
            "market_id": classes[min_cost_market]
        })

    except ValueError as e:

        return jsonify({
            "error": str(e)
        }), 400

    except Exception as e:

        return jsonify({
            "error": f"Unexpected Error: {str(e)}"
        }), 500


# -----------------------------
# Run App
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)