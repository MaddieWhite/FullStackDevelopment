## TODO: Something simular to the previous lambda function that returns a dictionary baesd on

#sailor_retrieve retrieves from the database and prints, need to write this for json and lambda though
def sailor_retrieve(uuid):
    with conn.cursor() as cur:
        cur.execute("""SELECT * FROM sailors WHERE sailor_uuid=%s""", uuid)
        conn.commit()
        print(cur.fetchone())
        cur.execute("""SELECT * FROM regattas WHERE sailor_uuid=%s""", uuid)
        conn.commit()
        print(cur.fetchall())
