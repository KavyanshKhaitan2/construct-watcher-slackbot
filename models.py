import peewee

db = peewee.SqliteDatabase('db.sqlite3')

class UserConfigs(peewee.Model):
    user_id = peewee.IntegerField(unique=True)
    goal = peewee.IntegerField(default=42)
    
    class Meta:
        database = db

class Devlogs(peewee.Model):
    user_id = peewee.IntegerField()
    user_name = peewee.CharField(max_length=200)

    project_id = peewee.IntegerField()
    project_name = peewee.CharField(max_length=200)
    
    devlog_id = peewee.IntegerField(unique=True)
    devlog_description = peewee.TextField()
    devlog_image = peewee.CharField()
    devlog_time_spent = peewee.IntegerField()
    devlog_created = peewee.CharField(max_length=200)

    class Meta:
        database = db

db.connect()
db.create_tables([UserConfigs, Devlogs])