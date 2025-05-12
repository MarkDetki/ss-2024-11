"""Minimale Flask Anwendung"""

# Import MySQL-Connector
import mysql.connector

# Import benötigter Flask-Module
from flask import Flask, render_template,  g, redirect, url_for, request, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

# Import der Verbindungsinformationen zur Datenbank:
# Variable DB_HOST: Servername des MySQL-Servers
# Variable DB_USER: Nutzername
# Variable DB_PASSWORD: Passwort
# Variable DB_DATABASE: Datenbankname
from db.db_credentials import DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE

app = Flask(__name__)
app.secret_key = 'MR9HTf8du-5bS#eZ?g,>4t{p6qaAC='
app.config['UPLOAD_FOLDER'] = 'static'
app.config['MAX_CONTENT_PATH'] = 1024 * 1024  # 1MB Max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

@app.before_request
def before_request():
    """ Verbindung zur Datenbank herstellen """
    g.con = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_DATABASE)
def check_login():
    """ Login überprüfen """
    if 'profil_id' in session:
        # Nutzer ist eingeloggt
        pass
    else:
        # Nutzer ist nicht eingeloggt
        return redirect(url_for('login'))

@app.teardown_request
def teardown_request(exception):  # pylint: disable=unused-argument
    """ Verbindung zur Datenbank trennen """
    con = getattr(g, 'con', None)
    if con is not None:
        con.close()

@app.route('/')
def index():
    """Startseite"""
    cur = g.con.cursor()
    # Namen aller Städte aus der Datenbank abfragen
    cur.execute("SELECT name FROM stadt")
    stadt = cur.fetchall()
    cur.close()

    if request.args.get('stadt'):
        # Überprüfen, ob im Anfrageparameter eine Stadt angegeben ist
        stadt_name = request.args.get('stadt')
        # Neuen Cursor öffnen, um Stadt-ID basierend auf dem Stadtnamen abzufragen
        cur = g.con.cursor()
        cur.execute("SELECT stadt_id FROM stadt WHERE name = %s", (stadt_name,))
        stadt = cur.fetchone()
        cur.close()
        # Wenn keine Stadt gefunden wurde, Fehler anzeigen
        if not stadt:
            flash("Es konnte keine Stadt gefunden werden", "error")
            return render_template("index.html")
        # Stadt-ID aus dem Abfrageergebnis holen und zur Beitragsseite weiterleiten
        stadt_id = stadt[0]
        return redirect(url_for('beitrag', stadt_id=stadt_id))

    return render_template('index.html', stadt=stadt)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registrierung"""
    # Daten von Registrierungsformular abrufen
    if request.method == 'POST':
        email = request.form.get('email')
        passwort = request.form.get('passwort')
        passwort2 = request.form.get('passwort2')
        nutzername = request.form.get('nutzername')
        vorname = request.form.get('vorname')
        nachname = request.form.get('nachname')

        # Überprüfen, ob Nutzername bereits vorhanden
        cur = g.con.cursor()
        cur.execute("SELECT nutzername FROM profil WHERE nutzername=%s", (nutzername,))
        benutzername = cur.fetchone()
        cur.close()
        if benutzername is not None:
            return render_template('register.html', error="Nutzername existiert bereits.")

        # Überprüfen, ob E-Mail bereits vorhanden
        cur = g.con.cursor()
        cur.execute("SELECT email FROM profil WHERE email=%s", (email,))
        e_mail = cur.fetchone()
        cur.close()
        if e_mail is not None:
            return render_template('register.html', error1="Es existiert bereits ein Account mit dieser E-Mail-Adresse.")

        # Überprüfen, ob Passwörter übereinstimmen
        if passwort == passwort2:

            # Passwort-Hash erzeugen
            pw = generate_password_hash(password=passwort)

            # Daten für Nutzer in Datenbank übernehmen
            cur = g.con.cursor()
            cur.execute("INSERT INTO profil (email, passwort, nutzername, vorname, nachname) VALUES (%s, %s, %s, %s, %s)",
                (email, pw, nutzername, vorname, nachname,))
            g.con.commit()
            cur.close()

            # Neue User-Session starten
            session['profil_id'] = cur.lastrowid
            return redirect(url_for('index'))

        # Wenn Passwörter nicht übereinstimmen
        return render_template('register.html', error2="Die Passwörter stimmen nicht überein.")

    # Registrierungsformular anzeigen
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Loginseite"""
    # Daten von Login-Formular abrufen
    if request.method == 'POST':
        email = request.form.get('email')
        passwort = request.form.get('passwort')

        # Überprüfen, ob E-Mail in Datenbank
        cur = g.con.cursor()
        cur.execute("SELECT profil_id, passwort,rolle FROM profil WHERE email=%s", (email,))
        daten = cur.fetchone()

        if daten is None:
            # Daten nicht in Datenbank gefunden
            cur.close()
            return render_template('login.html', error="Diese E-Mail-Adresse ist noch nicht registriert.")

        profil_id, pw_aus_db, rolle = daten
        # Überprüfen, ob Passwort bereits in Datenbank
        if check_password_hash(pwhash=pw_aus_db, password=passwort):
            # Wenn Passwörter übereinstimmen
            cur.close()
            session['profil_id'] = profil_id
            session['rolle'] = rolle
            return redirect(url_for('index'))

        # Wenn Passwörter nicht übereinstimmen
        cur.close()
        return render_template('login.html', error1="Falsches Passwort. Bitte versuche es erneut.")

    # Login-Formular anzeigen
    return render_template('login.html')

@app.route('/logout')
def logout():
    """ Ausloggen """
    session.clear()
    return redirect(url_for('index'))

def allowed_file(filename):
    """Prüft, ob die Datei eine erlaubte Erweiterung hat."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/profil', methods=['GET', 'POST'])
def profil():
    """ Benutzerverwaltung """
    if 'profil_id' not in session:
        flash('Sie müssen sich erst anmelden, um auf Ihr Profil zuzugreifen.')
        return redirect(url_for('login'))

    profil_id = session['profil_id']

    cur = g.con.cursor()
    # Daten bei Änderung abrufen
    if request.method == 'POST':
        vorname = request.form.get('vorname')
        nachname = request.form.get('nachname')
        email = request.form.get('email')
        nutzername = request.form.get('nutzername')
        adresse = request.form.get('adresse')
        profile_image = request.files.get('profile_image')

        # Aktualisierung des Profils bei Änderung
        cur.execute("UPDATE profil SET vorname = %s, nachname = %s, email = %s, nutzername = %s, adresse = %s WHERE profil_id = %s", (vorname, nachname, email, nutzername, adresse, profil_id))
        g.con.commit()

        # Überprüfen und Speichern des Profilbilds
        if profile_image and profile_image.filename != '':
            if allowed_file(profile_image.filename):
                filename = secure_filename(profile_image.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                profile_image.save(filepath)
                cur.execute("UPDATE profil SET profilbild = %s WHERE profil_id = %s", (filename, profil_id,))
                g.con.commit()
            else:
                flash('Ungültiges Dateiformat für Profilbild', 'error')

        flash('Profil aktualisiert!', 'success')
        return redirect(url_for('profil'))

    # Profildaten aus Datenbank abrufen
    cur.execute("SELECT vorname, nachname, email, nutzername, adresse, profilbild FROM profil WHERE profil_id = %s", (profil_id,))
    nutzer = cur.fetchone()

    # Angepasste SQL-Abfrage, um auch Stadt-ID und Stadt-Name zu holen
    cur.execute("""
            SELECT beitrag.beitrag_id, beitrag.titel, beitrag.text, beitrag.bilder, beitrag.bewertung, profil.nutzername, profil.profilbild
            FROM beitrag 
            JOIN favoriten ON beitrag.beitrag_id = favoriten.item_id 
            JOIN profil ON beitrag.profil_id = profil.profil_id
            WHERE favoriten.profil_id = %s AND favoriten.item_type = 'beitrag'""", (profil_id,))
    favorisierte_beitraege = cur.fetchall()

    # Liste für favorisierte Beiträge mit Kommentaren initialisieren
    favorisierte_beitraege_mit_kommentaren = []
    for beitrag in favorisierte_beitraege:
        beitrag_id = beitrag[0]
        # Kommentare zu jedem favorisierten Beitrag abfragen
        cur.execute("""
                SELECT kommentar.kommentar_id, kommentar.text, profil.nutzername, profil.profilbild 
                FROM kommentar 
                JOIN profil ON kommentar.profil_id = profil.profil_id
                WHERE kommentar.beitrag_id = %s
            """, (beitrag_id,))
        kommentare = cur.fetchall()
        # Beitrag und zugehörige Kommentare zur Liste hinzufügen
        favorisierte_beitraege_mit_kommentaren.append((beitrag, kommentare))

    # Favorisierte Städte des Benutzers abfragen
    cur.execute("""
           SELECT stadt.stadt_id, stadt.name 
           FROM stadt 
           JOIN favoriten ON stadt.stadt_id = favoriten.item_id 
           WHERE favoriten.profil_id = %s AND favoriten.item_type = 'stadt'
       """, (profil_id,))
    favorisierte_staedte = cur.fetchall()

    cur.close()

    return render_template('profil.html', nutzer=nutzer,favorisierte_beitraege_mit_kommentaren=favorisierte_beitraege_mit_kommentaren,favorisierte_staedte=favorisierte_staedte)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Adminbereich"""
    if 'profil_id' not in session or session.get('rolle') != 'admin':
        flash('Zugriff verweigert. Nur Administratoren dürfen auf diese Seite zugreifen.')
        return redirect(url_for('login'))

    # notwendige Daten der Orte abrufen
    cur = g.con.cursor()
    cur.execute("SELECT land_id, land_name FROM land ")
    land = cur.fetchall()
    cur.execute("SELECT stadt_id, land_id, name, breitengrad, laengengrad FROM stadt ")
    stadt = cur.fetchall()
    cur.close()

    # Daten aus Admin-Formular abrufen
    if request.method == 'POST':
        # neue Stadt hinzufügen
        neue_stadt = request.form.get('neue_stadt')
        if neue_stadt:
            cur = g.con.cursor()
            cur.execute("SELECT name FROM stadt WHERE name=%s", (neue_stadt,))
            neuestadt = cur.fetchall()
            if len(neuestadt) > 0:
                flash('Diese Stadt existiert bereits.')
            else:
                land_id = request.form.get('land')
                breitengrad = request.form.get('breitengrad')
                laengengrad = request.form.get('längengrad')
                cur.execute("INSERT INTO stadt (name, land_id, breitengrad, laengengrad) VALUES (%s, %s, %s, %s)", (neue_stadt, land_id, breitengrad, laengengrad,))
                g.con.commit()
                cur.close()
                flash('Die Stadt wurde hinzugefügt.')
                return redirect(url_for('admin'))

        # neues Land hinzufügen
        neues_land = request.form.get('neues_land')
        einwohneranzahl = request.form.get('einwohneranzahl')
        landimg = request.files.get('landimg')
        if neues_land and einwohneranzahl and landimg:
            cur = g.con.cursor()
            cur.execute("SELECT land_name FROM land WHERE land_name=%s", (neues_land,))
            neuesland = cur.fetchall()
            if len(neuesland) > 0:
                flash('Dieses Land existiert bereits.')
            else:
                cur.execute("INSERT INTO land (land_name, einwohneranzahl) VALUES (%s, %s)",
                            (neues_land, einwohneranzahl))
                g.con.commit()

                land_id = cur.lastrowid

                if landimg and allowed_file(landimg.filename):
                    filename = secure_filename(landimg.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    landimg.save(filepath)
                    cur.execute("UPDATE land SET land_bild = %s WHERE land_id = %s", (filename, land_id))
                    g.con.commit()
                cur.close()
                flash('Das Land wurde hinzugefügt.')
                return redirect(url_for('admin'))

    # Abrufen der Benutzerdaten
    cur = g.con.cursor()
    cur.execute("SELECT profil_id, rolle, email, nutzername, vorname, nachname, nationalität, geburtsdatum, adresse FROM profil")
    users = cur.fetchall()
    cur.close()

    # Abrufen der gemeldeten Beiträge
    cur = g.con.cursor()
    cur.execute("""SELECT beitrag.titel, beitrag.text, stadt.name, profil.nutzername, beitrag.beitrag_id, beitrag.stadt_id
                    FROM beitrag
                    JOIN stadt ON beitrag.stadt_id = stadt.stadt_id
                    JOIN profil ON beitrag.profil_id = profil.profil_id
                    WHERE melden = %s""", (1,))
    gemeldet = cur.fetchall()
    cur.close()

    return render_template('admin.html', land=land, stadt=stadt, users=users, gemeldet=gemeldet)

@app.route('/user_bearbeiten/<profil_id>', methods=['GET', 'POST'])
def user_bearbeiten(profil_id):
    """Bearbeiten der Benutzerdaten im Adminbereich"""
    if 'profil_id' not in session or session.get('rolle') != 'admin':
        flash('Zugriff verweigert. Nur Administratoren dürfen auf diese Seite zugreifen.')
        return redirect(url_for('login'))

    cur = g.con.cursor()
    # Daten für Profil-Bearbeitung abrufen
    if request.method == 'POST':
        nutzername = request.form.get('nutzername')
        email = request.form.get('email')
        nachname = request.form.get('nachname')
        vorname = request.form.get('vorname')
        adresse = request.form.get('adresse')
        rolle = request.form.get('rolle')
        nationalität = request.form.get('nationalität')
        geburtsdatum = request.form.get('geburtsdatum')

        # Daten aktualisieren
        cur.execute("UPDATE profil SET rolle=%s, email=%s, nutzername=%s, vorname=%s, nachname=%s, nationalität=%s, geburtsdatum=%s, adresse=%s WHERE profil_id=%s",
                    (rolle, email, nutzername, vorname, nachname, nationalität, geburtsdatum, adresse, profil_id))
        g.con.commit()
        cur.close()
        return redirect(url_for('admin'))

    # Abrufen der Benutzerdaten
    cur = g.con.cursor()
    cur.execute("SELECT profil_id, rolle, email, nutzername, vorname, nachname, nationalität, geburtsdatum, adresse FROM profil WHERE profil_id=%s", (profil_id,))
    user = cur.fetchone()
    cur.close()
    return render_template('user_bearbeiten.html', user=user)

@app.route('/admin/delete_profile', methods=['POST'])
def delete_profile():
    """Benutzerprofil löschen"""
    # Überprüfen, ob der Benutzer angemeldet ist und die Rolle 'admin' hat
    if 'profil_id' not in session or session.get('rolle') != 'admin':
        flash('Zugriff verweigert. Nur Administratoren dürfen auf diese Seite zugreifen.')
        return redirect(url_for('login'))

    # Profil-ID des zu löschenden Profils aus dem POST-Request abrufen und Cursor für die Datenbankoperation erstellen
    profil_id = request.form['profil_id']
    cur = g.con.cursor()
    try:
        # Profil löschen
        cur.execute("DELETE FROM profil WHERE profil_id = %s", (profil_id,))
        g.con.commit()
    except mysql.connector.Error as err:
        # Fehlerbehandlung
        print(f"Error: {err}")
        g.con.rollback()
    finally:
        cur.close()
    # Zur Admin-Seite weiterleiten
    return redirect(url_for('admin'))

@app.route('/staedteliste')
def staedteliste():
    """Auflistung aller Länder"""
    # Verbindung zur Datenbank herstellen, Länder und Städte abrufen
    cur = g.con.cursor()
    cur.execute("SELECT land_id, land_name, einwohneranzahl, land_bild FROM land ")
    land = cur.fetchall()
    cur.execute("SELECT stadt_id, land_id, name FROM stadt ")
    stadt = cur.fetchall()
    cur.close()
    return render_template('staedteliste.html', land=land, stadt=stadt, )

@app.route('/land_details/<land_id>')
def land_details(land_id):
    """Auflistung der Details über das Land und aller zugehörigen Städte"""
    # Verbindung zur Datenbank herstellen, Länder und zugehörige Städte abrufen
    cur = g.con.cursor()
    cur.execute("SELECT land_id, land_name, einwohneranzahl, land_bild FROM land WHERE land_id = %s", (land_id,))
    land = cur.fetchone()
    cur.execute("SELECT stadt_id, name FROM stadt WHERE land_id = %s", (land_id,))
    staedte = cur.fetchall()
    cur.close()
    return render_template('land_details.html', land=land, staedte=staedte)

@app.route('/beitrag/<stadt_id>', methods=['GET', 'POST'])
def beitrag(stadt_id):
    """Auflistung von Beiträgen und Möglichkeit zur Erstellung"""
    # Abfrage des Stadtnamens basierend auf der Stadt-ID
    cur = g.con.cursor()
    cur.execute("SELECT stadt_id, name FROM stadt WHERE stadt_id=%s", (stadt_id,))
    stadtname = cur.fetchone()

    # Abfrage von Beiträgen und dazugehörigen Likes
    cur.execute("""SELECT beitrag.beitrag_id, beitrag.titel, beitrag.text, beitrag.bilder, beitrag.bewertung, profil.nutzername, profil.profilbild,
                (SELECT COUNT(*) FROM likes WHERE likes.beitrag_id = beitrag.beitrag_id) AS like_count,
                EXISTS(SELECT 1 FROM likes WHERE likes.beitrag_id = beitrag.beitrag_id AND likes.profil_id = %s) AS user_liked,
                beitrag.profil_id
            FROM beitrag 
            JOIN profil ON beitrag.profil_id = profil.profil_id 
            WHERE beitrag.stadt_id=%s""", (session.get('profil_id'), stadt_id,))
    beitraege = cur.fetchall()

    # Überprüfung, ob die Methode POST ist
    if request.method == 'POST':

        # Überprüfen, ob das 'like'-Formular gesendet wurde
        if 'like' in request.form:
            beitrag_id = request.form.get('beitrag_id')
            profil_id = session.get('profil_id')
            if not profil_id:
                flash("Sie müssen eingeloggt sein, um einen Beitrag zu liken.")
                return redirect(url_for('beitrag', stadt_id=stadt_id))

            # Überprüfen, ob der Benutzer den Beitrag bereits geliked hat
            cur.execute("SELECT * FROM likes WHERE beitrag_id=%s AND profil_id=%s", (beitrag_id, profil_id))
            like = cur.fetchone()
            if like:
                # Wenn bereits geliked, den Like entfernen
                cur.execute("DELETE FROM likes WHERE like_id = %s", (like[0],))
                g.con.commit()
            else:
                # Andernfalls den Like hinzufügen
                cur.execute("INSERT INTO likes (beitrag_id, profil_id) VALUES (%s, %s)", (beitrag_id, profil_id))
                g.con.commit()
            return redirect(url_for('beitrag', stadt_id=stadt_id))

        # Formular zum Erstellen eines neuen Beitrags
        titel = request.form.get('titel')
        text = request.form.get('text')
        bilder = request.files.getlist('bilder')
        bewertung = request.form.get('bewertung')
        profil_id = session.get('profil_id')
        # Beitrag in der Datenbank speicher
        cur.execute("INSERT INTO beitrag (stadt_id, titel, text, bewertung, profil_id) VALUES (%s, %s, %s, %s, %s)",
                    (stadt_id, titel, text, bewertung, profil_id))
        g.con.commit()

        # Überprüfen, ob der Benutzer eingeloggt ist
        if not profil_id:
            flash("Sie müssen eingeloggt sein, um einen Beitrag zu erstellen.")
            return redirect(url_for('login'))

        beitrag_id = cur.lastrowid

        # Bilder speichern, falls vorhanden
        bild_pfade = []
        for bild in bilder:
            if bild and allowed_file(bild.filename):
                filename = secure_filename(bild.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                bild.save(filepath)
                bild_pfade.append(filename)

        if bild_pfade:
            bild_pfade_str = ','.join(bild_pfade)
            cur.execute("UPDATE beitrag SET bilder = %s WHERE beitrag_id = %s", (bild_pfade_str, beitrag_id,))
            g.con.commit()

        return redirect(url_for('beitrag', stadt_id=stadt_id))

    # Abfrage der Kommentare für jeden Beitrag
    beitraege_mit_kommentaren = []
    for beitrag in beitraege:
        beitrag_id = beitrag[0]
        cur.execute("""SELECT kommentar.kommentar_id, kommentar.text, profil.nutzername, profil.profilbild 
            FROM kommentar 
            JOIN profil ON kommentar.profil_id = profil.profil_id
            WHERE kommentar.beitrag_id = %s""", (beitrag_id,))
        kommentare = cur.fetchall()
        beitraege_mit_kommentaren.append((beitrag, kommentare))

    cur.close()
    return render_template('beitrag.html', stadtname=stadtname, beitraege=beitraege, beitraege_mit_kommentaren=beitraege_mit_kommentaren)

@app.route('/delete_beitrag/<int:beitrag_id>', methods=['POST'])
def delete_beitrag(beitrag_id):
    # löscht einen Beitrag
    cur = g.con.cursor()
    cur.execute("DELETE FROM beitrag WHERE beitrag_id=%s", (beitrag_id,))
    g.con.commit()
    cur.close()
    flash("Beitrag erfolgreich gelöscht.")
    # Weiterleitung zur Beitragsseite der entsprechenden Stadt
    return redirect(url_for('beitrag', stadt_id=request.form.get('stadt_id')))

@app.route('/kommentar', methods=['POST'])
def kommentar():
    """Kommentarfunktion"""
    # Überprüfen, ob der Benutzer eingeloggt ist
    if 'profil_id' not in session:
        flash('Sie müssen eingeloggt sein, um einen Kommentar zu verfassen.')
        return redirect(url_for('login'))

    # Beitrag-id und Kommentartext aus dem Formular abrufen
    beitrag_id = request.form.get('beitrag_id')
    text = request.form.get('text')
    profil_id = session.get('profil_id')

    # Überprüfen, ob der Kommentartext leer ist
    if not text:
        flash('Kommentartext darf nicht leer sein.')
        return redirect(url_for('beitrag', stadt_id=request.form.get('stadt_id')))

    # Kommentar in die Datenbank einfügen
    cur = g.con.cursor()
    cur.execute("INSERT INTO kommentar (beitrag_id, profil_id, text) VALUES (%s, %s, %s)",
                (beitrag_id, profil_id, text))
    g.con.commit()
    cur.close()
    # Weiterleitung zur Beitragsseite der entsprechenden Stadt
    return redirect(url_for('beitrag', stadt_id=request.form.get('stadt_id')))

@app.route('/länder')
def get_länder():
    # Länderinformationen aus der Datenbank abrufen
    cursor = g.con.cursor()
    cursor.execute('SELECT land_id, name, einwohneranzahl, land_bild FROM land')
    länder = cursor.fetchall()
    cursor.close()
    return jsonify(länder)

@app.route('/städte')
def get_städte():
    # Städteinformationen aus der Datenbank abrufen
    cursor = g.con.cursor()
    cursor.execute('SELECT stadt_id, land_id, name, breitengrad, längengrad FROM stadt')
    städte = cursor.fetchall()
    cursor.close()
    return jsonify(städte)

@app.route('/stadt/<int:stadt_id>')
def get_stadt(stadt_id):
    # Informationen über eine spezifische Stadt aus der Datenbank abrufen
    cursor = g.con.cursor()
    cursor.execute('SELECT stadt_id, land_id, name, breitengrad, längengrad FROM stadt WHERE id = %s', (stadt_id,))
    stadt = cursor.fetchone()
    cursor.close()
    # Überprüfen, ob die Stadt gefunden wurde
    if stadt:
        return jsonify(stadt)
    else:
        # Fehler zurückgeben, wenn die Stadt nicht gefunden wurde
        return jsonify({'error': 'Stadt nicht gefunden'}), 404

@app.route("/map")
def map_view():
    """Karte zeigen"""
    cursor = g.con.cursor()
    cursor.execute('SELECT stadt_id, name, breitengrad, laengengrad FROM stadt')
    cities = cursor.fetchall()
    cursor.close()

    # Erstellen einer Liste, um die Städte-Daten für die Karte zu speichern
    cities_array = []

    # Durchlaufen der Städte und Formatieren der Daten für die Karte
    for city in cities:
        city_id, name, breitengrad, laengengrad = city
        city_data = {
            "name": name,
            "coords": [breitengrad, laengengrad],
            "link": f"http://127.0.0.1:5000/beitrag/{city_id}"
        }
        # Hinzufügen der formatierten Stadt-Daten zur Liste
        cities_array.append(city_data)

    print(cities_array)

    return render_template('map.html', cities=cities_array)

@app.route('/add_favorite/<item_type>/<int:item_id>', methods=['POST'])
def add_favorite(item_type, item_id):
    # Überprüfen, ob der Benutzer eingeloggt ist
    if 'profil_id' not in session:
        flash('Sie müssen sich erst anmelden, um Elemente zu favorisieren.')
        return redirect(url_for('login'))

    # Überprüfen, ob der Elementtyp gültig ist
    if item_type not in ['beitrag', 'stadt']:
        flash('Ungültiger Elementtyp.')
        return redirect(request.referrer)

    # Abrufen der Benutzer-ID aus der Sitzung
    profil_id = session['profil_id']
    cur = g.con.cursor()
    # Überprüfen, ob das Element bereits in den Favoriten ist
    cur.execute("SELECT COUNT(*) FROM favoriten WHERE profil_id=%s AND item_id=%s AND item_type=%s",(profil_id, item_id, item_type))
    count = cur.fetchone()[0]
    cur.close()

    # Wenn das Element bereits in den Favoriten ist, einen Fehler anzeigen
    if count > 0:
        flash(f'{item_type.capitalize()} ist bereits in Ihren Favoriten.', 'warning')
    else:
        # Wenn das Element noch nicht in den Favoriten ist, es hinzufügen
        cur = g.con.cursor()
        cur.execute("INSERT INTO favoriten (profil_id, item_id, item_type) VALUES (%s, %s, %s)",
                    (profil_id, item_id, item_type))
        g.con.commit()
        cur.close()

        flash(f'{item_type.capitalize()} zu den Favoriten hinzugefügt!', 'success')

    return redirect(request.referrer)

@app.route('/remove_favorite/<item_type>/<int:item_id>', methods=['POST'])
def remove_favorite(item_type, item_id):
    # Überprüfen, ob der Benutzer eingeloggt ist
    if 'profil_id' not in session:
        flash('Sie müssen sich erst anmelden, um Elemente zu entfernen.')
        return redirect(url_for('login'))

    # Überprüfen, ob der Elementtyp gültig ist
    if item_type not in ['beitrag', 'stadt']:
        flash('Ungültiger Elementtyp.')
        return redirect(request.referrer)

    # Abrufen der Benutzer-ID aus der Sitzung
    profil_id = session['profil_id']
    cur = g.con.cursor()
    # Überprüfen, ob das Element in den Favoriten ist
    cur.execute("SELECT COUNT(*) FROM favoriten WHERE profil_id=%s AND item_id=%s AND item_type=%s",
                (profil_id, item_id, item_type))
    count = cur.fetchone()[0]
    # Wenn das Element nicht in den Favoriten ist, einen Fehler anzeigen
    if count == 0:
        flash(f'{item_type.capitalize()} ist nicht in Ihren Favoriten.', 'warning')
    else:
        # Wenn das Element in den Favoriten ist, es entfernen
        cur.execute("DELETE FROM favoriten WHERE profil_id=%s AND item_id=%s AND item_type=%s",
                    (profil_id, item_id, item_type))
        g.con.commit()
        cur.close()

        flash(f'{item_type.capitalize()} aus den Favoriten entfernt!', 'success')

    return redirect(request.referrer)

@app.route('/beitrag/edit/<int:beitrag_id>', methods=['GET', 'POST'])
def edit_post(beitrag_id):
    """Beitrag bearbeiten"""
    # Überprüfen, ob der Benutzer eingeloggt ist
    if 'profil_id' not in session:
        flash('Sie müssen eingeloggt sein, um diesen Beitrag zu bearbeiten.')
        return redirect(url_for('login'))  # Redirect to the login page

    # Aktuellen Benutzer und Rolle ermitteln
    current_user_id = session.get('profil_id')
    current_user_role = session.get('rolle')

    cur = g.con.cursor()

    # Holen des Beitrags und Überprüfen der Berechtigung
    cur.execute("SELECT profil_id, titel, text, bewertung, stadt_id FROM beitrag WHERE beitrag_id = %s", (beitrag_id,))
    post_data = cur.fetchone()

    # Überprüfen, ob der Beitrag existiert
    if post_data is None:
        cur.close()
        flash('Beitrag nicht gefunden')
        return redirect(url_for('index'))

    post_owner_id = post_data[0]
    stadt_id = post_data[4]

    # Überprüfen, ob der aktuelle Benutzer der Besitzer des Beitrags ist oder ein Admin ist
    if current_user_id != post_owner_id and current_user_role != 'admin':
        cur.close()
        flash('Sie haben keine Berechtigung, diesen Beitrag zu bearbeiten.')
        return redirect(url_for('index'))

    if request.method == 'GET':
        cur.close()
        return render_template('edit_post.html', beitrag_id=beitrag_id, post_data=post_data)

    elif request.method == 'POST':
        titel = request.form['titel']
        text = request.form['text']
        bewertung = request.form['bewertung']

        cur.execute("UPDATE beitrag SET titel = %s, text = %s, bewertung = %s WHERE beitrag_id = %s",
                    (titel, text, bewertung, beitrag_id))
        g.con.commit()
        cur.close()
        flash('Beitrag erfolgreich bearbeitet!')
        return redirect(url_for('beitrag', stadt_id=stadt_id))

@app.route('/report_post/<int:beitrag_id>', methods=['POST'])
def report_post(beitrag_id):
    """Beitrag melden"""
    # Beitrag als gemeldet markieren
    cur = g.con.cursor()
    cur.execute('UPDATE beitrag SET melden = %s WHERE beitrag_id = %s', (1, beitrag_id))
    g.con.commit()
    cur.close()
    flash('Beitrag wurde gemeldet')
    return redirect(request.referrer)

# Start der Flask-Anwendung
if __name__ == '__main__':
    app.run(debug=True)