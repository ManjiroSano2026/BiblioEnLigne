from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Clé secrète indispensable pour utiliser les sessions (remplacez par une phrase unique)
app.secret_key = os.environ.get('SECRET_KEY', 'une_cle_secrete_tres_difficile_a_deviner_12345')

# Connexion PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL', '')

def get_db_connection():
    url = DATABASE_URL
    # Correction automatique pour l'ancien format attendu par psycopg2
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgres://", 1)

    # Connexion sécurisée
    conn = psycopg2.connect(url)
    return conn

# ==============================================================================
# INITIALISATION ET MISE À JOUR DES TABLES
# ==============================================================================
def verifier_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Table Utilisateurs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Utilisateurs (
        id_utilisateur SERIAL PRIMARY KEY,
        nom_bibliotheque VARCHAR(100) NOT NULL,
        email VARCHAR(150) UNIQUE NOT NULL,
        mot_de_passe VARCHAR(255) NOT NULL
    )
    ''')
    
    # 2. Table Livres (liée à l'utilisateur)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Livres (
        id_livre VARCHAR(50) NOT NULL,
        id_utilisateur INTEGER NOT NULL,
        titre VARCHAR(255) NOT NULL,
        auteur VARCHAR(255) NOT NULL,
        annee INTEGER,
        quantite_totale INTEGER,
        quantite_dispo INTEGER,
        domaine VARCHAR(100),
        emplacement VARCHAR(100),
        PRIMARY KEY (id_livre, id_utilisateur),
        FOREIGN KEY (id_utilisateur) REFERENCES Utilisateurs(id_utilisateur) ON DELETE CASCADE
    )
    ''')
    
    # 3. Table Etudiants (liée à l'utilisateur)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Etudiants (
        id_carte VARCHAR(50) NOT NULL,
        id_utilisateur INTEGER NOT NULL,
        nom VARCHAR(255) NOT NULL,
        prenom VARCHAR(255) NOT NULL,
        filiere VARCHAR(100),
        niveau VARCHAR(50),
        telephone VARCHAR(50),
        statut VARCHAR(50) DEFAULT 'Actif',
        PRIMARY KEY (id_carte, id_utilisateur),
        FOREIGN KEY (id_utilisateur) REFERENCES Utilisateurs(id_utilisateur) ON DELETE CASCADE
    )
    ''')
    
    # 4. Table Emprunts (liée à l'utilisateur et vérifiant les clés composites)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Emprunts (
        id_emprunt SERIAL PRIMARY KEY,
        id_utilisateur INTEGER NOT NULL,
        id_carte VARCHAR(50) NOT NULL,
        id_livre VARCHAR(50) NOT NULL,
        date_sortie VARCHAR(50),
        date_rendu_prevue VARCHAR(50),
        statut_emprunt VARCHAR(50) DEFAULT 'En cours',
        FOREIGN KEY (id_utilisateur) REFERENCES Utilisateurs(id_utilisateur) ON DELETE CASCADE,
        FOREIGN KEY (id_carte, id_utilisateur) REFERENCES Etudiants(id_carte, id_utilisateur) ON DELETE CASCADE,
        FOREIGN KEY (id_livre, id_utilisateur) REFERENCES Livres(id_livre, id_utilisateur) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()

# Initialisation
verifier_tables()


# ==============================================================================
# AUTHENTIFICATION (CONNEXION / INSCRIPTION)
# ==============================================================================

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        nom_biblio = request.form['nom_bibliotheque']
        email = request.form['email']
        mdp = request.form['mot_de_passe']
        
        # Hachage sécurisé du mot de passe
        mdp_hache = generate_password_hash(mdp)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Utilisateurs (nom_bibliotheque, email, mot_de_passe) VALUES (%s, %s, %s)",
                           (nom_biblio, email, mdp_hache))
            conn.commit()
            flash("Inscription réussie ! Vous pouvez maintenant vous connecter.", "success")
            return redirect(url_for('connexion'))
        except Exception:
            conn.rollback()
            flash("Erreur : Cet email est déjà utilisé !", "danger")
        finally:
            cursor.close()
            conn.close()
            
    return render_template('inscription.html')


@app.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        email = request.form['email']
        mdp = request.form['mot_de_passe']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id_utilisateur, nom_bibliotheque, mot_de_passe FROM Utilisateurs WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user[2], mdp):
            # Enregistrement des infos dans la session Flask
            session['user_id'] = user[0]
            session['nom_biblio'] = user[1]
            return redirect(url_for('accueil'))
        else:
            flash("Email ou mot de passe incorrect.", "danger")
            
    return render_template('connexion.html')


@app.route('/deconnexion')
def deconnexion():
    session.clear()
    return redirect(url_for('connexion'))


# ==============================================================================
# ROUTES DE L'APPLICATION (TOUTES FILTRÉES PAR USER)
# ==============================================================================

@app.route('/')
def accueil():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
    return render_template('index.html')


@app.route('/livres')
def liste_livres():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    # On ne prend QUE les livres de l'utilisateur connecté
    cursor.execute("SELECT * FROM Livres WHERE id_utilisateur = %s", (session['user_id'],))
    tous_les_livres = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('livres.html', liste_livres=tous_les_livres)


@app.route('/ajouter_livre', methods=['GET', 'POST'])
def ajouter_livre():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
        
    if request.method == 'POST':
        id_livre = request.form['id_livre']
        titre = request.form['titre']
        auteur = request.form['auteur']
        annee = request.form['annee']
        quantite = request.form['quantite']
        domaine = request.form['domaine']
        emplacement = request.form['emplacement']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Livres VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                           (id_livre, session['user_id'], titre, auteur, annee, quantite, quantite, domaine, emplacement))
            conn.commit()
        except Exception:
            conn.rollback()
            flash("Erreur : Ce code de livre existe déjà dans votre bibliothèque !", "danger")
            return redirect(url_for('liste_livres'))
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('liste_livres'))
    return render_template('ajouter_livre.html')


@app.route('/modifier_livre/<id_livre>', methods=['GET', 'POST'])
def modifier_livre(id_livre):
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        titre = request.form['titre']
        auteur = request.form['auteur']
        annee = request.form['annee']
        quantite_totale = request.form['quantite_totale']
        quantite_dispo = request.form['quantite_dispo']
        domaine = request.form['domaine']
        emplacement = request.form['emplacement']
        
        cursor.execute('''UPDATE Livres SET titre=%s, auteur=%s, annee=%s, quantite_totale=%s, 
                          quantite_dispo=%s, domaine=%s, emplacement=%s WHERE id_livre=%s AND id_utilisateur=%s''',
                       (titre, auteur, annee, quantite_totale, quantite_dispo, domaine, emplacement, id_livre, session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('liste_livres'))
        
    cursor.execute("SELECT * FROM Livres WHERE id_livre = %s AND id_utilisateur = %s", (id_livre, session['user_id']))
    livre = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('modifier_livre.html', livre=livre)


@app.route('/supprimer_livre/<id_livre>')
def supprimer_livre(id_livre):
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Livres WHERE id_livre = %s AND id_utilisateur = %s", (id_livre, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('liste_livres'))


@app.route('/etudiants')
def liste_etudiants():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Etudiants WHERE id_utilisateur = %s", (session['user_id'],))
    tous_les_etudiants = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('etudiants.html', liste_etudiants=tous_les_etudiants)


@app.route('/inscrire_etudiant', methods=['GET', 'POST'])
def inscrire_etudiant():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
        
    if request.method == 'POST':
        id_carte = request.form['id_carte']
        nom = request.form['nom']
        prenom = request.form['prenom']
        filiere = request.form['filiere']
        niveau = request.form['niveau']
        telephone = request.form['telephone']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Etudiants (id_carte, id_utilisateur, nom, prenom, filiere, niveau, telephone) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                           (id_carte, session['user_id'], nom, prenom, filiere, niveau, telephone))
            conn.commit()
        except Exception:
            conn.rollback()
            flash("Erreur : Ce numéro de carte étudiant existe déjà dans votre base !", "danger")
            return redirect(url_for('liste_etudiants'))
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('liste_etudiants'))
    return render_template('inscrire_etudiant.html')


@app.route('/emprunter', methods=['GET', 'POST'])
def emprunter():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
        
    if request.method == 'POST':
        id_carte = request.form['id_carte']
        id_livre = request.form['id_livre']
        date_sortie = request.form['date_sortie']
        date_rendu = request.form['date_rendu']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT quantite_dispo FROM Livres WHERE id_livre = %s AND id_utilisateur = %s", (id_livre, session['user_id']))
        livre = cursor.fetchone()
        if not livre:
            cursor.close()
            conn.close()
            return "Erreur : Ce livre n'existe pas dans votre bibliothèque !", 400
        if livre[0] <= 0:
            cursor.close()
            conn.close()
            return "Erreur : Ce livre n'est plus disponible !", 400
            
        cursor.execute("SELECT nom FROM Etudiants WHERE id_carte = %s AND id_utilisateur = %s", (id_carte, session['user_id']))
        etudiant = cursor.fetchone()
        if not etudiant:
            cursor.close()
            conn.close()
            return "Erreur : Cet étudiant n'est pas inscrit chez vous !", 400
            
        cursor.execute("INSERT INTO Emprunts (id_utilisateur, id_carte, id_livre, date_sortie, date_rendu_prevue) VALUES (%s, %s, %s, %s, %s)",
                       (session['user_id'], id_carte, id_livre, date_sortie, date_rendu))
        cursor.execute("UPDATE Livres SET quantite_dispo = quantite_dispo - 1 WHERE id_livre = %s AND id_utilisateur = %s", (id_livre, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('liste_livres'))
        
    return render_template('emprunter.html')


@app.route('/historique', methods=['GET'])
def historique():
    if 'user_id' not in session:
        return redirect(url_for('connexion'))
        
    id_carte = request.args.get('id_carte', '')
    emprunts = []
    
    if id_carte:
        conn = get_db_connection()
        cursor = conn.cursor()
        requete = '''
            SELECT Emprunts.id_livre, Livres.titre, Livres.auteur, 
                   Emprunts.date_sortie, Emprunts.date_rendu_prevue, Emprunts.statut_emprunt
            FROM Emprunts
            JOIN Livres ON Emprunts.id_livre = Livres.id_livre AND Emprunts.id_utilisateur = Livres.id_utilisateur
            WHERE Emprunts.id_carte = %s AND Emprunts.id_utilisateur = %s
        '''
        cursor.execute(requete, (id_carte, session['user_id']))
        emprunts = cursor.fetchall()
        cursor.close()
        conn.close()
        
    return render_template('historique.html', emprunts=emprunts, id_carte_recherche=id_carte)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)