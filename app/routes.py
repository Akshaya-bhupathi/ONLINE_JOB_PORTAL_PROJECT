from flask import Blueprint, render_template, url_for, redirect, flash, request
from flask_login import login_user, current_user, logout_user, login_required
from app import db
from app import bcrypt
from app.models import User, Job, Application
from app.forms import RegistrationForm, LoginForm, JobForm, ApplicationForm
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import abort

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
jobs = Blueprint('jobs', __name__)
dashboard_bp = Blueprint('dashboard', __name__)

# Main Routes
@main.route('/')
@main.route('/home')
def home():
    jobs = Job.query.order_by(Job.date_posted.desc()).limit(5).all()
    return render_template('home.html', jobs=jobs)

# Auth Routes
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=hashed_password,
                role=form.role.data
            )
            db.session.add(user)
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Username or email already exists', 'danger')
    return render_template('auth/register.html', title='Register', form=form)
    
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard.dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('auth/login.html', title='Login', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))

# Job Routes
@jobs.route('/jobs')
def job_list():
    page = request.args.get('page', 1, type=int)
    jobs = Job.query.order_by(Job.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('jobs/list.html', jobs=jobs)

@jobs.route('/job/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('jobs/detail.html', job=job)


@jobs.route('/job/new', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role != 'employer':
        flash('Only employers can post jobs', 'danger')
        return redirect(url_for('main.home'))
    form = JobForm()
    if form.validate_on_submit():
        job = Job(title=form.title.data, company=form.company.data, 
                 location=form.location.data, salary=form.salary.data,
                 description=form.description.data, author=current_user)
        db.session.add(job)
        db.session.commit()
        flash('Your job has been posted!', 'success')
        return redirect(url_for('jobs.job_detail', job_id=job.id))
    return render_template('jobs/post.html', title='Post Job', form=form)

@jobs.route('/job/<int:job_id>/apply', methods=['GET', 'POST'])
@login_required
def apply_job(job_id):
    
    job = Job.query.get_or_404(job_id)
    # Only jobseekers can apply
    if current_user.role != 'jobseeker':
        flash("Only jobseekers can apply for jobs.", "danger")
        return redirect(url_for('jobs.job_detail', job_id=job.id))

    # Check if already applied
    if current_user.has_applied(job):
        flash("You have already applied for this job.", "warning")
        return redirect(url_for('jobs.job_detail', job_id=job.id))

    # Create application
    application = Application(user_id=current_user.id, job_id=job.id)
    db.session.add(application)
    db.session.commit()
    form = ApplicationForm()
    if form.validate_on_submit():
        application = Application(cover_letter=form.cover_letter.data, 
                                job=job, applicant=current_user)
        db.session.add(application)
        db.session.commit()
        flash('Your application has been submitted!', 'success')
        return redirect(url_for('jobs.job_detail', job_id=job.id))
    return render_template('jobs/apply.html', title='Apply Job', form=form, job=job)

@jobs.route('/job/<int:job_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    if current_user != job.author:
        abort(403)
    form = JobForm()
    if form.validate_on_submit():
        job.title = form.title.data
        job.description = form.description.data
        job.salary = form.salary.data
        job.location = form.location.data
        job.company = form.company.data
        db.session.commit()
        flash('Your job has been updated!', 'success')
        return redirect(url_for('jobs.job_detail', job_id=job.id))
    elif request.method == 'GET':
        form.title.data = job.title
        form.description.data = job.description
        form.salary.data = job.salary
        form.location.data = job.location
        form.company.data = job.company
    return render_template('jobs/edit.html', title='Edit Job', form=form, job=job)

@jobs.route('/job/<int:job_id>/delete', methods=['POST'])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    if current_user.id != job.user_id and current_user.role != 'admin':
        abort(403)
    try:
        db.session.delete(job)
        db.session.commit()
        flash('Job posting has been deleted!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting job', 'danger')
        abort(500)
    return redirect(url_for('jobs.job_list'))

# Dashboard Routes
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('dashboard.admin_dashboard'))
    elif current_user.role == 'employer':
        return redirect(url_for('dashboard.employer_dashboard'))
    else:
        return redirect(url_for('dashboard.jobseeker_dashboard'))

@dashboard_bp.route('/test')
def test():
    return "Blueprint is working"

@dashboard_bp.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('You are not authorized to view this page', 'danger')
        return redirect(url_for('main.home'))
    users = User.query.all()
    jobs = Job.query.all()
    applications = Application.query.all()
    return render_template('dashboard/admin.html', users=users, jobs=jobs, applications=applications)

@dashboard_bp.route('/employer')
@login_required
def employer_dashboard():
    if current_user.role != 'employer':
        flash('You are not authorized to view this page', 'danger')
        return redirect(url_for('main.home'))
    jobs = current_user.jobs
    applications = Application.query.join(Job).filter(Job.user_id == current_user.id).all()
    return render_template('dashboard/employer.html', jobs=jobs, applications=applications)

@dashboard_bp.route('/jobseeker')
@login_required
def jobseeker_dashboard():
    if current_user.role != 'jobseeker':
        flash('You are not authorized to view this page', 'danger')
        return redirect(url_for('main.home'))
    applications = current_user.job_applications
    return render_template('dashboard/jobseeker.html', applications=applications)

@dashboard_bp.route('/applications')
@login_required
def view_applications():
    applications = current_user.job_applications
    return render_template('dashboard/applications.html', applications=applications)