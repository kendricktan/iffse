from peewee import (
    CharField,
    TextField,
    SqliteDatabase,
    OperationalError,
    ForeignKeyField,
    Model
)

db = SqliteDatabase('selfiers.db')


class SelfiePost(Model):
    # Instagram shortcode
    # e.g. instagram.com/p/SHORTCODE
    shortcode = CharField(unique=True)
    img_url = TextField()

    class Meta:
        database = db


class FacialEmbeddings(Model):
    # Original Post
    op = ForeignKeyField(SelfiePost, related_name='op')
    latent_space = CharField()

    class Meta:
        database = db


if __name__ == '__main__':
    db.connect()

    try:
        db.create_tables([SelfiePost])
    except OperationalError:
        pass
