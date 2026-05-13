import pickle
import numpy as np

MODEL_PATH = "model/models/xgboost_model.pkl"

with open(MODEL_PATH, "rb") as f:
    data = pickle.load(f)

model = data["model"]
features = data["features"]

print("✅ Model loaded")
print("Features:", len(features))

# фейковые данные как в API
x = np.array([0] * len(features)).reshape(1, -1)

pred = model.predict(x)

print("Prediction:", pred)