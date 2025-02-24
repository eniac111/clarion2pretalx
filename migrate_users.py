#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import DictCursor

SOURCE_DB = "clarion"  # Clarion
TARGET_DB = "pretalx"  # Pretalx
DB_USER = "postgres"
DB_PASSWORD = "mysecretpassword"
DB_HOST = "localhost"
DB_PORT = "5432"

source_conn = psycopg2.connect(
    dbname=SOURCE_DB, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
)
target_conn = psycopg2.connect(
    dbname=TARGET_DB, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
)

source_cursor = source_conn.cursor(cursor_factory=DictCursor)
target_cursor = target_conn.cursor()

source_cursor.execute("""
    SELECT DISTINCT u.id,
           u.email,
           u.encrypted_password,
           u.created_at,
           u.updated_at,
           u.admin,
           u.language
    FROM users u
    LEFT JOIN participations p ON p.participant_id = u.id
    WHERE p.participant_id IS NOT NULL
       OR u.admin = TRUE
""")
users = source_cursor.fetchall()

DEFAULT_LOCALE = "en"
DEFAULT_TIMEZONE = "UTC"

migrated_count = 0

for user in users:
    email = user["email"]
    password = user["encrypted_password"]  # Bcrypt hash
    date_joined = user["created_at"]
    last_login = user["updated_at"]
    is_staff = user["admin"]
    is_superuser = user["admin"]
    is_active = True
    locale = user["language"] if user["language"] else DEFAULT_LOCALE
    timezone = DEFAULT_TIMEZONE
    name = email.split("@")[0]
    get_gravatar = False
    is_administrator = user["admin"]

    target_cursor.execute("SELECT id FROM person_user WHERE email = %s;", (email,))
    existing_user = target_cursor.fetchone()

    if existing_user:
        print(f"Skipping existing user: {email}")
        continue

    print(f"Importing user: {email}")
    target_cursor.execute("""
        INSERT INTO person_user 
        (password, last_login, name, email, is_active, is_staff, is_superuser, locale, timezone, get_gravatar, is_administrator) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (email) DO NOTHING;
    """, (
        password, last_login, name, email,
        is_active, is_staff, is_superuser,
        locale, timezone, get_gravatar,
        is_administrator
    ))
    migrated_count += 1

target_conn.commit()
source_conn.close()
target_conn.close()

print("Migration complete! Only users with participations or admin privileges were processed.")
print(f"{migrated_count} user(s) imported.")
