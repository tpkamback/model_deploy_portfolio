import os
import yfinance as yf
from google.cloud import storage, aiplatform
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
import joblib

project_id = os.environ.get('PROJECT_ID')
bucket_name = os.environ.get('BUCKET_NAME')
region = os.environ.get('REGION')

def deploy_model():
    aiplatform.init(project=project_id, location=region)
    model = aiplatform.Model.upload(
        display_name='decision-tree-model',
        artifact_uri='gs://' + bucket_name + '/latest/',
        serving_container_image_uri='us-docker.pkg.dev/vertex-ai/prediction/sklearn-cpu.0-24:latest',
    )
    model.deploy(machine_type='n1-standard-2')

def update_model():
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

    deploy_model()

    return f'Model updated and accuracy is {accuracy:.2f}'

if __name__ == "__main__":
    update_model()