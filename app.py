
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import re

# Connexion SQLite
@st.cache_resource
def get_connection():
    return sqlite3.connect("hotel_reservation.db", check_same_thread=False)

conn = get_connection()
cursor = conn.cursor()

# CSS personnalisé avec effets hover 
st.markdown("""
<style>
    /* Styles globaux */
    .reportview-container .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Boutons - Effet 3D au survol */
    .stButton>button {
    transition: all 0.3s ease-in-out;
    background-color:#50606b;
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

    .stButton>button:active {
        transform: translateY(1px);
    }
    
    /* DataFrames - Effet ligne surlignée */
    .dataframe tbody tr {
        transition: all 0.2s ease;
    }
    .dataframe tbody tr:hover {
        background-color: #4d6570 !important;
        transform: scale(1.01);
        
    }
    
    /* Inputs - Effet bordure animée */
    .stSelectbox>div, .stTextInput>div, 
    .stDateInput>div, .stNumberInput>div {
        transition: all 0.3s ease;
    }
    .stSelectbox>div:hover, .stTextInput>div:hover,
    .stDateInput>div:hover, .stNumberInput>div:hover {
        border: 1px solid #5dade2 !important;
    box-shadow: 0 0 6px rgba(93, 173, 226, 0.4);
    }
    
    /* Onglets - Animation fluide */
    .stTabs [data-baseweb="tab-list"] button {
        transition: all 0.3s ease;
        border-radius: 8px 8px 0 0 !important;
    }
    .stTabs [data-baseweb="tab-list"] button:hover {
        background-color: #8cd7e6 !important;
    }
    .stTabs [data-baseweb="tab-list"] button:hover p {
    color: #1B4F72 !important;
    transform: scale(1.03);
    font-weight: 500;
}

    
    /* Cartes (colonnes) - Effet de profondeur */
    .stColumn {
        transition: all 0.4s ease;
        border-radius: 12px;
        padding: 15px;
    }
    .stColumn:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1) !important;
        background-color: #8cd7e6;
    }
    
    /* Tooltips personnalisés */
    [data-testid="stTooltip"] {
        background-color: #2980B9 !important;
        color: white !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# En-tête avec logo animé
st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 0;">
    <h1 style="text-align:center; color: #154360; transition: all 0.3s ease;">🏨 Gestion de la Chaîne Hôtelière</h1>
    
</div>
""", unsafe_allow_html=True)

# Tabs de navigation avec icônes
tabs = st.tabs([
    "📖 Réservations", 
    "👥 Clients", 
    "🛏️ Chambres disponibles", 
    "➕ Ajouter client", 
    "📅 Ajouter réservation"
])

# --- Onglet : Liste des réservations --- #
with tabs[0]:
    st.subheader("📖 Liste des réservations")
    query = '''
        SELECT r.id_reservation, r.date_arrivee, r.date_depart, c.nom_complet, r.id_chambre
        FROM Reservation r
        JOIN Client c ON r.id_client = c.id_client
        ORDER BY r.date_arrivee
    '''
    reservations = pd.read_sql(query, conn)
    
    # Ajout d'une barre de recherche
    search_term = st.text_input("🔍 Rechercher une réservation")
    if search_term:
        reservations = reservations[reservations.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]
    
    st.dataframe(reservations)

# --- Onglet : Liste des clients --- #
with tabs[1]:
    st.subheader("👥 Liste des clients")
    query = '''
        SELECT id_client, nom_complet, adresse, ville, code_postal, email, telephone
        FROM Client
        ORDER BY id_client
    '''
    clients = pd.read_sql(query, conn)
    
    # Filtres interactifs
    col1, col2 = st.columns(2)
    with col1:
        ville_filter = st.selectbox("Filtrer par ville", ["Toutes"] + sorted(clients['ville'].unique()))
    with col2:
        search_client = st.text_input("🔍 Rechercher un client")
    
    if ville_filter != "Toutes":
        clients = clients[clients['ville'] == ville_filter]
    if search_client:
        clients = clients[clients.astype(str).apply(lambda x: x.str.contains(search_client, case=False)).any(axis=1)]
    
    st.dataframe(clients)

# --- Onglet : Chambres disponibles --- #
with tabs[2]:
    st.subheader("🛏️ Vérifier la disponibilité des chambres")
    
    with st.expander("🔎 Options de recherche", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            date_arrivee = st.date_input("Date d'arrivée", value=date.today())
        with col2:
            date_depart = st.date_input("Date de départ", value=date.today())
        
        type_chambre = st.selectbox("Type de chambre", ["Tous", "Standard", "Deluxe", "Suite"])
    
    if st.button("🔍 Vérifier la disponibilité", key="check_availability"):
        if date_depart <= date_arrivee:
            st.error("La date de départ doit être postérieure à la date d'arrivée.")
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
                sql += " AND type = ?"
                params += (type_chambre,)
            
            sql += " ORDER BY numero"
            
            df = pd.read_sql(sql, conn, params=params)
            if df.empty:
                st.info("Aucune chambre disponible pour cette période.")
            else:
                st.success(f"{len(df)} chambre(s) disponible(s)")
                st.dataframe(df)

# --- Onglet : Ajouter un client --- #
with tabs[3]:
    st.subheader("➕ Ajouter un nouveau client")
    
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
                st.warning("Veuillez remplir tous les champs obligatoires (*)")
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.warning("Veuillez entrer une adresse email valide.")
            elif not telephone.isdigit():
                st.warning("Le téléphone ne doit contenir que des chiffres.")
            else:
                try:
                    cursor.execute('''
                        INSERT INTO Client (nom_complet, adresse, ville, code_postal, email, telephone)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (nom, adresse, ville, code_postal, email, telephone))
                    conn.commit()
                    st.success("✅ Client ajouté avec succès !")
                except sqlite3.Error as e:
                    st.error(f"Erreur lors de l'ajout du client : {e}")

# --- Onglet : Ajouter une réservation --- #
with tabs[4]:
    st.subheader("📅 Ajouter une nouvelle réservation")
    
    with st.form("form_reservation", clear_on_submit=True):
        # Récupération des clients pour le selectbox
        clients_list = pd.read_sql("SELECT id_client, nom_complet FROM Client ORDER BY nom_complet", conn)
        client_selection = st.selectbox(
            "Client*",
            options=clients_list['nom_complet'],
            format_func=lambda x: f"{x} (ID: {clients_list[clients_list['nom_complet'] == x]['id_client'].values[0]})"
        )
        id_client = clients_list[clients_list['nom_complet'] == client_selection]['id_client'].values[0]
        
        # Sélection de la chambre avec vérification de disponibilité
        chambres = pd.read_sql("""
    SELECT c.id_chambre, c.numero, t.nom_type
FROM Chambre c
JOIN Type_Chambre t ON c.id_type = t.id_type

""", conn)

        chambre_selection = st.selectbox(
            "Chambre*",
            options=chambres['numero'],
           format_func=lambda x: f"Chambre {x} ({chambres[chambres['numero'] == x]['nom_type'].values[0]})"

        )
        chambre_id = chambres[chambres['numero'] == chambre_selection]['id_chambre'].values[0]
        
        col1, col2 = st.columns(2)
        with col1:
            date_arrivee = st.date_input("Date d'arrivée*", value=date.today())
        with col2:
            date_depart = st.date_input("Date de départ*", value=date.today() + pd.Timedelta(days=1))
        
        submitted = st.form_submit_button("💾 Enregistrer la réservation")
        
        if submitted:
            if date_depart <= date_arrivee:
                st.error("La date de départ doit être postérieure à la date d'arrivée.")
            else:
                # Vérification de la disponibilité
                sql_check = '''
                    SELECT * FROM Reservation
                    WHERE id_chambre = ? AND date_arrivee < ? AND date_depart > ?
                '''
                cursor.execute(sql_check, (chambre_id, date_depart, date_arrivee))
                conflit = cursor.fetchone()
                
                if conflit:
                    st.error("❌ Cette chambre est déjà réservée pour cette période.")
                else:
                    try:
                        cursor.execute('''
                            INSERT INTO Reservation (date_arrivee, date_depart, id_client, id_chambre)
                            VALUES (?, ?, ?, ?)
                        ''', (date_arrivee, date_depart, id_client, chambre_id))
                        conn.commit()
                        st.success("✅ Réservation enregistrée avec succès !")
                    except sqlite3.Error as e:
                        st.error(f"Erreur lors de l'ajout de la réservation : {e}")

# Pied de page avec effet hover
st.markdown("""
<div style="text-align: center; margin-top: 40px; padding: 15px; background-color: #f8f9fa; border-radius: 10px; transition: all 0.3s ease;">
    <p style="color: #6c757d; transition: all 0.3s ease;">© 2025 Gestion Hôtelière - Tous droits réservés par OUHAMMOU YOUSSEF & AYOUB LAKHLIL </p>
</div>
""", unsafe_allow_html=True)

