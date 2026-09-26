# ML-Based Wholesale Customer Segmentation

## Project Overview

ML-Based Wholesale Customer Segmentation is a Flask-based machine learning web application designed to analyze wholesale customer purchasing behavior and automatically divide customers into meaningful groups.

The system uses customer spending data from different product categories and applies K-Means Clustering to identify similar customer groups.

After clustering, the system converts the machine learning clusters into business-oriented customer segments such as:

- High Value
- Regular Value
- Growth Opportunity
- Low Value

The system also provides customer profiles, segment analysis, performance evaluation, PCA visualization, business insights, and segment-specific recommendations.

---

# Problem Statement

Wholesale businesses may have hundreds or thousands of customers with different purchasing behaviors.

Manually analyzing every customer's purchasing pattern can be difficult and time-consuming.

A business needs to understand:

- Which customers spend more?
- Which customers have similar purchasing behavior?
- Which customers have growth potential?
- Which customers may need re-engagement?
- What business strategy should be used for different customer groups?

This project uses machine learning to automatically analyze customer spending behavior and provide meaningful customer segmentation.

---

# Objectives

The main objectives of this project are:

1. Analyze wholesale customer purchasing behavior.

2. Upload and process customer CSV datasets.

3. Clean and preprocess customer spending data.

4. Apply feature scaling using StandardScaler.

5. Test different K values from 2 to 8.

6. Evaluate clustering using Inertia and Silhouette Score.

7. Select the best K value.

8. Apply K-Means clustering.

9. Convert clusters into meaningful business segments.

10. Provide individual customer profiles.

11. Generate segment-specific business recommendations.

12. Visualize customer clusters using PCA.

13. Provide an interactive web dashboard for analysis.

---

# Key Features

## 1. User Registration and Login

Users can create their own account and securely log into the system.

The system stores:

- Full Name
- Username
- Email
- Password
- Role

Passwords are stored using password hashing.

---

## 2. Dataset Upload

The user can upload a CSV dataset through the dashboard.

The system validates the dataset before processing it.

Required columns:

- Fresh
- Milk
- Grocery
- Frozen
- Detergents_Paper
- Delicatessen

A new compatible dataset can be uploaded and the machine learning analysis is refreshed according to the new dataset.

---

## 3. Data Validation

The system checks:

- Whether a CSV file is uploaded
- Whether the file is empty
- Whether all required columns are present
- Whether the dataset can be processed correctly

---

# Machine Learning Workflow

The machine learning workflow is:

```text
CSV Dataset
     |
     v
Dataset Validation
     |
     v
Data Preprocessing
     |
     v
Feature Selection
     |
     v
StandardScaler
     |
     v
K-Means Clustering
     |
     v
K = 2 to 8
     |
     +-------------------+
     |                   |
     v                   v
  Inertia        Silhouette Score
     |                   |
     +---------+---------+
               |
               v
            Best K
               |
               v
        Final Clustering
               |
               v
       Average Spending
               |
               v
       Business Segments
               |
               v
      Recommendations

      Recommendations
```

## 👩‍💻 Author

**Sanika Mendhe**

---

## 📌 Conclusion

This project analyzes wholesale customer data to identify meaningful customer segments based on their purchasing behavior. The segmentation provides a clearer understanding of customer patterns and can support data-driven business decisions.
