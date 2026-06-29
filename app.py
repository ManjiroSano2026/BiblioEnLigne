from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# ==============================================================================
# 1. VÉRIFICATION ET CRÉATION AUTOMATIQUE DES TABLES AU DÉMARRAGE
# ==============================================================================
def verifier_tables():
    conn = sqlite3.connect('bibliotheque.db')
    cursor = conn.cursor()
    
    # Table Livres (avec domaine et emplacement)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Livres (
        id_livre TEXT PRIMARY KEY,
        titre TEXT NOT NULL,
        auteur TEXT NOT NULL,
        annee INTEGER,
        quantite_totale INTEGER,
        quantite_dispo INTEGER,
        domaine TEXT,
        emplacement TEXT
    )
    ''')
    
    # Table Etudiants
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Etudiants (
        id_carte TEXT PRIMARY KEY,
        nom TEXT NOT NULL,
        prenom TEXT NOT NULL,
        filiere TEXT,
        niveau TEXT,
        telephone TEXT,
        statut TEXT DEFAULT 'Actif'
    )
    ''')
    
    # Table Emprunts
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Emprunts (
        id_emprunt INTEGER PRIMARY KEY AUTOINCREMENT,
        id_carte TEXT,
        id_livre TEXT,
        date_sortie TEXT,
        date_rendu_prevue TEXT,
        statut_emprunt TEXT DEFAULT 'En cours',
        FOREIGN KEY(id_carte) REFERENCES Etudiants(id_carte),
        FOREIGN KEY(id_livre) REFERENCES Livres(id_livre)
    )
    ''')
    conn.commit()
    conn.close()

# Exécution de la vérification des tables dès le lancement
verifier_tables()


# ==============================================================================
# 2. ROUTES GÉNÉRALES (ACCUEIL & HISTORIQUE)
# ==============================================================================

@app.route('/')
def accueil():
    return render_template('index.html')


@app.route('/historique', methods=['GET'])
def historique():
    id_carte = request.args.get('id_carte', '')
    emprunts = []
    
    if id_carte:
        conn = sqlite3.connect('bibliotheque.db')
        cursor = conn.cursor()
        requete = '''
            SELECT Emprunts.id_livre, Livres.titre, Livres.auteur, 
                   Emprunts.date_sortie, Emprunts.date_rendu_prevue, Emprunts.statut_emprunt
            FROM Emprunts
            JOIN Livres ON Emprunts.id_livre = Livres.id_livre
            WHERE Emprunts.id_carte = ?
        '''
        cursor.execute(requete, (id_carte,))
        emprunts = cursor.fetchall()
        conn.close()
        
    return render_template('historique.html', emprunts=emprunts, id_carte_recherche=id_carte)


# ==============================================================================
# 3. MODULE DE GESTION DES LIVRES (CRUD)
# ==============================================================================

@app.route('/livres')
def liste_livres():
    conn = sqlite3.connect('bibliotheque.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Livres")
    tous_les_livres = cursor.fetchall()
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
        
        conn = sqlite3.connect('bibliotheque.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Livres VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                           (id_livre, titre, auteur, annee, quantite, quantite, domaine, emplacement))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Erreur : Ce code de livre existe déjà !", 400
        finally:
            conn.close()
        return redirect(url_for('liste_livres'))
    return render_template('ajouter_livre.html')


@app.route('/modifier_livre/<id_livre>', methods=['GET', 'POST'])
def modifier_livre(id_livre):
    conn = sqlite3.connect('bibliotheque.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        titre = request.form['titre']
        auteur = request.form['auteur']
        annee = request.form['annee']
        quantite_totale = request.form['quantite_totale']
        quantite_dispo = request.form['quantite_dispo']
        domaine = request.form['domaine']
        emplacement = request.form['emplacement']
        
        cursor.execute('''UPDATE Livres SET titre=?, auteur=?, annee=?, quantite_totale=?, 
                          quantite_dispo=?, domaine=?, emplacement=? WHERE id_livre=?''',
                       (titre, auteur, annee, quantite_totale, quantite_dispo, domaine, emplacement, id_livre))
        conn.commit()
        conn.close()
        return redirect(url_for('liste_livres'))
        
    cursor.execute("SELECT * FROM Livres WHERE id_livre = ?", (id_livre,))
    livre = cursor.fetchone()
    conn.close()
    return render_template('modifier_livre.html', livre=livre)


@app.route('/supprimer_livre/<id_livre>')
def supprimer_livre(id_livre):
    conn = sqlite3.connect('bibliotheque.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Livres WHERE id_livre = ?", (id_livre,))
    conn.commit()
    conn.close()
    return redirect(url_for('liste_livres'))


# ==============================================================================
# 4. MODULE DE GESTION DES ÉTUDIANTS (CRUD)
# ==============================================================================

@app.route('/etudiants')
def liste_etudiants():
    conn = sqlite3.connect('bibliotheque.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Etudiants")
    tous_les_etudiants = cursor.fetchall()
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
        
        conn = sqlite3.connect('bibliotheque.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO Etudiants (id_carte, nom, prenom, filiere, niveau, telephone) VALUES (?, ?, ?, ?, ?, ?)", 
                           (id_carte, nom, prenom, filiere, niveau, telephone))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Erreur : Ce numéro de carte étudiant existe déjà !", 400
        finally:
            conn.close()
        return redirect(url_for('liste_etudiants'))
    return render_template('inscrire_etudiant.html')


@app.route('/modifier_etudiant/<id_carte>', methods=['GET', 'POST'])
def modifier_etudiant(id_carte):
    conn = sqlite3.connect('bibliotheque.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        filiere = request.form['filiere']
        niveau = request.form['niveau']
        telephone = request.form['telephone']
        
        cursor.execute('''UPDATE Etudiants SET nom=?, prenom=?, filiere=?, niveau=?, telephone=? 
                          WHERE id_carte=?''', (nom, prenom, filiere, niveau, telephone, id_carte))
        conn.commit()
        conn.close()
        return redirect(url_for('liste_etudiants'))
        
    cursor.execute("SELECT * FROM Etudiants WHERE id_carte = ?", (id_carte,))
    etudiant = cursor.fetchone()
    conn.close()
    return render_template('modifier_etudiant.html', etudiant=etudiant)


@app.route('/supprimer_etudiant/<id_carte>')
def supprimer_etudiant(id_carte):
    conn = sqlite3.connect('bibliotheque.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Etudiants WHERE id_carte = ?", (id_carte,))
    conn.commit()
    conn.close()
    return redirect(url_for('liste_etudiants'))


# ==============================================================================
# 5. MODULE DE TRANSACTION (EMPRUNTS)
# ==============================================================================

@app.route('/emprunter', methods=['GET', 'POST'])
def emprunter():
    if request.method == 'POST':
        id_carte = request.form['id_carte']
        id_livre = request.form['id_livre']
        date_sortie = request.form['date_sortie']
        date_rendu = request.form['date_rendu']
        
        conn = sqlite3.connect('bibliotheque.db')
        cursor = conn.cursor()
        
        # Vérification disponibilité Livre
        cursor.execute("SELECT quantite_dispo FROM Livres WHERE id_livre = ?", (id_livre,))
        livre = cursor.fetchone()
        if not livre:
            conn.close()
            return "Erreur : Ce code de livre n'existe pas !", 400
        if livre[0] <= 0:
            conn.close()
            return "Erreur : Ce livre n'est plus disponible en stock !", 400
            
        # Vérification existence Étudiant
        cursor.execute("SELECT nom FROM Etudiants WHERE id_carte = ?", (id_carte,))
        etudiant = cursor.fetchone()
        if not etudiant:
            conn.close()
            return "Erreur : Ce numéro de carte étudiant n'existe pas !", 400
            
        # Enregistrement de l'emprunt et mise à jour du stock
        cursor.execute("INSERT INTO Emprunts (id_carte, id_livre, date_sortie, date_rendu_prevue) VALUES (?, ?, ?, ?)",
                       (id_carte, id_livre, date_sortie, date_rendu))
        cursor.execute("UPDATE Livres SET quantite_dispo = quantite_dispo - 1 WHERE id_livre = ?", (id_livre,))
        
        conn.commit()
        conn.close()
        return redirect(url_for('liste_livres'))
        
    return render_template('emprunter.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)