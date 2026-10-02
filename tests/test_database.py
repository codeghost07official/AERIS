import uuid
import unittest
from unittest.mock import patch

from app import database


class FakeCursor:
    def __init__(self, one=None, many=None, rowcount=1):
        self.one = one or {"id": uuid.uuid4()}
        self.many = many or []
        self.rowcount = rowcount
        self.statements = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=None):
        self.statements.append((query, params))

    def fetchone(self):
        return self.one

    def fetchall(self):
        return self.many


class FakeConnection:
    def __init__(self, cursor):
        self.fake_cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def cursor(self):
        return self.fake_cursor

    def commit(self):
        pass


class DatabaseSchemaTests(unittest.TestCase):
    def test_app_initializes_database_at_startup(self):
        from app import create_app

        with patch("app.database.init_db") as initialize_database:
            create_app()

        initialize_database.assert_called_once_with()

    def test_init_db_creates_uuid_schema_for_new_database(self):
        cursor = FakeCursor()
        connection = FakeConnection(cursor)

        with patch.object(database, "get_user_id_type", return_value=None):
            with patch.object(
                database, "get_db_connection", return_value=connection
            ):
                database.init_db()

        statements = "\n".join(query for query, _ in cursor.statements)
        self.assertIn("id UUID PRIMARY KEY", statements)
        self.assertIn(
            "CREATE TABLE IF NOT EXISTS public.analysis_history", statements
        )
        self.assertIn("REFERENCES public.users(id) ON DELETE CASCADE", statements)
        self.assertIn("CONSTRAINT analysis_type_valid", statements)
        self.assertIn("CONSTRAINT anomaly_rate_valid", statements)
        self.assertIn("CONSTRAINT users_email_not_blank", statements)
        self.assertIn(
            "ADD COLUMN IF NOT EXISTS plain_language_explanation TEXT",
            statements,
        )
        self.assertNotRegex(statements, r"\b(DROP|TRUNCATE|DELETE FROM)\b")
        for query, _ in cursor.statements:
            if "CREATE TABLE" in query or "CREATE INDEX" in query:
                self.assertIn("IF NOT EXISTS", query)

    def test_init_db_keeps_existing_integer_schema(self):
        cursor = FakeCursor()
        connection = FakeConnection(cursor)

        with patch.object(database, "get_user_id_type", return_value="integer"):
            with patch.object(
                database, "get_db_connection", return_value=connection
            ):
                database.init_db()

        statements = "\n".join(query for query, _ in cursor.statements)
        self.assertIn("CREATE TABLE IF NOT EXISTS public.analyses", statements)
        self.assertIn(
            "ADD COLUMN IF NOT EXISTS plain_language_explanation TEXT",
            statements,
        )
        self.assertNotIn(
            "CREATE TABLE IF NOT EXISTS public.analysis_history", statements
        )

    def test_create_user_uses_uuid_id_when_required(self):
        user_id = uuid.uuid4()
        cursor = FakeCursor(one={"id": user_id})
        connection = FakeConnection(cursor)

        with patch.object(database, "get_user_id_type", return_value="uuid"):
            with patch.object(
                database, "get_db_connection", return_value=connection
            ):
                created_id = database.create_user(
                    "Test User", "test@example.com", "hashed-password"
                )

        query, params = cursor.statements[0]
        self.assertIn("(id, name, email, password_hash, google_id)", query)
        self.assertIsInstance(params[0], uuid.UUID)
        self.assertEqual(created_id, user_id)

    def test_create_user_uses_generated_integer_id(self):
        cursor = FakeCursor(one={"id": 42})
        connection = FakeConnection(cursor)

        with patch.object(database, "get_user_id_type", return_value="integer"):
            with patch.object(
                database, "get_db_connection", return_value=connection
            ):
                created_id = database.create_user(
                    "Test User", "test@example.com", "hashed-password"
                )

        query, params = cursor.statements[0]
        self.assertIn("(name, email, password_hash, google_id)", query)
        self.assertNotIn("(id, name", query)
        self.assertEqual(params, ("Test User", "test@example.com", "hashed-password", None))
        self.assertEqual(created_id, 42)

    def test_save_analysis_uses_uuid_history_table(self):
        cursor = FakeCursor(one={"id": uuid.uuid4()})
        connection = FakeConnection(cursor)
        user_id = uuid.uuid4()

        with patch.object(database, "get_user_id_type", return_value="uuid"):
            with patch.object(
                database, "get_db_connection", return_value=connection
            ):
                database.save_analysis(
                    user_id,
                    "data.csv",
                    "Telemetry",
                    8,
                    1,
                    12.5,
                    "summary",
                    plain_language_explanation="Plain explanation",
                )

        query, params = cursor.statements[0]
        self.assertIn("INSERT INTO analysis_history", query)
        self.assertIn("plain_language_explanation", query)
        self.assertEqual(params[1], user_id)
        self.assertEqual(params[2], "telemetry")
        self.assertEqual(params[-1], "Plain explanation")

    def test_save_analysis_uses_integer_analyses_table(self):
        cursor = FakeCursor(one={"id": 7})
        connection = FakeConnection(cursor)

        with patch.object(database, "get_user_id_type", return_value="integer"):
            with patch.object(
                database, "get_db_connection", return_value=connection
            ):
                database.save_analysis(
                    "42",
                    "data.csv",
                    "Telemetry",
                    8,
                    1,
                    12.5,
                    "summary",
                    plain_language_explanation="Plain explanation",
                )

        query, params = cursor.statements[0]
        self.assertIn("INSERT INTO analyses", query)
        self.assertIn("plain_language_explanation", query)
        self.assertEqual(params[0], 42)
        self.assertEqual(params[-1], "Plain explanation")

    def test_delete_uuid_analysis_checks_record_and_owner(self):
        cursor = FakeCursor(rowcount=1)
        connection = FakeConnection(cursor)
        owner_id = uuid.uuid4()
        analysis_id = uuid.uuid4()

        with patch.object(database, "get_user_id_type", return_value="uuid"):
            with patch.object(
                database, "get_db_connection", return_value=connection
            ):
                deleted = database.delete_analysis(
                    str(owner_id), str(analysis_id)
                )

        query, params = cursor.statements[0]
        self.assertIn("DELETE FROM public.analysis_history", query)
        self.assertIn("WHERE id = %s AND user_id = %s", query)
        self.assertEqual(params, (analysis_id, owner_id))
        self.assertTrue(deleted)

    def test_delete_integer_analysis_checks_record_and_owner(self):
        cursor = FakeCursor(rowcount=0)
        connection = FakeConnection(cursor)

        with patch.object(database, "get_user_id_type", return_value="integer"):
            with patch.object(
                database, "get_db_connection", return_value=connection
            ):
                deleted = database.delete_analysis("42", "17")

        query, params = cursor.statements[0]
        self.assertIn("DELETE FROM public.analyses", query)
        self.assertIn("WHERE id = %s AND user_id = %s", query)
        self.assertEqual(params, (17, 42))
        self.assertFalse(deleted)

    def test_history_query_matches_uuid_schema(self):
        cursor = FakeCursor(many=[])
        connection = FakeConnection(cursor)
        user_id = uuid.uuid4()

        with patch.object(database, "get_user_id_type", return_value="uuid"):
            with patch.object(
                database, "get_db_connection", return_value=connection
            ):
                database.get_user_history(str(user_id), limit=5)

        query, params = cursor.statements[0]
        self.assertIn("FROM analysis_history", query)
        self.assertIn("plain_language_explanation", query)
        self.assertEqual(params, [user_id, 5])

    def test_history_query_matches_integer_schema(self):
        cursor = FakeCursor(many=[])
        connection = FakeConnection(cursor)

        with patch.object(database, "get_user_id_type", return_value="integer"):
            with patch.object(
                database, "get_db_connection", return_value=connection
            ):
                database.get_user_history("42", limit=5)

        query, params = cursor.statements[0]
        self.assertIn("FROM analyses", query)
        self.assertIn("plain_language_explanation", query)
        self.assertEqual(params, [42, 5])


if __name__ == "__main__":
    unittest.main()
