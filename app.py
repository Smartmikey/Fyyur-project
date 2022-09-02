#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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
  return render_template('pages/venues.html', areas=venue_data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
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

  venue = Venue.query.get(venue_id)
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
  form = VenueForm(request.form)
  error = False
  try:
    venue = Venue(
      name =form.name.data,
      city =form.city.data,
      state =form.state.data,
      address =form.address.data,
      phone =form.phone.data,
      tmp_genres =form.getlist('genres'),
      genres = ','.join(tmp_genres),
      facebook_link =form.facebook_link.data,
      )
    
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
    if error:
        flash('ooopps, an error occured. Venue ' +
              venue.name + ' Could not be listed!')
    else:
        flash('Venue ' + venue.name +  ' was successfully listed!')
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



  artist = Artist.query.get(artist_id)

  artist_data = artist.to_dict()
  
  future_shows = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  future_shows_array = []

  previous_show = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()
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
  artist_data['previous_shows'] = previous_show_array
  artist_data['future_shows'] = future_shows_array
  artist_data['previous_shows_count'] = len(previous_shows)
  artist_data['future_shows_count'] = len(future_shows)
  
  return render_template('pages/show_artist.html', artist=artist_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist= Artist.query.get(artist_id)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):



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

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):


  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form)
  error = False
  try:
      artist = Artist.query.get(artist_id)
      artist['name'] = form.name.data
      artist['city'] = form.city.data
      artist['state'] = form.state.data
      artist['phone'] = form.phone.data
      tmp_genres = form.getlist('genres')
      artist['genres'] = ','.join(tmp_genres)
      artist['website'] = form.website.data
      artist['image_link'] = form.image_link.data
      artist['facebook_link'] = form.facebook_link.data
      artist['seeking_description'] = form.seeking_description.data
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
          flash('Artist ' + artist.name + ' was successfully listed!')
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

  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)
  error = False
  artist_id = form.artist_id.data
  venue_id = form.venue_id.data
  start_time = form.start_time.data
  
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
