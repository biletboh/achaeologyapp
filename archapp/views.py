from flask import render_template, request, url_for, flash, redirect
from myapp import app, db 
#from forms import LoginForm
#from flask import session as login_session
from flask.ext.login import LoginManager, UserMixin, login_user, logout_user, current_user
from oauth import OAuthSignIn
from models import Site, User
#import random, string
#from models import Site, OAuthSignIn, FacebookSignIn

#from oauth2client.client import flow_from_clientsecrets
#from oauth2client.client import FlowExchangeError
#from oauth2client.client import AccessTokenCredentials
#import httplib2
#import json
#from flask import make_response
#import requests



#CLIENT_ID = json.loads(
#    open('client_secrets.json', 'r').read())['web']['client_id']
#APPLICATION_NAME = "archaeology app"

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('welcomePage'))

@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous():
        return redirect(url_for('welcomePage'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()

@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous():
        return redirect(url_for('welcomePage'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('welcomePage'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('welcomePage'))

@app.route('/', methods=['GET', 'POST'])
def welcomePage():
    if request.method == 'POST':
        if request.form["name_of_site"]:
            results = request.form["name_of_site"]
            return redirect(url_for('search', query=results)) 
    else:
        return render_template('welcome.html')

@app.route('/new', methods=['GET', 'POST'])
def newSite():
    if request.method == 'POST':
        if request.form.get('name_of_site', None):
            results = request.form['name_of_site']
            return redirect(url_for('search', query=results)) 
        else: 
            TheNewSite = Site(name=request.form['name'], 
                toponim=request.form['toponim'])
#                type_of_site = request.form['type_of_site'])
#                oblast=request.form['oblast'],
#                rajon=request.form['rajon'],
#                punkt=request.form['punkt'],
#                prymitky=request.form['prymitky'],
#                kultnal=request.form['kultnal'],
#                chron=request.form['chron'],
#                nadijnist=request.form['nadijnist'],
#                rozkop=request.form['rozkop'],
#                zvit=request.form['zvit'],
#                publicacii = request.form['publicacii'],
#                kartograph = request.form['kartograph'],
#                coord = request.form['coord'],
#                tochkart = request.form['tochkart'],
#                toppotype = request.form['toppotype'],
#                geomorform = request.form['geomorform'],
#                vysotnadrm = request.form['vysotnadrm'], 
#                ploshch = request.form['ploshch'],
#                dovz = request.form['dovz'],
#                shyr = request.form['shyr'])
#                
            db.session.add(TheNewSite)
            db.session.commit()
            return redirect(url_for('allSites')) 
       # if request.form["name_of_site"]:
       #     results = request.form["name_of_site"]
       #     return redirect(url_for('search', query=results)) 

    else:
        return render_template('newsite.html')


@app.route('/<int:site_id>/', methods = ['GET', 'POST'])
def sitePage(site_id):
    if request.method == 'GET':
        onesite = db.session.query(Site).filter_by(id=site_id).one()

        return render_template('site.html', site=onesite) 
    if request.method == 'POST':
        if request.form["name_of_site"]:
            results = request.form["name_of_site"]
            return redirect(url_for('search', query=results)) 

@app.route('/<int:site_id>/edit/', methods = ['GET', 'POST'])
@app.route('/<int:site_id>/edit/base', methods = ['GET', 'POST'])
def siteEdit(site_id):
    siteToEdit = db.session.query(Site).filter_by(id=site_id).one()
    if request.method == 'POST':
        if request.form["name_of_site"]:
            results = request.form["name_of_site"]
            return redirect(url_for('search', query=results)) 
        if request.form['name']:
            siteToEdit.name = request.form['name']
        if request.form['toponim']:
            siteToEdit.toponim = request.form['toponim']
        if request.form['type_of_site']:
            siteToEdit.type_of_site = request.form['type_of_site']
        if request.form['oblast']:
            siteToEdit.oblast = request.form['oblast']
        if request.form['rajon']:
            siteToEdit.rajon = request.form['rajon']
        if request.form['punkt']:
            siteToEdit.punkt = request.form['punkt']
        if request.form['prymitky']:
            siteToEdit.prymitky = request.form['prymitky']
        if request.form['kultnal']:
            siteToEdit.kultnal = request.form['kultnal']
        if request.form['chron']:
            siteToEdit.chron = request.form['chron']
        if request.form['nadijnist']:
            siteToEdit.nadijnist = request.form['nadijnist']
        if request.form['rozkop']:
            siteToEdit.rozkop = request.form['rozkop']
        if request.form['zvit']:
            siteToEdit.zvit = request.form['zvit']
        if request.form['publicacii']:
            siteToEdit.publicacii = request.form['publicacii']
        if request.form['kartograph']:
            siteToEdit.kartograph = request.form['kartograph']
        if request.form['coord']:
            siteToEdit.coord = request.form['coord']
        if request.form['tochkart']:
            siteToEdit.tochkart = request.form['tochkart']
        if request.form['toppotype']:
            siteToEdit.toppotype = request.form['toppotype']
        if request.form['geomorform']:
            siteToEdit.geomorform = request.form['geomorform']
        if request.form['vysotnadrm']:
            siteToEdit.vysotnadrm = request.form['vysotnadrm']
        if request.form['ploshch']:
            siteToEdit.ploshch = request.form['ploshch']
        if request.form['dovz']:
            siteToEdit.dovz = request.form['dovz']
        if request.form['shyr']:
            siteToEdit.shyr = request.form['shyr']

        db.session.add(siteToEdit)
        db.session.commit()
        return redirect(url_for('sitePage', site_id=site_id))

    else:
        return render_template('edit.html', site=siteToEdit)

@app.route('/<int:site_id>/delete/', methods=['GET', 'POST'])
def siteDelete(site_id):
    siteToDelete = db.session.query(Site).filter_by(id=site_id).one()
    if request.method == 'POST':
        if request.form["name_of_site"]:
            results = request.form["name_of_site"]
            return redirect(url_for('search', query=results)) 
        db.session.delete(siteToDelete)
        db.session.commit
        return redirect(url_for('welcomePage'))
    else:
        return render_template('delete.html', site=siteToDelete)

@app.route('/all/', methods=['GET', 'POST'])
def allSites():
    if request.method == 'POST':
        if request.form["name_of_site"]:
            results = request.form["name_of_site"]
            return redirect(url_for('search', query=results)) 
    else:
        sites = db.session.query(Site).all()
        return render_template('all.html', sites=sites)


@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for OpenID="%s", remember_me=%s' % 
                (form.openid.data, str(form.remember_me.data)))
        return redirect(url_for('welcome'))
    return render_template('login.html', title="Sign in", form=form)

@app.route('/search/<query>', methods=['GET', 'POST'])
def search(query):
    if request.method == 'POST':
        if request.form["name_of_site"]:
            results = request.form["name_of_site"]
            return redirect(url_for('search', query=results)) 
    else:
        results = Site.query.whoosh_search(query).all()
        return render_template('search.html', results=results)

