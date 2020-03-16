from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_uploads import UploadSet, configure_uploads, patch_request_class, TEXT, IMAGES, DOCUMENTS
from flask_mail import Mail

app = Flask(__name__, static_folder='assets')
app.config['SECRET_KEY'] = b"\xb8Qh\xe1YtzA\x07\x9b\xa7_\x8e'\xbdy\xc1\x87\x1eJ\xbc\xcf^\x9e"

ENV = 'prod'

if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/patient_tracking'
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patient_tracking.db'
else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://ptdrtllqnjqsqc:78021fe1355d3d23d2e77f4723437b80a92008bb4f42c1569509fcec9a648290@ec2-54-195-247-108.eu-west-1.compute.amazonaws.com:5432/d4jthnc8l53kh'
    
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

migrate = Migrate(app, db)

#app.config.from_pyfile("config.cfg")

app.config['RECAPTCHA_USE_SSL']= False
app.config['RECAPTCHA_PUBLIC_KEY'] = "6LeihtwUAAAAAFiR3MtQ7wiMQrmXYq9o9oo6VwgT"
app.config['RECAPTCHA_PRIVATE_KEY'] = "6LeihtwUAAAAAMQRwK1K3FUdAYeoRbLxNIMSV9F9"


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'kofisoftteam@gmail.com'
app.config['MAIL_PASSWORD'] = 'kofisoft2019'

mail = Mail(app)

app.config['UPLOADED_FILES_DEST'] = 'files'
app.config['UPLOADED_FILES_ALLOW'] = ['pdf']
#app.config['UPLOADED_FILES_DENY'] = ['txt']

files = UploadSet('files', DOCUMENTS + ('pdf',) + TEXT + IMAGES)
configure_uploads(app, files)
patch_request_class(app, 32 * 1024 * 1024) #max 32 mb dosya boyutu, deger vermez isek default 16 mb


from views import *

if __name__ == "__main__":
    app.run()
