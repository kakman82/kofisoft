from app import app, db, files, mail
from flask import render_template, redirect, url_for, request, session, flash
from forms import RegisterForm, LoginForm, PatientForm, AppointmentForm, \
        UserForm, ExaminationForm, FileForm, RequestResetForm, ResetPasswordForm
from models import User, Company, Patient, Appointment, Examination, File
from werkzeug.security import generate_password_hash, check_password_hash
from flask_uploads import UploadNotAllowed
from sqlalchemy.sql.expression import extract
from datetime import datetime, timedelta
import os, locale
from flask_mail import Message


@app.route("/")
def home():
    return render_template("home.html")


def get_current_user():
    user_result = None

    if 'user' in session:
        user = session['user']
        user_result = User.query.filter_by(user_name=user).first()

    return user_result


@app.route("/register", methods=['GET', 'POST'])
def register():

    form = RegisterForm()

    if form.validate_on_submit():

        new_company = Company(company_name=form.company_name.data,
                              member_start=datetime.now(),
                              member_end=datetime.now() + timedelta(days=3),)

        db.session.add(new_company)

        new_registered_user = User(user_name=form.name.data,
                                   role=form.role.data,
                                   is_admin=True,
                                   user_email=form.email.data,
                                   user_phone=form.mobile_phone.data,
                                   password=generate_password_hash(form.password.data),
                                   created_date=datetime.now(),
                                   created_user=form.name.data,
                                   company=new_company)

        db.session.add(new_registered_user)
        db.session.commit()

        return redirect(url_for('login'))

    else:
        print(form.errors)

    return render_template("register.html", form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():

    form = LoginForm()
    failed_login_attempt = 0

    if request.method == 'POST':

        user_result = User.query.filter_by(user_email=form.email.data).first()

        if user_result and check_password_hash(user_result.password, form.password.data):

            session['user'] = user_result.user_name
            session['company'] = user_result.company_id
            session['user_id'] = user_result.user_id
            session['role'] = user_result.role
            flash("Uygulamaya Hoşgeldiniz", category="success")

            return redirect(url_for("dashboard"))

        else:
            failed_login_attempt += 1
            flash("Email adresi ya da şifre hatalı!", category="danger")
            print(failed_login_attempt)

    return render_template("login.html", form=form, failed_login_attempt=failed_login_attempt)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message(
        'Şifre Sıfırlama',
        sender='kofisoftteam@gmail.com',
        recipients=[user.user_email]
    )

    msg.html = f""" 
            <p>Merhaba <strong>{user.user_name}</strong>,</p>

            <p>Şifrenizi sıfırlamak için aşağıdaki linke tıklayınız:</p>
            <p>
            {url_for('reset_token', token=token, _external=True)}
            </p>
            
            <p>Eğer şifre sıfırlama ile ilgili bir talebiniz bulunmuyor ise bu mesajı dikkate almayınız.</p>

            <p>Bilgilerinize sunar,</p>
            <p>İyi günler dileriz.</p>
            <p>KofiSoft Team</p>
    """
    mail.send(msg)

@app.route("/reset_request", methods=['GET', 'POST'])
def reset_request():
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(user_email=form.email.data).first()
        send_reset_email(user)
        flash("Şifre sıfırlama adımları email adresinize gönderilmiştir.\n Lütfen email kutunuzu kontrol ediniz.",
               "primary")
        return redirect(url_for("reset_request"))
    return render_template('reset_request.html', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    user = User.verify_reset_token(token)
    if user is None:
        flash("Geçersiz ya da süresi geçmiş şifre sıfırlama istediği", "danger")
        return redirect(url_for("reset_request"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user.password = hashed_password
        db.session.commit()
        flash("Şifreniz başarıyla değiştirilmiştir! \n Yeni şifreniz ile giriş yapabilirsiniz", "success")
        return redirect(url_for("login"))
    return render_template('reset_token.html', form=form)


@app.route('/payment', methods=['GET', 'POST'])
def payment():
    form = RegisterForm()
    return render_template("register_for_payment.html", form=form)


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))


@app.route("/patient/add_patient", methods=['GET', 'POST'])
def add_patient():

    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    form = PatientForm()

    if request.method == 'POST' and form.validate_on_submit():

        locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
        dogtar = form.birthday.data
        str_dogtar = datetime.strptime(dogtar, '%d %B %Y')
        db_dogtar = datetime.strftime(str_dogtar, '%Y-%m-%d')

        new_patient = Patient(patient_name=form.name.data,
                              patient_tckn=form.tckn.data,
                              patient_phone=form.mobile_phone.data,
                              patient_email=form.email.data,
                              birthday=db_dogtar,
                              gender=form.gender.data,
                              city=form.city.data,
                              state=form.state.data,
                              address=form.address.data,
                              notes=form.notes.data,
                              created_date=datetime.now(),
                              created_user=session['user'],
                              company_id=session['company'])

        db.session.add(new_patient)
        db.session.commit()

        flash("Hasta kaydı başarıyla oluşturulmuştur.", category="success")
        return redirect(url_for("patient_list"))

    else:
        print(form.errors)

    return render_template("add_patient.html", form=form, days_left=remaining_day)


@app.route("/patient/patient_list")
def patient_list():
    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    form = PatientForm()

    patients = Patient.query.filter_by(company_id=session['company']).\
        order_by(Patient.patient_id.desc()).all()

    def patient_age(str_date):
        age_list = {}
        
        for i in range(0, len(patients)):
            str_date = datetime.strptime(patients[i].birthday, '%Y-%m-%d')
            year_str_date = datetime.strftime(str_date, '%Y')
            int_date = int(year_str_date)
            age = datetime.now().year - int_date
            age_list.update({i: age})
        return age_list
    
    def birthday_pretty_date(str_birthday):
        birthday_list = {}
        for i in range(0, len(patients)):
            str_birthday = datetime.strptime(patients[i].birthday, '%Y-%m-%d')
            pretty_date = datetime.strftime(str_birthday, '%d %B %Y')
            birthday_list.update({i: pretty_date})
        return birthday_list

    patient_zip = zip(patients, range(0, len(patients)))

    return render_template("patient_list.html", patients=patients, 
                            days_left=remaining_day, age=patient_age,
                            pretty_date=birthday_pretty_date,
                           len=len(patients), patient_zip=patient_zip, 
                           form=form
                           )


@app.route("/patient/update_patient/<int:id>", methods=['GET', 'POST'])
def update_patient(id):

    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    if request.method == 'GET':

        form = PatientForm()

        patient = db.session.query(Patient).filter(Patient.patient_id == id).first()

        str_dogtar = datetime.strptime(patient.birthday, '%Y-%m-%d')
        view_dogtar = datetime.strftime(str_dogtar, '%d %B %Y')

        form.name.data = patient.patient_name
        form.tckn.data = patient.patient_tckn
        form.mobile_phone.data = patient.patient_phone
        form.email.data = patient.patient_email
        form.birthday.data = view_dogtar
        form.gender.data = patient.gender
        form.city.data = patient.city
        form.state.data = patient.state
        form.address.data = patient.address
        form.notes.data = patient.notes

        return render_template("update_patient.html", form=form, patient=patient, days_left=remaining_day)

    form = PatientForm()

    if request.method == 'POST' and form.validate_on_submit():
        #POST request ise --> update için form
        patient = Patient.query.filter_by(patient_id=id).first()

        locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
        dogtar = form.birthday.data
        str_dogtar = datetime.strptime(dogtar, '%d %B %Y')
        db_dogtar = datetime.strftime(str_dogtar, '%Y-%m-%d')

        patient.patient_tckn = form.tckn.data
        patient.gender = form.gender.data
        patient.patient_name = form.name.data
        patient.patient_phone = form.mobile_phone.data
        patient.birthday = db_dogtar
        patient.patient_email = form.email.data
        patient.city = form.city.data
        patient.state = form.state.data
        patient.address = form.address.data
        patient.notes = form.notes.data
        patient.updated_date = datetime.now()
        patient.updated_user = session['user']

        db.session.commit()

        flash("Hasta kaydı başarıyla güncellenmiştir.", category="success")

        return redirect(url_for("patient_list", form=form))

    return render_template("update_patient.html", days_left=remaining_day)


@app.route("/patient/delete/<int:id>", methods=['POST'])
def delete_patient(id):
    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    patient_to_delete = Patient.query.filter(Patient.patient_id == id).first()
    db.session.delete(patient_to_delete)
    db.session.commit()
    flash("Hasta kaydı başarıyla silinmiştir.", category="success")
    return redirect(url_for('patient_list'))


def remaining_day():
    company_result = Company.query.filter_by(company_id=session['company']).first()
    total_day = company_result.member_end - datetime.now()
    days_left = total_day.days
    return days_left


def base_template():
    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    # HTML template da bir fonsiyon çağırmak için önce fonksiyona bir isim/tanım verilip template da çağırılır.
    return render_template("base.html", days_left=remaining_day)


@app.route("/dashboard")
def dashboard():
    user = get_current_user()

    if not user:
        return redirect(url_for("home"))
    # HTML template da bir fonsiyon çağırmak için önce fonksiyona bir isim/tanım verilip template da çağırılır.
    return render_template("dashboard.html", days_left=remaining_day)


@app.route("/appointment/add_appointment/<int:pat_id>", methods=['GET', 'POST'])
def add_appointment(pat_id):

    user = get_current_user()

    if not user:
        return redirect(url_for('home'))

    form = AppointmentForm()

    form.patient.data = Patient.query.filter(Patient.patient_id == pat_id).first().patient_name

    form.doctor.query = User.query.filter_by(company_id=session['company'], role="Doktor").order_by(User.user_name).all()

    if request.method == 'POST'and form.validate_on_submit():

        locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
        date = form.appointment_date.data
        duration = form.duration.data

        str_date = datetime.strptime(date, '%d %B %Y %A - %H:%M')
        db_start_date = datetime.strftime(str_date, '%Y-%m-%d %H:%M')
        end_date = str_date + timedelta(minutes=duration)
        db_end_date = datetime.strftime(end_date, '%Y-%m-%d %H:%M')

        pat_id = Patient.query.filter_by(patient_name=str(form.patient.data)).first().patient_id
        doc_id = User.query.filter_by(user_name=str(form.doctor.data)).first().user_id

        check_start_date = db.session.query(Appointment).filter(
                    str_date >= Appointment.start_time,
                    str_date < Appointment.end_time,
                    Appointment.doctor_id == doc_id).first()

        check_end_date = db.session.query(Appointment).filter(
                    end_date > Appointment.start_time,
                    end_date <= Appointment.end_time,
                    Appointment.doctor_id == doc_id).first()

        if check_start_date or check_end_date:

            doctor_name = form.doctor.data

            flash("Başka bir hastası için randevusu bulunmaktadır. "
                  "Lütfen farklı bir zaman seçimi yapınız.", category="danger")

            return render_template("add_appointment.html", form=form, doctor_name=doctor_name, days_left=remaining_day)

        #Tarih de hata alınmadığında DB'ye kayıt;
        else:
            new_appointment = Appointment(
                company_id=session['company'],
                patient_id=pat_id,
                doctor_id=doc_id,
                start_time=db_start_date,
                end_time=db_end_date,
                duration=duration,
                type=form.type.data,
                date_created=datetime.now(),
                user_created=session['user']
            )
            db.session.add(new_appointment)
            db.session.commit()

            # Her randevu kaydı oluşturulduğunda boş bir muayene kaydı oluşturalım dedik.
            # Muayene kaydını daha sonra her kaydet butonuna basıldığında update etmek için

            new_examination = Examination(
                company_id=session['company'],
                patient_id=pat_id,
                appointment_id = new_appointment.appointment_id
            )
            db.session.add(new_examination)
            db.session.commit()

            flash("Randevu kaydı oluşturulmuştur.", category="success")

            return redirect(url_for("appointment_list"))

    return render_template("add_appointment.html", form=form, days_left=remaining_day)


@app.route("/appointment/appointment_list", methods=['GET', 'POST'])
def appointment_list():
    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
    month_id=datetime.today().month
    day_id = datetime.today().day
    now = datetime.now()

    appointments = db.session.query(User.user_name, Patient.patient_name,Patient.patient_phone,
                                    Appointment.appointment_id, Appointment.type, Appointment.start_time,
                                    Appointment.end_time,
                                    Appointment.duration).filter(Appointment.company_id == session['company']).\
                                    join(User, Appointment.doctor_id == User.user_id).\
                                    join(Patient, Appointment.patient_id == Patient.patient_id).\
                                    order_by(Appointment.start_time.desc()).all()

    return render_template("appointment_list.html", len=len(appointments), appointments=appointments,
                           days_left=remaining_day, month_id=month_id, day_id=day_id, now=now)


@app.route("/appointment/appointment_list/this_month", methods=['GET', 'POST'])
def appointment_list_by_month():

    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    month_id = datetime.today().month
    year_id = datetime.today().year
    now = datetime.now()

    appointments = db.session.query(User.user_name, Patient.patient_name,Patient.patient_phone,
                                    Appointment.appointment_id, Appointment.type, Appointment.start_time,
                                    Appointment.end_time,
                                    Appointment.duration).filter(Appointment.company_id == session['company'],
                                                                extract('month', Appointment.start_time) == month_id,
                                                                 extract('year', Appointment.start_time) == year_id).\
                                    join(User, Appointment.doctor_id == User.user_id).\
                                    join(Patient, Appointment.patient_id == Patient.patient_id).\
                                    order_by(Appointment.start_time.desc()).all()

    return render_template("appointment_list.html", len=len(appointments), appointments=appointments,
                           days_left=remaining_day, month_id=month_id, now=now)


@app.route("/appointment/appointment_list/today", methods=['GET', 'POST'])
def appointment_list_by_today():

    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    today = datetime.today()
    day_id = today.day
    month_id = today.month
    year_id = today.year
    now = datetime.now()

    appointments = db.session.query(User.user_name, Patient.patient_name,Patient.patient_phone,
                                    Appointment.appointment_id, Appointment.type, Appointment.start_time,
                                    Appointment.end_time, Appointment.duration).\
                                    filter(Appointment.company_id == session['company'],
                                           extract('day', Appointment.start_time) == day_id,
                                           extract('month', Appointment.start_time) == month_id,
                                           extract('year', Appointment.start_time) == year_id).\
                                    join(User, Appointment.doctor_id == User.user_id).\
                                    join(Patient, Appointment.patient_id == Patient.patient_id).\
                                    order_by(Appointment.start_time.desc()).all()

    return render_template("appointment_list.html", len=len(appointments), appointments=appointments,
                           days_left=remaining_day, month_id=month_id, now=now)


@app.route("/appointment/appointment_list/this_week", methods=['GET', 'POST'])
def appointment_list_by_week():

    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    current_week_number = datetime.today().isocalendar()[1]
    month_id = datetime.today().month
    now = datetime.now()

    appointments = db.session.query(User.user_name, Patient.patient_name, Patient.patient_phone,
                                    Appointment.appointment_id, Appointment.type, Appointment.start_time,
                                    Appointment.end_time, Appointment.duration).\
                                    filter(Appointment.company_id == session['company'],
                                           extract('week', Appointment.start_time) == current_week_number).\
                                    join(User, Appointment.doctor_id == User.user_id).\
                                    join(Patient, Appointment.patient_id == Patient.patient_id).\
                                    order_by(Appointment.start_time.desc()).all()

    return render_template("appointment_list.html", len=len(appointments), appointments=appointments,
                           days_left=remaining_day, month_id=month_id, now=now)


@app.route("/appointment/delete/<int:id>", methods=['POST'])
def delete_appointment(id):

    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    appointment_to_delete = Appointment.query.filter(Appointment.appointment_id == id).first()
    db.session.delete(appointment_to_delete)
    db.session.commit()
    flash("Randevu iptal edilmiştir/silinmiştir.", "success")
    return redirect(url_for('appointment_list'))


@app.route("/appointment/update/<int:id>", methods=['GET', 'POST'])
def update_appointment(id):

    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    form = AppointmentForm()

    form.patient.query = Patient.query.filter_by(company_id=session['company']).order_by(Patient.patient_name).all()

    form.doctor.query = User.query.filter_by(company_id=session['company'], role="Doktor").order_by(
                                User.user_name).all()

    current_appointment = Appointment.query.filter(Appointment.appointment_id == id,
                                                   Appointment.company_id == session['company']).first()

    if request.method == 'GET':

        current_patient_name = Patient.query.filter(Patient.patient_id == current_appointment.patient_id).first()
        current_doctor_name = User.query.filter(User.user_id == current_appointment.doctor_id).first()

        form.doctor.data = current_doctor_name
        form.patient.data = current_patient_name
        form.type.data = current_appointment.type

        locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
        pretty_date = datetime.strftime(current_appointment.start_time, "%d %B %Y %A - %H:%M")
        form.appointment_date.data = pretty_date
        form.duration.data = current_appointment.duration

        return render_template("update_appointment.html", form=form, current_appointment=current_appointment,
                               days_left=remaining_day)

    if request.method == 'POST' and form.validate_on_submit():

        locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
        date = form.appointment_date.data
        duration = form.duration.data

        str_date = datetime.strptime(date, '%d %B %Y %A - %H:%M')
        db_start_date = datetime.strftime(str_date, '%Y-%m-%d %H:%M')
        end_date = str_date + timedelta(minutes=duration)
        db_end_date = datetime.strftime(end_date, '%Y-%m-%d %H:%M')

        pat_id = Patient.query.filter_by(patient_name=str(form.patient.data)).first().patient_id
        doc_id = User.query.filter_by(user_name=str(form.doctor.data)).first().user_id

        check_start_date = db.session.query(Appointment).filter(
            str_date >= Appointment.start_time,
            str_date < Appointment.end_time,
            Appointment.doctor_id == doc_id).first()

        check_end_date = db.session.query(Appointment).filter(
            end_date > Appointment.start_time,
            end_date <= Appointment.end_time,
            Appointment.doctor_id == doc_id).first()

        if check_start_date or check_end_date:

            doctor_name = form.doctor.data

            flash("Başka bir hastası için randevusu bulunmaktadır. "
                  "Lütfen farklı bir zaman seçimi yapınız.", category="danger")

            return render_template("add_appointment.html", form=form, doctor_name=doctor_name, days_left=remaining_day)

        else:
            current_appointment.patient_id=pat_id,
            current_appointment.doctor_id=doc_id,
            current_appointment.start_time=db_start_date,
            current_appointment.end_time=db_end_date,
            current_appointment.duration=duration,
            current_appointment.type=form.type.data,
            current_appointment.date_updated=datetime.now(),
            current_appointment.user_updated=session['user']

            db.session.commit()

            flash("Randevu kaydı güncellenmiştir.", category="success")

            return redirect(url_for("appointment_list"))

    else:
        print(form.errors)

    return render_template("update_appointment.html", form=form, current_appointment=current_appointment,
                               days_left=remaining_day)


@app.route("/examination/add_examination/<int:app_id>", methods=['GET', 'POST'])
def add_examination(app_id):

    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    app_for_title = db.session.query(Appointment).filter(Appointment.appointment_id == app_id).first()

    patient = db.session.query(Patient).filter(Appointment.patient_id == Patient.patient_id).\
                                        filter(Appointment.appointment_id == app_id).first()

    def patient_age_info(str_date):

        locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
        str_date = datetime.strptime(patient.birthday, '%Y-%m-%d')
        year_str_date = datetime.strftime(str_date, '%Y')
        int_date = int(year_str_date)
        age = datetime.now().year - int_date
        return age

    locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
    str_birthday = datetime.strptime(patient.birthday, '%Y-%m-%d')
    pretty_date = datetime.strftime(str_birthday, '%d %B %Y')
            
    appointments = db.session.query(Appointment.start_time, Appointment.end_time, Appointment.type, User.user_name,
                                    Examination.content, Examination.examination_id ).\
                            filter(Appointment.company_id == session['company']).\
                            filter(Appointment.doctor_id == User.user_id).\
                            filter(Appointment.patient_id == patient.patient_id).\
                            filter(Examination.appointment_id == Appointment.appointment_id).\
                            order_by(Appointment.start_time).all()

    ex_form = ExaminationForm(prefix='ex_form')
    file_form = FileForm(prefix='file_form')

    current_examination = Examination.query.filter(Examination.appointment_id == app_id).first()

    if request.method == 'GET':
        ex_form.content.data = current_examination.content

    if request.method == 'POST' and ex_form.validate_on_submit():

        current_examination.appointment_id = app_id
        current_examination.content = ex_form.content.data
        current_examination.date_created = datetime.now()
        current_examination.user_created = session['user']
        db.session.commit()

        #Her kaydet e basıldığında mesaj göstermek gereksiz oluyor ve satırı aşağıya çekiyor
        #flash(message="Muayene kaydı başarıyla oluşturuldu.", category='success')
        return redirect(url_for('add_examination', app_id=app_id))

    if request.method == 'POST' and 'thefile' in request.files and file_form.validate_on_submit():

        try:
            doc_filename = files.save(request.files['thefile'])
            new_file = File(
                appointment_id=app_id,
                patient_id=patient.patient_id,
                company_id=session['company'],
                file_url=files.url(doc_filename),
                file_name=file_form.file_name.data,
                server_file_name=doc_filename,
                date_uploaded=datetime.now(),
                user_uploaded=session['user']
            )

            db.session.add(new_file)
            db.session.commit()
            print(doc_filename)

            ex_form.content.data = current_examination.content

            flash("Dosya başarıyla yüklendi.", category='success')

            return redirect(url_for('add_examination', app_id=app_id))

        except UploadNotAllowed:
            flash("Herhangi bir dosya yüklemediniz ya da yüklenen dosyanın türü uygun değil",
                  category='danger')
            ex_form.content.data = current_examination.content
        return redirect(url_for('add_examination', app_id=app_id))

    else:
        ex_form.content.data = current_examination.content

    patient_files = File.query.filter(File.patient_id == patient.patient_id).all()

    return render_template("add_examination.html", patient=patient,
                           days_left=remaining_day, appointments=appointments,
                           len=len(appointments), app_for_title=app_for_title,
                           age=patient_age_info, current_examination=current_examination,
                           pretty_date=pretty_date, ex_form=ex_form, file_form=file_form,
                           patient_files=patient_files, len_patient_files=len(patient_files))


@app.route("/examination/delete_file/<int:file_id>", methods=['GET', 'POST'])
def delete_file(file_id):

    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    app_id = File.query.filter(File.file_id == file_id).first().appointment_id

    if request.method == 'POST':
        file_to_delete = File.query.filter(File.file_id == file_id).first()
        os.remove(os.path.join(app.config['UPLOADED_FILES_DEST'], file_to_delete.server_file_name))
        db.session.delete(file_to_delete)
        db.session.commit()
        flash("Doküman silinmiştir", category='success')
        return redirect(url_for('add_examination', app_id=app_id))

    return render_template(url_for("add_examination", app_id=app_id))


@app.route("/examination/examination_list")
def examination_list():

    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    examinations = db.session.query(Appointment.start_time, Appointment.type, User.user_name,
                                    Patient.patient_name, Examination.content, File.file_name,
                                    File.file_url, Appointment.appointment_id). \
                                    filter(Appointment.company_id == session['company']). \
                                    filter(Appointment.doctor_id == User.user_id). \
                                    filter(Appointment.patient_id == Patient.patient_id). \
                                    outerjoin(Examination, Examination.appointment_id == Appointment.appointment_id). \
                                    outerjoin(File, File.appointment_id == Appointment.appointment_id). \
                                    order_by(Appointment.start_time).all()

    return render_template("examination_list.html", days_left=remaining_day,
                           examinations=examinations, len=len(examinations))


@app.route("/add_user", methods=['GET', 'POST'])
def add_user():

    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    form = UserForm()

    if request.method == 'POST' and form.validate_on_submit():

        name = form.name.data
        role = form.role.data
        is_admin = True
        email = form.email.data
        phone = form.mobile_phone.data
        password = "1234"
        created_date = datetime.now()
        session_user = session['user']
        session_company_id = session['company']

        new_user = User(user_name=name, role=role, is_admin=is_admin, user_email=email,
                        user_phone=phone,
                        password=generate_password_hash(password),
                        created_date=created_date,
                        created_user=session_user,
                        company_id=session_company_id)

        db.session.add(new_user)
        db.session.commit()

        new_user_token = new_user.get_reset_token()

        msg = Message(
            'Yeni Şifre Belirleme',
            sender='kofisoftteam@gmail.com',
            recipients=[new_user.user_email]
        )
        msg.html = f""" 
        <p>Merhaba <strong>{new_user.user_name}</strong>,</p>
        
        <p>Uygulamaya hoşgeldiniz.</p> 
        <p>Şifrenizi belirlemek için aşağıdaki linke tıklayınız.</p>
        <p>Email adresiniz ve belirleyeceğiniz şifre ile birlikte uygulamaya giriş yapabilirsiniz.</p>
        <br>
        <p>
        {url_for('reset_token', token=new_user_token, _external=True)}
        </p>

        <p>Bilgilerinize sunar,</p>
        <p>İyi günler dileriz.</p>
        <p>KofiSoft Team</p>
        """
        mail.send(msg)

        flash("Kullanıcı başarıyla oluşturuldu. Şifresi oluşturma adımları e-mail adresine gönderilmiştir. ")

        return redirect(url_for("user_list"))

    else:
        print(form.errors)

    return render_template("add_user.html", form=form, days_left=remaining_day)


@app.route("/user/user_list", methods=["GET", "POST"])
def user_list():
    user = get_current_user()
    form = UserForm()

    if not user:
        return redirect(url_for("home"))

    users = User.query.filter_by(company_id=session['company']).order_by(User.user_id).all()

    return render_template("user_list.html", users=users, form=form, days_left=remaining_day)


@app.route("/user/delete/<int:id>", methods=['POST'])
def delete_user(id):
    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    user_to_delete = User.query.filter_by(user_id=id).first()
    db.session.delete(user_to_delete)
    db.session.commit()
    flash("Kullanıcı kaydı silinmiştir.")
    return redirect(url_for("user_list"))


@app.route("/user/update/<int:id>", methods=['GET', 'POST'])
def update_user(id):

    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    form = UserForm()

    user_to_update = User.query.filter_by(user_id=id).first()

    if request.method == 'GET':

        form.name.data = user_to_update.user_name
        form.role.data = user_to_update.role
        form.email.data = user_to_update.user_email
        form.mobile_phone.data = user_to_update.user_phone

        return render_template("update_user.html", form=form,  user=user_to_update, days_left=remaining_day)

    if request.method == 'POST' and form.validate_on_submit():

        user_to_update.user_name = form.name.data
        user_to_update.role = form.role.data
        user_to_update.user_email = form.email.data
        user_to_update.user_phone = form.mobile_phone.data
        user_to_update.updated_date = datetime.now()
        user_to_update.updated_user = session['user']

        db.session.commit()

        flash("Kullanıcı bilgileri başarıyla güncellendi.")

        return redirect(url_for("user_list"))

    else:
        print(form.errors)

    return render_template("update_user.html", form=form, days_left=remaining_day)


@app.route("/user_profile")
def user_profile():

    user = get_current_user()

    if not user:
        return redirect(url_for("home"))

    user_info = User.query.filter_by(user_id=session['user_id']).first()

    company_info = Company.query.filter_by(company_id=user_info.company_id).first()

    return render_template("user_profile.html", user=user_info, company=company_info, days_left=remaining_day)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404