from peewee import (
    CharField,
    TextField,
    SqliteDatabase,
    OperationalError,
    Model
)

db = SqliteDatabase('selfiers.db')


class SelfiePost(Model):
    # Instagram shortcode
    # e.g. instagram.com/p/SHORTCODE
    shortcode = CharField(unique=True)
    img_url = TextField()

    # 128 embedding
    latent_space = TextField()

    class Meta:
        database = db


if __name__ == '__main__':
    db.connect()

    try:
        db.create_tables([SelfiePost])
    except OperationalError:
        pass
