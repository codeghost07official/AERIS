import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import Config


def get_connection():
    """
    Create and return a PostgreSQL database connection.

    AERIS uses PostgreSQL (Neon) for persistent metadata such as
    users and analysis history. Large telemetry datasets and image
    files are stored on local disk rather than inside the database.
    """
    return psycopg2.connect(
        Config.DATABASE_URL,
        cursor_factory=RealDictCursor,
        connect_timeout=10,
    )


@contextmanager
def get_db():
    """
    Context manager for safe database operations.

    The transaction is committed when the operation succeeds and
    rolled back automatically if an exception occurs.
    """
    connection = get_connection()

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def execute_query(query, params=None, fetch=False, fetchone=False):
    """
    Execute a parameterized SQL query safely.

    Parameters:
        query: SQL statement.
        params: Values supplied to the SQL statement.
        fetch: Return all resulting rows.
        fetchone: Return only the first resulting row.

    Returns:
        Query results when requested, otherwise None.
    """
    with get_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params or ())

            if fetchone:
                return cursor.fetchone()

            if fetch:
                return cursor.fetchall()

            return None


# ----------------------------------------------------------------------
# User operations
# ----------------------------------------------------------------------

def create_user(
    email,
    password_hash=None,
    name=None,
    google_id=None,
):
    """
    Create a new AERIS user.

    Returns the newly created user's database row.
    """
    user_id = str(uuid.uuid4())

    query = """
        INSERT INTO users (
            id,
            email,
            password_hash,
            name,
            google_id,
            created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING
            id,
            email,
            password_hash,
            name,
            google_id,
            created_at
    """

    now = datetime.now(timezone.utc)

    return execute_query(
        query,
        (
            user_id,
            email.strip().lower(),
            password_hash,
            name,
            google_id,
            now,
        ),
        fetchone=True,
    )


def get_user_by_id(user_id):
    """
    Retrieve a user by their unique ID.
    """
    query = """
        SELECT
            id,
            email,
            password_hash,
            name,
            google_id,
            created_at
        FROM users
        WHERE id = %s
        LIMIT 1
    """

    return execute_query(
        query,
        (str(user_id),),
        fetchone=True,
    )


def get_user_by_email(email):
    """
    Retrieve a user using their email address.
    """
    if not email:
        return None

    query = """
        SELECT
            id,
            email,
            password_hash,
            name,
            google_id,
            created_at
        FROM users
        WHERE LOWER(email) = LOWER(%s)
        LIMIT 1
    """

    return execute_query(
        query,
        (email.strip(),),
        fetchone=True,
    )


def get_user_by_google_id(google_id):
    """
    Retrieve a user using their Google OAuth subject ID.
    """
    if not google_id:
        return None

    query = """
        SELECT
            id,
            email,
            password_hash,
            name,
            google_id,
            created_at
        FROM users
        WHERE google_id = %s
        LIMIT 1
    """

    return execute_query(
        query,
        (google_id,),
        fetchone=True,
    )


# ----------------------------------------------------------------------
# Analysis history operations
# ----------------------------------------------------------------------

def create_analysis_record(
    user_id,
    analysis_type,
    filename=None,
    status="completed",
    total_observations=None,
    anomalies_detected=None,
    anomaly_rate=None,
    features_used=None,
    method=None,
    method_description=None,
    file_path=None,
    result_data=None,
):
    """
    Store metadata and results for a completed AERIS analysis.

    Large source files are not stored in PostgreSQL. The database
    stores metadata, metrics and explainable result information.
    """
    analysis_id = str(uuid.uuid4())

    query = """
        INSERT INTO analysis_history (
            id,
            user_id,
            analysis_type,
            filename,
            status,
            total_observations,
            anomalies_detected,
            anomaly_rate,
            features_used,
            method,
            method_description,
            file_path,
            result_data,
            created_at
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        RETURNING *
    """

    now = datetime.now(timezone.utc)

    return execute_query(
        query,
        (
            analysis_id,
            str(user_id),
            analysis_type,
            filename,
            status,
            total_observations,
            anomalies_detected,
            anomaly_rate,
            features_used,
            method,
            method_description,
            file_path,
            result_data,
            now,
        ),
        fetchone=True,
    )


def get_analysis_history(
    user_id,
    analysis_type=None,
    search=None,
):
    """
    Retrieve analysis history for a particular user.

    Optional filtering can be applied by analysis type and filename.
    """
    conditions = ["user_id = %s"]
    params = [str(user_id)]

    if analysis_type:
        conditions.append("analysis_type = %s")
        params.append(analysis_type)

    if search:
        conditions.append("filename ILIKE %s")
        params.append(f"%{search}%")

    query = f"""
        SELECT *
        FROM analysis_history
        WHERE {" AND ".join(conditions)}
        ORDER BY created_at DESC
    """

    return execute_query(
        query,
        tuple(params),
        fetch=True,
    )


def get_analysis_by_id(analysis_id, user_id=None):
    """
    Retrieve one analysis record.

    When user_id is supplied, the query also verifies ownership.
    """
    if user_id is not None:
        query = """
            SELECT *
            FROM analysis_history
            WHERE id = %s
              AND user_id = %s
            LIMIT 1
        """

        return execute_query(
            query,
            (str(analysis_id), str(user_id)),
            fetchone=True,
        )

    query = """
        SELECT *
        FROM analysis_history
        WHERE id = %s
        LIMIT 1
    """

    return execute_query(
        query,
        (str(analysis_id),),
        fetchone=True,
    )


def delete_analysis_record(analysis_id, user_id):
    """
    Delete an analysis-history record belonging to the specified user.

    The actual uploaded source file can be removed separately by the
    route handling the request.
    """
    query = """
        DELETE FROM analysis_history
        WHERE id = %s
          AND user_id = %s
    """

    execute_query(
        query,
        (str(analysis_id), str(user_id)),
    )


# ----------------------------------------------------------------------
# Dashboard statistics
# ----------------------------------------------------------------------

def get_dashboard_statistics(user_id):
    """
    Calculate summary statistics for the authenticated user's
    dashboard.
    """
    query = """
        SELECT
            COUNT(*) AS total_analyses,

            COUNT(*) FILTER (
                WHERE analysis_type = 'telemetry'
            ) AS telemetry_analyses,

            COUNT(*) FILTER (
                WHERE analysis_type = 'image'
            ) AS image_analyses,

            COALESCE(
                SUM(anomalies_detected) FILTER (
                    WHERE analysis_type = 'telemetry'
                ),
                0
            ) AS total_anomalies

        FROM analysis_history
        WHERE user_id = %s
    """

    result = execute_query(
        query,
        (str(user_id),),
        fetchone=True,
    )

    if not result:
        return {
            "total_analyses": 0,
            "telemetry_analyses": 0,
            "image_analyses": 0,
            "total_anomalies": 0,
        }

    return dict(result)


def get_recent_analyses(user_id, limit=5):
    """
    Return the user's most recent analysis records.
    """
    # Keep the limit controlled by the application rather than allowing
    # arbitrary SQL fragments from user input.
    limit = max(1, min(int(limit), 50))

    query = f"""
        SELECT *
        FROM analysis_history
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT {limit}
    """

    return execute_query(
        query,
        (str(user_id),),
        fetch=True,
    )