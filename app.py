from flask import Flask, render_template, request, redirect, url_for
import os
import psycopg2

app = Flask(__name__)

# ==============================================================================
# CONNEXION À POSTGRESQL
# ==============================================================================
# En production, on récupère l'URL de Render. En local, collez votre URL copiée entre les guillemets.
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://bibliotheque_7u8k_user:jejlorzA8ukhZUMfOMVUOCR4ZVDBhJwu@dpg-d92bot67r5hc73fcav00-a.frankfurt-postgres.render.com/bibliotheque_7u8k')

def get_db_connection():
    # Connexion à PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# ==============================================================================
# 1. CRÉATION AUTOMATIQUE DES TABLES SUR POSTGRESQL
# ==============================================================================
def verifier_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table Livres
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Livres (
        id_livre VARCHAR(50) PRIMARY KEY,
        titre VARCHAR(255) NOT NULL,
        auteur VARCHAR(255) NOT NULL,
        annee INTEGER,
        quantite_totale INTEGER,
        quantite_dispo INTEGER,
        domaine VARCHAR(100),
        emplacement VARCHAR(100)
    )
    ''')
    
    # Table Etudiants
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Etudiants (
        id_carte VARCHAR(50) PRIMARY KEY,
        nom VARCHAR(255) NOT NULL,
        prenom VARCHAR(255) NOT NULL,
        filiere VARCHAR(100),
        niveau VARCHAR(50),
        telephone VARCHAR(50),
        statut VARCHAR(50) DEFAULT 'Actif'
    )
    ''')
    
    # Table Emprunts (Remplacement de AUTOINCREMENT par SERIAL pour Postgres)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Emprunts (
        id_emprunt SERIAL PRIMARY KEY,
        id_carte VARCHAR(50),
        id_livre VARCHAR(50),
        date_sortie VARCHAR(50),
        date_rendu_prevue VARCHAR(50),
        statut_emprunt VARCHAR(50) DEFAULT 'En cours',
        FOREIGN KEY(id_carte) REFERENCES Etudiants(id_carte) ON DELETE CASCADE,
        FOREIGN KEY(id_livre) REFERENCES Livres(id_livre) ON DELETE CASCADE
    )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

# Initialisation des tables
verifier_tables()


# ==============================================================================
# 2. ROUTES GÉNÉRALES
# ==============================================================================

@app.route('/')
def accueil():
    return render_template('index.html')


@app.route('/historique', methods=['GET'])
def historique():
    id_carte = request.args.get('id_carte', '')
    emprunts = []
    
    if id_carte:
        conn = get_db_connection()
        cursor = conn.cursor()
        requete = '''
            SELECT Emprunts.id_livre, Livres.titre, Livres.auteur, 
                   Emprunts.date_sortie, Emprunts.date_rendu_prevue, Emprunts.statut_emprunt
            FROM Emprunts
            JOIN Livres ON Emprunts.id_livre = Livres.id_livre
            WHERE Emprunts.id_carte = %s
        '''
        cursor.execute(requete, (id_carte,))
        emprunts = cursor.fetchall()
        cursor.close()
        conn.close()
        
    return render_template('historique.html', emprunts=emprunts, id_carte_recherche=id_carte)


# ==============================================================================
# 3. GESTION DES LIVRES (CRUD)
# ==============================================================================

@app.route('/livres')
def liste_livres():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Livres")
    tous_les_livres = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('livres.html', liste_livres=tous_les_livres)


@app.route('/ajouter_livre', methods=['GET', 'POST'])
def ajouter_livre():
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
            cursor.execute("INSERT INTO Livres VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", 
                           (id_livre, titre, auteur, annee, quantite, quantite, domaine, emplacement))
            conn.commit()
        except Exception:
            conn.rollback()
            cursor.close()
            conn.close()
            return "Erreur : Ce code de livre existe déjà !", 400
        finally:
            if conn:
                cursor.close()
                conn.close()
        return redirect(url_for('liste_livres'))
    return render_template('ajouter_livre.html')


@app.route('/modifier_livre/<id_livre>', methods=['GET', 'POST'])
def modifier_livre(id_livre):
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
                          quantite_dispo=%s, domaine=%s, emplacement=%s WHERE id_livre=%s''',
                       (titre, auteur, annee, quantite_totale, quantite_dispo, domaine, emplacement, id_livre))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('liste_livres'))
        
    cursor.execute("SELECT * FROM Livres WHERE id_livre = %s", (id_livre,))
    livre = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('modifier_livre.html', livre=livre)


@app.route('/supprimer_livre/<id_livre>')
def supprimer_livre(id_livre):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Livres WHERE id_livre = %s", (id_livre,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('liste_livres'))


# ==============================================================================
# 4. GESTION DES ÉTUDIANTS (CRUD)
# ==============================================================================

@app.route('/etudiants')
def liste_etudiants():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Etudiants")
    tous_les_etudiants = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('etudiants.html', liste_etudiants=tous_les_etudiants)


@app.route('/inscrire_etudiant', methods=['GET', 'POST'])
def inscrire_etudiant():
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
            cursor.execute("INSERT INTO Etudiants (id_carte, nom, prenom, filiere, niveau, telephone) VALUES (%s, %s, %s, %s, %s, %s)", 
                           (id_carte, nom, prenom, filiere, niveau, telephone))
            conn.commit()
        except Exception:
            conn.rollback()
            cursor.close()
            conn.close()
            return "Erreur : Ce numéro de carte étudiant existe déjà !", 400
        finally:
            if conn:
                cursor.close()
                conn.close()
        return redirect(url_for('liste_etudiants'))
    return render_template('inscrire_etudiant.html')


@app.route('/modifier_etudiant/<id_carte>', methods=['GET', 'POST'])
def modifier_etudiant(id_carte):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        filiere = request.form['filiere']
        niveau = request.form['niveau']
        telephone = request.form['telephone']
        
        cursor.execute('''UPDATE Etudiants SET nom=%s, prenom=%s, filiere=%s, niveau=%s, telephone=%s 
                          WHERE id_carte=%s''', (nom, prenom, filiere, niveau, telephone, id_carte))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('liste_etudiants'))
        
    cursor.execute("SELECT * FROM Etudiants WHERE id_carte = %s", (id_carte,))
    etudiant = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('modifier_etudiant.html', etudiant=etudiant)


@app.route('/supprimer_etudiant/<id_carte>')
def supprimer_etudiant(id_carte):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Etudiants WHERE id_carte = %s", (id_carte,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('liste_etudiants'))


# ==============================================================================
# 5. TRANSACTIONS (EMPRUNTS)
# ==============================================================================

@app.route('/emprunter', methods=['GET', 'POST'])
def emprunter():
    if request.method == 'POST':
        id_carte = request.form['id_carte']
        id_livre = request.form['id_livre']
        date_sortie = request.form['date_sortie']
        date_rendu = request.form['date_rendu']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT quantite_dispo FROM Livres WHERE id_livre = %s", (id_livre,))
        livre = cursor.fetchone()
        if not livre:
            cursor.close()
            conn.close()
            return "Erreur : Ce code de livre n'existe pas !", 400
        if livre[0] <= 0:
            cursor.close()
            conn.close()
            return "Erreur : Ce livre n'est plus disponible en stock !", 400
            
        cursor.execute("SELECT nom FROM Etudiants WHERE id_carte = %s", (id_carte,))
        etudiant = cursor.fetchone()
        if not etudiant:
            cursor.close()
            conn.close()
            return "Erreur : Ce numéro de carte étudiant n'existe pas !", 400
            
        cursor.execute("INSERT INTO Emprunts (id_carte, id_livre, date_sortie, date_rendu_prevue) VALUES (%s, %s, %s, %s)",
                       (id_carte, id_livre, date_sortie, date_rendu))
        cursor.execute("UPDATE Livres SET quantite_dispo = quantite_dispo - 1 WHERE id_livre = %s", (id_livre,))
        
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('liste_livres'))
        
    return render_template('emprunter.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)