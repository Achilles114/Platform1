from flask import render_template,request,flash,redirect,url_for,session,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from app import app
from models import db,User,Campaign,Advertisment,Ad_request,RequestStatus,Negotiation
from datetime import datetime

def auth_req(f):        
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def sponsor_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please Login')
            return redirect(url_for('login'))
        user=User.query.get(session['user_id'])
        if user.role!='S':
            flash('you are not authorized')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
        

def admin_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to login first")
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user:
            session.pop('user_id')
            return redirect(url_for('login'))
        if not user.is_admin:
            flash("You are not authorized to visit this page")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')

def home():
    return render_template('index.html')

@app.route('/sponsor')
@sponsor_req
def sponsor():
    
    user=User.query.get(session['user_id'])
    users=User.query.all()
    campaigns = Campaign.query.filter_by(sponsor_id=user.id).all()
    ad_request = Ad_request.query.filter_by(sent_to=user.id).all()
    negotiation=Negotiation.query.filter_by().all()

    
    return render_template('sponsor.html',user=user,campaigns=campaigns,ad_request=ad_request,users=users,negotiation=negotiation)

@app.route('/admin')
@admin_req
def admin():
    
    user = User.query.all()
    campaign=Campaign.query.all()
    requests=Ad_request.query.all()
    return render_template('/admin/admin.html',user=user,campaign=campaign,requests=requests)

@app.route('/influencer')
@auth_req
def influencer():
    user = User.query.get(session['user_id'])
    ad_request = Ad_request.query.filter_by(sent_to=user.id).all()
    
    advertisment = Advertisment.query.all()
    request_rec = [req.advertisment_id for req in ad_request]
    
      # Filter ad requests by sent_to
    return render_template('influencer.html', user=user, ad_request=ad_request,advertisment=advertisment,request_rec=request_rec)



@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username=request.form.get('username')
    password=request.form.get('password')
    user=User.query.filter_by(username=username).first()
    campaigns=Campaign.query.all()
    if username == " " or password == " ":
        flash('username or password could not be empty')
        return redirect(url_for('login'))
    if not user:
        flash('User not found')
        return redirect (url_for('login'))
    if not user.check_password(password):
        flash('Incorrect Password')
        return redirect(url_for('login'))
    # login successful
    session['user_id']=user.id
    if user.is_admin:
        return redirect(url_for('admin'))
    if user.role=='S':
        return redirect(url_for('sponsor'))
    if user.role=='I':
        return redirect(url_for('influencer'))


@app.route('/influencer_reg')
def influencer_reg():
    return render_template('influencer_reg.html')

@app.route('/influencer_reg', methods=['POST'])
def influencer_reg_post():
    username=request.form.get('username')
    password=request.form.get('password')
    name=request.form.get('name')
    niche=request.form.get('niche')
    if username == " " or password == " ":
        flash('username or password could not be empty')
        return redirect(url_for('influencer_reg'))
    
    if User.query.filter_by(username=username).first():
        flash('User already exists, choose other username')
        return redirect(url_for('influencer_reg'))
    user=User(username=username,password=password,name=name,role='I',niche=niche)
    db.session.add(user)
    db.session.commit()
    flash('User successfuly registered as Influencer')
    return redirect(url_for('login'))


@app.route('/sponsor_reg')
def sponsor_reg():
    return render_template('sponsor_reg.html')

@app.route('/sponsor_reg', methods=['POST'])
def sponsor_reg_post():
    username=request.form.get('username')
    password=request.form.get('password')
    name=request.form.get('name')
    industry=request.form.get('industry')
    if username == " " or password == " ":
        flash('username or password could not be empty')
        return redirect(url_for('sponsor_reg'))
    
    if User.query.filter_by(username=username).first():
        flash('User already exists, choose other username')
        return redirect(url_for('sponsor_reg'))
    user=User(username=username,password=password,name=name,role='S',industry=industry)
    db.session.add(user)
    db.session.commit()
    flash('User successfuly registered as sponsor')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user_id',None)
    return redirect(url_for('login'))



@app.route('/profile')
@auth_req
def profile():
    user=User.query.get(session['user_id'])
    ad_requests = Ad_request.query.filter_by(sent_to=user.id).all()
    return render_template('/user/profile.html', user=user,ad_requests=ad_requests)

@app.route('/profile', methods=['POST'])
@auth_req
def profile_post():
    
    nusername = request.form.get('username')
    password = request.form.get('password')
    npassword = request.form.get('npassword')
    user=User.query.get(session['user_id'])
    
    

    if password != "" and npassword != "":
        if user.check_password( password):
            user.passhash = generate_password_hash(npassword)
            flash("Password changed successfully")
        else:
            flash("Entered current password is incorrect")

    if nusername != user.username and nusername != "":
        quser = User.query.filter_by(username=nusername).first()
        if quser:
            flash("Username is already taken, please choose any other username")
            return redirect(url_for('profile'))
        user.username = nusername
        session['username']=nusername
        flash(f"Username changed to {nusername}")

    db.session.commit()
    return redirect(url_for('profile'))

@app.route('/campaign/add')
@sponsor_req
def add_campaign():
    return render_template('/campaign/add.html',user=User.query.get(session['user_id']))

@app.route('/campaign/add', methods=['POST'])
@sponsor_req
def add_campaign_post():
    user=User.query.get(session['user_id'])
    sponsor_id=user.id
    name=request.form.get('name')
    description=request.form.get('description')
    budget=request.form.get('budget')
    
    start_date = datetime.strptime(request.form.get('start-date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.form.get('end-date'), '%Y-%m-%d')
    visibility=request.form.get('visibility')
    if name=='':
        flash('Name cannot be empty')
        return redirect(url_for('add_campaign'))
    if len(name)>30:
        flash('Name should be less than 30 characters')
        return redirect(url_for('add_campaign'))
    if len(description)> 150:
        flash('Description should not be greater than 150 characters')
        return redirect(url_for('add_campaign'))
    if start_date>end_date:
        flash('Start date should be before end date')
        return redirect(url_for('add_campaign'))
    
    '''if not campaign.start_date<start_date<campaign.end_date or not campaign.start_date<end_date<campaign.end_date:
        flash('Advertisment dates should be within limits of campaign dates')
        return redirect((url_for('add_campaign')))'''
    
    campaign=Campaign(name=name,description=description,sponsor_id=sponsor_id,
                      budget=budget,start_date=start_date,end_date=end_date,visibility=visibility)
    db.session.add(campaign)
    db.session.commit()
    flash('campaign added successfully')
    return redirect(url_for('sponsor',user=user))
       


@app.route('/campaign/<int:campaign_id>/edit')
@sponsor_req
def edit_campaign(campaign_id):
    user=User.query.get(session['user_id'])
    campaign=Campaign.query.all()
    return render_template('/campaign/edit.html',user=user,campaign=campaign)

@app.route('/campaign/<int:campaign_id>/edit', methods=['POST'])
@sponsor_req
def edit_campaign_post(campaign_id):
    user = User.query.get(session['user_id'])
    name = request.form.get('name')
    description = request.form.get('description')
    
    budget=request.form.get('budget')
    
    start_date = datetime.strptime(request.form.get('start-date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.form.get('end-date'), '%Y-%m-%d')
    visibility=request.form.get('visibility')

    if not name:
        flash("Name is mandatory")
        return redirect(url_for('edit_campaign', campaign_id=campaign_id))

    current_campaign = Campaign.query.get(campaign_id)
    campaign = Campaign.query.filter_by(name=name).first()

    if campaign and campaign.id != current_campaign.id:
        flash("Campaign with this name already exists")
        return redirect(url_for('edit_campaign', campaign_id=campaign_id))

    if len(name) > 15:
        flash("Campaign Name cannot be more than 15 characters")
        return redirect(url_for('edit_campaign', campaign_id=campaign_id))

    if len(description) > 250:
        flash("Campaign Description cannot be more than 250 characters")
        return redirect(url_for('edit_campaign', campaign_id=campaign_id))
    
    if start_date>end_date:
        flash('Start date should be before end date')
        return redirect(url_for('edit_campaign'), campaign_id=campaign_id)

    
    current_campaign.name = name
    
    current_campaign.description = description
    
    current_campaign.budget = budget
    current_campaign.visibility = visibility
    current_campaign.start_date = start_date
    current_campaign.end_date = end_date
    db.session.commit()
    flash("Campaign edited Successfully")
    return redirect(url_for('sponsor'))




@app.route('/campaign/<int:campaign_id>/delete')
@sponsor_req
def delete_campaign(campaign_id):
    user=User.query.get(session['user_id'])
    campaign=Campaign.query.get(campaign_id)
    return render_template('/campaign/delete.html',user=user,campaign=campaign)

@app.route('/campaign/<int:campaign_id>/delete',methods=['POST'])
@sponsor_req
def delete_campaign_post(campaign_id):
    user=User.query.get(session['user_id'])
    campaign=Campaign.query.get(campaign_id)
    if not campaign:
        flash('campaign does not exist')
        return redirect(url_for('sponsor'))
    db.session.delete(campaign)
    db.session.commit()
    flash('campaign deleted successfully')
    
    return redirect(url_for('sponsor'))



@app.route('/campaign/<int:campaign_id>/show')
@sponsor_req
def show_campaign(campaign_id):
    user=User.query.get(session['user_id'])
    campaign=Campaign.query.get(campaign_id)
    advertisment=campaign.advertisment
    return render_template('/campaign/show.html',user=user,campaign=campaign,advertisment=advertisment)
    
@app.route('/campaign/<int:campaign_id>/addAdvertisment')
@sponsor_req
def add_advertisment(campaign_id):
    user=User.query.get(session['user_id'])
    campaign=Campaign.query.get(campaign_id)
    
    return render_template('/advertisment/add.html',user=user,campaign=campaign)    

@app.route('/campaign/<int:campaign_id>/addAdvertisment', methods=['POST'])
@sponsor_req
def add_advertisment_post(campaign_id):
    user = User.query.get(session['user_id'])
    campaign = Campaign.query.get(campaign_id)
    name = request.form.get('name')
    description = request.form.get('description')
    budget=float(request.form.get('budget'))
    
    start_date = datetime.strptime(request.form.get('start-date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.form.get('end-date'), '%Y-%m-%d')
    sponsor_id=user.id

    if not name:
        flash('Name cannot be empty')
        return redirect(url_for('add_advertisment', campaign_id=campaign_id))
    if len(name) > 30:
        flash('Name should be less than 30 characters')
        return redirect(url_for('add_advertisment', campaign_id=campaign_id))
    if len(description) > 150:
        flash('Description should not be greater than 150 characters')
        return redirect(url_for('add_advertisment', campaign_id=campaign_id))
    
    if start_date>end_date:
        flash('Start date should be after end date')
        return redirect(url_for('add_advertisment', campaign_id=campaign_id))
    
    if  not campaign.start_date<start_date<campaign.end_date and campaign.start_date<end_date<campaign.end_date:
        flash('Dates should be within limit of campaign date')
        return redirect(url_for('add_advertisment', campaign_id=campaign_id))
    
    total_ad_budget = sum(ad.budget for ad in campaign.advertisment)
    remaining_budget=campaign.budget-total_ad_budget

    if total_ad_budget + budget > campaign.budget:
        flash(f'Total budget of advertisements exceeds the remaining campaign budget amount of {remaining_budget}')
        return redirect(url_for('add_advertisment', campaign_id=campaign_id))

    advertisment = Advertisment(name=name, description=description, campaign_id=campaign_id,sponsor_id=sponsor_id,
                                budget=budget,start_date=start_date,end_date=end_date)
    db.session.add(advertisment)
    db.session.commit()
    flash('Advertisement added successfully')
    return redirect(url_for('show_campaign', campaign_id=campaign_id))

@app.route('/advertisment/<int:advertisment_id>/edit')
@sponsor_req
def edit_advertisment(advertisment_id):
    user=User.query.get(session['user_id'])
    
    advertisment=Advertisment.query.get(advertisment_id)
    
    return render_template('/advertisment/edit.html',user=user,advertisment=advertisment)

@app.route('/advertisment/<int:advertisment_id>/edit', methods=['POST'])
@sponsor_req
def edit_advertisment_post(advertisment_id):
    
    user = User.query.get(session['user_id'])
    name = request.form.get('name')
    description = request.form.get('description')
    budget=float(request.form.get('budget'))
    
    start_date = datetime.strptime(request.form.get('start-date'), '%Y-%m-%d')
    end_date = datetime.strptime(request.form.get('end-date'), '%Y-%m-%d')
    if not name:
        flash("Name is mandatory")
        return redirect(url_for('edit_advertisment', advertisment_id=advertisment_id))

    current_ad = Advertisment.query.get(advertisment_id)
    advertisment = Advertisment.query.filter_by(name=name).first()

    if advertisment and advertisment.id != current_ad.id:
        flash("advertisment with this name already exists")
        return redirect(url_for('edit_advertisment', advertisment_id=advertisment_id))

    if len(name) > 15:
        flash("Advertisment Name cannot be more than 15 characters")
        return redirect(url_for('edit_advertisment', advertisment_id=advertisment_id))

    if len(description) > 250:
        flash("Campaign Description cannot be more than 250 characters")
        return redirect(url_for('edit_advertisment', advertisment_id=advertisment_id))
    
    total_ad_budget = sum(ad.budget for ad in advertisment.campaign.advertisment)

    if total_ad_budget + budget > advertisment.campaign.budget:
        flash('Total budget of advertisements exceeds the campaign budget')
        return redirect(url_for('edit_advertisment', advertisment_id=advertisment_id))
    
    current_ad.name = name
    current_ad.description = description
    current_ad.budget=budget
    current_ad.start_date=start_date
    current_ad.end_date=end_date
    db.session.commit()
    flash("advertisment edited Successfully")
    return redirect(url_for('edit_advertisment', advertisment_id=advertisment_id))

@app.route('/advertisment/<int:advertisment_id>/show')
@auth_req
def show_advertisment(advertisment_id):
    user = User.query.get(session['user_id'])
    users=User.query.all()
    advertisment = Advertisment.query.get(advertisment_id)
    campaign=advertisment.campaign
    
    if user.role=='S':
        return render_template('/advertisment/show.html',user=user,users=users,advertisment=advertisment)
    if user.role=='I':
        return render_template('/advertisment/infshow.html',user=user)




@app.route('/advertisment/<int:advertisment_id>/delete')
@sponsor_req
def delete_advertisment(advertisment_id):
    user=User.query.get(session['user_id'])
    
    advertisment=Advertisment.query.get(advertisment_id)
    
    return render_template('/advertisment/delete.html',user=user,advertisment=advertisment)

@app.route('/advertisment/<int:advertisment_id>/delete', methods=['POST'])
@sponsor_req
def delete_advertisment_post(advertisment_id):
    user = User.query.get(session['user_id'])
    advertisment = Advertisment.query.get(advertisment_id)
    
    
    
    campaign_id = advertisment.campaign_id  
    
    db.session.delete(advertisment)
    db.session.commit()
    flash('Advertisment deleted successfully')
    
    return redirect(url_for('show_campaign', campaign_id=campaign_id))


    


@app.route('/users')
@admin_req
def user_list():
    user=User.query.get(session['user_id'])
    users=User.query.all()
    return render_template('/admin/users.html', user=user,users=users)

@app.route('/campaign')
@admin_req
def campaign_list():
    user=User.query.get(session['user_id'])
    campaigns = Campaign.query.all()
    return render_template('/admin/campaign.html', campaigns=campaigns,user=user)

@app.route('/user/<int:user_id>/delete')
def delete_user(user_id):
    user=User.query.get(user_id)
    
    return render_template('/admin/delete_user.html',user_id=user_id,user=user)

@app.route('/user/<int:user_id>/delete',methods=['Post'])
def delete_user_post(user_id):
    user=User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully')
    return redirect(url_for('admin'))

@app.route('/adminview/<int:campaign_id>')
@admin_req
def admin_view_campaign(campaign_id):
    user = User.query.all()
    campaign = Campaign.query.get(campaign_id)
    advertisment = Advertisment.query.filter_by(campaign_id=campaign_id).all()
    
    return render_template('/admin/view_campaign.html', advertisment=advertisment, user=user, campaign_id=campaign_id)


@app.route('/sponsor/<int:advertisment_id>/sendRequest', methods=['POST'])
def send_request_sponsor(advertisment_id):
    user = User.query.get(session['user_id'])
    users = User.query.all()
    advertisment = Advertisment.query.get(advertisment_id)
    sent_to = request.form.get('sent_to')  
    existing_request = Ad_request.query.filter(
        ((Ad_request.advertisment_id == advertisment_id) &
         (Ad_request.user_id == user.id) &
         (Ad_request.sent_to == sent_to)) |
        ((Ad_request.advertisment_id == advertisment_id) &
         (Ad_request.user_id == sent_to) &
         (Ad_request.sent_to == user.id))
    ).first()

    if existing_request:
        
        if user.role == "I":
            flash(f'This request already exists for {advertisment.name}')
            return redirect(url_for("influencer"))
        if user.role == "S":
            flash(f'This request already exists for this {advertisment.name}')
            return redirect(url_for("sponsor"))

    ad_request = Ad_request(
        advertisment_id=advertisment_id,
        
        user_id=user.id, 
        sent_to=sent_to
    )
    db.session.add(ad_request)
    db.session.commit()
    flash('Request sent','success')
    if user.role=="I":
        return redirect(url_for("influencer"))
    if user.role=="S":
        return redirect(url_for("sponsor"))

@app.route('/accept_request/<int:request_id>', methods=['POST'])
@auth_req
def accept_request(request_id):
    user = User.query.get(session['user_id'])
    ad_request = Ad_request.query.get(request_id)
    if ad_request and ad_request.sent_to == session['user_id']:
        ad_request.status = True  
        db.session.add(RequestStatus(request_id=request_id, action='accept'))
        db.session.commit()
        flash('Request accepted successfully.','success')
    else:
        flash('Request not found or you are not authorized to accept this request.','alert')
    if user.role=="I":
        return redirect(url_for('influencer'))
    elif user.role=="S":
        return redirect(url_for('sponsor'))

@app.route('/reject_request/<int:request_id>', methods=['POST'])
@auth_req
def reject_request(request_id):
    user = User.query.get(session['user_id'])
    ad_request = Ad_request.query.get(request_id)
    if ad_request and ad_request.sent_to == session['user_id']:
        ad_request.status = False  
        db.session.add(RequestStatus(request_id=request_id, action='reject'))
        db.session.commit()
        flash('Request rejected successfully.','danger')
    else:
        flash('Request not found or you are not authorized to reject this request.','alert')
    if user.role=="I":
        return redirect(url_for('influencer'))
    elif user.role=="S":
        return redirect(url_for('sponsor'))

@app.route('/negotiate/<int:request_id>', methods=['GET'])
@auth_req
def negotiate(request_id):
    ad_request=Ad_request.query.get(request_id)
    user = User.query.get(session['user_id'])

    return render_template('/negotiate.html',user=user,ad_request=ad_request)

@app.route('/negotiate/<int:request_id>', methods=['POST'])
@auth_req
def negotiate_post(request_id):
    ad_request = Ad_request.query.get(request_id)
    user = User.query.get(session['user_id'])
    
    proposed_budget = request.form.get('proposed-budget')
    message = request.form.get('message')

    negotiation = Negotiation(
        advertisment_id=ad_request.advertisment_id,
        influencer_id=user.id,
        proposed_budget=proposed_budget,
        message=message
    )
    db.session.add(negotiation)
    db.session.commit()
    
    flash("Payment Negotiation Request sent to Sponsor")  
    return redirect(url_for('influencer'))


@app.route('/accept_negotiation/<int:negotiation_id>', methods=['POST'])
@auth_req
def accept_negotiation(negotiation_id):
    negotiation = Negotiation.query.get(negotiation_id)
    if negotiation:
        advertisment = Advertisment.query.get(negotiation.advertisment_id)
        advertisment.budget = negotiation.proposed_budget
        negotiation.status = 'Accepted'
        db.session.commit()
        flash('Negotiation accepted and budget updated!', 'success')
    else:
        flash('Negotiation not found!', 'danger')

    return redirect(url_for('sponsor'))
@app.route('/reject_negotiation/<int:negotiation_id>', methods=['POST'])
@auth_req
def reject_negotiation(negotiation_id):
    negotiation = Negotiation.query.get(negotiation_id)
    if negotiation:
        negotiation.status = 'Rejected'
        db.session.commit()
        flash('Negotiation rejected!', 'danger')
    else:
        flash('Negotiation not found!', 'danger')

    return " "



@app.route('/search_influencer')
@auth_req
def search_influencer():
    user = User.query.get(session['user_id'])
    query=request.args.get('search')
    campaigns,advertisment,industry=None,None,None
    

    if query:
        campaigns=Campaign.query.filter(Campaign.name.ilike(f'%{query}%')).all()
        advertisment=Advertisment.query.filter(Advertisment.name.ilike(f'%{query}%')).all()
        industry=User.query.filter(User.industry.ilike(f'%{query}%')).all()
    return render_template('search_influencer.html', user=user,query=query, campaigns=campaigns,advertisment=advertisment,industry=industry)


@app.route('/search_sponsor')
@auth_req
def search_sponsor():
    user = User.query.get(session['user_id'])
    query = request.args.get('search')
    influencers = None
    niches = None

    if query:
        
        influencers = User.query.filter(User.name.ilike(f'%{query}%')).all()

        
        niches = User.query.filter(User.niche.ilike(f'%{query}%')).all()

    return render_template('search_sponsor.html', user=user, query=query, influencers=influencers, niches=niches)


@app.route('/flag_user/<int:user_id>', methods=['POST'])
@auth_req
def flag_user(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_admin:  
        if user.flagged:
            user.flagged = False
            flash('User has been unflagged.')
        else:
            user.flagged = True
            
        db.session.commit()
    return redirect(url_for('user_list'))  

@app.route('/chart_data')
def chart_data():
   
    influencers_count = User.query.filter_by(role='I').count()
    sponsors_count = User.query.filter_by(role='S').count()

    
    data = {
        'labels': ['Influencers', 'Sponsors'],
        'values': [influencers_count, sponsors_count]
    }
    
    return jsonify(data)














