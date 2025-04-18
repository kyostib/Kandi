import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.svm import LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, 
    matthews_corrcoef, precision_score, recall_score, f1_score
)
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from time import time
from preproc import load_data, create_text_pipeline


def train_model(X_train, y_train, classifier_type="svm", vectorizer_type="tfidf", use_stop_words=True):
    """Train the model with hyperparameter tuning"""
    pipeline, model_suffix = create_text_pipeline(classifier_type, vectorizer_type, use_stop_words)
    
    # Define parameter grid based on classifier type
    if classifier_type.lower() == "svm":
        param_grid = {
            'classifier__C': [0.1, 1.0, 10.0],
            'classifier__max_iter': [1000, 2000]
        }
    else:  # Random Forest
        param_grid = {
            'classifier__n_estimators': [100, 200],
            'classifier__max_depth': [None, 10, 20],
            'classifier__min_samples_split': [2, 5],
        }
    
    stop_words_msg = "without" if use_stop_words else "with"
    print(f"\nPerforming grid search for {classifier_type.upper()} with {vectorizer_type.upper()} vectorizer {stop_words_msg} stop words...")
    
    grid_search = GridSearchCV(
        pipeline,
        param_grid,
        cv=3,
        n_jobs=-1,  # Use all available cores
        verbose=1,
        scoring='accuracy'
    )
    
    start_time = time()
    grid_search.fit(X_train, y_train)
    train_time = time() - start_time
    
    print(f"Training completed in {train_time:.2f} seconds")
    print(f"Best parameters: {grid_search.best_params_}")
    print(f"Best cross-validation score: {grid_search.best_score_:.4f}")
    
    # Get the best model
    best_model = grid_search.best_estimator_
    
    return best_model, model_suffix, train_time

def compute_metrics(y_true, y_pred):
    """Compute all metrics from confusion matrix"""
    # Get confusion matrix components
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    # Metrics
    metrics = {
        'TP': tp,
        'TN': tn,
        'FP': fp,
        'FN': fn,
        'Accuracy': accuracy_score(y_true, y_pred),
        'Error Rate': 1 - accuracy_score(y_true, y_pred),
        'Precision': precision_score(y_true, y_pred, zero_division=0),
        'Recall': recall_score(y_true, y_pred, zero_division=0),
        'F1 Score': f1_score(y_true, y_pred, zero_division=0),
        'MCC': matthews_corrcoef(y_true, y_pred)
    }
    
    return metrics

def evaluate_model(model, X_val, y_val, model_suffix):
    """Evaluate the model performance"""
    start_time = time()
    y_val_pred = model.predict(X_val)
    pred_time = time() - start_time
    
    # Compute and store all metrics
    metrics = compute_metrics(y_val, y_val_pred)
    metrics['Prediction Time'] = pred_time
    
    # Plot confusion matrix
    conf_matrix = confusion_matrix(y_val, y_val_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues',
                xticklabels=['Negative', 'Positive'],
                yticklabels=['Negative', 'Positive'])
    plt.xlabel('Predicted labels')
    plt.ylabel('True labels')
    plt.title(f'Confusion Matrix - {model_suffix}')
    plt.tight_layout()
    plt.savefig(f'confusion_matrix_{model_suffix}.png')
    
    return metrics

def run_experiments():
    """Run all experiments and collect results"""
    X_train, y_train, X_val, y_val = load_data()
    
    # Define all experiment configurations
    experiments = [
        # SVM experiments
        {'classifier': 'svm', 'vectorizer': 'tfidf', 'stop_words': True},
        {'classifier': 'svm', 'vectorizer': 'tfidf', 'stop_words': False},
        {'classifier': 'svm', 'vectorizer': 'bow', 'stop_words': True},
        {'classifier': 'svm', 'vectorizer': 'bow', 'stop_words': False},
        
        # RF experiments
        {'classifier': 'rf', 'vectorizer': 'tfidf', 'stop_words': True},
        {'classifier': 'rf', 'vectorizer': 'tfidf', 'stop_words': False},
        {'classifier': 'rf', 'vectorizer': 'bow', 'stop_words': True},
        {'classifier': 'rf', 'vectorizer': 'bow', 'stop_words': False},
    ]
    
    # Results storage
    results = []
    
    # Run all experiments
    for exp in experiments:
        print("\n" + "="*80)
        print(f"Running experiment: {exp['classifier'].upper()} with {exp['vectorizer'].upper()}, " +
              f"{'without' if exp['stop_words'] else 'with'} stop words")
        print("="*80)
        
        # Train model
        model, model_suffix, train_time = train_model(
            X_train, y_train, 
            classifier_type=exp['classifier'], 
            vectorizer_type=exp['vectorizer'], 
            use_stop_words=exp['stop_words']
        )
        
        # Evaluate model
        metrics = evaluate_model(model, X_val, y_val, model_suffix)
        
        # Store configuration and results
        result = {
            'Classifier': exp['classifier'].upper(),
            'Vectorizer': exp['vectorizer'].upper(),
            'Stop Words': "No" if exp['stop_words'] else "Yes",
            'Training Time': train_time,
            **metrics
        }
        results.append(result)
    
    return results

def display_results(results):
    """Display results in formatted tables"""
    # Convert results to DataFrame
    df_results = pd.DataFrame(results)
    
    # Create confusion matrix table
    conf_matrix_data = []
    for r in results:
        conf_matrix_data.append({
            'Model': f"{r['Classifier']} ({r['Vectorizer']}, Stop Words: {r['Stop Words']})",
            'TP': r['TP'],
            'FN': r['FN'],
            'FP': r['FP'],
            'TN': r['TN']
        })
    df_conf = pd.DataFrame(conf_matrix_data)
    
    # Create metrics table
    metrics_data = []
    for r in results:
        metrics_data.append({
            'Model': f"{r['Classifier']} ({r['Vectorizer']}, Stop Words: {r['Stop Words']})",
            'Accuracy': f"{r['Accuracy']:.4f}",
            'Error Rate': f"{r['Error Rate']:.4f}",
            'Precision': f"{r['Precision']:.4f}",
            'Recall': f"{r['Recall']:.4f}",
            'F1 Score': f"{r['F1 Score']:.4f}",
            'MCC': f"{r['MCC']:.4f}",
            'Training Time': f"{r['Training Time']:.2f}s",
            'Prediction Time': f"{r['Prediction Time']:.4f}s"
        })
    df_metrics = pd.DataFrame(metrics_data)
    
    # Save tables to CSV
    df_conf.to_csv('confusion_matrix_results.csv', index=False)
    df_metrics.to_csv('metrics_results.csv', index=False)
    
    # Print formatted tables
    print("\n==== CONFUSION MATRIX COMPONENTS ====")
    print(df_conf.to_string(index=False))
    
    print("\n==== PERFORMANCE METRICS ====")
    print(df_metrics.to_string(index=False))
    
    # Create summary visualizations
    plt.figure(figsize=(14, 8))
    
    # Bar chart for accuracy comparison
    acc_data = [(r['Classifier'], r['Vectorizer'], r['Stop Words'], r['Accuracy']) for r in results]
    acc_df = pd.DataFrame(acc_data, columns=['Classifier', 'Vectorizer', 'Stop Words', 'Accuracy'])
    acc_df['Model'] = acc_df.apply(lambda x: f"{x['Classifier']} ({x['Vectorizer']}, SW:{x['Stop Words']})", axis=1)
    
    plt.subplot(2, 2, 1)
    sns.barplot(x='Model', y='Accuracy', data=acc_df)
    plt.xticks(rotation=45, ha='right')
    plt.title('Accuracy Comparison')
    plt.tight_layout()
    
    # Bar chart for MCC comparison
    mcc_data = [(r['Classifier'], r['Vectorizer'], r['Stop Words'], r['MCC']) for r in results]
    mcc_df = pd.DataFrame(mcc_data, columns=['Classifier', 'Vectorizer', 'Stop Words', 'MCC'])
    mcc_df['Model'] = mcc_df.apply(lambda x: f"{x['Classifier']} ({x['Vectorizer']}, SW:{x['Stop Words']})", axis=1)
    
    plt.subplot(2, 2, 2)
    sns.barplot(x='Model', y='MCC', data=mcc_df)
    plt.xticks(rotation=45, ha='right')
    plt.title('Matthews Correlation Coefficient Comparison')
    plt.tight_layout()
    
    # Bar chart for F1 Score comparison
    f1_data = [(r['Classifier'], r['Vectorizer'], r['Stop Words'], r['F1 Score']) for r in results]
    f1_df = pd.DataFrame(f1_data, columns=['Classifier', 'Vectorizer', 'Stop Words', 'F1 Score'])
    f1_df['Model'] = f1_df.apply(lambda x: f"{x['Classifier']} ({x['Vectorizer']}, SW:{x['Stop Words']})", axis=1)
    
    plt.subplot(2, 2, 3)
    sns.barplot(x='Model', y='F1 Score', data=f1_df)
    plt.xticks(rotation=45, ha='right')
    plt.title('F1 Score Comparison')
    plt.tight_layout()
    
    # Bar chart for Training Time comparison
    time_data = [(r['Classifier'], r['Vectorizer'], r['Stop Words'], r['Training Time']) for r in results]
    time_df = pd.DataFrame(time_data, columns=['Classifier', 'Vectorizer', 'Stop Words', 'Training Time'])
    time_df['Model'] = time_df.apply(lambda x: f"{x['Classifier']} ({x['Vectorizer']}, SW:{x['Stop Words']})", axis=1)
    
    plt.subplot(2, 2, 4)
    sns.barplot(x='Model', y='Training Time', data=time_df)
    plt.xticks(rotation=45, ha='right')
    plt.title('Training Time Comparison (seconds)')
    plt.tight_layout()
    
    plt.savefig('performance_metrics_comparison.png', dpi=300, bbox_inches='tight')
    print("Performance metrics visualization saved as 'performance_metrics_comparison.png'")

def main():
    """Main function to execute the entire workflow"""
    print("Starting sentiment analysis classifier comparison...")
    
    # Run all experiments
    results = run_experiments()
    
    # Display and visualize results
    display_results(results)
    
    print("\nExperiment completed successfully.")

if __name__ == "__main__":
    main()