import re
import os
from io import BytesIO
from datetime import datetime, timedelta
from flask import Flask, render_template, request, session, flash, redirect, url_for, send_file
from supabase import create_client, Client
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = 'funddonate_secret_key_2023'

# Supabase Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Configure upload settings
app.config['UPLOAD_FOLDER'] = 'static/uploads/receipts'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# ========== ROUTES ==========
@app.route('/')
def index():
    return render_template('index.html')


# ========== DONOR AUTH ==========
@app.route('/donor-login', methods=['GET', 'POST'])
def donor_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        result = supabase.table("donors").select("*").eq("email", email).eq("password", password).execute()

        if result.data:
            donor = result.data[0]
            session['donor_loggedin'] = True
            session['donor_id'] = donor['id']
            session['donor_name'] = donor['fullname']
            flash('Login successful!', 'success')
            return redirect(url_for('donor_dashboard'))
        else:
            flash('Invalid email or password!', 'error')

    return render_template('donor-login.html')


@app.route('/donor-register', methods=['GET', 'POST'])
def donor_register():
    print("=== DONOR REGISTER ROUTE CALLED ===")
    print(f"Request method: {request.method}")

    if request.method == 'POST':
        print("=== FORM DATA ===")
        for key, value in request.form.items():
            print(f"{key}: {value}")

        try:
            # Check passwords
            password = request.form.get('password', '')
            confirm = request.form.get('confirm_password', '')
            print(f"Password: {password}")
            print(f"Confirm: {confirm}")

            if password != confirm:
                flash('Passwords do not match!', 'error')
                print("Passwords don't match")
                return redirect(url_for('donor_register'))

            # Simple donor data - only required fields first
            donor_data = {
                "fullname": request.form.get('fullname', ''),
                "email": request.form.get('email', ''),
                "password": password,
                "designation": request.form.get('designation', ''),
                "address": request.form.get('address', ''),
                "city": request.form.get('city', ''),
                "taluka": request.form.get('taluka', ''),
                "district": request.form.get('district', ''),
                "state": request.form.get('state', ''),
                "country": request.form.get('country', ''),
                "phone": request.form.get('phone', ''),
                "aadhar_no": request.form.get('aadhar_no', ''),
                "pan_no": request.form.get('pan_no', '').upper(),
                "account_holder": request.form.get('account_holder', ''),
                "account_number": request.form.get('account_number', ''),
                "bank_name": request.form.get('bank_name', ''),
                "branch_name": request.form.get('branch_name', ''),
                "ifsc_code": request.form.get('ifsc_code', '').upper(),
                "branch_city": request.form.get('branch_city', ''),
                "donation_type": request.form.get('donation_type', 'one-time'),
                "donation_date": request.form.get('donation_date') or None,
                "tax_benefit": True if request.form.get('tax_benefit') else False
            }

            print(f"Donor data prepared: {donor_data}")

            # Check if email exists
            existing = supabase.table("donors").select("*").eq("email", donor_data["email"]).execute()
            print(f"Existing check result: {existing.data}")

            if existing.data:
                flash('Email already registered!', 'error')
                return redirect(url_for('donor_register'))

            # Insert
            result = supabase.table("donors").insert(donor_data).execute()
            print(f"Insert result: {result.data}")

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('donor_login'))

        except Exception as e:
            print(f"ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'Registration failed: {str(e)}', 'error')
            return redirect(url_for('donor_register'))

    return render_template('donor-register.html')


@app.route('/donor-logout')
def donor_logout():
    session.pop('donor_loggedin', None)
    session.pop('donor_id', None)
    session.pop('donor_name', None)
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('donor_login'))

@app.route('/test-supabase')
def test_supabase():
    try:
        result = supabase.table("donors").select("*").limit(1).execute()
        return f"Supabase connected! Data: {result.data}"
    except Exception as e:
        return f"Supabase error: {str(e)}"
# ========== NGO AUTH ==========
@app.route('/ngo-register', methods=['GET', 'POST'])
def ngo_register():
    if request.method == 'POST':
        try:
            ngo_data = {
                "org_name": request.form['org_name'],
                "activity_name": request.form['activity_name'],
                "org_description": request.form['org_description'],
                "contact_person": request.form['contact_person'],
                "contact_designation": request.form['contact_designation'],
                "email": request.form['email'],
                "phone": request.form['phone'],
                "org_address": request.form['org_address'],
                "city": request.form['city'],
                "state": request.form['state'],
                "pincode": request.form['pincode'],
                "website": request.form.get('website', ''),
                "registration_no": request.form['registration_no'],
                "registration_date": request.form['registration_date'],
                "certificate_80g": request.form.get('certificate_80g', ''),
                "account_holder": request.form['account_holder'],
                "account_number": request.form['account_number'],
                "bank_name": request.form['bank_name'],
                "branch_name": request.form['branch_name'],
                "ifsc_code": request.form['ifsc_code'].upper(),
                "branch_city": request.form['branch_city'],
                "password": request.form['password'],
                "status": "approved"
            }

            # Check if email exists
            existing = supabase.table("ngos").select("*").eq("email", ngo_data["email"]).execute()
            if existing.data:
                flash('NGO with this email already exists!', 'error')
                return redirect(url_for('ngo_register'))

            # Insert NGO
            ngo_result = supabase.table("ngos").insert(ngo_data).execute()
            ngo_id = ngo_result.data[0]['id']

            # Create Admin staff
            supabase.table("ngo_staff").insert({
                "ngo_id": ngo_id,
                "name": f"{ngo_data['contact_person']} (Admin)",
                "email": ngo_data['email'],
                "password": ngo_data['password'],
                "role": "admin"
            }).execute()

            # Create Accountant staff
            supabase.table("ngo_staff").insert({
                "ngo_id": ngo_id,
                "name": f"{ngo_data['contact_person']} (Accountant)",
                "email": ngo_data['email'],
                "password": ngo_data['password'],
                "role": "accountant"
            }).execute()

            flash('NGO registered successfully!', 'success')
            return redirect(url_for('ngo_login'))

        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'error')

    return render_template('ngo-register.html')


@app.route('/ngo-login', methods=['GET', 'POST'])
def ngo_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        # Get staff member
        staff_result = supabase.table("ngo_staff").select("*").eq("email", email).eq("password", password).eq("role",
                                                                                                              role).execute()

        if staff_result.data:
            staff = staff_result.data[0]

            # Get NGO info
            ngo_result = supabase.table("ngos").select("*").eq("id", staff['ngo_id']).execute()
            ngo = ngo_result.data[0] if ngo_result.data else None

            session['loggedin'] = True
            session['staff_id'] = staff['id']
            session['staff_name'] = staff['name']
            session['user_role'] = staff['role']
            session['ngo_id'] = staff['ngo_id']
            session['ngo_name'] = ngo['org_name'] if ngo else 'Unknown'

            flash(f'{role.capitalize()} login successful!', 'success')

            if role == 'admin':
                return redirect(url_for('ngo_admin_dashboard'))
            else:
                return redirect(url_for('ngo_accountant_dashboard'))
        else:
            flash('Invalid email, password or role mismatch!', 'error')

    return render_template('ngo-login.html')


@app.route('/ngo-logout')
def ngo_logout():
    session.pop('loggedin', None)
    session.pop('staff_id', None)
    session.pop('staff_name', None)
    session.pop('user_role', None)
    session.pop('ngo_id', None)
    session.pop('ngo_name', None)
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('ngo_login'))


# ========== DONOR DASHBOARD ==========
from datetime import datetime


@app.route('/make_donation', methods=['POST'])
def make_donation():
    if 'donor_loggedin' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('donor_login'))

    try:
        ngo_id = request.form.get('ngo_id')
        amount = float(request.form.get('amount', 0))
        donation_type = request.form.get('donation_type', 'one-time')
        payment_method = request.form.get('payment_method', 'upi')
        donation_date = request.form.get('donation_date')
        message = request.form.get('message', '')

        if not ngo_id:
            flash('Please select an NGO!', 'error')
            return redirect(url_for('donor_dashboard'))

        if amount < 100:
            flash('Minimum donation amount is ₹100!', 'error')
            return redirect(url_for('donor_dashboard'))

        donation_data = {
            "donor_id": session['donor_id'],
            "ngo_id": ngo_id,
            "amount": amount,
            "donation_type": donation_type,
            "payment_method": payment_method,
            "donation_date": donation_date if donation_date else datetime.now().strftime('%Y-%m-%d'),
            "message": message,
            "status": "Pending"
        }

        result = supabase.table("donations").insert(donation_data).execute()

        if result.data:
            donation_id = result.data[0]['id']
            flash('Donation created! Please complete payment.', 'success')
            return redirect(url_for('payment_qr', donation_id=donation_id))
        else:
            flash('Failed to create donation!', 'error')

    except Exception as e:
        print(f"Donation error: {str(e)}")
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('donor_dashboard'))

    print(f"=== AMOUNT CHECK ===")
    print(f"Amount before insert: {amount}")

    result = supabase.table("donations").insert(donation_data).execute()

    print(f"Amount in database: {result.data[0]['amount']}")

    if amount != result.data[0]['amount']:
        print(f"❌ DATABASE CHANGED AMOUNT from {amount} to {result.data[0]['amount']}")
    else:
        print(f"✅ Amount unchanged: {amount}")
@app.route('/confirm_payment/<donation_id>', methods=['POST'])
def confirm_payment(donation_id):
    try:
        result = supabase.table("donations").update({
            "status": "Completed"
        }).eq("id", donation_id).execute()

        if result.data:
            flash('✅ Payment confirmed! Thank you for your donation.', 'success')
        else:
            flash('Error confirming payment!', 'error')

    except Exception as e:
        print(f"Confirm error: {str(e)}")
        flash('Error processing payment!', 'error')

    return redirect(url_for('donor_dashboard'))


@app.route('/donor-dashboard')
def donor_dashboard():
    if 'donor_loggedin' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('donor_login'))

    # Get donor info
    donor_result = supabase.table("donors").select("*").eq("id", session['donor_id']).execute()
    donor = donor_result.data[0] if donor_result.data else None

    # Get NGOs
    ngos_result = supabase.table("ngos").select("*").eq("status", "approved").execute()
    ngos = ngos_result.data

    # Get donation history - SIMPLE SELECT, NO JOIN
    donations_result = supabase.table("donations").select("*").eq("donor_id", session['donor_id']).order(
        "donation_date", desc=True).execute()

    # Manually add NGO names
    donations = []
    for donation in donations_result.data:
        # Get NGO name separately
        ngo_info = supabase.table("ngos").select("org_name").eq("id", donation['ngo_id']).execute()
        donation['ngo_name'] = ngo_info.data[0]['org_name'] if ngo_info.data else 'Unknown'
        donations.append(donation)

    # Calculate totals
    total_donated = sum(d.get('amount', 0) for d in donations if d.get('status') == 'Completed')
    ngos_supported = len(set(d.get('ngo_id') for d in donations))
    tax_benefits = total_donated * 0.3

    return render_template('donor-dashboard.html',
                           donor=donor,
                           ngos=ngos,
                           donations=donations,
                           total_donated=total_donated,
                           ngos_supported=ngos_supported,
                           tax_benefits=tax_benefits)


@app.route('/payment_qr/<donation_id>')
def payment_qr(donation_id):
    try:
        # Get donation
        donation_result = supabase.table("donations").select("*").eq("id", donation_id).execute()

        if donation_result.data:
            donation = donation_result.data[0]
            # Get NGO name separately
            ngo_result = supabase.table("ngos").select("org_name").eq("id", donation['ngo_id']).execute()
            donation['ngo_name'] = ngo_result.data[0]['org_name'] if ngo_result.data else 'Unknown'
            return render_template('payment_qr.html', donation=donation)
        else:
            flash('Donation not found!', 'error')
            return redirect(url_for('donor_dashboard'))

    except Exception as e:
        print(f"Payment QR error: {str(e)}")
        flash('Error loading payment page!', 'error')
        return redirect(url_for('donor_dashboard'))


# ========== RECEIPTS ==========
@app.route('/download-receipts')
def download_receipts():
    if 'donor_loggedin' not in session:
        return redirect(url_for('donor_login'))

    # Get donations - NO JOIN
    donations_result = supabase.table("donations").select("*").eq("donor_id", session['donor_id']).order(
        "donation_date", desc=True).execute()

    # Add NGO names manually
    receipts = []
    for donation in donations_result.data:
        ngo_result = supabase.table("ngos").select("org_name").eq("id", donation['ngo_id']).execute()
        donation['ngo_name'] = ngo_result.data[0]['org_name'] if ngo_result.data else 'Unknown'
        receipts.append(donation)

    return render_template('download-receipts.html', receipts=receipts)


@app.route('/download-receipt/<donation_id>')
def download_receipt(donation_id):
    if 'donor_loggedin' not in session:
        return redirect(url_for('donor_login'))

    try:
        # Get donation - NO JOIN
        donation_result = supabase.table("donations").select("*").eq("id", donation_id).eq("donor_id", session[
            'donor_id']).execute()

        if not donation_result.data:
            return "Donation not found", 404

        donation = donation_result.data[0]

        # Get NGO details separately
        ngo_result = supabase.table("ngos").select("*").eq("id", donation['ngo_id']).execute()
        ngo = ngo_result.data[0] if ngo_result.data else {}

        # Get donor details separately
        donor_result = supabase.table("donors").select("*").eq("id", donation['donor_id']).execute()
        donor = donor_result.data[0] if donor_result.data else {}

        # Generate PDF
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.setTitle("Donation Receipt")

        # Title
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawCentredString(300, 800, "DONATION RECEIPT")

        pdf.setFont("Helvetica", 12)
        y = 770

        # NGO Details
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "NGO Details:")
        pdf.setFont("Helvetica", 12)
        y -= 20
        pdf.drawString(60, y, f"Name: {ngo.get('org_name', 'N/A')}")
        y -= 15
        pdf.drawString(60, y, f"Address: {ngo.get('org_address', 'N/A')}")
        y -= 15
        pdf.drawString(60, y, f"Registration No: {ngo.get('registration_no', 'N/A')}")

        # Donor Details
        y -= 30
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "Donor Details:")
        pdf.setFont("Helvetica", 12)
        y -= 15
        pdf.drawString(60, y, f"Name: {donor.get('fullname', 'N/A')}")
        y -= 15
        pdf.drawString(60, y, f"Address: {donor.get('address', 'N/A')}")
        y -= 15
        pdf.drawString(60, y, f"PAN: {donor.get('pan_no', 'N/A')}")

        # Donation Details
        y -= 30
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "Donation Details:")
        pdf.setFont("Helvetica", 12)
        y -= 20
        pdf.drawString(60, y, f"Amount: ₹{donation.get('amount', 0)}")
        y -= 15
        pdf.drawString(60, y, f"Type: {donation.get('donation_type', 'N/A')}")
        y -= 15
        pdf.drawString(60, y, f"Date: {donation.get('donation_date', 'N/A')}")
        y -= 15
        pdf.drawString(60, y, f"Status: {donation.get('status', 'N/A')}")

        # Footer
        y -= 40
        pdf.setFont("Helvetica-Oblique", 12)
        pdf.drawString(50, y, "We sincerely thank you for your generous contribution.")
        y -= 15
        pdf.drawString(50, y, "This receipt serves as an official acknowledgment of your donation.")

        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        filename = f"Receipt_{donation_id}.pdf"
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')

    except Exception as e:
        print(f"Download receipt error: {str(e)}")
        return f"Error generating receipt: {str(e)}", 500


@app.route('/donation-history')
def donation_history():
    if 'donor_loggedin' not in session:
        flash('Please login first!', 'error')
        return redirect(url_for('donor_login'))

    # Get donations - NO JOIN
    donations_result = supabase.table("donations").select("*").eq("donor_id", session['donor_id']).order(
        "donation_date", desc=True).execute()

    # Add NGO names manually
    donations = []
    for donation in donations_result.data:
        ngo_result = supabase.table("ngos").select("org_name").eq("id", donation['ngo_id']).execute()
        donation['ngo_name'] = ngo_result.data[0]['org_name'] if ngo_result.data else 'Unknown'
        donations.append(donation)

    return render_template('donation-history.html', donations=donations)


# ========== NGO ADMIN DASHBOARD ==========
@app.route('/ngo-admin-dashboard')
def ngo_admin_dashboard():
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']

    # Get NGO details
    ngo_result = supabase.table("ngos").select("*").eq("id", ngo_id).execute()
    ngo = ngo_result.data[0] if ngo_result.data else None

    # Calculate donation totals
    donations_result = supabase.table("donations").select("amount").eq("ngo_id", ngo_id).eq("status",
                                                                                            "Completed").execute()
    total_donations_received = sum(d.get('amount', 0) for d in donations_result.data)
    donation_count = len(donations_result.data)

    # Calculate budget totals
    budget_result = supabase.table("master_budgets").select("total_amount").eq("ngo_id", ngo_id).execute()
    total_budgeted = sum(b.get('total_amount', 0) for b in budget_result.data)

    # Calculate spent totals
    expenses_result = supabase.table("expenditures").select("amount_spent").eq("ngo_id", ngo_id).execute()
    total_spent = sum(e.get('amount_spent', 0) for e in expenses_result.data)
    expense_count = len(expenses_result.data)

    # Calculate balances
    available_for_budget = total_donations_received - total_budgeted
    remaining_in_budget = total_budgeted - total_spent

    # Get pending requests
    pending_result = supabase.table("budget_requests").select("*, budget_programs(program_name)").eq("ngo_id",
                                                                                                     ngo_id).eq(
        "status", "pending").execute()
    pending_requests = pending_result.data

    # Get recent donations
    recent_result = supabase.table("donations").select("*").eq("ngo_id", ngo_id).eq("status", "Completed").order(
        "donation_date", desc=True).limit(5).execute()
    recent_donations = recent_result.data

    # Add donor names
    for donation in recent_donations:
        donor_result = supabase.table("donors").select("fullname").eq("id", donation['donor_id']).execute()
        donation['donor_name'] = donor_result.data[0]['fullname'] if donor_result.data else 'Unknown'

    return render_template("ngo-admin-dashboard.html",
                           ngo=ngo,
                           total_donations_received=total_donations_received,
                           total_budgeted=total_budgeted,
                           total_spent=total_spent,
                           available_for_budget=available_for_budget,
                           remaining_in_budget=remaining_in_budget,
                           donation_count=donation_count,
                           expense_count=expense_count,
                           pending_requests=pending_requests,
                           recent_donations=recent_donations)


# ========== NGO ACCOUNTANT DASHBOARD ==========
@app.route('/ngo-accountant-dashboard')
def ngo_accountant_dashboard():
    if 'loggedin' not in session or session.get('user_role') != 'accountant':
        flash('Access denied! Accountant login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']
    staff_id = session['staff_id']

    # Get NGO details
    ngo_result = supabase.table("ngos").select("*").eq("id", ngo_id).execute()
    ngo = ngo_result.data[0] if ngo_result.data else None

    # Get my budget requests
    my_result = supabase.table("budget_requests").select("*, budget_programs(program_name)").eq("ngo_id", ngo_id).eq(
        "requested_by", staff_id).order("id", desc=True).execute()
    my_requests = my_result.data

    # FIX: Convert date strings to strings (no strftime needed in template)
    # Your template can just display the date as is
    for req in my_requests:
        if req.get('request_date'):
            # Keep as string, don't convert to datetime
            pass

    # Get expense summary
    expenses_result = supabase.table("expenditures").select("amount_spent").eq("ngo_id", ngo_id).eq("recorded_by",
                                                                                                    staff_id).execute()
    total_spent = sum(e.get('amount_spent', 0) for e in expenses_result.data)

    expense_summary = {
        "total_spent": total_spent,
        "expense_count": len(expenses_result.data)
    }

    return render_template("ngo-accountant-dashboard.html",
                           ngo=ngo,
                           my_requests=my_requests,
                           expense_summary=expense_summary)


# ========== BUDGET MANAGEMENT ==========
@app.route('/admin/create-master-budget', methods=['GET', 'POST'])
def create_master_budget():
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']

    # Calculate available amount from donations
    donations_result = supabase.table("donations").select("amount").eq("ngo_id", ngo_id).eq("status",
                                                                                            "Completed").execute()
    total_donations_received = sum(d.get('amount', 0) for d in donations_result.data)

    budget_result = supabase.table("master_budgets").select("total_amount").eq("ngo_id", ngo_id).execute()
    already_budgeted = sum(b.get('total_amount', 0) for b in budget_result.data)

    available_for_budget = total_donations_received - already_budgeted

    # Block if no funds available
    if available_for_budget <= 0:
        flash(
            f'No funds available! Total donations: ₹{total_donations_received}, Already budgeted: ₹{already_budgeted}',
            'error')
        return redirect(url_for('ngo_admin_dashboard'))

    if request.method == 'POST':
        try:
            budget_name = request.form['budget_name']
            total_amount = float(request.form['total_amount'])
            fiscal_year = request.form['fiscal_year']
            description = request.form['description']

            # Check if enough donations available
            if total_amount > available_for_budget:
                flash(f'Cannot create budget! Only ₹{available_for_budget} available from donations.', 'error')
                return redirect(url_for('create_master_budget'))

            # Insert master budget
            budget_data = {
                "budget_name": budget_name,
                "total_amount": total_amount,
                "fiscal_year": fiscal_year,
                "description": description,
                "created_by": session['staff_id'],
                "ngo_id": ngo_id,
                "status": "active"
            }

            budget_result = supabase.table("master_budgets").insert(budget_data).execute()
            master_budget_id = budget_result.data[0]['id']

            # Insert programs
            programs = request.form.getlist('program_name[]')
            program_amounts = request.form.getlist('program_amount[]')

            total_allocated = 0
            for i in range(len(programs)):
                if programs[i].strip():
                    allocated = float(program_amounts[i])
                    total_allocated += allocated
                    supabase.table("budget_programs").insert({
                        "master_budget_id": master_budget_id,
                        "program_name": programs[i].strip(),
                        "allocated_amount": allocated
                    }).execute()

            flash('Master budget created successfully!', 'success')
            return redirect(url_for('ngo_admin_dashboard'))

        except Exception as e:
            flash(f'Error creating budget: {str(e)}', 'error')

    return render_template('admin/create_master_budget.html',
                           total_donations_received=total_donations_received,
                           already_budgeted=already_budgeted,
                           available_for_budget=available_for_budget)


@app.route('/admin/budget-requests')
def admin_budget_requests():
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']

    # Remove the ngo_staff join
    result = supabase.table("budget_requests").select("*, budget_programs(program_name)").eq("ngo_id", ngo_id).eq(
        "status", "pending").execute()
    pending_requests = result.data

    return render_template('admin/budget_requests.html', requests=pending_requests)


@app.route('/admin/approve-request/<request_id>', methods=['POST'])
def approve_budget_request(request_id):
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    action = request.form.get('action')
    approval_notes = request.form.get('approval_notes', '')

    try:
        # Get the request details
        req_result = supabase.table("budget_requests").select("*").eq("id", request_id).execute()
        if not req_result.data:
            flash('Request not found!', 'error')
            return redirect(url_for('admin_budget_requests'))

        request_data = req_result.data[0]

        if action == 'approve':
            # Full approval
            supabase.table("budget_requests").update({
                "status": "approved",
                "approved_amount": request_data['requested_amount'],
                "approved_by": session['staff_id'],
                "approval_date": datetime.now().date().isoformat(),
                "approval_notes": approval_notes
            }).eq("id", request_id).execute()

            # Deduct from budget_programs allocated_amount
            program_result = supabase.table("budget_programs").select("allocated_amount").eq("id", request_data[
                'program_id']).execute()
            if program_result.data:
                new_allocated = program_result.data[0]['allocated_amount'] - request_data['requested_amount']
                supabase.table("budget_programs").update({
                    "allocated_amount": new_allocated
                }).eq("id", request_data['program_id']).execute()

            flash('Request fully approved! Budget deducted.', 'success')

        elif action == 'partial':
            approved_amount = float(request.form.get('approved_amount', 0))
            supabase.table("budget_requests").update({
                "status": "partially_approved",
                "approved_amount": approved_amount,
                "approved_by": session['staff_id'],
                "approval_date": datetime.now().date().isoformat(),
                "approval_notes": approval_notes
            }).eq("id", request_id).execute()

            # Deduct partial from budget_programs
            program_result = supabase.table("budget_programs").select("allocated_amount").eq("id", request_data[
                'program_id']).execute()
            if program_result.data:
                new_allocated = program_result.data[0]['allocated_amount'] - approved_amount
                supabase.table("budget_programs").update({
                    "allocated_amount": new_allocated
                }).eq("id", request_data['program_id']).execute()

            flash('Request partially approved!', 'success')

        elif action == 'reject':
            supabase.table("budget_requests").update({
                "status": "rejected",
                "approved_amount": 0,
                "approved_by": session['staff_id'],
                "approval_date": datetime.now().date().isoformat(),
                "approval_notes": approval_notes
            }).eq("id", request_id).execute()
            flash('Request rejected!', 'success')

        else:
            flash('Unknown action!', 'error')

    except Exception as e:
        flash(f'Error updating request: {str(e)}', 'error')

    return redirect(url_for('admin_budget_requests'))


@app.route('/accountant/request-funds', methods=['GET', 'POST'])
def request_funds():
    if 'loggedin' not in session or session.get('user_role') != 'accountant':
        flash('Access denied! Accountant login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']

    if request.method == 'POST':
        try:
            program_id = request.form['program_id']
            requested_amount = float(request.form['requested_amount'])
            purpose = request.form['purpose']
            request_date = request.form['request_date']

            # Check against allocated amount
            program_result = supabase.table("budget_programs").select("allocated_amount, program_name").eq("id",
                                                                                                           program_id).execute()
            if program_result.data:
                current_allocated = program_result.data[0]['allocated_amount']
                if requested_amount > current_allocated:
                    flash(f'Requested amount exceeds available amount (₹{current_allocated})!', 'error')
                    return redirect(url_for('request_funds'))

            request_data = {
                "program_id": program_id,
                "requested_by": session['staff_id'],
                "requested_amount": requested_amount,
                "purpose": purpose,
                "request_date": request_date,
                "ngo_id": ngo_id,
                "status": "pending"
            }

            supabase.table("budget_requests").insert(request_data).execute()
            flash('Fund request submitted successfully!', 'success')
            return redirect(url_for('ngo_accountant_dashboard'))

        except Exception as e:
            flash(f'Error submitting request: {str(e)}', 'error')

    # Get available programs with allocated_amount > 0
    programs_result = supabase.table("budget_programs").select("*, master_budgets(budget_name)").gt("allocated_amount",
                                                                                                    0).execute()
    programs = programs_result.data

    return render_template('accountant/request_funds.html', programs=programs)


@app.route('/accountant/approved-requests')
def approved_requests():
    if 'loggedin' not in session or session.get('user_role') != 'accountant':
        flash('Access denied! Accountant login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']
    staff_id = session['staff_id']

    # FIXED: use the correct relationship
    result = supabase.table("budget_requests").select(
        "*, budget_programs(program_name, master_budgets(budget_name))").eq("ngo_id", ngo_id).eq("requested_by",
                                                                                                 staff_id).in_("status",
                                                                                                               [
                                                                                                                   "approved",
                                                                                                                   "partially_approved"]).execute()
    approved_requests = result.data

    return render_template('accountant/approved_requests.html', requests=approved_requests)


# ========== EXPENDITURES ==========
@app.route('/accountant-add-expenditure', methods=['GET', 'POST'])
def accountant_add_expenditure():
    if 'loggedin' not in session or session.get('user_role') != 'accountant':
        flash('Access denied! Accountant login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']
    staff_id = session['staff_id']

    # Get approved budgets with remaining amounts
    budget_result = supabase.table("budget_requests").select("*, budget_programs(program_name)").eq("ngo_id",
                                                                                                    ngo_id).eq(
        "requested_by", staff_id).in_("status", ["approved", "partially_approved"]).execute()

    available_budgets = []
    for budget in budget_result.data:
        program_name = budget['budget_programs']['program_name']

        # Calculate spent amount for this program
        spent_result = supabase.table("expenditures").select("amount_spent").eq("ngo_id", ngo_id).eq("program_name",
                                                                                                     program_name).execute()
        spent = sum(s.get('amount_spent', 0) for s in spent_result.data)
        remaining = budget['approved_amount'] - spent

        if remaining > 0:
            available_budgets.append({
                'program_name': program_name,
                'approved_amount': budget['approved_amount'],
                'remaining_amount': remaining
            })

    if request.method == 'POST':
        try:
            program_name = request.form['program_name']
            amount_spent = float(request.form['amount_spent'])
            spending_date = request.form['spending_date']
            paid_to = request.form['paid_to']
            payment_method = request.form['payment_method']
            location = request.form.get('location', '')
            receipt_number = request.form['receipt_number']
            details = request.form['details']
            notes = request.form.get('notes', '')

            # Find the budget to check remaining amount
            selected_budget = None
            for budget in available_budgets:
                if budget['program_name'] == program_name:
                    selected_budget = budget
                    break

            if not selected_budget:
                flash('Invalid budget selected!', 'error')
                return redirect(url_for('accountant_add_expenditure'))

            # Check remaining amount
            if amount_spent > selected_budget['remaining_amount']:
                flash(f"Amount exceeds remaining budget! Available: ₹{selected_budget['remaining_amount']}", 'error')
                return redirect(url_for('accountant_add_expenditure'))

            # Handle file upload
            receipt_filename = None
            if 'receipt_file' in request.files:
                file = request.files['receipt_file']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    receipt_filename = f"{timestamp}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], receipt_filename)
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file.save(file_path)

            # Insert expenditure
            expenditure_data = {
                "ngo_id": ngo_id,
                "program_name": program_name,
                "amount_spent": amount_spent,
                "spending_date": spending_date,
                "paid_to": paid_to,
                "payment_method": payment_method,
                "location": location,
                "receipt_number": receipt_number,
                "receipt_file": receipt_filename,
                "details": details,
                "notes": notes,
                "recorded_by": staff_id,
                "recorded_at": datetime.now().isoformat()
            }

            supabase.table("expenditures").insert(expenditure_data).execute()
            flash("Expenditure recorded successfully!", "success")
            return redirect(url_for('ngo_accountant_dashboard'))

        except Exception as e:
            flash(f'Error: {str(e)}', 'error')

    return render_template('accountant-add-expenditure.html', available_budgets=available_budgets)


@app.route('/ngo-accountant/expenditures')
def accountant_view_expenditures():
    if 'loggedin' not in session or session.get('user_role') != 'accountant':
        flash('Access denied! Accountant login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']
    staff_id = session['staff_id']

    # Get expenditures
    result = supabase.table("expenditures").select("*").eq("ngo_id", ngo_id).order("spending_date", desc=True).execute()
    expenditures = result.data

    # Get approved budgets for this accountant
    budget_result = supabase.table("budget_requests").select("approved_amount, budget_programs(program_name)").eq(
        "ngo_id", ngo_id).eq("requested_by", staff_id).execute()

    # Create lookup dictionary
    approved_dict = {}
    for b in budget_result.data:
        if b.get('budget_programs') and b['budget_programs'].get('program_name'):
            program = b['budget_programs']['program_name']
            approved_dict[program] = b['approved_amount']

    # Calculate running spent and remaining
    spent_dict = {}
    for exp in expenditures:
        program = exp.get('program_name')
        if program:
            exp['approved_amount'] = approved_dict.get(program, 0)
            spent_dict[program] = spent_dict.get(program, 0) + exp['amount_spent']
            exp['remaining_after'] = exp['approved_amount'] - spent_dict[program]
        else:
            exp['approved_amount'] = 0
            exp['remaining_after'] = 0

    return render_template('view_expenditures.html', expenditures=expenditures, user_role='accountant')


@app.route('/ngo-admin/expenditures')
def admin_view_expenditures():
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']

    # Get expenditures
    result = supabase.table("expenditures").select("*").eq("ngo_id", ngo_id).order("spending_date", desc=True).execute()
    expenditures = result.data

    # Get ALL approved budgets for this NGO
    budget_result = supabase.table("budget_requests").select("approved_amount, budget_programs(program_name)").eq(
        "ngo_id", ngo_id).execute()

    # Create lookup dictionary
    approved_dict = {}
    for b in budget_result.data:
        if b.get('budget_programs') and b['budget_programs'].get('program_name'):
            program = b['budget_programs']['program_name']
            approved_dict[program] = b['approved_amount']

    # Calculate running spent and remaining
    spent_dict = {}
    for exp in expenditures:
        program = exp.get('program_name')
        if program:
            exp['approved_amount'] = approved_dict.get(program, 0)
            spent_dict[program] = spent_dict.get(program, 0) + exp['amount_spent']
            exp['remaining_after'] = exp['approved_amount'] - spent_dict[program]
        else:
            exp['approved_amount'] = 0
            exp['remaining_after'] = 0

        # Add NGO name
        ngo_result = supabase.table("ngos").select("org_name").eq("id", ngo_id).execute()
        exp['ngo_name'] = ngo_result.data[0]['org_name'] if ngo_result.data else 'Unknown'

    return render_template('view_expenditures.html', expenditures=expenditures, user_role='admin')


# ========== REPORT GENERATION ==========
@app.route('/download-expenditure-report/admin')
def download_expenditure_report_admin():
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']

    # Get expenditures
    result = supabase.table("expenditures").select("*").eq("ngo_id", ngo_id).order("spending_date", desc=True).execute()
    expenditures = result.data

    # Get approved budgets
    budget_result = supabase.table("budget_requests").select("approved_amount, budget_programs(program_name)").eq(
        "ngo_id", ngo_id).execute()

    # Create lookup dictionary
    approved_dict = {}
    for b in budget_result.data:
        if b.get('budget_programs') and b['budget_programs'].get('program_name'):
            approved_dict[b['budget_programs']['program_name']] = b['approved_amount']

    # Calculate remaining
    spent_dict = {}
    for exp in expenditures:
        program = exp.get('program_name')
        if program:
            exp['approved_amount'] = approved_dict.get(program, 0)
            spent_dict[program] = spent_dict.get(program, 0) + exp.get('amount_spent', 0)
            exp['remaining_after'] = exp['approved_amount'] - spent_dict[program]
        else:
            exp['approved_amount'] = 0
            exp['remaining_after'] = 0

    # Generate PDF with data
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    pdf.setTitle("Expenditure Report")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 40, "EXPENDITURE REPORT")
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 65, f"Generated on: {datetime.now().strftime('%d/%m/%Y')}")
    pdf.drawCentredString(width / 2, height - 80, "Role: Admin")

    # Table headers
    y = height - 120
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(30, y, "ID")
    pdf.drawString(80, y, "Program Name")
    pdf.drawString(180, y, "Approved (₹)")
    pdf.drawString(280, y, "Spent (₹)")
    pdf.drawString(380, y, "Remaining (₹)")
    pdf.drawString(480, y, "Spending Date")
    pdf.drawString(580, y, "Paid To")

    y -= 20
    pdf.setFont("Helvetica", 9)

    for exp in expenditures:
        if y < 50:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(30, y, "ID")
            pdf.drawString(80, y, "Program Name")
            pdf.drawString(180, y, "Approved (₹)")
            pdf.drawString(280, y, "Spent (₹)")
            pdf.drawString(380, y, "Remaining (₹)")
            pdf.drawString(480, y, "Spending Date")
            pdf.drawString(580, y, "Paid To")
            y -= 20
            pdf.setFont("Helvetica", 9)

        pdf.drawString(30, y, str(exp.get('id', '-'))[:8])
        pdf.drawString(80, y, (exp.get('program_name', '-') or '-')[:20])
        pdf.drawString(180, y, f"{exp.get('approved_amount', 0):.2f}")
        pdf.drawString(280, y, f"{exp.get('amount_spent', 0):.2f}")
        pdf.drawString(380, y, f"{exp.get('remaining_after', 0):.2f}")
        pdf.drawString(480, y, str(exp.get('spending_date', '-'))[:10])
        pdf.drawString(580, y, (exp.get('paid_to', '-') or '-')[:20])
        y -= 18

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f"Expenditure_Report_Admin_{datetime.now().strftime('%Y%m%d')}.pdf",
                     mimetype='application/pdf')


@app.route('/download-expenditure-report/accountant')
def download_expenditure_report_accountant():
    if 'loggedin' not in session or session.get('user_role') != 'accountant':
        flash('Access denied! Accountant login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']
    staff_id = session['staff_id']

    # Get expenditures
    result = supabase.table("expenditures").select("*").eq("ngo_id", ngo_id).eq("recorded_by", staff_id).order(
        "spending_date", desc=True).execute()
    expenditures = result.data

    # Get approved budgets for this accountant
    budget_result = supabase.table("budget_requests").select("approved_amount, budget_programs(program_name)").eq(
        "ngo_id", ngo_id).eq("requested_by", staff_id).execute()

    # Create lookup dictionary
    approved_dict = {}
    for b in budget_result.data:
        if b.get('budget_programs') and b['budget_programs'].get('program_name'):
            approved_dict[b['budget_programs']['program_name']] = b['approved_amount']

    # Calculate remaining
    spent_dict = {}
    for exp in expenditures:
        program = exp.get('program_name')
        if program:
            exp['approved_amount'] = approved_dict.get(program, 0)
            spent_dict[program] = spent_dict.get(program, 0) + exp.get('amount_spent', 0)
            exp['remaining_after'] = exp['approved_amount'] - spent_dict[program]
        else:
            exp['approved_amount'] = 0
            exp['remaining_after'] = 0

    # Generate PDF
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    pdf.setTitle("Expenditure Report")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 40, "EXPENDITURE REPORT")
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 65, f"Generated on: {datetime.now().strftime('%d/%m/%Y')}")
    pdf.drawCentredString(width / 2, height - 80, "Role: Accountant")

    # Table headers
    y = height - 120
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(30, y, "ID")
    pdf.drawString(80, y, "Program Name")
    pdf.drawString(180, y, "Approved (₹)")
    pdf.drawString(280, y, "Spent (₹)")
    pdf.drawString(380, y, "Remaining (₹)")
    pdf.drawString(480, y, "Spending Date")
    pdf.drawString(580, y, "Paid To")

    y -= 20
    pdf.setFont("Helvetica", 9)

    for exp in expenditures:
        if y < 50:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(30, y, "ID")
            pdf.drawString(80, y, "Program Name")
            pdf.drawString(180, y, "Approved (₹)")
            pdf.drawString(280, y, "Spent (₹)")
            pdf.drawString(380, y, "Remaining (₹)")
            pdf.drawString(480, y, "Spending Date")
            pdf.drawString(580, y, "Paid To")
            y -= 20
            pdf.setFont("Helvetica", 9)

        pdf.drawString(30, y, str(exp.get('id', '-'))[:8])
        pdf.drawString(80, y, (exp.get('program_name', '-') or '-')[:20])
        pdf.drawString(180, y, f"{exp.get('approved_amount', 0):.2f}")
        pdf.drawString(280, y, f"{exp.get('amount_spent', 0):.2f}")
        pdf.drawString(380, y, f"{exp.get('remaining_after', 0):.2f}")
        pdf.drawString(480, y, str(exp.get('spending_date', '-'))[:10])
        pdf.drawString(580, y, (exp.get('paid_to', '-') or '-')[:20])
        y -= 18

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f"Expenditure_Report_Accountant_{datetime.now().strftime('%Y%m%d')}.pdf",
                     mimetype='application/pdf')


# ========== ADDITIONAL ADMIN ROUTES ==========
@app.route('/admin/all-requests')
def admin_all_requests():
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']

    # FIXED: Use the correct relationship syntax
    result = supabase.table("budget_requests").select(
        "*, budget_programs(program_name), ngo_staff!budget_requests_requested_by_fkey(name)").eq("ngo_id",
                                                                                                  ngo_id).order(
        "request_date", desc=True).execute()

    # Rename the field in the response
    all_requests = []
    for req in result.data:
        if 'ngo_staff' in req:
            req['accountant_name'] = req['ngo_staff']['name']
            del req['ngo_staff']
        all_requests.append(req)

    return render_template('admin/all_requests.html', requests=all_requests)


@app.route('/admin/monthly-consolidated')
def admin_monthly_consolidated():
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']
    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))

    try:
        year, month = selected_month.split('-')
        year = int(year)
        month = int(month)
    except:
        year = datetime.now().year
        month = datetime.now().month

    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)

    # Get monthly donations
    donations_result = supabase.table("donations").select("amount, donation_date, donation_type, donor_id").eq("ngo_id",
                                                                                                               ngo_id).eq(
        "status", "Completed").gte("donation_date", start_date.date().isoformat()).lte("donation_date",
                                                                                       end_date.date().isoformat()).execute()
    total_deposits = sum(d.get('amount', 0) for d in donations_result.data)
    deposit_count = len(donations_result.data)

    # Get monthly expenditures
    expenses_result = supabase.table("expenditures").select(
        "amount_spent, spending_date, program_name, paid_to, details").eq("ngo_id", ngo_id).gte("spending_date",
                                                                                                start_date.date().isoformat()).lte(
        "spending_date", end_date.date().isoformat()).execute()
    total_expenditures = sum(e.get('amount_spent', 0) for e in expenses_result.data)
    expense_count = len(expenses_result.data)

    # Get monthly approvals
    approvals_result = supabase.table("budget_requests").select(
        "approved_amount, approval_date, budget_programs(program_name)").eq("ngo_id", ngo_id).in_("status", ["approved",
                                                                                                             "partially_approved"]).gte(
        "approval_date", start_date.date().isoformat()).lte("approval_date", end_date.date().isoformat()).execute()
    total_approved = sum(a.get('approved_amount', 0) for a in approvals_result.data)
    approval_count = len(approvals_result.data)

    # Build transactions list
    transactions = []

    # Add donations
    for d in donations_result.data:
        # Get donor name
        donor_result = supabase.table("donors").select("fullname").eq("id", d['donor_id']).execute()
        donor_name = donor_result.data[0]['fullname'] if donor_result.data else 'Unknown'

        transactions.append({
            'date': d['donation_date'],
            'type': 'Donation',
            'amount': d['amount'],
            'description': f"From: {donor_name}",
            'category': d['donation_type'],
            'status': 'Completed'
        })

    # Add expenditures
    for e in expenses_result.data:
        transactions.append({
            'date': e['spending_date'],
            'type': 'Expenditure',
            'amount': -e['amount_spent'],  # Negative for expenses
            'description': f"Paid to: {e.get('paid_to', 'Unknown')} - {e.get('details', '')}",
            'category': e.get('program_name', 'General'),
            'status': 'Completed'
        })

    # Add approvals
    for a in approvals_result.data:
        program_name = a.get('budget_programs', {}).get('program_name') if a.get('budget_programs') else 'Unknown'
        transactions.append({
            'date': a['approval_date'],
            'type': 'Budget Approval',
            'amount': a['approved_amount'],
            'description': f"Approved for: {program_name}",
            'category': a.get('status', 'approved'),
            'status': 'Approved'
        })

    # Sort by date
    transactions.sort(key=lambda x: x['date'], reverse=True)

    # Calculate opening balance (simplified)
    opening_balance = 0

    # Get available months for dropdown
    available_months = []

    return render_template('admin/monthly_consolidated.html',
                           selected_month=selected_month,
                           available_months=available_months,
                           opening_balance=opening_balance,
                           total_deposits=total_deposits,
                           total_expenditures=total_expenditures,
                           total_approved=total_approved,
                           available_balance=total_deposits - total_expenditures,
                           remaining_budget=total_approved - total_expenditures,
                           deposit_count=deposit_count,
                           expense_count=expense_count,
                           approval_count=approval_count,
                           transactions=transactions,
                           month_name=start_date.strftime('%B %Y'))


@app.route('/download-consolidated-pdf')
def download_consolidated_pdf():
    if 'loggedin' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin login required.', 'error')
        return redirect(url_for('ngo_login'))

    ngo_id = session['ngo_id']
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))

    try:
        year, month_num = month.split('-')
        year = int(year)
        month_num = int(month_num)
    except:
        year = datetime.now().year
        month_num = datetime.now().month

    start_date = datetime(year, month_num, 1)
    if month_num == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month_num + 1, 1) - timedelta(days=1)

    # Get monthly donations
    donations_result = supabase.table("donations").select("amount, donation_date, donation_type, donor_id").eq("ngo_id",
                                                                                                               ngo_id).eq(
        "status", "Completed").gte("donation_date", start_date.date().isoformat()).lte("donation_date",
                                                                                       end_date.date().isoformat()).execute()
    total_deposits = sum(d.get('amount', 0) for d in donations_result.data)
    deposit_count = len(donations_result.data)

    # Get monthly expenditures
    expenses_result = supabase.table("expenditures").select(
        "amount_spent, spending_date, program_name, paid_to, details").eq("ngo_id", ngo_id).gte("spending_date",
                                                                                                start_date.date().isoformat()).lte(
        "spending_date", end_date.date().isoformat()).execute()
    total_expenditures = sum(e.get('amount_spent', 0) for e in expenses_result.data)
    expense_count = len(expenses_result.data)

    # Get monthly approvals
    approvals_result = supabase.table("budget_requests").select(
        "approved_amount, approval_date, budget_programs(program_name)").eq("ngo_id", ngo_id).in_("status", ["approved",
                                                                                                             "partially_approved"]).gte(
        "approval_date", start_date.date().isoformat()).lte("approval_date", end_date.date().isoformat()).execute()
    total_approved = sum(a.get('approved_amount', 0) for a in approvals_result.data)
    approval_count = len(approvals_result.data)

    # Build transactions list
    transactions = []

    # Add donations
    for d in donations_result.data:
        donor_result = supabase.table("donors").select("fullname").eq("id", d['donor_id']).execute()
        donor_name = donor_result.data[0]['fullname'] if donor_result.data else 'Unknown'

        transactions.append({
            'date': d['donation_date'],
            'type': 'Donation',
            'amount': d['amount'],
            'description': f"From: {donor_name}",
            'category': d['donation_type']
        })

    # Add expenditures
    for e in expenses_result.data:
        transactions.append({
            'date': e['spending_date'],
            'type': 'Expenditure',
            'amount': e['amount_spent'],
            'description': f"Paid to: {e.get('paid_to', 'Unknown')}",
            'category': e.get('program_name', 'General')
        })

    # Add approvals
    for a in approvals_result.data:
        program_name = a.get('budget_programs', {}).get('program_name') if a.get('budget_programs') else 'Unknown'
        transactions.append({
            'date': a['approval_date'],
            'type': 'Budget Approval',
            'amount': a['approved_amount'],
            'description': f"Approved for: {program_name}",
            'category': 'Budget'
        })

    # Sort by date
    transactions.sort(key=lambda x: x['date'])

    # Generate PDF
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Title
    pdf.setTitle("Consolidated Report")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 40, "MONTHLY CONSOLIDATED REPORT")
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 65, f"Month: {start_date.strftime('%B %Y')}")
    pdf.drawCentredString(width / 2, height - 80, f"Generated on: {datetime.now().strftime('%d/%m/%Y')}")

    # Summary Section
    y = height - 120
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Financial Summary")
    y -= 25

    pdf.setFont("Helvetica", 10)
    pdf.drawString(70, y, f"Opening Balance: ₹0.00")
    pdf.drawString(300, y, f"Total Deposits: ₹{total_deposits:,.2f} ({deposit_count} transactions)")
    y -= 18
    pdf.drawString(70, y, f"Total Expenditures: ₹{total_expenditures:,.2f} ({expense_count} expenses)")
    pdf.drawString(300, y, f"Total Approved: ₹{total_approved:,.2f} ({approval_count} approvals)")
    y -= 18
    pdf.drawString(70, y, f"Closing Balance: ₹{total_deposits - total_expenditures:,.2f}")
    pdf.drawString(300, y, f"Remaining Budget: ₹{total_approved - total_expenditures:,.2f}")

    # Transactions Table
    y -= 40
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Transaction Details")
    y -= 20

    # Table Headers
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(50, y, "Date")
    pdf.drawString(130, y, "Type")
    pdf.drawString(210, y, "Amount (₹)")
    pdf.drawString(310, y, "Description")
    pdf.drawString(510, y, "Category")

    y -= 15
    pdf.setFont("Helvetica", 8)

    for trans in transactions:
        if y < 50:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(50, y, "Date")
            pdf.drawString(130, y, "Type")
            pdf.drawString(210, y, "Amount (₹)")
            pdf.drawString(310, y, "Description")
            pdf.drawString(510, y, "Category")
            y -= 15
            pdf.setFont("Helvetica", 8)

        # Format date
        date_str = trans['date'][:10] if trans['date'] else 'N/A'

        # Format amount with color indication (red for expenses)
        amount_str = f"₹{trans['amount']:,.2f}"

        pdf.drawString(50, y, date_str)
        pdf.drawString(130, y, trans['type'])
        pdf.drawString(210, y, amount_str)

        # Truncate description if too long
        desc = trans['description'][:35] if len(trans['description']) > 35 else trans['description']
        pdf.drawString(310, y, desc)

        category = trans['category'][:20] if len(trans['category']) > 20 else trans['category']
        pdf.drawString(510, y, category)

        y -= 15

    # Footer
    pdf.setFont("Helvetica", 8)
    pdf.drawString(50, 30, f"This report is computer generated and does not require signature.")
    pdf.drawRightString(width - 50, 30, f"Page 1")

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"Consolidated_Report_{month}.pdf",
                     mimetype='application/pdf')


# ========== RUN APP ==========
if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000, debug=True)