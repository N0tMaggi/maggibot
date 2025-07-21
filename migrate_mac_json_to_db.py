

import json
import os
from handlers.database import get_db_connection, DB_TYPE

def migrate_json_to_sql():
    if not os.path.exists('data/mac.json'):
        print("mac.json not found. Skipping migration.")
        return

    with open('data/mac.json', 'r') as f:
        bans = json.load(f)

    if not bans:
        print("mac.json is empty. Nothing to migrate.")
        return

    conn = get_db_connection()
    if conn is None:
        print("Database connection not available. Skipping migration.")
        return

    cursor = conn.cursor()

    if DB_TYPE == 'mysql':
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS mac_bans (
            id BIGINT PRIMARY KEY,
            name VARCHAR(255),
            bandate VARCHAR(255),
            reason TEXT,
            serverid BIGINT,
            servername VARCHAR(255),
            bannedby VARCHAR(255)
        );
        """
    elif DB_TYPE == 'sqlite':
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS mac_bans (
            id INTEGER PRIMARY KEY,
            name TEXT,
            bandate TEXT,
            reason TEXT,
            serverid INTEGER,
            servername TEXT,
            bannedby TEXT
        );
        """
    else:
        print(f"Unsupported DB_TYPE: {DB_TYPE}")
        return

    cursor.execute(create_table_sql)

    # Helper to format values for SQL file
    def sql_format_value(value):
        if value is None:
            return "NULL"
        if isinstance(value, (int, float)):
            return str(value)
        # Escape single quotes for SQL
        return "'" + str(value).replace("'", "''") + "'"

    with open('mac_bans.sql', 'w', encoding='utf-8') as f:
        f.write(create_table_sql)
        for user_id, ban in bans.items():
            # Ensure all fields are present
            if 'id' not in ban or ban['id'] is None:
                try:
                    ban['id'] = int(user_id) # Use the key from the JSON as the ID
                except (ValueError, TypeError):
                    print(f"Skipping invalid user_id: {user_id}")
                    continue

            ban.setdefault('name', None)
            ban.setdefault('bandate', None)
            ban.setdefault('reason', None)
            ban.setdefault('serverid', None)
            ban.setdefault('servername', None)
            ban.setdefault('bannedby', None)

            if DB_TYPE == 'mysql':
                # Execute against DB with parameter substitution
                db_sql = """INSERT INTO mac_bans (id, name, bandate, reason, serverid, servername, bannedby) VALUES (%(id)s, %(name)s, %(bandate)s, %(reason)s, %(serverid)s, %(servername)s, %(bannedby)s) ON DUPLICATE KEY UPDATE name=%(name)s, bandate=%(bandate)s, reason=%(reason)s, serverid=%(serverid)s, servername=%(servername)s, bannedby=%(bannedby)s;"""
                cursor.execute(db_sql, ban)
                
                # Create a version of the SQL for the file with real data
                file_values = {k: sql_format_value(v) for k, v in ban.items()}
                file_sql = f"INSERT INTO mac_bans (id, name, bandate, reason, serverid, servername, bannedby) VALUES ({file_values['id']}, {file_values['name']}, {file_values['bandate']}, {file_values['reason']}, {file_values['serverid']}, {file_values['servername']}, {file_values['bannedby']}) ON DUPLICATE KEY UPDATE name={file_values['name']}, bandate={file_values['bandate']}, reason={file_values['reason']}, serverid={file_values['serverid']}, servername={file_values['servername']}, bannedby={file_values['bannedby']};\n"
                f.write(file_sql)

            elif DB_TYPE == 'sqlite':
                # Execute against DB with parameter substitution
                db_sql = """INSERT OR REPLACE INTO mac_bans (id, name, bandate, reason, serverid, servername, bannedby) VALUES (?, ?, ?, ?, ?, ?, ?);"""
                db_values = (ban['id'], ban['name'], ban['bandate'], ban['reason'], ban['serverid'], ban['servername'], ban['bannedby'])
                cursor.execute(db_sql, db_values)

                # Create a version of the SQL for the file with real data
                file_values_formatted = [sql_format_value(v) for v in db_values]
                file_sql = f"INSERT OR REPLACE INTO mac_bans (id, name, bandate, reason, serverid, servername, bannedby) VALUES ({', '.join(file_values_formatted)});\n"
                f.write(file_sql)

    conn.commit()
    conn.close()
    print("Migration to SQL file successful. You can find the SQL commands in mac_bans.sql")


if __name__ == "__main__":
    migrate_json_to_sql()

