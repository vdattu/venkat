from flask import flash,Flask,render_template,redirect,url_for,jsonify,request,session
from flask_mysqldb import MySQL
from flask_session import Session
from py_mail import mail_sender
from datetime import datetime
from datetime import date
from otp import genotp
from sdmail import sendmail
from tokenreset import token
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

app=Flask(__name__)
app.secret_key='A@Bullela@_3'
app.config['MYSQL_HOST'] ='localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD']='root'
app.config['MYSQL_DB']='pyl'
app.config["SESSION_TYPE"] = "filesystem"
mysql=MySQL(app)
Session(app)
@app.route('/')
def welcome():
    return render_template('title.html')
@app.route('/create',methods=['GET','POST'])
def create():
    cursor=mysql.connection.cursor()
    cursor.execute('SELECT COUNT(*) from admin')
    count=cursor.fetchone()[0]
    cursor.close()
    if request.method=="POST":
        if int(count)>=1:
            flash('Only One Admin is allowed to operate this application')
            return render_template('signup.html')
        name=request.form['name']
        email=request.form['email']
        password=request.form['password']
        passcode=request.form['passcode']
        cursor=mysql.connection.cursor()
        cursor.execute('insert into admin values(%s,%s,%s,%s)',[name,email,passcode,password])
        mysql.connection.commit()
        flash('Details Registered Successfully')
        return redirect(url_for('adminlogin'))
    return render_template('signup.html')
@app.route('/adminlogin',methods=['GET','POST'])
def adminlogin():
    if request.method=="POST":
        user=request.form['user']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('select email from admin')
        email=cursor.fetchone()[0]
        cursor.execute('select password from admin')
        user_password=cursor.fetchone()[0]
        cursor.execute('select passcode from admin')
        passcode=cursor.fetchone()[0]
        print(password)
        print(user_password)
        cursor.close()
        if email==user:
            if password==user_password:
                session['email']=email
                session['passcode']=passcode
                return redirect(url_for('panel'))
            else:
                flash('Invalid Password')
                render_template('adminlogin.html')
        else:
            flash('Invalid User Id')
            render_template('adminlogin.html')

    return render_template('adminlogin.html')
@app.route('/adminpanel')
def panel():
    if session.get('email'):
        return render_template('homepage.html')
    return redirect(url_for('adminlogin'))
@app.route('/facultyregistration',methods=['GET','POST'])
def faculty():
    if session.get('email'):
        if request.method=='POST':
            id1=request.form['Id']
            name=request.form['Name']
            gender=request.form['gender']
            phone=request.form['phone']
            mail=request.form['mail']
            password=request.form['password']
            Address=request.form['Address']
            dept=request.form['dept']
            pay=request.form['pay']
            print(request.form)
            otp=genotp()
            subject='Thanks for registering'
            body = 'your one time password is- '+otp
            sendmail(mail,subject,body)
            print(request.form)
            return render_template('otp.html',otp=otp,id1=id1,name=name,gender=gender,phone=phone,mail=mail,password=password,Address=Address,dept=dept,pay=pay)
        return render_template('registerpage.html')
    else:
        return redirect(url_for('adminlogin'))
    
@app.route('/otp/<otp>/<id1>/<name>/<gender>/<phone>/<mail>/<password>/<Address>/<dept>/<pay>',methods=['POST','GET'])
def getotp(otp,id1,name,gender,phone,mail,password,Address,dept,pay):
    if request.method == 'POST':
        OTP=request.form['otp']
        if otp == OTP:
            cursor=mysql.connection.cursor() 
            cursor.execute('insert into employee values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',[id1,name,gender,phone,mail,password,Address,dept,pay])
            mysql.connection.commit()
            cursor.close()
            flash('Details Registered Successfully')
            return redirect(url_for('login'))
        else:
            flash('wrong OTP')

    return render_template('otp.html',otp=otp,id1=id1,name=name,gender=gender,phone=phone,mail=mail,password=password,Address=Address,dept=dept,pay=pay)
@app.route('/forgotpassword',methods=('GET', 'POST'))
def forgotpassword():
    if request.method=='POST':
        mail = request.form['email']
        cursor=mysql.connection.cursor() 
        cursor.execute('select mail from employee ') 
        deta=cursor.fetchall()
        print(deta)
        if (mail,) in deta:
            subject=f'forgot password conformation'
            tokenreset=token(mail,300)
            url=url_for('resetpwd',token=tokenreset,_external=True)
            body=f'reset password using this link-{url}'
            sendmail(mail,subject,body)
            flash('link sended to ur mail')
        else:
            flash('user does not exits')
    return render_template('forgot.html')

@app.route('/resetpwd/<token>',methods=('GET', 'POST'))
def resetpwd(token):
    try:
        s=Serializer(app.config['SECRET_KEY'])
        mail=s.loads(token)['user']
        if request.method=='POST':
            npwd = request.form['npassword']
            cpwd = request.form['cpassword']
            if npwd == cpwd:
                cursor=mysql.connection.cursor()
                cursor.execute('update employee set  password=%s where mail=%s',[npwd,mail])
                mysql.connection.commit()
                cursor.close()
                return 'Password reset Successfull'
            else:
               return 'Password does not matched try again'
        return render_template('newpassword.html')
    except Exception as e:
        abort(410,description='reset link expired')

    return redirect(url_for('adminlogin'))
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('fachome'))
    if request.method=='POST':
        user=request.form['user']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT id from employee')
        data=cursor.fetchall()
        cursor.execute('SELECT PASSWORD from employee WHERE id=%s',[user])
        password_user=cursor.fetchone()
        cursor.close()
        if (int(user),) in data:
            if password==password_user[0]:
                session['user']=user
                return redirect(url_for('fachome'))
            else:
                flash('Invalid password')
                return render_template('login.html')
        else:
            flash('Invalid user Id')
            return render_template('login.html')
    return render_template('login.html')
@app.route('/fachome')
def fachome():
    if session.get('user'):
        return render_template('facultypage.html')
    return redirect(url_for('login'))
@app.route('/adminlogout')
def alogout():
    session.pop('email')
    return redirect(url_for('welcome'))
@app.route('/logout')
def logout():
    session.pop('user')
    return redirect(url_for('welcome'))
@app.route('/employeecheckin')
def emp():
    if session.get('user'):
        today=date.today()
        day=today.day
        month=today.month
        year=today.year
        today_date=datetime.strptime(f'{year}-{month}-{day}','%Y-%m-%d')
        date_today=datetime.strftime(today_date,'%Y-%m-%d')
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM RECORDS WHERE DATE=%s AND id=%s',[date_today,session.get('user')])
        count=cursor.fetchone()[0]
        cursor.execute('select * from records where id=%s',[session.get('user')])
        data=cursor.fetchall()
        cursor.close()
        if count==0:
            cursor=mysql.connection.cursor()
            cursor.execute('select pay from employee where id=%s',[session.get('user')])
            pay=(cursor.fetchone()[0])/12
            cursor.execute('select target from working_days')
            target=cursor.fetchone()[0]
            day_pay=pay/target
            cursor.execute('select name from employee where id=%s',[session.get('user')])
            name=cursor.fetchone()[0]
            cursor.execute('insert into records(date,id,name,day_pay) values(%s,%s,%s,%s)',[date_today,session.get('user'),name,day_pay])
            mysql.connection.commit()
            cursor.execute('select * from records where id=%s',[session.get('user')])
            data=cursor.fetchall()
            cursor.close()
            return render_template('table.html',data=data)
        return render_template('table.html',data=data)
    return redirect(url_for('login'))
@app.route('/checkoutupdate/<date>/<id1>')
def checkoutupdate(id1,date):
    cursor=mysql.connection.cursor()
    cursor.execute('update records set checkout=current_timestamp() where Id=%s and date=%s',[id1,date])
    mysql.connection.commit()
    return redirect(url_for('emp'))
@app.route('/checkinupdate/<date>/<id1>')
def checkinupdate(id1,date):
    cursor=mysql.connection.cursor()
    cursor.execute('update records set checkin=current_timestamp() where Id=%s and date=%s',[id1,date])
    mysql.connection.commit()
    return redirect(url_for('emp'))
@app.route('/emprecords')
def records():
    cursor=mysql.connection.cursor()
    cursor.execute('select * from records order by date')
    data=cursor.fetchall()
    cursor.close()
    return render_template('status.html',data=data)
@app.route('/empsalary')
def salary_emp():
    cursor=mysql.connection.cursor()
    cursor.execute("select id,date_format(date,'%M %Y') as Month,COUNT(*) AS DAYS from records group by ID,MONTH ORDER BY MONTH")
    data=cursor.fetchall()
    cursor.close()
    return render_template('months.html',data=data)
@app.route('/empsalaryattend')
def salary_emp_attend():
    id1=session.get('user')
    cursor=mysql.connection.cursor()
    cursor.execute("select id,date_format(date,'%%M %%Y') as Month,COUNT(*) AS DAYS from records  where id=%s group by ID,MONTH ORDER BY MONTH",[id1])
    data=cursor.fetchall()
    cursor.close()
    return render_template('months.html',data=data)
app.run(debug=True,use_reloader=True)
'''cursor=mysql.connection.cursor()
            cursor.execute('insert ignore into employee values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',[id1,name,gender,phone,mail,password,Address,dept,pay])
            mysql.connection.commit()
            from_mail=session['email']
            passcode=session['passcode']
            subject=f'{name}, Your details are successfully with us!'
            url_path=request.host_url+url_for('adminlogin')
            body=f'Your user is {id1} and password is {password}\n\nYOU can login to the pay roll system with these details by going through\n\n\n {url_path} '
            try:
                mail_sender(from_mail,mail,subject,body,passcode)
            except Exception as e:
                print(e)
                flash('There is trouble sending email confirmation\n check the sender mail but')
            flash('Details Registered Successfully')'''