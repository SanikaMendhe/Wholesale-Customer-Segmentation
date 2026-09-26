import os
import sqlite3
from functools import wraps

import pandas as pd
import numpy as np

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from ml_model import (
    run_segmentation,
    FEATURES
)


# ============================================================
# FLASK CONFIGURATION
# ============================================================

app = Flask(__name__)

app.secret_key = "wholesale_customer_segmentation_secret_key"

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE = os.path.join(
    BASE_DIR,
    "wholesale.db"
)

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads"
)

DATASET_PATH = os.path.join(
    UPLOAD_FOLDER,
    "customer_dataset.csv"
)

ALLOWED_EXTENSIONS = {"csv"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["MAX_CONTENT_LENGTH"] = (
    16 * 1024 * 1024
)


# ============================================================
# GLOBAL ML RESULT
# ============================================================

ML_RESULT = None


# ============================================================
# DATABASE
# ============================================================

def get_db_connection():

    conn = sqlite3.connect(
        DATABASE
    )

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    os.makedirs(
        UPLOAD_FOLDER,
        exist_ok=True
    )

    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'Manager',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    conn.close()


# ============================================================
# LOGIN REQUIRED
# ============================================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login first.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        return function(
            *args,
            **kwargs
        )

    return wrapper


# ============================================================
# FILE VALIDATION
# ============================================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(
            ".",
            1
        )[1].lower() in ALLOWED_EXTENSIONS
    )


def validate_dataset(df):

    missing_columns = [
        column
        for column in FEATURES
        if column not in df.columns
    ]

    return missing_columns


# ============================================================
# ML RESULT
# ============================================================

def get_ml_result():

    global ML_RESULT

    if ML_RESULT is None:

        if not os.path.exists(
            DATASET_PATH
        ):
            return None

        try:

            ML_RESULT = run_segmentation(
                DATASET_PATH
            )

            print(
                "ML MODEL LOADED SUCCESSFULLY"
            )

        except Exception as error:

            print(
                "ML ERROR:",
                error
            )

            ML_RESULT = None

    return ML_RESULT


def refresh_ml_result():

    global ML_RESULT

    ML_RESULT = None

    return get_ml_result()


# ============================================================
# LANDING PAGE
# ============================================================

@app.route("/")
def landing():

    if "user_id" in session:

        return redirect(
            url_for(
                "manager_dashboard"
            )
        )

    return render_template(
        "landing.html"
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if (
            not full_name
            or not username
            or not email
            or not password
        ):

            flash(
                "Please fill all required fields.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        conn = get_db_connection()

        existing_user = conn.execute(
            """
            SELECT id
            FROM users
            WHERE username = ?
               OR email = ?
            """,
            (
                username,
                email
            )
        ).fetchone()

        if existing_user:

            conn.close()

            flash(
                "Username or email already exists.",
                "danger"
            )

            return render_template(
                "register.html"
            )

        hashed_password = generate_password_hash(
            password
        )

        conn.execute(
            """
            INSERT INTO users
            (
                full_name,
                username,
                email,
                password,
                role
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                full_name,
                username,
                email,
                hashed_password,
                "Manager"
            )
        )

        conn.commit()

        conn.close()

        flash(
            "Account created successfully. Please login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Please enter username and password.", "warning")
            return render_template("login.html")

        conn = get_db_connection()

        try:

            user = conn.execute(
                """
                SELECT *
                FROM users
                WHERE username = ?
                   OR email = ?
                """,
                (username, username)
            ).fetchone()

        finally:
            conn.close()

        if user is not None:

            stored_password = user["password"]

            if check_password_hash(
                stored_password,
                password
            ):

                session["user_id"] = user["id"]
                session["full_name"] = user["full_name"]
                session["username"] = user["username"]
                session["email"] = user["email"]
                session["role"] = user["role"]

                flash(
                    "Login successful.",
                    "success"
                )

                return redirect(
                    url_for("manager_dashboard")
                )

        flash(
            "Invalid username/email or password.",
            "danger"
        )

    return render_template("login.html")
# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "info"
    )

    return redirect(
        url_for("landing")
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
@login_required
def manager_dashboard():

    result = get_ml_result()

    if result is None:

        return render_template(
            "manager_dashboard.html",

            ml_available=False,

            total_customers=0,

            total_spending=0,

            average_spending=0,

            best_k="N/A",

            silhouette="N/A",

            summary=[]
        )

    return render_template(

        "manager_dashboard.html",

        ml_available=True,

        total_customers=result[
            "total_customers"
        ],

        total_spending=result[
            "total_spending"
        ],

        average_spending=result[
            "average_spending"
        ],

        best_k=result[
            "best_k"
        ],

        silhouette=result[
            "silhouette"
        ],

        summary=result[
            "summary"
        ]
    )


# ============================================================
# UPLOAD DATASET
#
# IMPORTANT:
# This route is now used ONLY for processing the upload.
# User should upload from Dashboard.
#
# GET /upload -> Dashboard
# POST /upload -> process CSV -> Dashboard
# ============================================================

@app.route(
    "/upload",
    methods=["GET", "POST"]
)
@login_required
def upload():

    # --------------------------------------------------------
    # IF USER DIRECTLY OPENS /upload
    # SEND THEM BACK TO DASHBOARD
    # --------------------------------------------------------

    if request.method == "GET":

        return redirect(
            url_for(
                "manager_dashboard"
            )
        )


    # --------------------------------------------------------
    # GET FILE
    # --------------------------------------------------------

    file = request.files.get(
        "file"
    )

    if file is None:

        file = request.files.get(
            "dataset"
        )


    # --------------------------------------------------------
    # NO FILE
    # --------------------------------------------------------

    if (
        file is None
        or file.filename == ""
    ):

        flash(
            "Please select a CSV file.",
            "danger"
        )

        return redirect(
            url_for(
                "manager_dashboard"
            )
        )


    # --------------------------------------------------------
    # FILE EXTENSION
    # --------------------------------------------------------

    if not allowed_file(
        file.filename
    ):

        flash(
            "Only CSV files are allowed.",
            "danger"
        )

        return redirect(
            url_for(
                "manager_dashboard"
            )
        )


    try:

        # ----------------------------------------------------
        # READ CSV
        # ----------------------------------------------------

        df = pd.read_csv(
            file
        )


        # ----------------------------------------------------
        # CLEAN COLUMN NAMES
        # ----------------------------------------------------

        df.columns = [
            str(column).strip()
            for column in df.columns
        ]


        # ----------------------------------------------------
        # EMPTY DATASET
        # ----------------------------------------------------

        if df.empty:

            flash(
                "The uploaded CSV file is empty.",
                "danger"
            )

            return redirect(
                url_for(
                    "manager_dashboard"
                )
            )


        # ----------------------------------------------------
        # VALIDATE REQUIRED COLUMNS
        # ----------------------------------------------------

        missing_columns = validate_dataset(
            df
        )

        if missing_columns:

            flash(
                "Missing required columns: "
                + ", ".join(
                    missing_columns
                ),
                "danger"
            )

            return redirect(
                url_for(
                    "manager_dashboard"
                )
            )


        # ----------------------------------------------------
        # CREATE UPLOAD FOLDER
        # ----------------------------------------------------

        os.makedirs(
            UPLOAD_FOLDER,
            exist_ok=True
        )


        # ----------------------------------------------------
        # SAVE DATASET
        # ----------------------------------------------------

        file.seek(0)

        file.save(
            DATASET_PATH
        )


        # ----------------------------------------------------
        # VERIFY FILE
        # ----------------------------------------------------

        if not os.path.exists(
            DATASET_PATH
        ):

            flash(
                "Dataset could not be saved.",
                "danger"
            )

            return redirect(
                url_for(
                    "manager_dashboard"
                )
            )


        # ----------------------------------------------------
        # RUN ML
        # ----------------------------------------------------

        result = refresh_ml_result()


        if result is None:

            flash(
                "Dataset was saved, but ML processing failed. "
                "Check the terminal for the ML error.",
                "danger"
            )

            return redirect(
                url_for(
                    "manager_dashboard"
                )
            )


        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        flash(
            f"Dataset uploaded successfully. "
            f"{len(df)} customers loaded.",
            "success"
        )


        # ----------------------------------------------------
        # IMPORTANT:
        # DIRECTLY GO TO DASHBOARD
        # ----------------------------------------------------

        return redirect(
            url_for(
                "manager_dashboard"
            )
        )


    except Exception as error:

        print(
            "UPLOAD ERROR:",
            error
        )

        flash(
            f"Dataset upload failed: {error}",
            "danger"
        )

        return redirect(
            url_for(
                "manager_dashboard"
            )
        )


# ============================================================
# DATASET PAGE
# ============================================================

@app.route("/dataset")
@login_required
def dataset():

    if not os.path.exists(
        DATASET_PATH
    ):

        return render_template(

            "dataset.html",

            data=[],

            columns=[],

            total_rows=0,

            total_columns=0,

            features=FEATURES,

            error=(
                "Dataset not found. "
                "Please upload a CSV dataset."
            )
        )

    try:

        df = pd.read_csv(
            DATASET_PATH
        )

        df.columns = [
            str(column).strip()
            for column in df.columns
        ]

        display_df = df.replace(
            {np.nan: ""}
        )

        data = display_df.to_dict(
            orient="records"
        )

        return render_template(

            "dataset.html",

            data=data,

            columns=list(
                df.columns
            ),

            total_rows=len(df),

            total_columns=len(
                df.columns
            ),

            features=FEATURES,

            error=None
        )

    except Exception as error:

        print(
            "DATASET ERROR:",
            error
        )

        return render_template(

            "dataset.html",

            data=[],

            columns=[],

            total_rows=0,

            total_columns=0,

            features=FEATURES,

            error=str(error)
        )


# ============================================================
# CUSTOMER SEARCH
# ============================================================

@app.route("/customers")
@login_required
def customer_search():

    result = get_ml_result()

    query = request.args.get(
        "q",
        ""
    ).strip()

    customers = []

    if result is not None:

        df = result[
            "customers"
        ].copy()

        if query:

            mask = pd.Series(
                False,
                index=df.index
            )

            for column in df.columns:

                try:

                    mask = (
                        mask
                        |
                        df[column]
                        .astype(str)
                        .str.contains(
                            query,
                            case=False,
                            na=False
                        )
                    )

                except Exception:
                    pass

            df = df[mask]

        customers = df.head(
            100
        ).to_dict(
            orient="records"
        )

    return render_template(

        "customer_search.html",

        customers=customers,

        query=query
    )


# ============================================================
# CUSTOMER PROFILE
# ============================================================

@app.route("/customer/<int:index>")
@login_required
def customer_profile(index):

    result = get_ml_result()

    if result is None:

        flash(
            "No dataset available. Please upload a dataset first.",
            "warning"
        )

        return redirect(
            url_for(
                "customer_search"
            )
        )

    df = result[
        "customers"
    ].copy()

    if (
        index < 0
        or index >= len(df)
    ):

        flash(
            "Customer not found.",
            "danger"
        )

        return redirect(
            url_for(
                "customer_search"
            )
        )

    customer = df.iloc[
        index
    ].to_dict()

    spending = 0

    for feature in FEATURES:

        try:

            spending += float(
                customer.get(
                    feature,
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            pass

    customer[
        "Annual_Spending"
    ] = spending

    order_columns = [
        "Orders",
        "Order_Count",
        "OrderCount",
        "Number_of_Orders"
    ]

    aov_columns = [
        "Average_Order_Value",
        "Average Order Value",
        "AOV"
    ]

    orders = None

    average_order_value = None

    for column in order_columns:

        if column in customer:

            orders = customer[
                column
            ]

            break

    for column in aov_columns:

        if column in customer:

            average_order_value = customer[
                column
            ]

            break

    if (
        orders is not None
        and average_order_value is None
    ):

        try:

            if float(orders) != 0:

                average_order_value = (
                    spending
                    /
                    float(orders)
                )

        except Exception:

            pass

    customer[
        "Orders"
    ] = orders

    customer[
        "Average_Order_Value"
    ] = average_order_value

    customer[
        "Recommendation"
    ] = customer.get(
        "Recommendation",
        "No recommendation available."
    )

    return render_template(

        "customer_profile.html",

        customer=customer,

        features=FEATURES
    )


# ============================================================
# SEGMENTS
# ============================================================

@app.route("/segments")
@login_required
def segments():

    result = get_ml_result()

    if result is None:

        return render_template(
            "segments.html",
            segments=[]
        )

    return render_template(

        "segments.html",

        segments=result[
            "summary"
        ]
    )


# ============================================================
# SEGMENT COMPARISON
# ============================================================

@app.route("/segment-comparison")
@login_required
def segment_comparison():

    result = get_ml_result()

    if result is None:

        return render_template(
            "segment_comparison.html",
            segments=[]
        )

    return render_template(

        "segment_comparison.html",

        segments=result[
            "summary"
        ]
    )


# ============================================================
# RECOMMENDATIONS
# ============================================================

@app.route("/recommendations")
@login_required
def recommendations():

    result = get_ml_result()

    if result is None:

        return render_template(
            "recommendations.html",
            segments=[]
        )

    return render_template(

        "recommendations.html",

        segments=result[
            "summary"
        ]
    )


# ============================================================
# EDA
# ============================================================

@app.route("/eda")
@login_required
def eda():

    result = get_ml_result()

    if result is None:

        return render_template(

            "eda.html",

            statistics=[],

            correlation={}
        )

    df = result[
        "cleaned"
    ]

    statistics = []

    for feature in FEATURES:

        if feature in df.columns:

            statistics.append({

                "feature": feature,

                "mean": float(
                    df[feature].mean()
                ),

                "median": float(
                    df[feature].median()
                ),

                "min": float(
                    df[feature].min()
                ),

                "max": float(
                    df[feature].max()
                )
            })

    correlation = (
        df[FEATURES]
        .corr()
        .round(3)
        .to_dict()
    )

    return render_template(

        "eda.html",

        statistics=statistics,

        correlation=correlation
    )


# ============================================================
# PREPROCESSING
# ============================================================

@app.route("/preprocessing")
@login_required
def preprocessing():

    result = get_ml_result()

    if result is None:

        return render_template(

            "preprocessing.html",

            features=FEATURES,

            original_shape=(0, 0),

            cleaned_shape=(0, 0),

            missing_before=0,

            missing_after=0
        )

    raw = result[
        "raw"
    ]

    cleaned = result[
        "cleaned"
    ]

    missing_before = int(
        raw[FEATURES]
        .isna()
        .sum()
        .sum()
    )

    missing_after = int(
        cleaned[FEATURES]
        .isna()
        .sum()
        .sum()
    )

    return render_template(

        "preprocessing.html",

        features=FEATURES,

        original_shape=raw.shape,

        cleaned_shape=cleaned.shape,

        missing_before=missing_before,

        missing_after=missing_after
    )


# ============================================================
# ELBOW
# ============================================================

@app.route("/elbow")
@login_required
def elbow():

    result = get_ml_result()

    if result is None:

        return render_template(

            "elbow.html",

            k_results=[],

            best_k="N/A"
        )

    return render_template(

        "elbow.html",

        k_results=result[
            "k_results"
        ],

        best_k=result[
            "best_k"
        ]
    )


# ============================================================
# CLUSTERING
# ============================================================

@app.route("/clustering")
@login_required
def clustering():

    result = get_ml_result()

    if result is None:

        return render_template(

            "clustering.html",

            customers=[],

            best_k="N/A"
        )

    df = result[
        "customers"
    ].copy()

    return render_template(

        "clustering.html",

        customers=df.head(
            100
        ).to_dict(
            orient="records"
        ),

        best_k=result[
            "best_k"
        ]
    )


# ============================================================
# PERFORMANCE
# ============================================================

@app.route("/performance")
@login_required
def performance():

    result = get_ml_result()

    if result is None:

        return render_template(

            "performance.html",

            best_k="N/A",

            silhouette="N/A",

            k_results=[]
        )

    return render_template(

        "performance.html",

        best_k=result[
            "best_k"
        ],

        silhouette=result[
            "silhouette"
        ],

        k_results=result[
            "k_results"
        ]
    )


# ============================================================
# PCA
# ============================================================
@app.route("/pca")
@login_required
def pca():

    result = get_ml_result()

    if result is None:
        return render_template(
            "pca.html",
            pca_data=[],
            best_k="N/A",
            total_customers=0
        )

    df = result["cleaned"].copy()

    # PCA coordinates
    try:
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import PCA

        # Required ML features
        features = [
            "Fresh",
            "Milk",
            "Grocery",
            "Frozen",
            "Detergents_Paper",
            "Delicatessen"
        ]

        # Make sure features exist
        available_features = [
            feature for feature in features
            if feature in df.columns
        ]

        if len(available_features) < 2:
            return render_template(
                "pca.html",
                pca_data=[],
                best_k=result.get("best_k", "N/A"),
                total_customers=len(df)
            )

        # Numeric conversion
        data = df[available_features].apply(
            pd.to_numeric,
            errors="coerce"
        )

        # Replace missing values
        data = data.fillna(data.median())

        # Scaling
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data)

        # PCA
        pca_model = PCA(n_components=2)
        pca_values = pca_model.fit_transform(scaled_data)

        # Get clusters
        cluster_values = result.get("clusters", [])

        # If clusters are not available, try dataframe
        if not cluster_values:
            if "Cluster" in df.columns:
                cluster_values = df["Cluster"].tolist()
            elif "cluster" in df.columns:
                cluster_values = df["cluster"].tolist()
            else:
                cluster_values = ["N/A"] * len(df)

        # Business segments
        segments = []

        if "Business Segment" in df.columns:
            segments = df["Business Segment"].tolist()

        elif "Segment" in df.columns:
            segments = df["Segment"].tolist()

        else:
            segments = ["Unknown"] * len(df)

        # Create PCA records
        pca_data = []

        for i in range(len(pca_values)):

            pca_data.append({
                "PC1": float(pca_values[i][0]),
                "PC2": float(pca_values[i][1]),
                "Cluster": cluster_values[i]
                    if i < len(cluster_values)
                    else "N/A",
                "Business Segment": segments[i]
                    if i < len(segments)
                    else "Unknown"
            })

        # Find PCA ranges
        x_values = [
            row["PC1"]
            for row in pca_data
        ]

        y_values = [
            row["PC2"]
            for row in pca_data
        ]

        min_x = min(x_values) if x_values else 0
        max_x = max(x_values) if x_values else 1

        min_y = min(y_values) if y_values else 0
        max_y = max(y_values) if y_values else 1

        # Calculate graph positions
        for row in pca_data:

            if max_x != min_x:
                row["x_position"] = (
                    (row["PC1"] - min_x)
                    /
                    (max_x - min_x)
                    * 100
                )
            else:
                row["x_position"] = 50

            if max_y != min_y:
                row["y_position"] = (
                    (max_y - row["PC2"])
                    /
                    (max_y - min_y)
                    * 100
                )
            else:
                row["y_position"] = 50

        return render_template(
            "pca.html",
            pca_data=pca_data,
            best_k=result.get("best_k", "N/A"),
            total_customers=len(df)
        )

    except Exception as error:

        print("PCA ERROR:", error)

        return render_template(
            "pca.html",
            pca_data=[],
            best_k=result.get("best_k", "N/A"),
            total_customers=len(df)
        )
# ============================================================
# INSIGHTS
# ============================================================

@app.route("/insights")
@login_required
def insights():

    result = get_ml_result()

    insights_data = []

    if result is not None:

        for segment in result[
            "summary"
        ]:

            # Support both possible summary key styles
            segment_name = segment.get(
                "segment",
                segment.get(
                    "Business_Segment",
                    "Unknown"
                )
            )

            customers_count = segment.get(
                "customers",
                segment.get(
                    "Customer_Count",
                    0
                )
            )

            average_spending = segment.get(
                "average_spending",
                segment.get(
                    "Average_Spending",
                    0
                )
            )

            total_spending = segment.get(
                "total_spending",
                segment.get(
                    "Total_Spending",
                    0
                )
            )

            recommendation = segment.get(
                "recommendation",
                segment.get(
                    "Recommendation",
                    "No recommendation available."
                )
            )

            insights_data.append({

                "segment": segment_name,

                "customers": customers_count,

                "average_spending": average_spending,

                "total_spending": total_spending,

                "recommendation": recommendation

            })

    return render_template(

        "insights.html",

        insights=insights_data
    )


# ============================================================
# USERS
# ============================================================

@app.route("/users")
@login_required
def users():

    conn = get_db_connection()

    users_data = conn.execute(
        """
        SELECT
            id,
            full_name,
            username,
            email,
            role,
            created_at
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    return render_template(

        "users.html",

        users=users_data
    )


# ============================================================
# DELETE USER
# ============================================================

@app.route(
    "/users/delete/<int:user_id>",
    methods=["POST"]
)
@login_required
def delete_user(user_id):

    current_user_id = session.get(
        "user_id"
    )

    if current_user_id == user_id:

        flash(
            "You cannot delete your own account while logged in.",
            "danger"
        )

        return redirect(
            url_for("users")
        )

    conn = get_db_connection()

    conn.execute(
        """
        DELETE FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    conn.commit()

    conn.close()

    flash(
        "User deleted successfully.",
        "success"
    )

    return redirect(
        url_for("users")
    )


# ============================================================
# API - DASHBOARD
# ============================================================

@app.route("/api/dashboard")
@login_required
def dashboard_api():

    result = get_ml_result()

    if result is None:

        return jsonify({

            "success": False,

            "message": (
                "Dataset not available."
            )
        })

    return jsonify({

        "success": True,

        "total_customers":
            result[
                "total_customers"
            ],

        "total_spending":
            result[
                "total_spending"
            ],

        "average_spending":
            result[
                "average_spending"
            ],

        "best_k":
            result[
                "best_k"
            ],

        "silhouette":
            result[
                "silhouette"
            ],

        "segments":
            result[
                "summary"
            ]
    })


# ============================================================
# API - SEGMENTS
# ============================================================

@app.route("/api/segments")
@login_required
def segments_api():

    result = get_ml_result()

    if result is None:

        return jsonify({

            "success": False,

            "segments": []
        })

    return jsonify({

        "success": True,

        "segments":
            result[
                "summary"
            ]
    })


# ============================================================
# API - K VALUES
# ============================================================

@app.route("/api/k-values")
@login_required
def k_values_api():

    result = get_ml_result()

    if result is None:

        return jsonify({

            "success": False,

            "results": []
        })

    return jsonify({

        "success": True,

        "results":
            result[
                "k_results"
            ],

        "best_k":
            result[
                "best_k"
            ]
    })


# ============================================================
# API - PCA
# ============================================================

@app.route("/api/pca")
@login_required
def pca_api():

    result = get_ml_result()

    if result is None:

        return jsonify({

            "success": False,

            "data": []
        })

    try:

        from sklearn.decomposition import PCA

        pca_model = PCA(
            n_components=2
        )

        components = (
            pca_model.fit_transform(
                result["scaled"]
            )
        )

        customers = result[
            "customers"
        ]

        data = []

        for i, point in enumerate(
            components
        ):

            data.append({

                "pc1": float(
                    point[0]
                ),

                "pc2": float(
                    point[1]
                ),

                "cluster": int(
                    customers.iloc[i][
                        "Cluster"
                    ]
                ),

                "segment":
                    customers.iloc[i][
                        "Segment"
                    ]
            })

        return jsonify({

            "success": True,

            "explained_variance": [
                float(value)
                for value in
                pca_model.explained_variance_ratio_
            ],

            "data": data
        })

    except Exception as error:

        return jsonify({

            "success": False,

            "message": str(error),

            "data": []
        })


# ============================================================
# API - CUSTOMER SEARCH
# ============================================================

@app.route("/api/customers/search")
@login_required
def customer_search_api():

    result = get_ml_result()

    if result is None:

        return jsonify({

            "success": False,

            "customers": []
        })

    query = request.args.get(
        "q",
        ""
    ).strip()

    df = result[
        "customers"
    ].copy()

    if query:

        mask = pd.Series(
            False,
            index=df.index
        )

        for column in df.columns:

            try:

                mask = (
                    mask
                    |
                    df[column]
                    .astype(str)
                    .str.contains(
                        query,
                        case=False,
                        na=False
                    )
                )

            except Exception:
                pass

        df = df[mask]

    data = df.head(
        100
    ).to_dict(
        orient="records"
    )

    return jsonify({

        "success": True,

        "count": len(data),

        "customers": data
    })


# ============================================================
# ERROR HANDLER - 404
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    if "user_id" in session:

        flash(
            "Page not found.",
            "danger"
        )

        return redirect(
            url_for(
                "manager_dashboard"
            )
        )

    return redirect(
        url_for("landing")
    )


# ============================================================
# ERROR HANDLER - 413
# ============================================================

@app.errorhandler(413)
def file_too_large(error):

    flash(
        "File is too large. Maximum size is 16 MB.",
        "danger"
    )

    return redirect(
        url_for(
            "manager_dashboard"
        )
    )


# ============================================================
# INITIALIZATION
# ============================================================

init_db()


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print("=" * 65)

    print(
        "ML-Based Wholesale Customer Segmentation"
    )

    print("=" * 65)

    print(
        "Database:",
        DATABASE
    )

    print(
        "Dataset:",
        DATASET_PATH
    )

    print("=" * 65)

    if os.path.exists(
        DATASET_PATH
    ):

        print(
            "Dataset found."
        )

        try:

            result = get_ml_result()

            if result:

                print(
                    "Customers:",
                    result[
                        "total_customers"
                    ]
                )

                print(
                    "Best K:",
                    result[
                        "best_k"
                    ]
                )

                print(
                    "Silhouette:",
                    result[
                        "silhouette"
                    ]
                )

        except Exception as error:

            print(
                "Initial ML processing error:",
                error
            )

    else:

        print(
            "Dataset not found."
        )

        print(
            "Upload the dataset from the Dashboard."
        )

    print("=" * 65)

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )