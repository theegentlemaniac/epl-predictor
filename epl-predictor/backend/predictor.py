import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os

def train_match_predictor(data_path="backend/data/prem_matches.csv"):
    """Train the prediction model and save it."""
    # Load data
    df = pd.read_csv(data_path)
    
    # Preprocess data
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Create target variable (1 if home team wins, 0 otherwise)
    df['target'] = (df['gf'] > df['ga']).astype(int)
    
    # Feature selection
    features = ['sh', 'sot', 'dist', 'fk', 'pk', 'pkatt']
    X = df[features]
    y = df['target']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Model accuracy: {accuracy:.2f}")
    
    # Ensure models directory exists
    os.makedirs('backend/models', exist_ok=True)
    
    # Save model
    joblib.dump(model, 'backend/models/epl_predictor.joblib')
    return model

def predict_match(home_stats, away_stats, model_path='backend/models/epl_predictor.joblib'):
    """Predict match outcome based on team statistics."""
    # Load model
    model = joblib.load(model_path)
    
    # Prepare features
    home_features = pd.DataFrame([home_stats])
    away_features = pd.DataFrame([away_stats])
    
    # Predict probabilities
    home_win_prob = model.predict_proba(home_features)[0][1]
    away_win_prob = model.predict_proba(away_features)[0][0]
    
    # Calculate draw probability
    draw_prob = 1 - abs(home_win_prob - away_win_prob)
    
    # Normalize probabilities
    total = home_win_prob + draw_prob + away_win_prob
    home_win_prob /= total
    draw_prob /= total
    away_win_prob /= total
    
    return {
        'home_win': round(home_win_prob * 100, 1),
        'draw': round(draw_prob * 100, 1),
        'away_win': round(away_win_prob * 100, 1)
    }

if __name__ == "__main__":
    # Train the model (run this periodically)
    model = train_match_predictor()
    
    # Example prediction
    home_team_stats = {
        'sh': 15,   # Shots
        'sot': 5,    # Shots on target
        'dist': 18,  # Average shot distance
        'fk': 3,     # Free kicks
        'pk': 0,     # Penalties made
        'pkatt': 0   # Penalties attempted
    }
    
    away_team_stats = {
        'sh': 10,
        'sot': 3,
        'dist': 20,
        'fk': 5,
        'pk': 0,
        'pkatt': 0
    }
    
    prediction = predict_match(home_team_stats, away_team_stats)
    print("Prediction:", prediction)
