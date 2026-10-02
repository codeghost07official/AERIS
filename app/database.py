
import os
import uuid

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from dotenv import load_dotenv

load_dotenv(".env")


def get_db_connection():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is missing from .env")

    return psycopg.connect(
        database_url,
        row_factory=dict_row,
    )


def get_user_id_type():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND table_name = 'users'
                    AND column_name = 'id'
            """)
            result = cur.fetchone()

    return result["data_type"] if result else None


def create_user(name, email, password_hash=None, google_id=None):
    id_type = get_user_id_type()

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if id_type == "uuid":
                user_id = uuid.uuid4()
                cur.execute("""
                    INSERT INTO public.users
                        (id, name, email, password_hash, google_id)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (user_id, name, email, password_hash, google_id))
            else:
                cur.execute("""
                    INSERT INTO public.users
                        (name, email, password_hash, google_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (name, email, password_hash, google_id))

            result = cur.fetchone()

    if not result:
        raise RuntimeError("User creation returned no ID.")

    return result["id"]


def init_db():
    user_id_type = get_user_id_type()

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if user_id_type is None:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS public.users (
                        id UUID PRIMARY KEY,
                        name VARCHAR(150),
                        email VARCHAR(320) NOT NULL UNIQUE,
                        password_hash TEXT,
                        google_id VARCHAR(255) UNIQUE,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT users_email_not_blank
                            CHECK (length(trim(email)) > 0)
                    );
                """)
                user_id_type = "uuid"

            if user_id_type == "uuid":
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS public.analysis_history (
                        id UUID PRIMARY KEY,
                        user_id UUID NOT NULL
                            REFERENCES public.users(id) ON DELETE CASCADE,
                        analysis_type VARCHAR(30) NOT NULL
                            CONSTRAINT analysis_type_valid
                                CHECK (analysis_type IN ('telemetry', 'image')),
                        filename VARCHAR(255),
                        status VARCHAR(30) NOT NULL DEFAULT 'completed'
                            CONSTRAINT analysis_status_valid
                                CHECK (status IN ('processing', 'completed', 'failed')),
                        total_observations INTEGER,
                        anomalies_detected INTEGER,
                        anomaly_rate DOUBLE PRECISION,
                        features_used INTEGER,
                        method VARCHAR(100),
                        method_description TEXT,
                        file_path TEXT,
                        result_data JSONB,
                        plain_language_explanation TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT anomaly_rate_valid CHECK (
                            anomaly_rate IS NULL OR
                            (anomaly_rate >= 0 AND anomaly_rate <= 100)
                        ),
                        CONSTRAINT total_observations_valid CHECK (
                            total_observations IS NULL OR total_observations >= 0
                        ),
                        CONSTRAINT anomalies_detected_valid CHECK (
                            anomalies_detected IS NULL OR anomalies_detected >= 0
                        ),
                        CONSTRAINT features_used_valid CHECK (
                            features_used IS NULL OR features_used >= 0
                        )
                    );
                """)
                cur.execute("""
                    ALTER TABLE public.analysis_history
                    ADD COLUMN IF NOT EXISTS plain_language_explanation TEXT;
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_analysis_user_id
                    ON public.analysis_history(user_id);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_analysis_created_at
                    ON public.analysis_history(created_at DESC);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_analysis_type
                    ON public.analysis_history(analysis_type);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_analysis_status
                    ON public.analysis_history(status);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_analysis_result_data
                    ON public.analysis_history USING GIN(result_data);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_email
                    ON public.users(email);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_users_google_id
                    ON public.users(google_id);
                """)
            elif user_id_type in {"integer", "bigint", "smallint"}:
                user_id_sql_type = {
                    "integer": "INTEGER",
                    "bigint": "BIGINT",
                    "smallint": "SMALLINT",
                }[user_id_type]
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS public.analyses (
                        id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                        user_id {user_id_sql_type} NOT NULL
                            REFERENCES public.users(id) ON DELETE CASCADE,
                        filename VARCHAR(255) NOT NULL,
                        analysis_type VARCHAR(30) NOT NULL,
                        observations INTEGER DEFAULT 0,
                        anomaly_count INTEGER DEFAULT 0,
                        anomaly_percentage DOUBLE PRECISION DEFAULT 0,
                        summary TEXT NOT NULL,
                        plain_language_explanation TEXT,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("""
                    ALTER TABLE public.analyses
                    ADD COLUMN IF NOT EXISTS plain_language_explanation TEXT;
                """)
            else:
                raise RuntimeError(
                    f"Unsupported users.id database type: {user_id_type}"
                )

        conn.commit()


def save_analysis(
    user_id,
    filename,
    analysis_type,
    observations,
    anomaly_count,
    anomaly_percentage,
    summary,
    plain_language_explanation=None,
):
    id_type = get_user_id_type()

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if id_type == "uuid":
                analysis_id = uuid.uuid4()
                cur.execute("""
                    INSERT INTO analysis_history (
                        id, user_id, analysis_type, filename,
                        total_observations, anomalies_detected, anomaly_rate,
                        method, method_description, result_data,
                        plain_language_explanation
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    analysis_id,
                    uuid.UUID(str(user_id)),
                    analysis_type.lower(),
                    filename,
                    observations,
                    anomaly_count,
                    anomaly_percentage,
                    "IsolationForest" if analysis_type.lower() == "telemetry"
                    else "OpenCV image metrics",
                    summary,
                    Jsonb({"summary": summary}),
                    plain_language_explanation,
                ))
            else:
                cur.execute("""
                    INSERT INTO analyses (
                        user_id, filename, analysis_type, observations,
                        anomaly_count, anomaly_percentage, summary,
                        plain_language_explanation
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    int(user_id),
                    filename,
                    analysis_type,
                    observations,
                    anomaly_count,
                    anomaly_percentage,
                    summary,
                    plain_language_explanation,
                ))

            result = cur.fetchone()

        conn.commit()
        return result["id"]


def delete_analysis(user_id, analysis_id):
    id_type = get_user_id_type()

    if id_type == "uuid":
        table = "public.analysis_history"
        record_id = uuid.UUID(str(analysis_id))
        owner_id = uuid.UUID(str(user_id))
    elif id_type in {"integer", "bigint", "smallint"}:
        table = "public.analyses"
        record_id = int(analysis_id)
        owner_id = int(user_id)
    else:
        raise RuntimeError(f"Unsupported users.id database type: {id_type}")

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {table} WHERE id = %s AND user_id = %s",
                (record_id, owner_id),
            )
            deleted = cur.rowcount == 1
        conn.commit()

    return deleted


def get_user_history(user_id, limit=None):
    id_type = get_user_id_type()
    if id_type == "uuid":
        query = """
            SELECT
                id,
                user_id,
                filename,
                INITCAP(analysis_type) AS analysis_type,
                total_observations AS observations,
                anomalies_detected AS anomaly_count,
                anomaly_rate AS anomaly_percentage,
                COALESCE(result_data ->> 'summary', method_description, '') AS summary,
                plain_language_explanation,
                created_at
            FROM analysis_history
            WHERE user_id = %s
            ORDER BY created_at DESC
        """
        user_id = uuid.UUID(str(user_id))
    else:
        query = """
            SELECT
                id, user_id, filename, analysis_type, observations,
                anomaly_count, anomaly_percentage, summary,
                plain_language_explanation, created_at
            FROM analyses
            WHERE user_id = %s
            ORDER BY created_at DESC
        """
        user_id = int(user_id)

    params = [user_id]

    if limit is not None:
        query += " LIMIT %s"
        params.append(limit)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

