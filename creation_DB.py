import sqlite3

conn = sqlite3.connect("hotel_reservation.db")
cursor = conn.cursor()

# Suppression des tables si elles existent (sécurité en dev)
cursor.executescript("""
DROP TABLE IF EXISTS Evaluation;
DROP TABLE IF EXISTS Reservation;
DROP TABLE IF EXISTS Chambre;
DROP TABLE IF EXISTS TypeChambre;
DROP TABLE IF EXISTS Prestation;
DROP TABLE IF EXISTS Client;
DROP TABLE IF EXISTS Hotel;
""")

# Création des tables
cursor.execute("""CREATE TABLE IF NOT EXISTS Hotel (

    id_hotel INTEGER PRIMARY KEY,
    ville TEXT,
    pays TEXT,
    code_postal INTEGER
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Client (
    id_client INTEGER PRIMARY KEY,
    adresse TEXT,
    ville TEXT,
    code_postal INTEGER,
    email TEXT,
    telephone TEXT,
    nom_complet TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Prestation (
    id_prestation INTEGER PRIMARY KEY,
    prix REAL,
    description TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS TypeChambre (
    id_type INTEGER PRIMARY KEY,
    nom_type TEXT,
    prix REAL
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Chambre (
    id_chambre INTEGER PRIMARY KEY,
    numero INTEGER,
    etage INTEGER,
    balcon INTEGER,
    id_type INTEGER,
    id_hotel INTEGER,
    FOREIGN KEY (id_type) REFERENCES TypeChambre(id_type),
    FOREIGN KEY (id_hotel) REFERENCES Hotel(id_hotel)
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Reservation (
    id_reservation INTEGER PRIMARY KEY,
    date_arrivee TEXT,
    date_depart TEXT,
    id_client INTEGER,
    id_chambre INTEGER,
    FOREIGN KEY (id_client) REFERENCES Client(id_client),
    FOREIGN KEY (id_chambre) REFERENCES Chambre(id_chambre)
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS Evaluation (
    id_evaluation INTEGER PRIMARY KEY,
    date TEXT,
    note INTEGER,
    commentaire TEXT,
    id_client INTEGER,
    id_hotel INTEGER,
    FOREIGN KEY (id_client) REFERENCES Client(id_client),
    FOREIGN KEY (id_hotel) REFERENCES Hotel(id_hotel)
)""")

# Hotel
cursor.executemany("INSERT INTO Hotel VALUES (?, ?, ?, ?)", [
    (1, 'Paris', 'France', 75001),
    (2, 'Lyon', 'France', 69002)
])

# Client
cursor.executemany("INSERT INTO Client VALUES (?, ?, ?, ?, ?, ?, ?)", [
    (1, '12 Rue de Paris', 'Paris', 75001, 'jean.dupont@email.fr', '0612345678', 'Jean Dupont'),
    (2, '5 Avenue Victor Hugo', 'Lyon', 69002, 'marie.leroy@email.fr', '0623456789', 'Marie Leroy'),
    (3, '8 Boulevard Saint-Michel', 'Marseille', 13005, 'paul.moreau@email.fr', '0634567890', 'Paul Moreau'),
    (4, '27 Rue Nationale', 'Lille', 59800, 'lucie.martin@email.fr', '0645678901', 'Lucie Martin'),
    (5, '3 Rue des Fleurs', 'Nice', 6000, 'emma.giraud@email.fr', '0656789012', 'Emma Giraud')
])

# Prestation
cursor.executemany("INSERT INTO Prestation VALUES (?, ?, ?)", [
    (1, 15, 'Petit-déjeuner'),
    (2, 30, 'Navette aéroport'),
    (3, 0, 'Wi-Fi gratuit'),
    (4, 50, 'Spa et bien-être'),
    (5, 20, 'Parking sécurisé')
])

# TypeChambre
cursor.executemany("INSERT INTO TypeChambre VALUES (?, ?, ?)", [
    (1, 'Simple', 80),
    (2, 'Double', 120)
])

# Chambre
cursor.executemany("INSERT INTO Chambre VALUES (?, ?, ?, ?, ?, ?)", [
    (1, 201, 2, 0, 1, 1),
    (2, 502, 5, 1, 1, 2),
    (3, 305, 3, 0, 2, 1),
    (4, 410, 4, 0, 2, 2),
    (5, 104, 1, 1, 2, 2),
    (6, 202, 2, 0, 1, 1),
    (7, 307, 3, 1, 1, 2),
    (8, 101, 1, 0, 1, 1)
])

# Réservations (avec id_chambre)
cursor.executemany("INSERT INTO Reservation VALUES (?, ?, ?, ?, ?)", [
    (1, '2025-06-15', '2025-06-18', 1, 1),
    (2, '2025-07-01', '2025-07-05', 2, 2),
    (3, '2025-08-10', '2025-08-14', 3, 3),
    (4, '2025-09-05', '2025-09-07', 4, 4),
    (5, '2025-09-20', '2025-09-25', 5, 5),
    (7, '2025-11-12', '2025-11-14', 2, 6),
    (9, '2026-01-15', '2026-01-18', 4, 7),
    (10, '2026-02-01', '2026-02-05', 2, 8)
])

# Évaluations (avec id_hotel)
cursor.executemany("INSERT INTO Evaluation VALUES (?, ?, ?, ?, ?, ?)", [
    (1, '2025-06-15', 5, 'Excellent séjour, personnel très accueillant.', 1, 1),
    (2, '2025-07-01', 4, 'Chambre propre, bon rapport qualité/prix.', 2, 1),
    (3, '2025-08-10', 3, 'Séjour correct mais bruyant la nuit.', 3, 1),
    (4, '2025-09-05', 5, 'Service impeccable, je recommande.', 4, 1),
    (5, '2025-09-20', 4, 'Très bon petit-déjeuner, hôtel bien situé.', 5, 1)
])

conn.commit()
conn.close()
