from flask import Flask, request, render_template, flash, redirect, url_for , session; from flask_cors import CORS; 
from flask import Flask, jsonify
from flask import Flask
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import abort
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# import routes  # Import routes (we’ll create this later)
from models import Campaign, Feedback, Department ,Users, Question, Docket  
# from models import *
# with app.app_context():            #import app and db from your app package
#     db.create_all()                #create the tables based on models




app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/your_database'
app.config['SECRET_KEY'] = 'your_secret_key'

if __name__== '__main__':
    app.run(debug=True)


# Import models here (User, Department, Campaign, Feedback, etc.)
# from models import User, Department, Campaign, Feedback

# Helper function for role-based access control
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_role = session.get("user_role")
            if user_role != role:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

@app.route('/assign_role', methods=['GET', 'POST'])
@login_required
@role_required('super_admin')
def assign_role():
    if request.method == 'POST':
        email = request.form['email']
        user = Users.query.filter_by(email=email).first()
        role = request.form['role']
        if user:
            user.role = role
            db.session.commit()
            flash(f"Role '{role}' assigned to {email}.", "success")
        else:
            flash("User not found", "danger")
    users = Users.query.all()
    return render_template('assign_role.html')

@app.route('/submit_feedback', methods=['GET', 'POST'])
@login_required
def submit_feedback():
    if request.method == 'POST':
        department_id = request.form['department_id']
        campaign_id = request.form['campaign_id']
        comments = request.form['comments']
        feedback = Feedback(department_id=department_id, campaign_id=campaign_id, comments=comments, created_at=datetime.datetime.utcnow())
        db.session.add(feedback)
        db.session.commit()
        flash("Feedback submitted successfully", "success")
        return redirect(url_for('index'))
    departments = departments.query.all()
    campaigns = Campaign.query.all()
    return render_template('submit_feedback.html', departments=departments, campaigns=campaigns)



@app.route('/manage_departments', methods=['GET', 'POST'])
@login_required
@role_required('super_admin')
def manage_departments():
    if request.method == 'POST':
        name = request.form.get('name').strip()

    
      
    # Query all active departments
    def get_all_departments():
        departments = Department.query.filter(Department.department_id == current_user.department_id).all()
        print(departments)
    return render_template('manage_departments.html')
    
@app.route('/add_department', methods=['GET', 'POST'])
@login_required
@role_required('super_admin')
def add_department():
    if request.method == 'POST':
        name = request.form['name'].strip()
        admin_id = request.form.get('user_id')
        

        # Check if the department name already exists
        
        if db.session.query(Department).filter_by(name=name).first():
            flash("Department is already registered.", "danger")
            return redirect(url_for('manage_departments'))
        
        

        # Check if the specified admin exists and has an 'admin' role
        admin_user = db.session.execute(db.select(Users).filter_by( id=admin_id, role='admin')).scalar_one()
        print(admin_user)
        if not admin_user:
            flash("Selected admin does not exist or is not eligible.", "danger")
            return redirect(url_for('manage_departments'))
        
        # Create the new department
        new_department = Department(name=name, created_at=datetime.datetime.now())
        db.session.add(new_department)
        db.session.commit()
        
        # Assign the selected admin to the new department
        admin_user.department_id = new_department.department_id
        db.session.commit()
        
        flash(f"Department '{name}' added and assigned to {admin_user.name}.", "success")
        return redirect(url_for('manage_departments'))
    
    # Get a list of eligible admin users to assign
    eligible_admins = Users.query.filter_by(role='admin').all()
    departments = db.session.execute(db.select(Department)).scalars()
    return render_template('manage_departments.html', eligible_admins=eligible_admins, departments=departments)




@app.route('/delete_department/<int:department_id>', methods=['POST'])
@login_required
@role_required('super_admin')
def delete_department(department_id):
    department = Department.query.get_or_404(department_id)
    department.deleted_at = datetime.utcnow()  # Implementing soft delete
    db.session.commit()
    flash(f"Department '{department.name}' deleted.", "success")
    return redirect(url_for('manage_departments'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        print(email)

        # Validate email domain
        if not email.endswith('@strathmore.edu'):
            flash("Please use a valid organization email address.", "danger")
            return redirect(url_for('register'))

        # Check if user already exists
        if db.session.query(Users.query.filter_by(email=email).exists()).scalar():
            flash("Email is already registered.", "danger")
            return redirect(url_for('register'))

        # Create new user
        new_user = Users(name=name, email=email, role='viewer')  # Default role
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        

        # user = db.session.query(Users.query.filter_by(email=email))
        user =  db.session.execute(db.select(Users).filter_by(email=email)).scalar_one()
    
        # user = Users.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password ,password):

            session['user_id'] = user.id
            session['user_role'] = user.role
            flash("Login successful", "success")
            # Redirect based on role
            if user.role == 'super_admin':
                return redirect(url_for('dashboard'))  # Super Admin dashboard
            elif user.role == 'admin':
                return redirect(url_for('dashboard'))  # Admin dashboard
            else:
                return redirect(url_for('dashboard'))  # Viewer route
        else:
            flash("Invalid email or password", "danger")
    return render_template('login.html')



@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))

class Users(db.Model):
    _tablename_ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='viewer')

    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session or session['user_role'] not in roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

@app.route('/create_campaign', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def create_campaign():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        feedback_type = request.form['feedback_type']

        if not hasattr(current_user, 'department_id') or current_user.department_id is None:
            flash("Your account is not associated with any department.", "error")
            return redirect(url_for('dashboard'))
        
        department_id = current_user.department_id  # Assuming admins belong to a department
        
        # Create a new campaign
        new_campaign = Campaign(name=name, description=description, feedback_type=feedback_type, department_id=department_id)
        db.session.add(new_campaign)
        db.session.commit()
        flash("Campaign created successfully. Now design your feedback form.", "success")
        return redirect(url_for('design_feedback_form', campaign_id=new_campaign.campaign_id))
    
    return render_template('create_campaign.html')

@app.route('/add_questions/<int:campaign_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_questions(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)

    if request.method == 'POST':
        questions = request.form.getlist('questions')

        for question_text in questions:
            new_question = Question(campaign_id=campaign_id, question_text=question_text)
            db.session.add(new_question)

        db.session.commit()
        flash(f"Questions added successfully to the campaign '{campaign.name}'.", "success")
        return redirect(url_for('dashboard'))

    return render_template('add_questions.html', campaign=campaign)

@app.route('/design_feedback_form/<int:campaign_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def design_feedback_form(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)

    if request.method == 'POST':
        logo_url = request.form.get('logo_url', None)
        questions = request.form.getlist('questions')

        # Save each question to the database and link it to the campaign
        for question_text in questions:
            new_question = Question(campaign_id=campaign_id, question_text=question_text)
            db.session.add(new_question)

        # Optionally update the campaign with the logo URL
        if logo_url:
            campaign.logo_url = logo_url

        db.session.commit()
        flash(f"Feedback form for campaign '{campaign.name}' has been designed successfully.", "success")
        return redirect(url_for('dashboard'))

    return render_template('feedback_form.html', campaign=campaign)


@app.route('/dashboard')
@login_required
def dashboard():
    # Code for displaying the dashboard
    # Show different data based on the role (admin or viewer)
    user_role = session.get('user_role')
    return render_template('dashboard.html', user_role=user_role)


@app.route('/view_feedback/<int:campaign_id>', methods=['GET'])
@login_required
@role_required('admin', 'viewer')
def view_feedback(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    feedbacks = feedbacks.query.filter_by(campaign_id=campaign_id).all()  # Customize this query as needed
    return render_template('view_feedback.html', campaign=campaign, feedbacks=feedbacks)

@app.route('/manage_dockets', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def manage_dockets():
    department_id = current_user.department_id
    department = Department.query.get_or_404(department_id)

    if request.method == 'POST':
        action = request.form.get('action')
        docket_name = request.form.get('docket_name')

        if action == 'add':
            new_docket = Docket(name=docket_name, department_id=department_id)
            db.session.add(new_docket)
            db.session.commit()
            flash(f"Docket '{docket_name}' added successfully.", "success")
        elif action == 'delete':
            docket_id = request.form.get('docket_id')
            docket = Docket.query.get(docket_id)
            if docket:
                db.session.delete(docket)
                db.session.commit()
                flash(f"Docket '{docket.name}' deleted successfully.", "success")
            else:
                flash("Invalid docket ID.", "danger")

        return redirect(url_for('manage_dockets'))

    dockets = Docket.query.filter_by(department_id=department_id).all()
    return render_template('manage_dockets.html', department=department, dockets=dockets)

# @app.route('/add_users_departments', methods=['GET', 'POST'])
# @login_required
# @role_required('admin')
# def add_users_departments():
#     if request.method == 'POST':
#         user_id = request.form.get('user_id')
#         user = Users.query.get(user_id)
        
#         # Fetch the user and the current admin's department
#         user = Users.query.get(user_id)
#         current_department = Department.query.get(current_user.department_id)
        
#         # Validate the user and ensure they are not a super admin
#         if not user or user.role == 'super_admin':
#             flash("Invalid user or role. Only admins and viewers can be added.", "danger")
#             return redirect(url_for('manage_department_users'))
        
#         # Assign the user to the current department
#         user.department_id = current_user.department_id
#         db.session.commit()
        
#         flash(f"User '{user.name}' has been added to the department '{current_department.name}'.", "success")
#         return redirect(url_for('manage_department_users'))
    
#     # Fetch users eligible to be added to the department
#     eligible_users = Users.query.filter((user.role == 'admin') | (user.role == 'viewer'),
#      Users.department_id == None  # Ensure the user isn't already in a department
#     ).all()
    
#     return render_template('manage_department_users.html', eligible_users=eligible_users)


    # Fetch eligible users
    #eligible_users = Users.query.filter((Users.role.in_(['admin', 'viewer'])) & (Users.department_id == None)).all()