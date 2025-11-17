import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

MODEL_PATH = Path("models/intent_model.pkl")
MODEL_PATH.parent.mkdir(exist_ok=True)

TRAINING_DATA = [
    ("buy premium", "order"), ("order package", "order"), ("purchase", "order"),
    ("pay with bank", "order"), ("pay with paystack", "order"), ("use paypal", "order"),
    ("deliver to lagos", "order"), ("what is ai", "chat"), ("hello", "chat")
]

def train_model():
    texts, labels = zip(*TRAINING_DATA)
    model = make_pipeline(TfidfVectorizer(lowercase=True), LogisticRegression())
    model.fit(texts, labels)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

def load_classifier():
    if not MODEL_PATH.exists():
        train_model()
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)

classifier = load_classifier()