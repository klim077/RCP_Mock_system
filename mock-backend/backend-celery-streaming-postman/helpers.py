from config import *


def getMachineType(machine_uuid):
    query = f"SELECT type FROM machines \
        WHERE uuid='{machine_uuid}'"
    with PDB(postgres_user, postgres_password, postgres_db, postgres_ip) as conn:
        c = conn.cursor()
        c.execute(query)
        row = c.fetchall()[0]

    return row[0]