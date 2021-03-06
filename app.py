from flask import Flask, render_template, flash, request, url_for, redirect,session
import gc
from flask_mail import Mail, Message
from passlib.hash import sha256_crypt
from wtforms import Form,  StringField, SelectField, validators
import socket
import smtplib
import re
import flask_excel as excel
import dns.resolver
from dbconnection import connection
from flask_socketio import SocketIO, emit

app = Flask(__name__)
excel.init_excel(app)
app.config.update(
	DEBUG=True,
	#EMAIL SETTINGS
	MAIL_SERVER='smtp.googlemail.com',
	MAIL_PORT=465,
	MAIL_USE_SSL=True,
	MAIL_USERNAME = 'narayanamurthy.gidugu@gmail.com',
	MAIL_PASSWORD = ''
	)
app.config['SECRET_KEY'] = 'redsfsfsfsfis'
mail = Mail(app)
socketio = SocketIO(app)
@socketio.on('disconnect')
def disconnect_user():
    session.clear()
def mailverify(email):
   
    try:
        addressToVerify =email
        match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', addressToVerify)

        if match == None:
            return 'syntax not valid'
        m=email.split('@')[1]
        m=str(m)
        records = dns.resolver.query(m, 'MX')
        mxRecord = records[0].exchange
        mxRecord = str(mxRecord)
        host = socket.gethostname()
        server = smtplib.SMTP()
        server.set_debuglevel(0)
        server.connect(mxRecord)
        server.helo(host)
        server.mail(email)
        code, message = server.rcpt(str(addressToVerify))
        server.quit()
        if code == 250:
            return 1
        else:
            return 0
    except Exception :
        
        return 0
def send_mail(email,id):
	try:
        
		msg = Message("RESONANCE-2k19!",sender="narayanamurthy.gidugu@gmail.com",recipients=[str(email)])
		msg.body = "Thanks for registering.\nYour ID:"+str(id)+"\n\tYour application has been shared with our related co-ordinators.Please forward your abstract to below mails  depending on your stream. \nCSE:   resonance2k19.cse@bvcgroup.in\nECE:   resonance2k19.ece@bvcgroup.in \nEEE:    resonance2k19.eee@bvcgroup.in\nCE:   resonance2k19.civil@bvcgroup.in\nME:   resonance2k19.mech@bvcgroup.in\n Make sure that your abstract file name should be your id and the abstract must be in IEEE format.\n\n\t\tRegards\n\tBVC ENGG COLLEGE\n\nPlease do not reply tho this mail.If you have any queries mail to your respective department mails mentioned above."
		mail.send(msg)
		return 'Mail sent!'
	except Exception as e:
		return(str(e)) 
@app.route('/')
def homepage():
    if 'logged_in' in session:
        c,conn = connection()
    
        c.execute("SELECT * FROM festusers WHERE branch = %s",(session['username'],))
        colname=[desc[0] for desc in c.description]
        tab_data=c.fetchall()
        l=len(tab_data)
        tab_data.insert(0,colname)
        return render_template("home.html",data=tab_data,l=l)
    return render_template("home.html")
@app.route('/resonance/')
def Resonance():
    return render_template("resonance.html")
@app.route('/register/', methods=["GET","POST"])
def register():
    try:
        if request.method=="POST":
            return render_template("register.html")
    except Exception:
        return render_template("resonance.html")
    return render_template("register.html")

    
    

@app.route('/kreeda/')
def kreeda():
    return render_template("kreeda.html")
@app.route('/contact/')
def contact():
    return render_template("contact.html")


@app.route('/registration/', methods=["GET","POST"])
def registration():
    try:
        if request.method == "POST" :
            if 'submit_button' in request.form:
                name  = request.form['name']
                clgname = request.form['clgname']
                email=request.form['email']
                branch = request.form['branch']
                paper_title=request.form['papertitle']
                x=mailverify(email)
                
                
                if x == 1:
                    c, conn = connection()
                    c.execute("SELECT MAX(id) FROM festusers")
                    id=c.fetchone()
                    c.execute("INSERT INTO festusers VALUES (%s,%s, %s,%s, %s, %s)",(id[0]+1,name,clgname,email,paper_title,branch))
                    conn.commit()                    
                    
                    
                    
                    z=send_mail(str(email),id[0]+1)
                    
                    c.close()
                    conn.close()
                    gc.collect()
                    flash("Successfully Registered !! Please check your email for further communication!!")
                    return render_template("resonance.html")
                else:
                    flash("Invalid email!!")
                    return render_template('register.html')
            return render_template("register.html")

    except Exception as e:
        return render_template("home.html", error = e) 
		
@app.route("/admin/")
def admin():
    return render_template("admin.html")
@app.route("/logout/")
def logout():
    session.clear()
    return render_template("admin.html")
@app.route('/login/', methods=["GET","POST"])
def login():
    c,conn = connection()
   
    try:
        
        if request.method == "POST" :

            if 'adminsubmit' in request.form:
                c.execute("SELECT * FROM admin WHERE email = ('%s')" %request.form["adminmail"])
               
                data = c.fetchone()
              
                if sha256_crypt.verify(request.form['password'],data[1] ):
                    
                    
                    c.execute("SELECT * FROM festusers WHERE branch = %s",(data[2],))
                    colname=[desc[0] for desc in c.description]
                    tab_data=c.fetchall()
                    l=len(tab_data)

                    tab_data.insert(0,colname)
                    c.close()
                    session['logged_in'] = True
                    session['username'] = request.form['adminmail']
                    conn.commit()
                    conn.close()
                    gc.collect()
                    return render_template("home.html",data = tab_data,l=l)
    except Exception as e:
        return render_template("admin.html")
    return render_template("admin.html")
@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html")
@app.errorhandler(405)
def page_not_found(e):
    return render_template("error.html")
@app.errorhandler(500)
def page_not_found(e):
    return render_template("error.html")
@app.route("/download/", methods=['GET','POST'])
def download():
    c,conn=connection()
    with conn:
        with c:
           
            c.execute("SELECT * FROM festusers WHERE branch = %s",(session['username'],))
            colname=[desc[0] for desc in c.description]
            tab_data=c.fetchall()
            tab_data.insert(0,colname)
            return excel.make_response_from_array(tab_data, "csv",file_name="registered_candidates")
if __name__ == "__main__":
    app.secret_key="bvcfest2k19"
    
    app.run()
