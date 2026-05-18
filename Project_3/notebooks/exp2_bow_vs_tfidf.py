import setuptools
import os
import re
import string
import time
import pandas as pd
pd.set_option('future.no_silent_downcasting', True)

import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import scipy.sparse

import warnings
warnings.simplefilter("ignore", UserWarning)
warnings.filterwarnings("ignore")


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
LOCAL_TRACKING_URI = f"file:///{os.path.join(PROJECT_ROOT, 'mlruns').replace(os.sep, '/')}"
PLACEHOLDER_TOKENS = {"replace_with_your_dagshub_token", "your_dagshub_token", ""}


def expand_env_vars(value):
    def replace_match(match):
        return os.environ.get(match.group(1), match.group(0))

    return re.sub(r"\$\{([^}]+)\}", replace_match, value)


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
            value = expand_env_vars(value)
            os.environ[key] = value


def get_required_env(key):
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Missing required environment variable: {key}")
    return value


def is_valid_secret(value):
    value = (value or "").strip()
    return value not in PLACEHOLDER_TOKENS and not value.lower().startswith("replace_with")


def setup_mlflow():
    use_dagshub = os.getenv("USE_DAGSHUB", "true").strip().lower() not in {"0", "false", "no"}
    dagshub_token = os.getenv("DAGSHUB_USER_TOKEN", "").strip()

    if use_dagshub and is_valid_secret(dagshub_token):
        import dagshub

        os.environ["MLFLOW_TRACKING_USERNAME"] = get_required_env("DAGSHUB_USERNAME")
        os.environ["MLFLOW_TRACKING_PASSWORD"] = dagshub_token
        os.environ["DAGSHUB_USER_TOKEN"] = dagshub_token
        mlflow.set_tracking_uri(CONFIG["mlflow_tracking_uri"])
        dagshub.init(
            repo_owner=CONFIG["dagshub_repo_owner"],
            repo_name=CONFIG["dagshub_repo_name"],
            host=CONFIG["dagshub_host"],
            mlflow=True,
        )
        print(f"MLflow tracking set to DagsHub: {CONFIG['mlflow_tracking_uri']}", flush=True)
    else:
        reason = "DAGSHUB_USER_TOKEN is missing or still has the placeholder value." if use_dagshub else "USE_DAGSHUB is false."
        mlflow.set_tracking_uri(LOCAL_TRACKING_URI)
        print(f"Using local MLflow tracking at {LOCAL_TRACKING_URI}. {reason}", flush=True)

    mlflow.set_experiment(CONFIG["experiment_name"])


load_env_file(ENV_PATH)

# ========================== CONFIGURATION ==========================
CONFIG = {
    "data_path": os.path.join(PROJECT_ROOT, get_required_env("DATA_PATH")),
    "test_size": float(get_required_env("TEST_SIZE")),
    "mlflow_tracking_uri": get_required_env("MLFLOW_TRACKING_URI"),
    "dagshub_host": get_required_env("DAGSHUB_HOST"),
    "dagshub_repo_owner": get_required_env("DAGSHUB_REPO_OWNER"),
    "dagshub_repo_name": get_required_env("DAGSHUB_REPO_NAME"),
    "experiment_name": os.getenv("MLFLOW_EXPERIMENT_NAME_EXP2", "Bow vs TfIdf")
}

# ========================== SETUP MLflow & DAGSHUB ==========================
setup_mlflow()

# ========================== TEXT PREPROCESSING ==========================
def lemmatization(text):
    lemmatizer = WordNetLemmatizer()
    return " ".join([lemmatizer.lemmatize(word) for word in text.split()])

def remove_stop_words(text):
    stop_words = set(stopwords.words("english"))
    return " ".join([word for word in text.split() if word not in stop_words])

def removing_numbers(text):
    return ''.join([char for char in text if not char.isdigit()])

def lower_case(text):
    return text.lower()

def removing_punctuations(text):
    return re.sub(f"[{re.escape(string.punctuation)}]", ' ', text)

def removing_urls(text):
    return re.sub(r'https?://\S+|www\.\S+', '', text)

def normalize_text(df):
    try:
        df['review'] = df['review'].apply(lower_case)
        df['review'] = df['review'].apply(remove_stop_words)
        df['review'] = df['review'].apply(removing_numbers)
        df['review'] = df['review'].apply(removing_punctuations)
        df['review'] = df['review'].apply(removing_urls)
        df['review'] = df['review'].apply(lemmatization)
        return df
    except Exception as e:
        print(f"Error during text normalization: {e}")
        raise

# ========================== LOAD & PREPROCESS DATA ==========================
def load_data(file_path):
    try:
        df = pd.read_csv(file_path)
        df = normalize_text(df)
        df = df[df['sentiment'].isin(['positive', 'negative'])]
        df['sentiment'] = df['sentiment'].replace({'negative': 0, 'positive': 1}).infer_objects(copy=False)
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        raise

# ========================== FEATURE ENGINEERING ==========================
VECTORIZERS = {
    'BoW': CountVectorizer(),
    'TF-IDF': TfidfVectorizer()
}

ALGORITHMS = {
    'LogisticRegression': LogisticRegression(),
    'MultinomialNB': MultinomialNB(),
    'XGBoost': XGBClassifier(),
    'RandomForest': RandomForestClassifier(),
    'GradientBoosting': GradientBoostingClassifier()
}

# ========================== TRAIN & EVALUATE MODELS ==========================
def train_and_evaluate(df):
    with mlflow.start_run(run_name="All Experiments") as parent_run:
        for algo_name, algorithm in ALGORITHMS.items():
            for vec_name, vectorizer in VECTORIZERS.items():
                with mlflow.start_run(run_name=f"{algo_name} with {vec_name}", nested=True) as child_run:
                    try:
                        # Feature extraction
                        X = vectorizer.fit_transform(df['review'])
                        y = df['sentiment']
                        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=CONFIG["test_size"], random_state=42)

                        # Log preprocessing parameters
                        mlflow.log_params({
                            "vectorizer": vec_name,
                            "algorithm": algo_name,
                            "test_size": CONFIG["test_size"]
                        })

                        # Train model
                        model = algorithm
                        model.fit(X_train, y_train)

                        # Log model parameters
                        log_model_params(algo_name, model)

                        # Evaluate model
                        y_pred = model.predict(X_test)
                        metrics = {
                            "accuracy": accuracy_score(y_test, y_pred),
                            "precision": precision_score(y_test, y_pred),
                            "recall": recall_score(y_test, y_pred),
                            "f1_score": f1_score(y_test, y_pred)
                        }
                        mlflow.log_metrics(metrics)

                        # Log model
                        # mlflow.sklearn.log_model(model, "model")
                        input_example = X_test[:5] if not scipy.sparse.issparse(X_test) else X_test[:5].toarray()
                        mlflow.sklearn.log_model(model, "model", input_example=input_example)

                        # Print results for verification
                        print(f"\nAlgorithm: {algo_name}, Vectorizer: {vec_name}")
                        print(f"Metrics: {metrics}")

                    except Exception as e:
                        print(f"Error in training {algo_name} with {vec_name}: {e}")
                        mlflow.log_param("error", str(e))

def log_model_params(algo_name, model):
    """Logs hyperparameters of the trained model to MLflow."""
    params_to_log = {}
    if algo_name == 'LogisticRegression':
        params_to_log["C"] = model.C
    elif algo_name == 'MultinomialNB':
        params_to_log["alpha"] = model.alpha
    elif algo_name == 'XGBoost':
        params_to_log["n_estimators"] = model.n_estimators
        params_to_log["learning_rate"] = model.learning_rate
    elif algo_name == 'RandomForest':
        params_to_log["n_estimators"] = model.n_estimators
        params_to_log["max_depth"] = model.max_depth
    elif algo_name == 'GradientBoosting':
        params_to_log["n_estimators"] = model.n_estimators
        params_to_log["learning_rate"] = model.learning_rate
        params_to_log["max_depth"] = model.max_depth

    mlflow.log_params(params_to_log)

# ========================== EXECUTION ==========================
if __name__ == "__main__":
    started_at = time.time()
    print("Loading and preprocessing data...", flush=True)
    df = load_data(CONFIG["data_path"])
    print(f"Loaded {len(df)} rows. Training experiments...", flush=True)
    train_and_evaluate(df)
    print(f"Finished in {time.time() - started_at:.1f} seconds.", flush=True)
