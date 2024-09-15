import os
import yfinance as yf
from google.cloud import storage
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
import joblib

def update_model(request):
    ticker = 'GOOGL'
    google_stock = yf.Ticker(ticker)
    stock_data = google_stock.history(period='1y')
    
    stock_data['Price_Change'] = stock_data['Close'].diff().shift(-1)
    stock_data['Target'] = (stock_data['Price_Change'] > 0).astype(int)
    stock_data['MA_5'] = stock_data['Close'].rolling(window=5).mean()
    stock_data['MA_10'] = stock_data['Close'].rolling(window=10).mean()
    stock_data['MA_30'] = stock_data['Close'].rolling(window=30).mean()
    stock_data = stock_data.dropna()

    X = stock_data[['Open', 'High', 'Low', 'Close', 'Volume', 'MA_5', 'MA_10', 'MA_30']]
    y = stock_data['Target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    clf = DecisionTreeClassifier(random_state=42)
    clf.fit(X_train, y_train)
    
    accuracy = accuracy_score(y_test, clf.predict(X_test))
    print(f'Model Accuracy: {accuracy:.2f}')
    
    model_filename = './model.joblib'
    joblib.dump(clf, model_filename)
    
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(os.environ.get('BUCKET_NAME'))
    blob = bucket.blob('latest/model.joblib')
    blob.upload_from_filename(model_filename)

    return f'Model updated and accuracy is {accuracy:.2f}'
