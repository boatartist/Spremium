from flask import Flask, session, redirect, url_for, request, render_template, send_file, flash
from datetime import timedelta
from sqlalchemy import create_engine, text
import hashlib
import requests
from werkzeug.utils import secure_filename
import os
import requests

#setup database/engine
engine = create_engine('sqlite:///spremium.db')
connection = engine.connect()

#users table, see ERD
query = text('''CREATE TABLE IF NOT EXISTS Users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password_hash TEXT,
    num_songs_listened_to INTEGER DEFAULT 0,
    is_admin INTEGER NOT NULL DEFAULT 0,
    description LONGTEXT,
    tadb_id INTEGER NOT NULL DEFAULT 0,
    image_file TEXT
);''')
connection.execute(query)

#byproduct of development where I reformatted the albums table and needed to delete it without deleting the entire database
'''connection.execute(text('DROP TABLE Albums;'))
connection.execute(text('DROP TABLE album_songs;'))
connection.commit()'''

#albums table
query = text('''CREATE TABLE IF NOT EXISTS Albums(
    tadb_id INTEGER PRIMARY KEY,
    name TEXT,
    album_cover_image TEXT DEFAULT 'https://127-0-0-1-5000-a8cdl4t0stubdi6joroo857ffg.au.edusercontent.com/static/images/jack_russell_basic.svg',
    creator INTEGER,
    is_album INTEGER NOT NULL DEFAULT 0
);''')
connection.execute(query)

#songs table
query = text('''CREATE TABLE IF NOT EXISTS Songs(
    tadb_id INTEGER PRIMARY KEY,
    name TEXT,
    lyrics TEXT,
    num_listens INTEGER DEFAULT 0,
    artist INT,
    genre TEXT
);''')
connection.execute(query)

#album_songs table
query = text('''CREATE TABLE IF NOT EXISTS album_songs(
    song_id INT NOT NULL,
    album_id INT NOT NULL
);''')
connection.execute(query)
connection.commit()

salt = '|ab5&*.)' #randomised salt used for hashing passwords

#a function to create an artist from a given tadb_id and save it to the database
def create_artist(artist):
    path = f'https://www.theaudiodb.com/api/v1/json/2/artist.php?i={artist}'
    headers = {"x-rapidapi-host": "theaudiodb.p.rapidapi.com"}
    response = requests.get(path, headers=headers).json()
    print(response)
    name = response['artists'][0]['strArtist']
    description = response['artists'][0]['strBiographyEN']
    image_file = response['artists'][0]['strArtistThumb']
    query = text('INSERT INTO Users(name, description, tadb_id, image_file) VALUES(:name, :description, :tadb_id, :image_file);')
    connection.execute(query, {'name':name, 'description':description, 'tadb_id':artist, 'image_file':image_file})
    connection.commit()

#function to add song to database
def create_song(tadb_id, lyrics=None):
    path = f'https://www.theaudiodb.com/api/v1/json/2/track.php?h={tadb_id}?lan=en'
    headers = {"x-rapidapi-host": "theaudiodb.p.rapidapi.com"}
    response = requests.get(path, headers=headers).json()
    name = response['track'][0]['strTrack']
    artist = response['track'][0]['idArtist']
    if not connection.execute(text('SELECT * FROM Users WHERE tadb_id=:artist;'), {'artist':artist,}).fetchall():
        create_artist(artist)
    if not lyrics:
        lyrics = response['track'][0]['strTrackLyrics']
    genre = response['track'][0]['strGenre']
    print(name, artist, lyrics, genre)
    query = text('INSERT INTO Songs(tadb_id, name, lyrics, artist, genre) VALUES (:tadb_id, :name, :lyrics, :artist, :genre);')
    connection.execute(query, {'tadb_id':tadb_id, 'name':name, 'lyrics':lyrics, 'artist':artist, 'genre':genre})
    connection.commit()

#when database has been deleted/on first run this creates the 'admin' user with login 'admin@admin.com' and password 'admin'
#also give information for default song and artist (never gonna give you up/Rick Astley)
if len(connection.execute(text('SELECT * FROM Users;')).fetchall()) <= 0:
    #creating admin
    hashed = hashlib.sha256(('admin'+salt).encode()).hexdigest()
    query = text(f'INSERT INTO Users(name, email, is_admin, password_hash) VALUES("admin", "admin@admin.com", "1", "{hashed}");')
    connection.execute(query)
    #creating never gonna give you up (file manually installed)
    query = text
    connection.commit()
    create_artist('112884')
    create_song('32861727', '''We're no strangers to love
You know the rules and so do I
A full commitment's what I'm thinkin' of
You wouldn't get this from any other guy

I just wanna tell you how I'm feeling
Gotta make you understand

Never gonna give you up, never gonna let you down
Never gonna run around and desert you
Never gonna make you cry, never gonna say goodbye
Never gonna tell a lie and hurt you

We've known each other for so long
Your heart's been aching, but you're too shy to say it
Inside, we both know what's been going on
We know the game and we're gonna play it

And if you ask me how I'm feeling
Don't tell me you're too blind to see

Never gonna give you up, never gonna let you down
Never gonna run around and desert you
Never gonna make you cry, never gonna say goodbye
Never gonna tell a lie and hurt you

Never gonna give you up, never gonna let you down
Never gonna run around and desert you
Never gonna make you cry, never gonna say goodbye
Never gonna tell a lie and hurt you

We've known each other for so long
Your heart's been aching, but you're too shy to say it
Inside, we both know what's been going on
We know the game and we're gonna play it

I just wanna tell you how I'm feeling
Gotta make you understand

Never gonna give you up, never gonna let you down
Never gonna run around and desert you
Never gonna make you cry, never gonna say goodbye
Never gonna tell a lie and hurt you

Never gonna give you up, never gonna let you down
Never gonna run around and desert you
Never gonna make you cry, never gonna say goodbye
Never gonna tell a lie and hurt you

Never gonna give you up, never gonna let you down
Never gonna run around and desert you
Never gonna make you cry, never gonna say goodbye
Never gonna tell a lie and hurt you''')

#flask setup
app = Flask(__name__, static_folder='static', template_folder='static/templates') 
app.secret_key = 'xA2!}' 

#app.permanent_session_lifetime = timedelta(minutes=60)  # Set session timeout 

#this function is run whenever there is insufficient session data to create the queue (playing never gonna give you up) and get songs and artists data for display
def startup():
    new_stuff = {}
    new_stuff['queue'] = ['32861727']
    #list of all songs
    query = text('SELECT tadb_id, name, artist, genre FROM Songs;')
    results = list(connection.execute(query).fetchall())
    results = list(map(list, results))
    songs = {}
    for i in results:
        songs[i[0]] = i[1:]
    print(songs)
    new_stuff['songs'] = songs
    #list of genres
    query = text('SELECT genre FROM Songs ORDER BY RANDOM() LIMIT 8;')
    results = list(connection.execute(query).fetchall())
    genres = list(set(map(lambda x: list(x)[0], results)))
    print(genres)
    new_stuff['genres'] = genres
    #list of all albums
    query = text('SELECT * FROM Albums;')
    results = list(connection.execute(query).fetchall())
    results = list(map(list, results))
    print(results)
    new_stuff['albums'] = results
    #list of artist names and icons
    query = text('SELECT tadb_id, name, image_file FROM Users WHERE tadb_id >0;')
    results = list(connection.execute(query).fetchall())
    results = list(map(list, results))
    artists = {}
    for i in results:
        artists[i[0]] = i[1:]
    new_stuff['artists'] = artists
    for album in new_stuff['albums']: #user made playlists will have artist ids which are not in the list of artists
        if not album[3] in new_stuff['artists'].keys():
            query = text(f'SELECT name, image_file FROM Users WHERE id=:user_id;')
            results = list(connection.execute(query, {'user_id':album[3],}).fetchone())
            print(results)
            new_stuff['artists'][album[3]] = results
    print('here is the new stuff')
    print(new_stuff)
    return new_stuff

#gets required data about the currently playing song, run whenever new page is loaded for consistency
def current_song(song_id = '32861727', album=None):
    song = {}
    query = text(f'SELECT * FROM Songs WHERE tadb_id = "{song_id}";')
    data = connection.execute(query).fetchone()
    if not data: #if the song id is wrong
        song_id = '32861727'
        query = text(f'SELECT * FROM Songs WHERE tadb_id = "{song_id}";')
        data = list(connection.execute(query).fetchone())
    data = list(data)
    song['song_id'] = song_id
    song['song_data'] = data
    song['time_seconds'] = 0
    song['album'] = album
    song['artist_data'] = artist_data = list(connection.execute(text('SELECT * FROM Users WHERE tadb_id = :id;'), {'id':song['song_data'][4],}).fetchone())
    return song

"""@app.before_request
def make_session_permanent():
    session.permanent = True
    print('there is a session?')"""

#home page
@app.route('/', methods=['GET', 'POST']) 
def index(): 
    print('before') #backend checks to help me navigate changes in session and verify that correct changes have been made
    print(session)
    #remove song and artist data to save space in session variable
    #avoiding duplicates because session["current_song"] will have all the necessary data
    if session.get('song_data'):
        session.pop('song_data')
    if session.get('artist_data'):
        session.pop('artist_data')
    
    if not session.get('queue'):
        new_stuff = startup()
        for thing in new_stuff:
            session[thing] = new_stuff[thing]

    #play currently listening song
    song_id = session['queue'][0]
    session['current_song'] = current_song(song_id)
    #session['song_data'] = session['current_song']['song_data']
    #session['artist_data'] = session['current_song']['artist_data']
    print('after')
    print(session)
    return render_template('home.html', session=session)

#login page
@app.route('/login', methods=['GET', 'POST']) 
def login(): 
    if request.method == 'POST': 
        email = request.form['email'].lower()
        pwd = request.form['password']
        hashed = hashlib.sha256((pwd+salt).encode()).hexdigest() #hash and salt password for security
        query = text('SELECT id, name, email, is_admin FROM Users WHERE email =:email AND password_hash =:hashed ;')
        result = connection.execute(query, {'email':email, 'hashed':hashed}).fetchall()
        if len(result) == 1: #if there is a valid user row found in database
            session['email'] = email
            session['id'] = result[0][0]
            session['name'] = result[0][1]
            session['is_admin'] = result[0][3]
            del(pwd) #delete variable for maximal security/privacy
            del(hashed)
            return redirect(url_for('index')) 
        else:
            flash('Incorrect email or password')
    return render_template('login.html', session=session)

#register new account page
@app.route('/register', methods=['GET', 'POST'])
def register():
    data = ['','','']
    if request.method == 'POST': 
        name = request.form['name']
        email = request.form['email'].lower()
        pwd = request.form['password']
        confirm_pwd = request.form['confirm']
        if pwd != confirm_pwd:
            data = [name, email, pwd]
            flash('Passwords must match')
        else:
            hashed = hashlib.sha256((pwd+salt).encode()).hexdigest()
            query = text('INSERT INTO Users(name, email, password_hash) VALUES (:name, :email, :hashed);')
            connection.execute(query, {'name':name, 'email':email, 'hashed':hashed})
            connection.commit()
            session.permanent = True  # Make the session permanent to apply the timeout 
            session['email'] = email
            session['id'] = connection.execute(text('SELECT id FROM Users WHERE name=:name AND email=:email;'), {'name':name, 'email':email}).fetchone()[0]
            session['name'] = name
            session['is_admin'] = 0
            flash(f'Welcome to Spremium, {name}!')
            return redirect('/')
        del(pwd)
        del(confirm_pwd)
    return render_template('register.html', data=data, session=session)

#logout page/method (no actual page for this as it simply redirects)
@app.route('/logout') 
def logout(): 
    session.pop('name', None) 
    session.pop('email', None)
    session.pop('is_admin', None)
    session.pop('id', None)
    return redirect(url_for('index')) 

#restricted admin-only page for uploading songs, creating albums etc
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('is_admin', 0) == 1: #verify that user is an admin
        flash('must be admin to admin')
        return redirect('/')
    query = text('SELECT * FROM Songs;')
    results1 = connection.execute(query).fetchall()
    query = text('SELECT * FROM Users WHERE NOT tadb_id=0;')
    results2 = connection.execute(query).fetchall()
    return render_template('admin.html', session=session, stuff=[results1, results2])

#upload song sub-method of admin page
@app.route('/uploadSong', methods=['GET', 'POST'])
def uploadSong():
    tadb_id = request.form.get('tadb_id', 0)
    lyrics = request.form.get('lyrics', None)
    fileobject = request.files.get('file', None)
    if not fileobject.filename:
        flash('File needed to upload song')
    else:
        fileobject.save(os.path.join('./static/music/', f'{tadb_id}.mp3'))
        create_song(tadb_id, lyrics)
    return redirect(url_for('admin'))

#create artist method (sub-process of admin page)
@app.route('/createArtist', methods=['GET', 'POST'])
def createArtist():
    tadb_id = request.form['tadb_id']
    create_artist(tadb_id)
    return redirect(url_for('admin'))

#create album method (sub-process of admin page)
@app.route('/createAlbum', methods=['GET', 'POST'])
def createAlbum():
    tadb_id = request.form['tadb_id']
    songs = request.form.getlist('songs')
    print(songs)
    url = f'https://www.theaudiodb.com/api/v1/json/2/album.php?m={tadb_id}'
    headers = {"x-rapidapi-host": "theaudiodb.p.rapidapi.com"}
    response = requests.get(url, headers=headers).json()
    name = response['album'][0]['strAlbum']
    album_cover_image = response['album'][0]['strAlbumThumb']
    creator = response['album'][0]['idArtist']
    is_album = 1
    query = text('INSERT INTO Albums(tadb_id, name, album_cover_image, creator, is_album) VALUES (:tadb_id, :name, :album_cover_image, :creator, :is_album);')
    connection.execute(query, {'tadb_id':tadb_id, 'name':name, 'album_cover_image':album_cover_image, 'creator':creator, 'is_album':is_album})
    for song_id in songs:
        query = text('INSERT INTO album_songs(song_id, album_id) VALUES (:song_id, :album_id);')
        connection.execute(query, {'song_id':song_id, 'album_id':tadb_id})
    connection.commit()
    return redirect(url_for('admin'))

#song page based on id
@app.route('/song/<song_id>', methods=['GET', 'POST'])
def song(song_id):
    if len(session.get('queue', [])) < 1: #if there is no song playing/in queue then play the song currently being viewed
        session['queue'] = [song_id]
    try:
        if not session.get('queue'):
            new_stuff = startup()
            for thing in new_stuff:
                session[thing] = new_stuff[thing]
    except:
        print('confuse') #error mitigation from testing (may no longer be required)
    session['current_song'] = current_song(session['queue'][0])
    if not session['queue'][0] == song_id:#if a separate song_data and artist_data is required than what is available for the currently playing song
        if session.get('current_song'):
            session['current_song']['song_data'][2] = 'lyrics here' #reducing size of unneccessary variables to save space in session cookie
            session['current_song']['artist_data'][6] = 'artist info'
        print(song_id)
        query = text(f'SELECT * FROM Songs WHERE tadb_id = "{song_id}";')
        data = connection.execute(query).fetchone()
        if not data:
            return redirect('/')
        data = list(data)
        #data[2] = str(data[2]).split('\r\n')
        print(data[2])
        artist_data = list(connection.execute(text('SELECT * FROM Users WHERE tadb_id = :id;'), {'id':data[4],}).fetchone())
        session['song_data'] = data
        session['artist_data'] = artist_data
    else:
        print('they match')
    print(session)
    return render_template('song.html', session=session)

@app.route('/album/<album_id>', methods=['GET', 'POST'])
def album(album_id):
    query = text('SELECT * FROM Albums WHERE tadb_id=:tadb_id;')
    album = list(connection.execute(query, {'tadb_id':album_id,}).fetchone())
    if not album:
        return redirect('/')
    session['album'] = album
    query = text('SELECT album_songs.song_id, Songs.name FROM album_songs INNER JOIN Songs ON album_songs.song_id = Songs.tadb_id WHERE album_songs.album_id=:tadb_id;')
    songs = list(map(list, connection.execute(query, {'tadb_id':album_id,}).fetchall()))
    print(songs)
    session['album_songs'] = songs
    print(connection.execute(text('SELECT * FROM album_songs;')).fetchall())
    if session.get('song_id', None) and session.get('song_id', None) != 'undefined':
        song_id = session['song_id']
    else:
        song_id = songs[0][0]
        session['song_id'] = song_id
    query = text(f'SELECT * FROM Songs WHERE tadb_id = "{song_id}";')
    data = list(connection.execute(query).fetchone())
    session['song_data'] = data
    session['song_data'][2] = 'lyrics here'
    artist_data = list(connection.execute(text('SELECT * FROM Users WHERE tadb_id = :id;'), {'id':data[4],}).fetchone())
    session['artist_data'] = artist_data
    for i in session.values():
        print(type(i))
    for key, value in session.items():
        print(key, value)
    return render_template('album.html', session=session)

@app.route('/nextSong', methods=['GET', 'POST'])
def nextSong():
    print('you sure you want to next song?')
    if len(session['queue']) > 1:
        session['queue'].pop(0)
        session['time_seconds'] = 0.00
    else:
        session['queue'].append('32861727')
    return redirect('/')

@app.route('/addToQueue', methods=['POST'])
def addToQueue():
    songs = request.form.getlist('song')
    print(songs)
    #print(session)
    og_queue = session.get('queue', [])
    print(og_queue)
    temp = [og_queue[0]]
    temp.extend(songs)
    temp.extend(og_queue[1:])
    session['queue'] = temp
    print(session['queue'])
    return redirect(url_for('nextSong'))

@app.route('/addToQueueBottom', methods=['POST'])
def addToQueueBottom():
    print('adding to queue bottom')
    songs = request.form.getlist('song_id')
    print(songs)
    #print(session)
    og_queue = session.get('queue', [])
    og_queue.extend(songs)
    session['queue'] = og_queue
    print(session['queue'])
    return redirect('/')

@app.route('/updateTime', methods=['POST'])
def updateTime():
    next_url = request.form.get('new_url', '/')
    current_time = request.form.get('start_time', 0)
    session['current_song']['time_seconds'] = current_time
    print(current_time)
    return redirect(next_url)

@app.route('/deleteFromQueue', methods=['POST'])
def deleteFromQueue():
    print(session['queue'])
    index = request.form.get('songIndex')
    if index:
        queue = session['queue']
        queue.pop(int(index))
        session['queue'] = queue
        print(f'popped song at index {index}')
    print(session['queue'])
    return redirect('/')

@app.route('/newPlaylist', methods=['GET', 'POST'])
def newPlaylist():
    if not session.get('email'):
        flash('Create a free Spremium account to make playlists')
        return redirect('/')
    if request.method == 'POST':
        name = request.form.get('playlist_name', 'New Playlist')
        print(connection.execute(text('SELECT * FROM Albums;')).fetchall())
        query = text(f'SELECT tadb_id FROM Albums WHERE tadb_id < 999999 ORDER BY tadb_id DESC LIMIT 1;')
        prev_id = connection.execute(query).fetchone()
        if prev_id:
            album_id = int(prev_id[0]) + 1
        else:
            album_id = 0
        print(album_id)
        fileobject = request.files.get('file', None)
        if not fileobject.filename:
            cover_image = './static/images/tennis_ball.svg'
        else:
            cover_image = os.path.join('./static/images/', f'{album_id}.{secure_filename(fileobject.filename).split(".")[1]}')
            fileobject.save(cover_image)
        print(cover_image)
        songs = request.form.getlist('songs')
        print(songs)
        query = text('INSERT INTO Albums(tadb_id, name, album_cover_image, creator, is_album) VALUES (:tadb_id, :name, :album_cover_image, :creator, :is_album);')
        connection.execute(query, {'tadb_id':album_id, 'name':name, 'album_cover_image':cover_image, 'creator':session['id'], 'is_album':0})
        for song_id in songs:
            query = text('INSERT INTO album_songs(song_id, album_id) VALUES (:song_id, :album_id);')
            connection.execute(query, {'song_id':song_id, 'album_id':album_id})
        connection.commit()
        print(connection.execute(text('SELECT * FROM Albums;')).fetchall())
        #rerun startup to add put new playlist on home page
        new_stuff = startup()
        for thing in new_stuff:
            session[thing] = new_stuff[thing]
        flash(f'Successfully created playlist "{name}"')
        return redirect('/')
    return render_template('playlist.html', session=session)

@app.route('/manifest.json')
def serve_manifest():
    return send_file('manifest.json', mimetype='application/manifest+json')

@app.route('/sw.js')
def serve_sw():
    return send_file('sw.js', mimetype='application/javascript')
    
if __name__ == '__main__': 
    app.run(debug=True) 
