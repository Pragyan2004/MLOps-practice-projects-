import os
import re
import string
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn
import httpx
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

import warnings
warnings.simplefilter("ignore", UserWarning)
warnings.filterwarnings("ignore")

# Suppress MLflow artifact download warnings
# os.environ["MLFLOW_DISABLE_ARTIFACTS_DOWNLOAD"] = "1"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")


def load_env_file(env_path):
    """Load KEY=VALUE pairs from .env without requiring an extra package."""
    if not os.path.exists(env_path):
        raise FileNotFoundError(f".env file not found at: {env_path}")

    with open(env_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            value = os.path.expandvars(value)
            os.environ.setdefault(key, value)


load_env_file(ENV_PATH)


def get_required_env(key):
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


EXPERIMENT_NAME = os.getenv("MLFLOW_EXPERIMENT_NAME", "LoR Hyperparameter Tuning")
DAGSHUB_REPO_OWNER = get_required_env("DAGSHUB_REPO_OWNER")
DAGSHUB_REPO_NAME = get_required_env("DAGSHUB_REPO_NAME")
DAGSHUB_HOST = get_required_env("DAGSHUB_HOST").rstrip("/")
DAGSHUB_TRACKING_URI = get_required_env("MLFLOW_TRACKING_URI")
LOCAL_TRACKING_URI = f"file:///{os.path.join(PROJECT_ROOT, 'mlruns').replace(os.sep, '/')}"
DATA_PATH = os.path.join(PROJECT_ROOT, get_required_env("DATA_PATH"))


def setup_mlflow():
    """Use DagsHub when available, otherwise log runs locally."""
    use_dagshub = os.getenv("USE_DAGSHUB", "true").strip().lower() not in {"0", "false", "no"}

    if use_dagshub:
        try:
            import dagshub

            dagshub_username = os.getenv("DAGSHUB_USERNAME")
            dagshub_token = os.getenv("DAGSHUB_USER_TOKEN")
            if dagshub_username and dagshub_token:
                os.environ.setdefault("MLFLOW_TRACKING_USERNAME", dagshub_username)
                os.environ.setdefault("MLFLOW_TRACKING_PASSWORD", dagshub_token)

            dagshub.init(repo_owner=DAGSHUB_REPO_OWNER, repo_name=DAGSHUB_REPO_NAME, mlflow=True)
            mlflow.set_tracking_uri(DAGSHUB_TRACKING_URI)
            print(f"MLflow tracking set to DagsHub: {DAGSHUB_TRACKING_URI}")
        except (httpx.HTTPError, OSError) as exc:
            mlflow.set_tracking_uri(LOCAL_TRACKING_URI)
            print(f"DagsHub is not reachable ({exc}). Logging MLflow runs locally: {LOCAL_TRACKING_URI}")
        except Exception as exc:
            mlflow.set_tracking_uri(LOCAL_TRACKING_URI)
            print(f"Could not initialize DagsHub ({exc}). Logging MLflow runs locally: {LOCAL_TRACKING_URI}")
    else:
        mlflow.set_tracking_uri(LOCAL_TRACKING_URI)
        print(f"USE_DAGSHUB is disabled. Logging MLflow runs locally: {LOCAL_TRACKING_URI}")

    mlflow.set_experiment(EXPERIMENT_NAME)


# ==========================
# Text Preprocessing Functions
# ==========================
def preprocess_text(text):
    """Applies multiple text preprocessing steps."""
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words("english"))

    text = text.lower()  # Convert to lowercase
    text = re.sub(r'\d+', '', text)  # Remove numbers
    text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)  # Remove punctuation
    text = re.sub(r'https?://\S+|www\.\S+', '', text)  # Remove URLs
    text = " ".join([lemmatizer.lemmatize(word) for word in text.split() if word not in stop_words])  # Lemmatization & stopwords removal
    
    return text.strip()


# ==========================
# Load & Prepare Data
# ==========================
def load_and_prepare_data(filepath):
    """Loads, preprocesses, and vectorizes the dataset."""
    df = pd.read_csv(filepath)
    
    # Apply text preprocessing
    df["review"] = df["review"].astype(str).apply(preprocess_text)
    
    # Filter for binary classification
    df = df[df["sentiment"].isin(["positive", "negative"])]
    df["sentiment"] = df["sentiment"].map({"negative": 0, "positive": 1})
    
    # Convert text data to TF-IDF vectors
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(df["review"])
    y = df["sentiment"]
    
    return train_test_split(X, y, test_size=0.2, random_state=42), vectorizer


# ==========================
# Train & Log Model
# ==========================
def train_and_log_model(X_train, X_test, y_train, y_test, vectorizer):
    """Trains a Logistic Regression model with GridSearch and logs results to MLflow."""
    
    param_grid = {
        "C": [0.1, 1, 10],
        "penalty": ["l1", "l2"],
        "solver": ["liblinear"]
    }
    
    with mlflow.start_run():
        grid_search = GridSearchCV(LogisticRegression(), param_grid, cv=5, scoring="f1", n_jobs=-1)
        grid_search.fit(X_train, y_train)

        # Log all hyperparameter tuning runs
        for params, mean_score, std_score in zip(grid_search.cv_results_["params"], 
                                                 grid_search.cv_results_["mean_test_score"], 
                                                 grid_search.cv_results_["std_test_score"]):
            with mlflow.start_run(run_name=f"LR with params: {params}", nested=True):
                model = LogisticRegression(**params)
                model.fit(X_train, y_train)
                
                y_pred = model.predict(X_test)
                
                metrics = {
                    "accuracy": accuracy_score(y_test, y_pred),
                    "precision": precision_score(y_test, y_pred),
                    "recall": recall_score(y_test, y_pred),
                    "f1_score": f1_score(y_test, y_pred),
                    "mean_cv_score": mean_score,
                    "std_cv_score": std_score
                }
                
                # Log parameters & metrics
                mlflow.log_params(params)
                mlflow.log_metrics(metrics)
                
                print(f"Params: {params} | Accuracy: {metrics['accuracy']:.4f} | F1: {metrics['f1_score']:.4f}")

        # Log the best model
        best_params = grid_search.best_params_
        best_model = grid_search.best_estimator_
        best_f1 = grid_search.best_score_

        mlflow.log_params(best_params)
        mlflow.log_metric("best_f1_score", best_f1)
        mlflow.sklearn.log_model(best_model, "model")
        
        print(f"\nBest Params: {best_params} | Best F1 Score: {best_f1:.4f}")


# ==========================
# Main Execution
# ==========================
if __name__ == "__main__":
    setup_mlflow()
    (X_train, X_test, y_train, y_test), vectorizer = load_and_prepare_data(DATA_PATH)
    train_and_log_model(X_train, X_test, y_train, y_test, vectorizer)
