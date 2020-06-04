import os
import base64
from passlib.hash import pbkdf2_sha256
from flask import Flask, render_template, request, redirect, url_for, session

from model import Donation, Donor

app = Flask(__name__)
# add the secret_key to the app, so that we can store infor in the session
# variable.
app.secret_key = os.environ.get("SECRET_KEY").encode()
#app.secret_key = b'\xff\xb6Q\xe3C\xc5\x118\xca\xe2S\x10\xe3\xe7bA]E\xdbm\xd8u9{'

@app.route('/')
def home():
    return redirect(url_for('all'))

@app.route('/donations/')
def all():
    donations = Donation.select()
    return render_template('donations.jinja2', donations=donations)


@app.route('/creating/', methods=['GET', 'POST'])
def create_donation():
    # redirect the user to login page if not logged in.
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":
        try:
            the_donor = Donor.select()\
                             .where(Donor.name == request.form['name'])\
                             .get()
        except Donor.DoesNotExist:
            # solution1: if donor doesn't exist, then re-display the donation
            # creation form and inject a message describing the error.
            #return render_template('create.jinja2',
            #                       error='Donor does not exist.')

            # solution2: if donor doesn't exist, then create a new donor with
            # the given name, along with the indicated donation.
            the_donor = Donor(name=request.form['name'],
                              password=pbkdf2_sha256.hash(request.form['name']))
            the_donor.save()
        Donation(value=request.form['amount'], donor=the_donor).save()
        return redirect(url_for('home'))

    return render_template('create.jinja2')

@app.route('/view_donoation')
def view_donation():
    # redirect the user to login page if not logged in.
    if 'username' not in session:
        return redirect(url_for('login'))

    # NOTE: for 'GET' request, we need to use request.args.get() method
    # to get the data. Because the data is stored in the URL query string.
    # For 'POST' request, we need to use request.form() method.
    if request.args.get('submit_button') == 'submit':
        the_donor = Donor.select()\
                         .where(Donor.name == request.args.get('name'))\
                         .get()
        # NOTE: the 'select()' method return a query and you need to iterate
        # to get each result. By adding get() after select(), it limits
        # the search result to be one result.
        all_donation = Donation.select()\
                               .where(Donation.donor == the_donor)
        return render_template('single_donor.jinja2', donors=Donor.select(),
                               list=True, donor_name=the_donor.name,
                               all_donation=all_donation)

    return render_template('single_donor.jinja2', donors=Donor.select(),
                           list=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # if the request is POST method.
    if request.method == 'POST':
        # if the user name and password are matched with the data in database
        # then send the username to session['username'], and log the user in.
        # and redirect the user to the list of all tasks corresponding to this
        # user.
        # Otherwise, render the login.jinja2 template and include an error
        # message.
        try:
            the_donor = Donor.select().where(Donor.name ==
                                             request.form['username']).get()
        except Donor.DoesNotExist:
            return render_template('login.jinja2',
                                   error='Incorrect username')
        if pbkdf2_sha256.verify(request.form['password'], the_donor.password):
            session['username'] = the_donor.name
            return redirect(url_for('all'))
        return render_template('login.jinja2', error='Incorrect password')

    # if the request is GET method, then just display the login page.
    return render_template('login.jinja2')


@app.route('/logout')
def logout():
    # before logout, we need to make sure the donor was logged in.
    if 'username' not in session:
        return redirect(url_for('login'))
    # log out the donor by clear the session
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 6738))
    app.run(host='0.0.0.0', port=port)
