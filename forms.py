from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, \
    IntegerField, TextAreaField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import *


class NameForm(FlaskForm):
    name = StringField("Name:")
    date = StringField("Date:")
    phone = IntegerField("Phone Number:")
    remember_me = BooleanField("Satış Sözleşmesi", default=False, validators=[
        DataRequired(message="Lütfen onaylayın")])
    submit = SubmitField("Save")


class RegisterForm(FlaskForm):

    company_name = StringField("Firma İsmi", validators=[
        DataRequired(message="Lütfen firma adını giriniz."),
        Length(min=2, max=100,
               message="Girilen değer 2 ile 100 karakter arasında olmalıdır.")
    ])
    name = StringField("İsim ve Soyisim", validators=[
        DataRequired(message="Lütfen adınızı ve soyadınızı giriniz."),
        Length(min=2, max=100,
               message="Girilen değer 2 ile 50 karakter arasında olmalıdır.")
    ])
    role = SelectField("Göreviniz(*)", choices=[("", "Seçiniz"), ("Doktor", "Doktor"),
                                          ("Hasta Kabul", "Hasta Kabul")],
                       render_kw={"placeholder": "Göreviniz"},
                        coerce=str,
        validators=[DataRequired(message="Lütfen bir seçim yapınız.")])

    email = StringField("Email Adresi", validators=[
        DataRequired(message="Lütfen email adresinizi giriniz."),
        Email(message="Lütfen geçerli bir email adresi giriniz.")
    ])
    mobile_phone = StringField("Telefon Numarası",
                       validators=[
        DataRequired(message="Lütfen cep telefon numaranızı giriniz.")])

    password = PasswordField("Şifre", validators=[
        DataRequired(message="Lütfen bir şifre belirleyiniz."),
        Length(min=3, max=80,
               message="Girilen değer en az 3 karakter içermelidir.")
    ])
    confirm = PasswordField("Şifre (Tekrar)", validators=[
        DataRequired(message="Lütfen belirlediğiniz şifreyi tekrar giriniz."),
        EqualTo("password", message="Girilen şifre ile uyuşmamaktadır...")
    ])
    sales_doc = BooleanField("Satış Sözleşmesi", default=False, validators=[
        DataRequired(message="Lütfen satış sözleşmesini okuyup onay için işaretleyiniz.")
    ])
    recaptcha = RecaptchaField()


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Parola', validators=[DataRequired()])
    recaptcha = RecaptchaField(
        validators=[DataRequired(message="Lütfen kutucuğu işaretleyiniz.")
    ])


class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(
        message="Lütfen kayıtlı email adresiniz giriniz."
    )])

    def validate_email(self, email):
        user = User.query.filter(User.user_email == email.data).first()
        if user is None:
            raise ValidationError('Bu email adresine ait kayıtlı kullanıcı bulunmamaktadır. Lütfen önce kayıt olunuz.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Şifre", validators=[
        DataRequired(message="Lütfen yeni bir şifre belirleyiniz."),
        Length(min=3, max=80,
               message="Girilen değer en az 3 karakter içermelidir.")
    ])
    confirm = PasswordField("Şifre (Tekrar)", validators=[
        DataRequired(message="Lütfen yeni belirlediğiniz şifreyi tekrar giriniz."),
        EqualTo("password", message="Girilen şifre ile uyuşmamaktadır...")
    ])


class UserForm(FlaskForm):

    name = StringField("İsim ve Soyisim", validators=[
        DataRequired(message="Lütfen isim ve soyisim bilgisi giriniz."),
        Length(min=2, max=100,
               message="Girilen değer 2 ile 50 karakter arasında olmalıdır.")
    ])

    role = SelectField("Göreviniz(*)", choices=[("", ""), ("Doktor", "Doktor"),
                                          ("Hasta Kabul", "Hasta Kabul")], coerce=str,
        validators=[DataRequired(message=
                                 "Lütfen bir seçim yapınız.")])

    email = StringField("Email Adresi", validators=[
        DataRequired(message="Lütfen email adres bilgisi giriniz."),
        Email(message="Lütfen geçerli bir email adresi giriniz.")
    ])
    mobile_phone = StringField("Telefon Numarası",
                       validators=[
        DataRequired(message="Lütfen cep telefon numara bilgisini giriniz.")])


class PatientForm(FlaskForm):

    tckn = StringField(validators=[
        Length(min=11, max=11, message="En az 11 karakter içermelidir.")])

    name = StringField(validators=[
        DataRequired(message="Lütfen hastanın isim ve soyismini giriniz."),
        Length(min=3, max=50, message="En az 3 karakter içermelidir.")
    ])
    mobile_phone = StringField(validators=[
        DataRequired(message="Lütfen hastanın cep telefon numarasını giriniz.")])
    email = StringField()
    birthday = StringField(validators=[
        DataRequired(message="Lütfen hastanın doğum tarihi bilgisini giriniz.")
    ])
    gender = SelectField(choices=[("", ""), ("Erkek"," Erkek"), ("Kadın", "Kadın")], coerce=str,
                         validators=[DataRequired(message="Lütfen bir seçim yapınız.")])
    city = StringField()
    state = StringField()
    address = StringField()
    notes = TextAreaField()


class AppointmentForm(FlaskForm):
    doctor = QuerySelectField(query_factory=doctor_query, allow_blank=True, get_label='user_name',
                              validators=[DataRequired(message="Lütfen doktor seçimi yapınız.")])

    patient = StringField()

    type = SelectField(choices=[("", ""), ("Muayene", "Muayene"), ("Kontrol", "Kontrol")], coerce=str,
                                validators=[DataRequired(message="Lütfen bir seçim yapınız.")])

    appointment_date = StringField(
                        validators=[DataRequired(message="Lütfen randevu tarih ve saat bilgisini giriniz.")])

    duration = SelectField(choices=[(0, ""), (15, "15 dk."), (30, "30 dk."), (45, "45 dk."), (60, "1 saat"),
                                    (90, "1.5 saat"), (120, "2 saat"), (150, "2.5 saat"), (180, "3 saat")],
                                    coerce=int,
                           validators=[DataRequired(message="Lütfen randevu süresini seçiniz.")])


class ExaminationForm(FlaskForm):
    title = StringField()
    content = TextAreaField()
    save = SubmitField()


class FileForm(FlaskForm):
    file_name = StringField(validators=[DataRequired(message="Yüklemek istediğiniz dosyaya bir isim veriniz.")])
    upload = SubmitField()
