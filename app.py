#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy, Column
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
  __tablename__ = 'Venues'
  id = Column(db.Integer, primary_key=True)
  name = Column(db.String)
  city = Column(db.String(120))
  state = Column(db.String(120))
  address = Column(db.String(120))
  phone = Column(db.String(120))
  image_link = Column(db.String(500))
  facebook_link = Column(db.String(120))
  venue_web_url = Column(db.String(120))
  talent_description = Column(db.String(255))
  seeking_talent = Column(db.Boolean, default=False)
  shows = db.relationship("Show", backref="Venue", lazy=True)

class Artist(db.Model):
  __tablename__ = 'Artists'
  id = Column(db.Integer, primary_key=True)
  name = Column(db.String)
  city = Column(db.String(120))
  state = Column(db.String(120))
  phone = Column(db.String(120))
  genres = Column(db.String(120))
  image_link = Column(db.String(500))
  facebook_link = Column(db.String(120))
  artist_web_url = Column(db.String(120))
  artist_talent_description = Column(db.String(255))
  artist_seeking_talent = Column(db.Boolean, default=False)


class Show(db.Model):
  __tablename__ = 'Shows'
  id = Column(db.Integer, primary_key=True)
  artist_id = Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
  venue_id = Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
  start_time = Column(db.DateTime, nullable=False)

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.order_by(Venue.state, Venue.city).all()
  venue_data = []
  temp_data  = {}

  city = None
  state = None

  for item in venues:
    single_venue = {
      'id': item['id'],
      'name': item['name'],
      'future_show_count': len(list(filter(lambda x: x.start_time > datetime.today(), item['shows'])))
    }

    if item['city'] == city and item['state'] == state:
      temp_data['venue'].append(single_venue)
    else:
      if city is not None:
        venue_data.append(temp_data)
      temp_data['city'] = item['city']
      temp_data['state'] = item['state']
      temp_data['venue'] = [single_venue]
    city = item['city']
    state = item['state']
  venue_data.append(temp_data)
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  # data=[{
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "venues": [{
  #     "id": 1,
  #     "name": "The Musical Hop",
  #     "num_upcoming_shows": 0,
  #   }, {
  #     "id": 3,
  #     "name": "Park Square Live Music & Coffee",
  #     "num_upcoming_shows": 1,
  #   }]
  # }, {
  #   "city": "New York",
  #   "state": "NY",
  #   "venues": [{
  #     "id": 2,
  #     "name": "The Dueling Pianos Bar",
  #     "num_upcoming_shows": 0,
  #   }]
  # }]
  return render_template('pages/venues.html', areas=venue_data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_query = request.form.get('search_term', '')
  result = Venue.query.filter(Venue.name.ilike(f'%{search_query}%')).all()
  query_data = []

  for item in result:
    query_data.append({
      'id': item['id'],
      'name': item['name'],
      'future_show_count': len(db.session.query(Show).filter(Show.venue_id ==item.id).filter(Show.start_time > datetime.now()).all())
    })
  response={
    "count": len(result),
    "data": query_data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  # previous_show = list(filter(lambda x: x.start_time < datetime.today(), venue.shows))
  # future_shows = list(filter(lambda x: x.start_time >= datetime.today(), venue.shows))

  future_shows = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  future_shows_array = []

  previous_show = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  previous_show_array = []

  for show in previous_show:
    previous_show_array.append({
      "artist_id": show['artist_id'],
      "artist_name": show['artist'].name,
      "artist_image_link": show['artist'].image_link,
      "start_time": show['start_time'].strftime('%Y-%m-%d %H:%M:%S')
    })

  for show in future_shows:
    future_shows_array.append({
      "artist_id": show['artist_id'],
      "artist_name": show['artist'].name,
      "artist_image_link": show['artist'].image_link,
      "start_time": show['start_time'].strftime("%Y-%m-%d %H:%M:%S")    
    })
  venue_data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": previous_show_array,
    "upcoming_shows": future_shows_array,
    "past_shows_count": len(previous_show_array),
    "upcoming_shows_count": len(future_shows_array),
  }

  return render_template('pages/show_venue.html', venue=venue_data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()

  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  error = False
  try:
    venue = Venue()
    venue['name'] = request.form['name']
    venue['city'] = request.form['city']
    venue['state'] = request.form['state']
    venue['address'] = request.form['address']
    venue['phone'] = request.form['phone']
    tmp_genres = request.form.getlist('genres')
    venue['genres'] = ','.join(tmp_genres)
    venue['facebook_link'] = request.form['facebook_link']
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
    if error:
        flash('ooopps, an error occured. Venue ' +
              request.form['name'] + ' Could not be listed!')
    else:
        flash('Venue ' + request.form['name'] +  ' was successfully listed!')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    delete = Venue.query.get(venue_id)
    db.session.delete(delete)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error: 
    flash(f'oopps, an error occurred. Venue {venue_id} could not be deleted.')
  if not error: 
    flash(f'Venue {venue_id} was successfully deleted.')
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.all()
  
  return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_query = request.form.get('search_term', '')
  artist_result = Artist.query.filter(Artist.name.ilike(f'%{search_query}%')).all()
  Artist_data = []


  for item in artist_result:
    Artist_data.append({
      'id': item['id'],
      'name': item['name'],
      'total_upcoming_shows': Show.query.filter(Show.id == item['id']).filter(Show.start_time > datetime.now()).all(),
    })

  response={
    "count": len(artist_result),
    "data": Artist_data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id

  artist = Artist.query.get(artist_id)

  artist_data = artist.to_dict()
  previous_shows = list(filter(lambda x: x.start_time < datetime.today(), artist.shows))
  future_shows = list(filter(lambda x: x.start_time >= datetime.today(), artist.shows))
  
  previous_shows = list(map(lambda x: x.show_venue(), previous_shows))
  future_shows = list(map(lambda x: x.show_venue(), future_shows))

  artist_data['previous_shows'] = previous_shows
  artist_data['future_shows'] = future_shows
  artist_data['previous_shows_count'] = len(previous_shows)
  artist_data['future_shows_count'] = len(future_shows)
  
  return render_template('pages/show_artist.html', artist=artist_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist= Artist.query.get(artist_id)
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue={
    "id": 1,
    "name": "The Musical Hop",
    "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    "address": "1015 Folsom Street",
    "city": "San Francisco",
    "state": "CA",
    "phone": "123-123-1234",
    "website": "https://www.themusicalhop.com",
    "facebook_link": "https://www.facebook.com/TheMusicalHop",
    "seeking_talent": True,
    "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60"
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
      artist = Artist.query.get(artist_id)
      artist['name'] = request.form['name']
      artist['city'] = request.form['city']
      artist['state'] = request.form['state']
      artist['phone'] = request.form['phone']
      tmp_genres = request.form.getlist('genres')
      artist['genres'] = ','.join(tmp_genres)
      artist['website'] = request.form['website']
      artist['image_link'] = request.form['image_link']
      artist['facebook_link'] = request.form['facebook_link']
      artist['seeking_description'] = request.form['seeking_description']
      db.session.add(artist)
      db.session.commit()
  except:
      error = True
      db.session.rollback()
  finally:
      db.session.close()
      if error:
          return redirect(url_for('server_error'))
      else:
          flash('Artist ' + request.form['name'] + ' was successfully listed!')
          return redirect(url_for('show_artist', artist_id=artist_id))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  show_data = []
  shows = Show.query.all()
  
  for show in shows:
      show_data.append({
          "venue_id": show['venue'].id,
          "venue_name": show['venue'].name,
          "artist_id": show['artist'].id,
          "artist_name": show['artist'].name,
          "artist_image_link": show['artist'].image_link,
          "start_time": format_datetime(str(show.start_time))
      })
  return render_template('pages/shows.html', shows=show_data)

@app.route('/shows/create', methods=['GET'])
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  artist_id = request.form['artist_id']
  venue_id = request.form['venue_id']
  start_time = request.form['start_time']
  
  try:
      new_show = Show(start_time=start_time, artist_id=artist_id, venue_id=venue_id)
      db.session.add(new_show)
      db.session.commit()
  except:
      error = True
      db.session.rollback()
  finally:
      db.session.close()
  if error:
      flash(f'Opp, an error occurred.')
  else:
      flash('Show was successfully listed!')
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
