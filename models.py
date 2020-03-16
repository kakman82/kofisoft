from app import db, app
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


class User(db.Model):

    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50))
    role = db.Column(db.String(20), )
    is_admin = db.Column(db.Boolean)
    user_email = db.Column(db.String(50))
    user_phone = db.Column(db.String(20))
    password = db.Column(db.String(200))
    created_date = db.Column(db.DateTime)
    created_user = db.Column(db.String(50))
    updated_date = db.Column(db.DateTime)
    updated_user = db.Column(db.String(50))

    company_id = db.Column(db.Integer, db.ForeignKey('company.company_id'), nullable=False)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.user_id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __str__(self):
        return self.user_name

    @staticmethod
    def doctor_query():
        return User.query.all()


class Company(db.Model):
    company_id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String())
    member_start = db.Column(db.DateTime)
    member_end = db.Column(db.DateTime)

    user_id = db.relationship('User', backref='company', lazy=True)


class Patient(db.Model):
    patient_id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100))
    patient_tckn = db.Column(db.String(20))
    patient_phone = db.Column(db.String(20))
    patient_email = db.Column(db.String(100))
    birthday = db.Column(db.String(30))
    gender = db.Column(db.String(10))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    address = db.Column(db.String(200))
    company_id = db.Column(db.Integer)
    notes = db.Column(db.String)
    created_date = db.Column(db.DateTime)
    created_user = db.Column(db.String())
    updated_date = db.Column(db.DateTime)
    updated_user = db.Column(db.String(50))

    def __str__(self):
        return self.patient_name


class Appointment(db.Model):
    appointment_id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer)
    patient_id = db.Column(db.Integer)
    doctor_id = db.Column(db.Integer)
    type = db.Column(db.String(50))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)
    date_created = db.Column(db.DateTime)
    user_created = db.Column(db.String())
    date_updated = db.Column(db.DateTime)
    user_updated = db.Column(db.String(50))


class Examination(db.Model):
    examination_id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer)
    patient_id = db.Column(db.Integer)
    company_id = db.Column(db.Integer)
    content = db.Column(db.Text)
    date_created = db.Column(db.DateTime)
    user_created = db.Column(db.String())


class File(db.Model):
    file_id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer)
    patient_id = db.Column(db.Integer)
    company_id = db.Column(db.Integer)
    file_url = db.Column(db.String())
    file_name = db.Column(db.String())
    server_file_name = db.Column(db.String())
    date_uploaded = db.Column(db.DateTime)
    user_uploaded = db.Column(db.String())
