import os
import pandas as pd
import numpy as np

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


# ============================================================
# REQUIRED FEATURES
# ============================================================

FEATURES = [
    "Fresh",
    "Milk",
    "Grocery",
    "Frozen",
    "Detergents_Paper",
    "Delicatessen"
]


# ============================================================
# BUSINESS SEGMENTS
# ============================================================

SEGMENT_NAMES = [
    "High Value",
    "Regular Value",
    "Growth Opportunity",
    "Low Value"
]


# ============================================================
# BUSINESS RECOMMENDATIONS
# ============================================================

RECOMMENDATIONS = {

    "High Value":
        "Retention + loyalty programs + premium offers",

    "Regular Value":
        "Repeat purchase campaigns + bundles + cross-selling",

    "Growth Opportunity":
        "Targeted offers + cross-selling + category expansion",

    "Low Value":
        "Re-engagement campaigns + follow-up + limited-time offers"
}


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset(csv_path):

    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Dataset not found: {csv_path}"
        )

    df = pd.read_csv(csv_path)

    # Remove spaces from column names
    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    # Check required columns
    missing_columns = [
        column
        for column in FEATURES
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Required columns are missing: "
            + ", ".join(missing_columns)
        )

    return df


# ============================================================
# PREPROCESSING
#
# Missing values
#       ↓
# Numeric conversion
#       ↓
# Negative values handling
#       ↓
# Feature selection
#       ↓
# StandardScaler
# ============================================================

def preprocess_data(df):

    data = df.copy()

    # --------------------------------------------------------
    # 1. NUMERIC CONVERSION
    # --------------------------------------------------------

    for column in FEATURES:

        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # 2. MISSING VALUES
    # --------------------------------------------------------

    for column in FEATURES:

        median_value = data[column].median()

        if pd.isna(median_value):
            median_value = 0

        data[column] = data[column].fillna(
            median_value
        )

    # --------------------------------------------------------
    # 3. NEGATIVE VALUES
    # --------------------------------------------------------

    data[FEATURES] = data[FEATURES].clip(
        lower=0
    )

    # --------------------------------------------------------
    # 4. FEATURE SELECTION
    # --------------------------------------------------------

    X = data[FEATURES].copy()

    # --------------------------------------------------------
    # 5. STANDARD SCALER
    # --------------------------------------------------------

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    return (
        data,
        X,
        X_scaled,
        scaler
    )


# ============================================================
# TEST K = 2 TO 8
#
# K
# ↓
# K-Means
# ↓
# Inertia
# ↓
# Silhouette Score
# ============================================================

def evaluate_k_values(
    X_scaled,
    min_k=2,
    max_k=8
):

    number_of_customers = len(X_scaled)

    if number_of_customers < 3:
        raise ValueError(
            "At least 3 customers are required."
        )

    # K cannot be equal to or greater than
    # number of customers
    max_allowed_k = min(
        max_k,
        number_of_customers - 1
    )

    if max_allowed_k < min_k:
        raise ValueError(
            "Not enough customers to test the requested K values."
        )

    results = []

    for k in range(
        min_k,
        max_allowed_k + 1
    ):

        model = KMeans(
            n_clusters=k,
            random_state=42,
            n_init=20
        )

        labels = model.fit_predict(
            X_scaled
        )

        inertia = model.inertia_

        silhouette = silhouette_score(
            X_scaled,
            labels
        )

        results.append({

            "k": int(k),

            "inertia": float(
                inertia
            ),

            "silhouette": float(
                silhouette
            )
        })

    return results


# ============================================================
# FIND BEST K
#
# Highest silhouette score
# If scores are same → smaller K
# ============================================================

def find_best_k(results):

    if not results:
        raise ValueError(
            "No K-Means results available."
        )

    best_result = sorted(
        results,
        key=lambda item: (
            -item["silhouette"],
            item["k"]
        )
    )[0]

    return int(
        best_result["k"]
    )


# ============================================================
# BUSINESS SEGMENT RANKING
#
# IMPORTANT:
#
# Cluster numbers are NOT directly mapped.
#
# First:
#
# Cluster
#     ↓
# Average Annual Spending
#     ↓
# Spending Rank
#     ↓
# Business Segment
#
# If there are more than 4 ML clusters,
# multiple clusters can belong to the
# same business segment.
# ============================================================

def create_business_segments(
    data,
    cluster_labels
):

    result = data.copy()

    # --------------------------------------------------------
    # Add ML Cluster
    # --------------------------------------------------------

    result["Cluster"] = cluster_labels

    # --------------------------------------------------------
    # Calculate Annual Spending
    # --------------------------------------------------------

    result["Annual_Spending"] = (
        result["Fresh"]
        + result["Milk"]
        + result["Grocery"]
        + result["Frozen"]
        + result["Detergents_Paper"]
        + result["Delicatessen"]
    )

    # --------------------------------------------------------
    # Calculate average spending for each cluster
    # --------------------------------------------------------

    cluster_average = (
        result
        .groupby("Cluster")["Annual_Spending"]
        .mean()
        .sort_values(
            ascending=False
        )
    )

    # --------------------------------------------------------
    # Ordered clusters
    #
    # Highest spending → first
    # Lowest spending  → last
    # --------------------------------------------------------

    ordered_clusters = list(
        cluster_average.index
    )

    number_of_clusters = len(
        ordered_clusters
    )

    # --------------------------------------------------------
    # Map clusters to 4 business segments
    #
    # This is the important fix.
    #
    # For K <= 4:
    #
    # 1st → High Value
    # 2nd → Regular Value
    # 3rd → Growth Opportunity
    # 4th → Low Value
    #
    # For K > 4:
    # clusters are distributed across
    # the four spending-based segments.
    # --------------------------------------------------------

    cluster_to_segment = {}

    for position, cluster in enumerate(
        ordered_clusters
    ):

        if number_of_clusters == 1:

            segment_index = 0

        else:

            # Convert cluster position into
            # one of four segment levels.

            segment_index = int(
                position
                * len(SEGMENT_NAMES)
                / number_of_clusters
            )

            # Safety limit
            segment_index = min(
                segment_index,
                len(SEGMENT_NAMES) - 1
            )

        segment_name = SEGMENT_NAMES[
            segment_index
        ]

        cluster_to_segment[
            cluster
        ] = segment_name

    # --------------------------------------------------------
    # Add Business Segment
    # --------------------------------------------------------

    result["Segment"] = (
        result["Cluster"]
        .map(cluster_to_segment)
    )

    # --------------------------------------------------------
    # Add Recommendation
    # --------------------------------------------------------

    result["Recommendation"] = (
        result["Segment"]
        .map(RECOMMENDATIONS)
    )

    # --------------------------------------------------------
    # Create Segment Summary
    # --------------------------------------------------------

    summary = []

    for cluster in ordered_clusters:

        cluster_data = result[
            result["Cluster"] == cluster
        ]

        segment = cluster_to_segment[
            cluster
        ]

        summary.append({

            "cluster": int(
                cluster
            ),

            "segment": segment,

            "customers": int(
                len(cluster_data)
            ),

            "average_spending": float(
                cluster_data[
                    "Annual_Spending"
                ].mean()
            ),

            "total_spending": float(
                cluster_data[
                    "Annual_Spending"
                ].sum()
            ),

            "minimum_spending": float(
                cluster_data[
                    "Annual_Spending"
                ].min()
            ),

            "maximum_spending": float(
                cluster_data[
                    "Annual_Spending"
                ].max()
            ),

            "recommendation":
                RECOMMENDATIONS[
                    segment
                ]
        })

    return (
        result,
        summary,
        cluster_to_segment
    )


# ============================================================
# COMPLETE ML PIPELINE
# ============================================================

def run_segmentation(csv_path):

    # --------------------------------------------------------
    # STEP 1: LOAD DATASET
    # --------------------------------------------------------

    raw_data = load_dataset(
        csv_path
    )

    # --------------------------------------------------------
    # STEP 2: PREPROCESSING
    # --------------------------------------------------------

    cleaned_data, X, X_scaled, scaler = (
        preprocess_data(
            raw_data
        )
    )

    # --------------------------------------------------------
    # STEP 3: TEST K = 2 TO 8
    # --------------------------------------------------------

    k_results = evaluate_k_values(
        X_scaled,
        min_k=2,
        max_k=8
    )

    # --------------------------------------------------------
    # STEP 4: FIND BEST K
    # --------------------------------------------------------

    best_k = find_best_k(
        k_results
    )

    # --------------------------------------------------------
    # STEP 5: FINAL K-MEANS
    # --------------------------------------------------------

    final_model = KMeans(
        n_clusters=best_k,
        random_state=42,
        n_init=20
    )

    cluster_labels = (
        final_model.fit_predict(
            X_scaled
        )
    )

    # --------------------------------------------------------
    # STEP 6: FINAL SILHOUETTE SCORE
    # --------------------------------------------------------

    final_silhouette = silhouette_score(
        X_scaled,
        cluster_labels
    )

    # --------------------------------------------------------
    # STEP 7: BUSINESS SEGMENTATION
    # --------------------------------------------------------

    (
        customers,
        segment_summary,
        cluster_mapping
    ) = create_business_segments(
        cleaned_data,
        cluster_labels
    )

    # --------------------------------------------------------
    # STEP 8: DASHBOARD STATISTICS
    # --------------------------------------------------------

    total_customers = len(
        customers
    )

    total_spending = float(
        customers[
            "Annual_Spending"
        ].sum()
    )

    average_spending = float(
        customers[
            "Annual_Spending"
        ].mean()
    )

    # --------------------------------------------------------
    # RETURN EVERYTHING
    # --------------------------------------------------------

    return {

        "raw": raw_data,

        "cleaned": cleaned_data,

        "features": X,

        "scaled": X_scaled,

        "scaler": scaler,

        "model": final_model,

        "customers": customers,

        "summary": segment_summary,

        "cluster_map": cluster_mapping,

        "k_results": k_results,

        "best_k": best_k,

        "silhouette": float(
            final_silhouette
        ),

        "total_customers":
            int(total_customers),

        "total_spending":
            total_spending,

        "average_spending":
            average_spending
    }


# ============================================================
# OPTIONAL DIRECT TEST
# ============================================================

if __name__ == "__main__":

    dataset_path = os.path.join(
        "uploads",
        "customer_dataset.csv"
    )

    try:

        result = run_segmentation(
            dataset_path
        )

        print("\n================================")
        print("WHOLESALE CUSTOMER SEGMENTATION")
        print("================================")

        print(
            "Total Customers:",
            result["total_customers"]
        )

        print(
            "Total Spending:",
            result["total_spending"]
        )

        print(
            "Average Spending:",
            result["average_spending"]
        )

        print(
            "Best K:",
            result["best_k"]
        )

        print(
            "Silhouette Score:",
            result["silhouette"]
        )

        print("\nSEGMENTS")
        print("--------------------------------")

        for segment in result[
            "summary"
        ]:

            print(
                segment
            )

    except Exception as error:

        print(
            "\nERROR:",
            error
        )