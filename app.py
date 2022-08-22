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
from flask_migrate import Migrate
from forms import *
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
class Genre(db.Model):
  __tablename__='Genre'
  id = db.Column(db.Integer, primary_key=True)
  genre_class =db.Column(db.String)

artist_genre_table = db.Table('artist_genre_table',
    db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True)
)

venue_genre_table = db.Table('venue_genre_table',
    db.Column('genre_id', db.Integer, db.ForeignKey('Genre.id'), primary_key=True),
    db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True)
)

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    genres=db.relationship('Genre', secondary=venue_genre_table, backref=db.backref('venues'))

    web_url=db.Column(db.String(120))
    seeking_talent=db.Column(db.Boolean, default=False)
    talent_description=db.Column(db.String(240))

    shows=db.relationship('Show', backref='venue', lazy=True)

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

class Show(db.Model):
    __tablename__ ='Show'

    id=db.Column(db.Integer, primary_key=True)
    show_time=db.Column(db.DateTime, nullable=False, default=datetime.utcnow)    
    artist_id=db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)   
    venue_id=db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

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
  venues=Venue.query.all()
  
  data=[]
  cities_states=set()
  for venue in venues:
    cities_states.add(venue.city, venue.state)

    cities_states=list(cities_states)
    cities_states.sort(key=itemgetter(1,0))

    present_time=datetime.now()
  
  for place in cities_states:
    venue_list=[]
    for venue in venues:
      if (venue.city==place[0]) and (venue.state==place[1]):
        venue_shows=Show.query.filter_by(venue_id=venue.id).all()
        upcomingShows=0
        for show in venue_shows:
          if show.show_time>present_time:
            upcomingShows +=1

        venue_list.append({
          "id": venue.id,
          "name": venue.name,
          "Upcoming_Shows": upcomingShows
        })
    data.append({
      "city": place[0],
      "state": place[1],
      "venues": venue_list
    })


  return render_template('pages/venues.html', areas=data);
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  venue_search=request.form.get('search_venue', '').strip()
  venues=Venue.query.filter(Venue.name.ilike('%' + venue_search + '%')).all()
  searchResult=[]
  present_time=datetime.now()

  for venue in venues:
    showVenue=Show.query.filter_by(venue_id=venue.id).all()
    upcomingShows=0

    for show in showVenue:
      if show.show_time>present_time:
        upcomingShows +=1

    searchResult.append({
      "id": venue.id,
      "name": venue.name,
      "Upcoming_Shows": upcomingShows
    })

  searchOutput= {
    "search_count": len(venues),
    "search_details": searchResult
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue=Venue.query.get(venue_id)
  print(venue)
  if not venue:
    return redirect(url_for('index'))
  else:
    genres= [genre.name for genre in venue.genres]

    prev_shows=[]
    prev_show_count=0
    upcoming_shows=[]
    upcoming_shows_count=0
    present_time=datetime.now()
    for show in venue.shows:
      if show.show_time > present_time:
        upcoming_shows_count +=1
        upcoming_shows.append({

          "artist_id": show.artist_id,
          "artist_name": show.Artist.name,
          "artist_display_image": show.Artist.image_link,
          "show_Time": format_datetime(str(show.show_time))
        })

      if show.show_time < present_time:
        prev_show_count += 1
        prev_shows.append({ 

          "artist_id": show.artist_id,
          "artist_name": show.Artist.name,
          "artist_display_image": show.Artist.image_link,
          "show_Time": format_datetime(str(show.show_time))
          
        })

  data= {
    "id": venue_id,
    "name": venue.name,
    "genres": genres,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "web_url": venue.web_url,
    "facebook_link":venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "talent_description": venue.talent_description,
    "image_link": venue.image_link,
    "prev_shows": prev_show_count,
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": upcoming_shows_count
  }
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  name = form.name.data.strip()
  city = form.city.data.strip()
  state = form.state.data
  address = form.address.data.strip()
  phone = form.phone.data
  phone = re.sub('\D', '', phone) 
  genres = form.genres.data                  
  seeking_talent = True if form.seeking_talent.data == 'Yes' else False
  talent_description = form.seeking_description.data.strip()
  image_link = form.image_link.data.strip()
  web_url = form.website.data.strip()
  facebook_link = form.facebook_link.data.strip()
  
  if not form.validate():
      flash( form.errors )
      return redirect(url_for('create_venue_submission'))
  else:
      error_in_insert = False
      try:
          new_venue = Venue(name=name, city=city, state=state, address=address, phone=phone, \
              seeking_talent=seeking_talent, talent_description=talent_description, image_link=image_link, \
              web_url=web_url, facebook_link=facebook_link)
          
          for genre in genres:
              fetch_genre = Genre.query.filter_by(name=genre).one_or_none() 
              if fetch_genre:
                  new_venue.genres.append(fetch_genre)
              else:
                  new_genre = Genre(name=genre)
                  db.session.add(new_genre)
                  new_venue.genres.append(new_genre) 
          db.session.add(new_venue)
          db.session.commit()
      except Exception as e:
          error_in_insert = True
          print(f'Exception "{e}" in create_venue_submission()')
          db.session.rollback()
      finally:
          db.session.close()
      if not error_in_insert:
          flash('Venue ' + request.form['name'] + ' was successfully registered!')
          return redirect(url_for('index'))
      else:
          flash('An error occurred. Venue ' + name + ' could not be registered.')
          print("Error in create_venue_submission()")
          abort(500)
  flash('Venue ' + request.form['name'] + ' was successfully registered!')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>/delete', methods=['GET'])
def delete_venue(venue_id):
  venue = Venue.query.get(venue_id)
  if not venue:
    return redirect(url_for('index'))
  else:
    error_on_delete = False
    venue_name = venue.name
    try:
      db.session.delete(venue)
      db.session.commit()
    except:
      error_on_delete = True
      db.session.rollback()
    finally: 
      db.session.close()
    if error_on_delete:
      flash(f'An error occurred while deleting venue {venue_name}.')
      print("Error in delete_venue()")
      abort(500)
    else:
      flash(f'Successfully removed venue {venue_name} from venue list')
      return redirect(url_for('venues'))
  return None
@app.route('/artists')
def artists():
  
  artists=Artist.query.order_by(Artist.name).all() 
  
  data=[]
  for artist in artists:
    data.append({
      "id": artist.id,
      "name": artist.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  artist_search=request.form.get('search_artists', '').strip()
  artists=Artist.query.filter(Artist.name.ilike('%' + artist_search + '%')).all()
  #implementing search for similar type strings inserted in the search field
  artist_search_result=[]
  present_time = datetime.now()
  for artist in artists:
    artist_shows = Show.query.filter_by(artist_id=artist.id).all()
    upcoming_shows = 0
    for show in artist_shows:
      if show.show_time > present_time:
        upcoming_shows += 1

    artist_search_result.append({
      "id": artist.id,
      "name": artist.name,
      "upcoming_shows": upcoming_shows
    })
  response={
    "count": len(artists),
    "data": artist_search_result
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  print(artist)
  if not artist: #to return to homepage if user types an unacceptable string format into browser
    return redirect(url_for('index'))
  else:
    genres = [genre.name for genre in artist.genres]

    prev_shows = []
    prev_shows_count =0
    upcoming_shows = []
    upcoming_shows_count = 0
    present_time = datetime.now()
    for show in artist.shows:
      if show.show_time > present_time:
        upcoming_shows_count += 1
        upcoming_shows.append({
          "venue_id": show.venue_id,
          "venue_name": show.venue.name,
          "venue_display_image": show.venue.image_link,
          "show_time": format_datetime(str(show.show_time))
        })
      if show.show_time < present_time:
        prev_shows_count += 1
        prev_shows.append({
          "venue_id": show.venue_id,
          "venue_name": show.venue.name,
          "venue_display_image": show.venue.image_link,
          "show_time": format_datetime(str(show.show_time))
        })
  data= {
          "id": artist_id,
          "name": artist.name,
          "genres": genres,
          "city": artist.city,
          "state": artist.state,
          "phone": artist.phone,
          "website": artist.web_url,
          "facebook_link": artist.facebook_link,
          "seeking_venue": artist.seeking_venue,
          "venue_description": artist.venue_description,
          "image_link": artist.image_link,
          "prev_shows": prev_shows,
          "prev_shows_count": prev_shows_count,
          "upcoming_shows": upcoming_shows,
          "upcoming_shows_count": upcoming_shows_count
        }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist =Artist.query.get(artist_id)
  if not artist:
    return redirect(url_for('index'))
  
  else:
    form = ArtistForm(obj=artist)
    genres =[genre.name for genre in artist.genres]
    artist={
        "id": artist_id,
        "name": artist.name,
        "genres": genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_talent,
        "venue_description": artist.talent_description,
        "image_link": artist.image_link
    }

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form= ArtistForm()
  name = form.name.data.strip()
  city = form.city.data.strip()
  state = form.state.data.strip()
  phone = form.phone.data.strip()
  phone = re.sub('\D', '', phone)
  genre = form.genre.data.strip()
  seeking_venue = True if form.seeking_venue.data == 'Yes' else False
  venue_description = form.seeking_description.data.strip()
  image_link = form.image_link.data.strip()
  web_url = form.website.data.strip()
  facebook_link = form.facebook_link.data.strip()

  #Form Error Handling
  if not form.validate():
    flash(form.errors)
    return redirect(url_for('show_artist', artist_id=artist_id))
  else:
    error_in_edit = False
    try: 
      artist = Artist.query.filter_by(id=artist_id).one_or_none()
      artist.name = name
      artist.city = city
      artist.state = state
      artist.phone = phone
      artist.seeking_venue = seeking_venue
      artist.venue_description = venue_description
      artist.image_link = image_link
      artist.web_url = web_url
      artist.facebook_link = facebook_link
      
      # clearing all populated genre names in artist genre list
      genres =[ (artist.genres.clear())] 
      for genre in genres:
            fetch_genre = Genre.query.filter_by(name=genre).one_or_none()
            if fetch_genre:
              artist.genres.append(fetch_genre)
            else:
              new_genre = Genre(name=genre)
              db.session.add(new_genre)
              artist.genres.append(new_genre)
              db.session.commit()
    except Exception as e:
      error_in_edit =True
      print(f'Exception "{e}" in edit_artist_submission()')
      db.session.rollback()
    finally:
      db.session.close()

      if not error_in_edit:
        #Assuming a successful edit of artist details.....
        flash('Artist ' + request.form['name'] + 'was successfully updated...')
        return redirect(url_for('show_artist', artist_id=artist_id))
      else: flash ('An error occurred while attempting to update ' + name )
      print ("error in edit_artist_submission()")
      abort(500)
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  if not venue:
    return redirect(url_for('index'))
  else:
    form = VenueForm(obj=venue)
  genres = [genre.name for genre in venue.genres]
  venue={
    "id": venue_id,
    "name": venue.name,
    "genres": genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "venue_description": venue.venue_description,
    "image_link": venue.image_link
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm()

  name = form.name.data.strip()
  city = form.city.data.strip()
  state = form.state.data
  address = form.address.data.strip()
  phone = form.phone.data
  phone = re.sub('\D', '', phone) # normalizing any form of phone number e.g. (819) 392-1234 --> 8193921234
  genres = form.genres.data                   # ['Alternative', 'Classical', 'Country']
  seeking_talent = True if form.seeking_talent.data == 'Yes' else False
  venue_description = form.seeking_description.data.strip()
  image_link = form.image_link.data.strip()
  web_url = form.website.data.strip()
  facebook_link = form.facebook_link.data.strip()

  if not form.validate():
        flash( form.errors )
        return redirect(url_for('edit_venue_submission', venue_id=venue_id))

  else:
        error_in_update = False
        try:
            # Database insert by getting existing database object
            venue = Venue.query.get(venue_id)
            # Updating database columns/fields
            venue.name = name
            venue.city = city
            venue.state = state
            venue.address = address
            venue.phone = phone
            venue.seeking_talent = seeking_talent
            venue.venue_description = venue_description
            venue.image_link = image_link
            venue.web_url = web_url
            venue.facebook_link = facebook_link

            venue.genres =[]

            for genre in genres:
              fetch_genre = Genre.query.filter(name=genre).one_or_none()
              if fetch_genre:
                #append any genre found
                venue.genres.append(fetch_genre)
              else:
                #if no genre was found in the genre query (line 839)
                new_genre = Genre(name=genre)
                db.session.add(new_genre)
                venue.genres.append(new_genre)
                db.session.commit()
        except Exception as e:
          error_in_edit = True
          print(f'Exception "{e}" in edit_venue_submission()')
          db.session.rollback()
        finally:
          db.session.close()
        
        if not error_in_edit:
          #for every successful update
          flash('Venue ' + request.form['name'] + 'was successfully updated...')
          return redirect(url_for('show_venue', venue_id=venue_id))
        else:
          flash('An error occurred while updating ' + name + 'as a venue...')
          print("Error in edit_venue_submission()")
          abort(500)

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm()

  name = form.name.data.strip()
  city = form.city.data.strip()
  state = form.state.data
  phone = form.phone.data
  phone = re.sub('\D', '', phone) # e.g. (819) 392-1234 --> 8193921234
  genres = form.genres.data                   # ['Alternative', 'Classical', 'Country']
  seeking_venue = True if form.seeking_venue.data == 'Yes' else False
  venue_description = form.seeking_description.data.strip()
  image_link = form.image_link.data.strip()
  web_url = form.website.data.strip()
  facebook_link = form.facebook_link.data.strip()

  if not form.validate():
        flash( form.errors )
        return redirect(url_for('create_artist_submission'))
  else:
        error_in_insert = False

        
        try:# Inserting details from form data into DB
            # creates the new artist with all fields but not genre yet
            new_artist = Artist(name=name, city=city, state=state, phone=phone, \
                seeking_venue=seeking_venue, venue_description=venue_description, image_link=image_link, \
                web_url=web_url, facebook_link=facebook_link)
            
            for genre in genres:
                fetch_genre = Genre.query.filter_by(name=genre).one_or_none()  # Throws an exception if more than one returned, returns None if none
                if fetch_genre:
                    # if found a genre, append it to the list
                    new_artist.genres.append(fetch_genre)

                else:
                    new_genre = Genre(name=genre)
                    db.session.add(new_genre)
                    new_artist.genres.append(new_genre)
                    db.session.add(new_artist)
            db.session.commit()
        except Exception as e:
            error_in_insert = True
            print(f'Exception "{e}" in create_artist_submission()')
            db.session.rollback()
        finally:
            db.session.close()

        if not error_in_insert:
            flash('Artist ' + request.form['name'] + ' was successfully registered!')
            return redirect(url_for('index'))
        else:
            flash('An error occurred. Artist ' + name + ' could not be registered.')
            print("Error in create_artist_submission()")
            abort(500)
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = []
  shows = Show.query.all()
    
  for show in shows:
        # Can reference show.artist, show.venue
        data.append({
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "show_time": format_datetime(str(show.start_time))
        })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm()
  artist_id = form.artist_id.data.strip()
  venue_id = form.venue_id.data.strip()
  start_time = form.start_time.data
  error_in_insert = False
    
  try:
        new_show = Show(start_time=start_time, artist_id=artist_id, venue_id=venue_id)
        db.session.add(new_show)
        db.session.commit()
  except Exception as e:
        error_in_insert = True
        print(f'Exception "{e}" in create_show_submission()')
        db.session.rollback()
  finally:
        db.session.close()

  if error_in_insert:
        flash(f'An error occurred.  Show could not be registered.')
        print("Error in create_show_submission()")
  else:
        flash('Show was successfully registered!')
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
