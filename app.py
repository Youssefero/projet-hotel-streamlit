
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, timedelta
import re


@st.cache_resource
def get_connection():
    return sqlite3.connect("hotel_reservation.db", check_same_thread=False)

conn = get_connection()
cursor = conn.cursor()

# CSS personnalisé avec effets hover
st.markdown("""
<style>
    .reportview-container .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        transition: all 0.3s ease-in-out;
        background-color: #50606b;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 6px;
        padding: 0.6em 1.2em;
    }
    .stButton>button:hover {
        background-color: #5dade2 !important;
        color: white !important;
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    .dataframe tbody tr:hover {
        background-color: #f5f5f5;
    }
</style>
""", unsafe_allow_html=True)

# Titre principal
st.markdown("""
<div style="display: flex; align-items: center; justify-content: center; padding: 10px 0;">
    <h1 style="color: #154360;">🏨 Gestion de la Chaîne Hôtelière</h1>
</div>
""", unsafe_allow_html=True)

# Onglets
tabs = st.tabs([
    "📖 Réservations", 
    "👥 Clients", 
    "🛏️ Chambres disponibles", 
    "➕ Ajouter client", 
    "📅 Ajouter réservation"
])

# --- Réservations
with tabs[0]:
    st.subheader("📖 Liste des réservations")
    query = '''
        SELECT r.id_reservation, r.date_arrivee, r.date_depart, c.nom_complet, r.id_chambre
        FROM Reservation r
        JOIN Client c ON r.id_client = c.id_client
        ORDER BY r.date_arrivee
    '''
    reservations = pd.read_sql(query, conn)
    search_term = st.text_input("🔍 Rechercher une réservation")
    if search_term:
        reservations = reservations[
            reservations.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
        ]
    st.dataframe(reservations)

# --- Clients
with tabs[1]:
    st.subheader("👥 Liste des clients")
    query = '''
        SELECT id_client, nom_complet, adresse, ville, code_postal, email, telephone
        FROM Client
        ORDER BY id_client
    '''
    clients = pd.read_sql(query, conn)
    col1, col2 = st.columns(2)
    with col1:
        ville_filter = st.selectbox("Filtrer par ville", ["Toutes"] + sorted(clients['ville'].unique()))
    with col2:
        search_client = st.text_input("🔍 Rechercher un client")
    if ville_filter != "Toutes":
        clients = clients[clients['ville'] == ville_filter]
    if search_client:
        clients = clients[
            clients.astype(str).apply(lambda x: x.str.contains(search_client, case=False)).any(axis=1)
        ]
    st.dataframe(clients)

# --- Chambres disponibles
with tabs[2]:
    st.subheader("🛏️ Vérifier la disponibilité des chambres")
    with st.expander("🔎 Options de recherche", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            date_arrivee = st.date_input("Date d'arrivée", value=date.today())
        with col2:
            date_depart = st.date_input("Date de départ", value=date.today() + timedelta(days=1))
        type_chambre = st.selectbox("Type de chambre", ["Tous", "Simple", "Double"])
    if st.button("🔍 Vérifier la disponibilité"):
        if date_depart <= date_arrivee:
            st.error("Date de départ invalide.")
        else:
            sql = '''
                SELECT * FROM Chambre
                WHERE id_chambre NOT IN (
                    SELECT id_chambre FROM Reservation
                    WHERE date_arrivee < ? AND date_depart > ?
                )
            '''
            params = (date_depart, date_arrivee)
            if type_chambre != "Tous":
                sql += " AND id_type = ?"
                params += (1 if type_chambre == "Simple" else 2,)
            df = pd.read_sql(sql, conn, params=params)
            if df.empty:
                st.info("Aucune chambre disponible pour cette période.")
            else:
                st.success(f"{len(df)} chambre(s) disponible(s)")
                st.dataframe(df)

# --- Ajouter client
with tabs[3]:
    st.subheader("➕ Ajouter un client")
    with st.form("form_client", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nom = st.text_input("Nom complet*")
            adresse = st.text_input("Adresse*")
            ville = st.text_input("Ville*")
        with col2:
            code_postal = st.text_input("Code postal*")
            email = st.text_input("Email*")
            telephone = st.text_input("Téléphone*")
        submitted = st.form_submit_button("💾 Enregistrer le client")
        if submitted:
            if not all([nom, adresse, ville, code_postal, email, telephone]):
                st.warning("Veuillez remplir tous les champs obligatoires.")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.warning("Email invalide.")
            elif not telephone.isdigit():
                st.warning("Téléphone invalide.")
            else:
                try:
                    cursor.execute('''
                        INSERT INTO Client (nom_complet, adresse, ville, code_postal, email, telephone)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (nom, adresse, ville, code_postal, email, telephone))
                    conn.commit()
                    st.success("✅ Client ajouté avec succès.")
                except sqlite3.Error as e:
                    st.error(f"Erreur : {e}")

# --- Ajouter réservation
with tabs[4]:
    st.subheader("📅 Ajouter une réservation")
    with st.form("form_reservation", clear_on_submit=True):
        # Sélection du client avec dictionnaire pour une identification claire
        clients_df = pd.read_sql("SELECT id_client, nom_complet FROM Client ORDER BY nom_complet", conn)
        if clients_df.empty:
            st.error("Aucun client trouvé. Veuillez d'abord ajouter un client.")
            st.stop()
        clients_options = {
            f"{row['nom_complet']} (ID: {row['id_client']})": row['id_client']
            for _, row in clients_df.iterrows()
        }
        # Fixation d'un index par défaut pour être sûr d'avoir une valeur non None
        client_selection = st.selectbox("Client*", list(clients_options.keys()), index=0)
        id_client = clients_options[client_selection]

        # Sélection des chambres
        chambres_df = pd.read_sql("""
            SELECT c.id_chambre, c.numero, t.nom_type
            FROM Chambre c
            JOIN TypeChambre t ON c.id_type = t.id_type
            ORDER BY c.numero
        """, conn)

        if chambres_df.empty:
            st.error("Aucune chambre trouvée.")
            st.stop()
        chambres_options = {
            f"Chambre {row['numero']} ({row['nom_type']})": row['id_chambre']
            for _, row in chambres_df.iterrows()
        }
        # Ici, nous fixons également l'index par défaut pour éviter un résultat None.
        chambre_selection = st.selectbox("Chambre*", list(chambres_options.keys()), index=0)
        chambre_id = chambres_options[chambre_selection]

        col1, col2 = st.columns(2)
        with col1:
            date_arrivee = st.date_input("Date d'arrivée*", value=date.today())
        with col2:
            date_depart = st.date_input("Date de départ*", value=date.today() + timedelta(days=1))

        submitted = st.form_submit_button("💾 Réserver")
        
        if submitted:
            if date_depart <= date_arrivee:
                st.error("La date de départ doit être après la date d'arrivée.")
            else:
                # Vérification des conflits de réservation pour la chambre sélectionnée
                sql_check = '''
                    SELECT * FROM Reservation
                    WHERE id_chambre = ? AND date_arrivee < ? AND date_depart > ?
                '''
                cursor.execute(sql_check, (chambre_id, date_depart, date_arrivee))
                conflit = cursor.fetchone()
                if conflit:
                    st.error("❌ Cette chambre est déjà réservée pour la période sélectionnée.")
                else:
                    try:
                        cursor.execute('''
                            INSERT INTO Reservation (date_arrivee, date_depart, id_client, id_chambre)
                            VALUES (?, ?, ?, ?)
                        ''', (date_arrivee, date_depart, id_client, chambre_id))
                        conn.commit()
                        st.success("✅ Réservation enregistrée.")
                    except sqlite3.Error as e:
                        st.error(f"Erreur : {e}")

# Pied de page
st.markdown("""
<div style="text-align: center; margin-top: 40px; padding: 15px; background-color: #f8f9fa; border-radius: 10px;">
    <p style="color: #6c757d;">© 2025 Projet Gestion Hôtelière - OUHAMMOU YOUSSEF & AYOUB LAKHLIL</p>
</div>
""", unsafe_allow_html=True)



