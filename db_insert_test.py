import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

dsn = os.getenv("DATABASE_URL")
print("🌐 Verbindung zu:", dsn)

with psycopg2.connect(dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO public.termine (telefonnummer, nachricht, intent)
            VALUES (%s, %s, %s) RETURNING id;
        """, ("01700000000", "Testeintrag aus Python", "termin_buchen"))
        new_id = cur.fetchone()[0]
        print("✅ Neuer Eintrag mit ID:", new_id)