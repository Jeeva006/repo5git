# -*- coding: utf-8 -*-
"""InsClaimPred - Sanika Vavhal.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1U-Ut-92Pa4r7r6t6RvCPWwoB1_BR3N0x

# Insurance Claim Prediction

## *Importing libraries*
"""

import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, classification_report, precision_recall_curve, auc
from imblearn.over_sampling import SMOTE, ADASYN
import warnings
from xgboost import XGBClassifier
warnings.filterwarnings('ignore')

"""## *Loading the Dataset*"""

df = pd.read_csv('/content/train.csv')

df.head()

"""## *Basic Check*"""

df.describe()

df.info()

df.isnull().sum()

df.shape

df['target'].value_counts()

"""## *Seperate features and target*"""

X = df.drop('target', axis=1)
y = df['target']

y

"""## *Feature Scaling*"""

# Handling missing values
imputer = SimpleImputer(strategy='mean')
X_imputed = imputer.fit_transform(X)

# Data scaling
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_imputed)

"""## *Train-Test split*"""

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

"""## *Applying SMOTE and ADASYN on data*"""

smote = SMOTE(random_state=42)
adasyn = ADASYN(random_state=42)
X_smote, y_smote = smote.fit_resample(X_train, y_train)
X_adasyn, y_adasyn = adasyn.fit_resample(X_train, y_train)

"""- ## Model Training and Evaluation
## *Initialising the model*
"""

# Initialize models
models = {
    "Logistic Regression": LogisticRegression(class_weight='balanced'),
    "Decision Tree": DecisionTreeClassifier(class_weight='balanced'),
    "Random Forest": RandomForestClassifier(class_weight='balanced'),
    "Gradient Boosting": GradientBoostingClassifier(),
    "XGBoost": XGBClassifier(scale_pos_weight=(len(y) - sum(y)) / sum(y))  # Adjusting class imbalance for XGBoost
}

"""## *Train and Evaluate Models*"""

def evaluate_models(X_resampled, y_resampled):
    model_performance_resampled = {}
    for model_name, model in models.items():
        model.fit(X_resampled, y_resampled)
        y_pred = model.predict(X_test)
        model_performance_resampled[model_name] = {
            "Accuracy": accuracy_score(y_test, y_pred),
            "Precision": precision_score(y_test, y_pred),
            "Recall": recall_score(y_test, y_pred),
            "F1 Score": f1_score(y_test, y_pred),
            "ROC AUC": roc_auc_score(y_test, y_pred)
        }
        print(f"Classification report for {model_name}:\n", classification_report(y_test, y_pred))
    return model_performance_resampled

print("Model Performance with SMOTE:")
performance_smote = evaluate_models(X_smote, y_smote)
print("Model Performance with ADASYN:")
performance_adasyn = evaluate_models(X_adasyn, y_adasyn)

"""## *Evaluate Models using Precision-Recall AUC*"""

# Evaluate Models using Precision-Recall AUC
def evaluate_model_pr_auc(model, X_test, y_test):
    y_pred = model.predict(X_test)
    precision, recall, _ = precision_recall_curve(y_test, y_pred)
    auc_score = auc(recall, precision)
    return auc_score

# Evaluate models using precision-recall curve AUC for both SMOTE and ADASYN
def evaluate_pr_auc(models, X_resampled, y_resampled):
    pr_auc_scores = {}
    for model_name, model in models.items():
        model.fit(X_resampled, y_resampled)
        pr_auc_scores[model_name] = evaluate_model_pr_auc(model, X_test, y_test)
    return pr_auc_scores

pr_auc_smote = evaluate_pr_auc(models, X_smote, y_smote)
pr_auc_adasyn = evaluate_pr_auc(models, X_adasyn, y_adasyn)

# Convert PR AUC scores to DataFrame for better visualization
pr_auc_df_smote = pd.DataFrame(pr_auc_smote, index=["PR AUC"]).T
pr_auc_df_adasyn = pd.DataFrame(pr_auc_adasyn, index=["PR AUC"]).T
print("PR AUC with SMOTE:")
print(pr_auc_df_smote)
print("PR AUC with ADASYN:")
print(pr_auc_df_adasyn)

"""## *Hyperparameter Tuning with XGBoost*"""

# Initialize XGBoost Classifier with class weights adjustment
xgb_model = XGBClassifier(scale_pos_weight=(len(y) - sum(y)) / sum(y))  # Adjust scale_pos_weight based on class imbalance

# Hyperparameter tuning
param_grid = {
    'n_estimators': [100, 200],
    'max_depth': [3, 5],
    'learning_rate': [0.01, 0.1]
}
grid_search = GridSearchCV(estimator=xgb_model, param_grid=param_grid, scoring='roc_auc', cv=3)
grid_search.fit(X_smote, y_smote)

# Best model and parameters
best_model = grid_search.best_estimator_
print("Best parameters:", grid_search.best_params_)

# Evaluate on test set
y_pred = best_model.predict(X_test)
print("Classification report for XGBoost:\n", classification_report(y_test, y_pred))

"""## *Geature importance from Random Forest, Gradient Boosting, and XGBoost*"""

def get_feature_importance(model, model_name):
    feature_importances = model.feature_importances_
    importance_df = pd.DataFrame({'Feature': range(len(feature_importances)), 'Importance': feature_importances})
    importance_df = importance_df.sort_values(by='Importance', ascending=False)
    importance_df['Model'] = model_name
    return importance_df

feature_importances = pd.DataFrame()
for model_name, model in models.items():
    if model_name in ["Random Forest", "Gradient Boosting"]:
        model.fit(X_smote, y_smote)  # Ensure model is fitted
        importance_df = get_feature_importance(model, model_name)
        feature_importances = pd.concat([feature_importances, importance_df])

# XGBoost feature importance
best_model.fit(X_smote, y_smote)
xgb_importance_df = get_feature_importance(best_model, "XGBoost")
feature_importances = pd.concat([feature_importances, xgb_importance_df])

# Display feature importance
print("Feature Importances:")
print(feature_importances)

"""- ## *Comparing the models*"""

import matplotlib.pyplot as plt
import numpy as np

# Model performance data from classification reports
models = ["Logistic Regression", "Decision Tree", "Random Forest", "Gradient Boosting", "XGBoost"]

performance_smote = {
    "Logistic Regression": {"Precision": 0.04, "Recall": 0.44, "F1 Score": 0.07, "Accuracy": 0.62},
    "Decision Tree": {"Precision": 0.03, "Recall": 0.06, "F1 Score": 0.04, "Accuracy": 0.90},
    "Random Forest": {"Precision": 0.00, "Recall": 0.00, "F1 Score": 0.00, "Accuracy": 0.97},
    "Gradient Boosting": {"Precision": 0.00, "Recall": 0.00, "F1 Score": 0.00, "Accuracy": 0.97},
    "XGBoost": {"Precision": 0.00, "Recall": 0.00, "F1 Score": 0.00, "Accuracy": 0.96}
}

performance_adasyn = {
    "Logistic Regression": {"Precision": 0.04, "Recall": 0.44, "F1 Score": 0.07, "Accuracy": 0.61},
    "Decision Tree": {"Precision": 0.03, "Recall": 0.06, "F1 Score": 0.04, "Accuracy": 0.90},
    "Random Forest": {"Precision": 0.00, "Recall": 0.00, "F1 Score": 0.00, "Accuracy": 0.97},
    "Gradient Boosting": {"Precision": 0.00, "Recall": 0.00, "F1 Score": 0.00, "Accuracy": 0.97},
    "XGBoost": {"Precision": 0.00, "Recall": 0.00, "F1 Score": 0.00, "Accuracy": 0.96}
}

# Extract metrics for plotting
def extract_metrics(performance):
    metrics = ["Precision", "Recall", "F1 Score", "Accuracy"]
    return {metric: [performance[model][metric] for model in models] for metric in metrics}

metrics_smote = extract_metrics(performance_smote)
metrics_adasyn = extract_metrics(performance_adasyn)

# Plotting
fig, axs = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('Model Performance with SMOTE and ADASYN')

metrics = ["Precision", "Recall", "F1 Score", "Accuracy"]
positions = np.arange(len(models))

for i, metric in enumerate(metrics):
    row, col = divmod(i, 2)
    ax = axs[row, col]
    width = 0.35

    ax.bar(positions - width/2, metrics_smote[metric], width, label='SMOTE')
    ax.bar(positions + width/2, metrics_adasyn[metric], width, label='ADASYN')

    ax.set_title(metric)
    ax.set_xticks(positions)
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.legend()

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.show()

"""- ## *Suggestions to the Insurance market team to make customers buy the product.*

**Step 6:** **Feature Importance Analysis and Suggestions for the Marketing Team**
"""

def provide_suggestions(feature_importances):
    top_features = feature_importances.groupby('Model').apply(lambda x: x.nlargest(5, 'Importance')).reset_index(drop=True)
    suggestions = """
    Based on the feature importance analysis, the following features are most indicative of customer purchasing behavior:
    {}
    Marketing Strategies:
    1. Targeted Marketing Campaigns: Focus your marketing campaigns on customers who exhibit high values in these top features.
       - These features are highly predictive of a customer's likelihood to purchase insurance.
       - Tailor your messaging to highlight the benefits that align with these characteristics.
    2. Personalized Communication: Develop personalized communication strategies for high-potential buyers.
       - Use insights from these features to address specific customer needs and preferences.
       - Provide customized offers and incentives that resonate with these customers.
    3. Feature Monitoring and Updates: Regularly monitor the importance of these features and update your models accordingly.
       - Customer behavior and preferences can change over time, so ensure your models are updated with the latest data.
       - Periodic retraining and feature re-evaluation will help maintain model accuracy and relevance.
    4. Enhanced Data Collection: Consider collecting additional data on these top features if not already available.
       - Enriching your dataset with more detailed information on these features can further improve model performance.
       - Use surveys, feedback forms, and other methods to gather more granular data.
    """
    feature_list = '\n    '.join(f"- Feature {int(f)} (Model: {m})" for f, m in zip(top_features['Feature'], top_features['Model']))
    print(suggestions.format(feature_list))

provide_suggestions(feature_importances)

"""- ## Based on the feature importance analysis, the following features are most indicative of customer purchasing behavior:
  
    Marketing Strategies:
    1. **Targeted Marketing Campaigns**: Focus your marketing campaigns on customers who exhibit high values in these top features.
       - These features are highly predictive of a customer's likelihood to purchase insurance.
       - Tailor your messaging to highlight the benefits that align with these characteristics.
    2. **Personalized Communication**: Develop personalized communication strategies for high-potential buyers.
       - Use insights from these features to address specific customer needs and preferences.
       - Provide customized offers and incentives that resonate with these customers.
    3. **Feature Monitoring and Updates**: Regularly monitor the importance of these features and update your models accordingly.
       - Customer behavior and preferences can change over time, so ensure your models are updated with the latest data.
       - Periodic retraining and feature re-evaluation will help maintain model accuracy and relevance.
    4. **Enhanced Data Collection**: Consider collecting additional data on these top features if not already available.
       - Enriching your dataset with more detailed information on these features can further improve model performance.
       - Use surveys, feedback forms, and other methods to gather more granular data.

## Challenges Faced

1. **Imbalanced Dataset:**

The dataset was highly imbalanced, making it difficult for models to learn effectively. This was addressed using SMOTE and ADASYN to generate synthetic samples for the minority class.

2. **Model Performance:**

Despite handling class imbalance, achieving high recall and F1 scores for the minority class was challenging. This required careful tuning and evaluation of multiple models.

3. **Hyperparameter Tuning:**

Tuning hyperparameters for XGBoost was computationally intensive and time-consuming. Grid search was used to find the optimal parameters, which improved model performance.

4. **Feature Importance Interpretation:**

Interpreting feature importance across different models required careful analysis to ensure actionable insights for the marketing team.
"""

