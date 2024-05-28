from flask import Flask,request,render_template,redirect,url_for,session,flash,session,send_file
from flask_session import Session
from otp import genotp
import flask_excel as excel
from itsdangerous import URLSafeTimedSerializer
from tokens import token 
from keys import secret_key,salt,salt2
from cmail import sendmail
import mysql.connector
import io 
from io import BytesIO




app=Flask(__name__)
app.config['SESSION_TYPE']='filesystem'
Session(app) 
mydb=mysql.connector.connect(host='localhost',user="root",password="Admin",db="spm")
excel.init_excel(app)
app.secret_key=b'@\xdd/%ea'
@app.route('/') 
def home():
    return render_template('welcome.html')
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form['name'] 
        email=request.form['email']
        password=request.form['password']
        cpassword=request.form['cpassword']
        print(request.form) 
        if password==cpassword:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from user where email=%s',[email])
            count=cursor.fetchone()[0]
            if count == 1:
                flash("Email already exist")
                return redirect(url_for('register'))
            else:

                otp=genotp() 
                data={'name':name,'email':email,'password':password,'otp':otp}
                subject='OTP for SPM Application' 
                body=f'This is the otp for spm register verification{otp}' 
                sendmail(to=email,subject=subject,body=body)
                otp=token(data=data,salt=salt)
                print(otp)
                serializer=URLSafeTimedSerializer(secret_key)
                flash(' verification mail has sent to given Email pls check')
                return redirect(url_for('otp',otp=otp))# `two otp gen avuthunnay difference kosam raasam url lo otp manaku display avuthindhi
        else:
            flash('mismatch of password confirmation.')
            return redirect(url_for('register'))
    return render_template('register.html') 
@app.route('/otp/<otp>',methods=['GET','POST']) 
def otp(otp):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(otp,salt=salt,max_age=60)
    except Exception as e:
        flash("otp expire")
        return render_template('otp.html')
        
    else:
        if request.method=='POST':
           otp1=request.form['otp']
           if data['otp']==otp1:
              cursor=mydb.cursor(buffered='True')
              cursor.execute('insert into user(name,email,password) values(%s,%s,%s)',[data['name'],data['email'],data['password']])
              mydb.commit()
              cursor.close()
              flash('Registration has successfully done')
              return redirect(url_for('login'))
           else:
                flash('otp was incorrect') 
                return redirect(url_for('otp',otp=otp))
                    
    return render_template('otp.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('dashboard'))
    if request.method=='POST':
            email=request.form['email']
            password=request.form['password']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from user where email=%s',[email])
            data=cursor.fetchone()
            cursor.close()
            print(data)
            if data[0] == 1:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select email,password from user where email=%s',[email])
                data=cursor.fetchone()
                cursor.close()
                if data[1]==password:
                    session['user']=email
                    return redirect(url_for('dashboard'))
                    
                else:
                    flash('incorrect password')
                    return redirect(url_for('login'))    
            else:
                flash('Pls register for the application')
                return redirect(url_for('register'))
            
    return render_template('login.html')
@app.route('/forgot',methods=['GET','POST'])
def forgot():
    if request.method=='POST':
        email=request.form['email']
        subject='reset link for SPM application'
        body=f"reset link for forgot password of SPM : {url_for('fconfirm',token=token(data=email,salt=salt2),_external=True)}"
        sendmail(to=email,subject=subject,body=body)

        flash('reset link has sent to  given email pls check')
        return redirect(url_for('forgot'))
    return render_template('forgot.html') 
@app.route('/fconfirm/<token>',methods=["GET","POST"])
def fconfirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        email=serializer.loads(token,salt=salt2,max_age=180) 
    except Exception as e:
        return 'link expired'
    else:    
        if request.method=="POST":
            npassword=request.form['npassword']
            cpassword=request.form['cpassword']
            if npassword==cpassword:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update user set password=%s  where email=%s',[npassword,email])
                mydb.commit()
                cursor.close()
                return redirect(url_for('login'))
            else:
                flash('password mismatch') 
                return render_template('updatepassword.html')   
        return render_template('updatepassword.html') 




@app.route('/dashboard',methods=["GET"])
def dashboard():
    if session.get('user'):
        return  render_template('dashboard.html')       
    else:
        return redirect(url_for('login'))
    

@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))
    return  redirect(url_for('login'))

@app.route('/addnotes',methods=['GET','POST']) 
def addnotes():
    if session.get('user'): 
        if request.method=='POST':
            title=request.form['title']
            content=request.form['content']
            
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select id from user where email=%s',[session.get('user')])
            uid=cursor.fetchone()[0]
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into notes(title,description,u_id)values(%s,%s,%s)',[title,content,uid])
            mydb.commit()
            cursor.close()
            flash('notes has added successfully')
            return redirect(url_for('dashboard'))
        return render_template('addnotes.html')
    else:
        return redirect(url_for('login')) 

@app.route('/view_allnotes')
def view_allnotes():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select id from user where email=%s',[session.get('user')])
        uid=cursor.fetchone()[0]
        
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from notes where u_id=%s',[uid])
        allnotes=cursor.fetchall()
        return render_template('table.html',data=allnotes)
    else:
        return redirect(url_for('login'))

@app.route('/view_notes/<nid>')
def view_notes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select title,description,created_at from notes where nid=%s',[nid])
        allnotes=cursor.fetchall()
        print(allnotes)
        return render_template('viewnotes.html',data1=allnotes) 
    return redirect(url_for('login'))

@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select title,description,created_at from notes where nid=%s',[nid])
        allnotes=cursor.fetchall()
        if request.method=='POST':
            title=request.form['title']
            content=request.form['content']
            cursor.execute('update notes set title=%s ,description=%s where nid=%s',[title,content,nid])
            mydb.commit()
            return redirect(url_for('updatenotes',nid=nid))
        return render_template('update.html',var1=allnotes) 
    else:
        return redirect(url_for('login'))

@app.route('/deletenotes/<nid>')
def deletenotes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from notes where nid=%s',[nid])
        mydb.commit()
        
        return redirect(url_for('view_allnotes'))
    else:
        return redirect(url_for('login'))
    
@app.route('/fileupload',methods=['GET','POST'])
def fileupload():
    if session.get('user'):
        if request.method=='POST':
            file_data=request.files['file']
            print(file_data)
            file_ext=file_data.filename.split('.')[-1]
            data=file_data.read()
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select id from user where email=%s',[session.get('user')])
            uid=cursor.fetchone()[0]
           
            cursor.execute('insert into files(extension,filedata,added_by) values(%s,%s,%s)',[file_ext,data,uid])
            mydb.commit()
            cursor.close()
            flash('File has successfully uploaded')
            return redirect(url_for('dashboard'))
           
            
        return render_template('fileupload.html')
    else:
        return redirect(url_for('login')) 

@app.route('/view_allfiles')
def view_allfiles():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select id from user where email=%s',[session.get('user')])
        uid=cursor.fetchone()[0]
        
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from files where added_by=%s',[uid])
        allnotes=cursor.fetchall()
        print(allnotes)
        

        return render_template('table2.html',data=allnotes)
    else:
        return redirect(url_for('login'))

@app.route('/viewfile/<fid>')
def viewfile(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select extension,filedata from files where fid=%s',[fid])
        data=cursor.fetchone()
        cursor.close()
        print(data)
        byte_data=BytesIO(data[1])
        filename='file.'+data[0]
        return send_file(byte_data,download_name=filename)   
    return redirect(url_for('login'))


@app.route('/downloadfile/<fid>')
def downloadfile(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select extension,filedata from files where fid=%s',[fid])
        data=cursor.fetchone()
        cursor.close()
        print(data)
        byte_data=BytesIO(data[1])
        filename='file.'+data[0]
        return send_file(byte_data,download_name=filename,as_attachment=True)   
    return redirect(url_for('login'))
            
@app.route('/deletefiles/<fid>')
def deletefile(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from files where fid=%s',[fid])
        mydb.commit()
        flash(f"File {fid} has been deleted ")
        
        return redirect(url_for('view_allfiles'))
    else:
        return redirect(url_for('login'))

@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select id from user where email=%s',[session.get('user')])
        uid=cursor.fetchone()[0] 
        cursor.execute('select title,description,created_at from notes where u_id=%s',[uid])
        data=cursor.fetchall()
        columns=['Title','Description']
        array_data=[list(i) for i in data]
        print(array_data)
        array_data.insert(0,columns)
        return excel.make_response_from_array(array_data,'xlsx',filename='notesdata')

    return redirect(url_for('login')) 
            
           

                     
            
            
           
        # print(otp1)
        # print(otp)
    
# print(genotp())
app.run(debug=True,use_reloader=True)

