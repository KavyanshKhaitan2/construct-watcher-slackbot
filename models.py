import peewee

db = peewee.SqliteDatabase('db.sqlite3')

class UserConfigs(peewee.Model):
    user_id = peewee.IntegerField(unique=True)
    goal = peewee.IntegerField(default=42)
    
    class Meta:
        database = db

db.connect()
db.create_tables([UserConfigs])