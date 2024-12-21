
from app import app
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from datetime import datetime



class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(50),nullable=False)
    passhash=db.Column(db.String(128),nullable=False)
    name=db.Column(db.String(15))
    is_admin=db.Column(db.Boolean,default=False,nullable=False)
    role=db.Column(db.String(10),nullable=True)
    
    niche=db.Column(db.String(15),nullable=True)
    reach=db.Column(db.Integer,nullable=True)
    
    industry=db.Column(db.String(15),nullable=True)
    budget=db.Column(db.Float,nullable=True)

    flagged = db.Column(db.Boolean, default=False)
    
    advertisment = db.relationship('Advertisment', backref='user', lazy=True, cascade='all,delete-orphan')

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self,password):
        self.passhash=generate_password_hash(password)


    def check_password(self,password):
        return check_password_hash(self.passhash,password)



class Campaign(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(30))
    description=db.Column(db.String(150))
    sponsor = db.relationship('User', backref='campaigns')
    sponsor_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    start_date=db.Column(db.DateTime(),nullable=True)
    end_date=db.Column(db.DateTime(),nullable=True)
    budget=db.Column(db.Float,nullable=True)
    
    visibility=db.Column(db.String(10),nullable=True)
    
    advertisment = db.relationship('Advertisment', backref='campaign', lazy=True, cascade='all,delete-orphan')

class Advertisment(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(30))
    description=db.Column(db.String(150))
    campaign_id=db.Column(db.Integer,db.ForeignKey('campaign.id'))
    sponsor_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    budget=db.Column(db.Integer)
    start_date=db.Column(db.DateTime(),nullable=True)
    end_date=db.Column(db.DateTime(),nullable=True)
    ad_request = db.relationship('Ad_request', backref='advertisment', lazy=True, cascade='all,delete-orphan')
    negotiation = db.relationship('Negotiation', backref='advertisment', lazy=True, cascade='all,delete-orphan')

class Ad_request(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    status=db.Column(db.Boolean,nullable=True)
    advertisment_id=db.Column(db.Integer,db.ForeignKey('advertisment.id'))
    
    sent_to=db.Column(db.Integer,db.ForeignKey('user.id'))
    


   
class RequestStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('ad_request.id'))
    action = db.Column(db.String(10))  # 'accept' / 'reject'
    timestamp = db.Column(db.DateTime, default=datetime.now)


class Negotiation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    advertisment_id = db.Column(db.Integer, db.ForeignKey('advertisment.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    proposed_budget = db.Column(db.Float,nullable=True)
    message=db.Column(db.String(100))
    status = db.Column(db.String(20), default='Pending')  # Status can be 'Pending', 'Accepted', 'Rejected'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



with app.app_context():
    db.create_all()
    # create admin if admin doesnt exist
    admin=User.query.filter_by(username='admin').first()
    if not admin:
        psd=generate_password_hash('admin')
        admin=User(username='admin',passhash=psd,name='admin',is_admin=True)
        db.session.add(admin)
        db.session.commit()

