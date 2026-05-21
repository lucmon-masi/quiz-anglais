import json
import random
import pathlib
import sys
import time
import os
from collections import defaultdict

# --- IMPORT SECURISE ---
try:
    import questionary
    from questionary import Style
except ImportError:
    print("Erreur : La bibliothèque 'questionary' n'est pas installée.")
    print("Installez-la avec : pip install questionary")
    sys.exit(1)

BASE_DIR = pathlib.Path(__file__).resolve().parent

# --- STATS CHRONO ---
stats = {
    "temps_par_question": [],
    "zone_optimale": 0,
    "rapides": 0,
    "lentes": 0,
    "temps_total": 0
}

# --- STYLE ---
custom_style = Style([
    ('qmark', 'fg:#E91E63 bold'),
    ('question', 'bold'),
    ('answer', 'fg:#2196f3 bold'),
    ('pointer', 'fg:#673ab7 bold'),
    ('highlighted', 'fg:#673ab7 bold'),
    ('selected', 'fg:#cc5454'),
    ('separator', 'fg:#cc5454'),
    ('instruction', 'fg:#8e8e8e italic')
])

# -----------------------------
#     OUTILS D'AFFICHAGE
# -----------------------------
def clear_screen():
    """Nettoie la console (Windows & Linux/Mac)."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header_selection():
    """Affiche l'en-tête persistant de sélection."""
    print("\n" + "=" * 50)
    print("🧠 SÉLECTION DU FICHIER DE QUESTIONS")
    print("=" * 50 + "\n")

# -----------------------------
#     GESTION DES FICHIERS
# -----------------------------

def get_json_files_recursive(directory):
    """Récupère tous les fichiers JSON récursivement."""
    return sorted(list(directory.rglob("*.json")))

def browse_files(current_dir):
    """
    Menu de navigation interactif dans les dossiers.
    Retourne le chemin complet du fichier choisi ou None.
    """
    while True:
        # --- NETTOYAGE ET HEADER À CHAQUE TOUR DE BOUCLE ---
        clear_screen()
        print_header_selection()
        # ---------------------------------------------------

        # Lister contenu : Dossiers d'abord, puis fichiers JSON
        items = sorted(list(current_dir.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
        
        choices = []
        
        # Option Retour si on n'est pas à la racine
        if current_dir != BASE_DIR:
            choices.append(questionary.Choice(".. 🔙 [Retour]", value="BACK"))

        # Ajouter les dossiers et fichiers à la liste
        has_content = False
        for item in items:
            if item.is_dir():
                if list(item.rglob("*.json")):
                    choices.append(questionary.Choice(f"📁 {item.name}/", value=item))
                    has_content = True
            elif item.suffix == '.json':
                choices.append(questionary.Choice(f"📄 {item.name}", value=item))
                has_content = True

        if not has_content and current_dir == BASE_DIR:
             print("❌ Aucun fichier JSON ou dossier contenant des JSON trouvé.")
             sys.exit(0)
        elif not has_content:
             print("❌ Dossier vide.")
             time.sleep(1)
             return None

        # Afficher le menu
        selection = questionary.select(
            f"📂 Dossier actuel : {current_dir.relative_to(BASE_DIR) if current_dir != BASE_DIR else 'Racine'}",
            choices=choices,
            style=custom_style,
            qmark="🔍",
            pointer="👉"
        ).ask()

        # --- CORRECTION CTRL+C ---
        if selection is None:
            raise KeyboardInterrupt
        # -------------------------

        if selection == "BACK":
            return None 
        
        if isinstance(selection, pathlib.Path):
            if selection.is_file():
                return selection 
            elif selection.is_dir():
                result = browse_files(selection)
                if result:
                    return result

def choose_mode():
    clear_screen()
    choice = questionary.select(
        "Choisissez le mode de quiz :",
        choices=[
            "Fichier unique (Navigation)",
            "All-Star (Mix de TOUS les sous-dossiers)"
        ],
        style=custom_style,
        qmark="🎮"
    ).ask()

    # --- CORRECTION CTRL+C ---
    if choice is None:
        raise KeyboardInterrupt
    # -------------------------
    
    return choice

def load_questions_from_single_file():
    selected_file = browse_files(BASE_DIR)

    if not selected_file:
        print("Aucun fichier sélectionné. Arrêt.")
        sys.exit(0)

    clear_screen()
    print(f"\n✅ Fichier choisi : {selected_file.name}")
    print("=" * 50 + "\n")

    with selected_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    random.shuffle(data)
    return data

def load_questions_all_star(nb_total=20):
    json_files = get_json_files_recursive(BASE_DIR)
    
    if not json_files:
        raise FileNotFoundError("Aucun fichier JSON trouvé dans l'arborescence.")

    clear_screen()
    print("\n" + "=" * 50)
    print("🌟 MODE ALL-STAR : MIX GLOBAL")
    print("=" * 50)
    print(f"Fichiers détectés (total) : {len(json_files)}")
    
    dirs_found = set(f.parent.name for f in json_files)
    print(f"Sources : {', '.join(dirs_found)}")
    print("=" * 50)

    all_questions = []

    if len(json_files) >= nb_total:
        selected_files = random.sample(json_files, nb_total)
        for fpath in selected_files:
            with fpath.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not data: continue
            q = random.choice(data)
            all_questions.append(q)
    else:
        base = nb_total // len(json_files)
        reste = nb_total % len(json_files)

        for i, fpath in enumerate(json_files):
            with fpath.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if not data: continue

            nb_from_file = base + (1 if i < reste else 0)
            nb_from_file = min(nb_from_file, len(data))
            
            subset = random.sample(data, nb_from_file)
            all_questions.extend(subset)

    random.shuffle(all_questions)
    if len(all_questions) > nb_total:
        all_questions = all_questions[:nb_total]

    print(f"\n✅ Mode All-Star chargé : {len(all_questions)} questions sélectionnées.\n")
    return all_questions

# -----------------------------
#        LOGIQUE QUIZ
# -----------------------------
def analyze_time(temps):
    if temps < 15:
        stats["rapides"] += 1
        return "⚡ RAPIDE", "Attention à bien comprendre."
    elif 15 <= temps <= 45:
        stats["zone_optimale"] += 1
        return "✅ OPTIMAL", "Parfait équilibre vitesse/compréhension !"
    else:
        stats["lentes"] += 1
        return "⏳ LENT", "Prenez des notes pour accélérer."

def ask_question(q, is_retry=False):
    t0 = time.time()

    original_correct_indices = q["answer"] if isinstance(q["answer"], list) else [q["answer"]]
    is_multiple = len(original_correct_indices) > 1

    shuffled = q["choices"][:]
    random.shuffle(shuffled)

    correct_indices_shuffled = []
    for old_idx in original_correct_indices:
        new_idx = shuffled.index(q["choices"][old_idx])
        correct_indices_shuffled.append(new_idx)

    choices_display = [f"{i}. {choice}" for i, choice in enumerate(shuffled, start=1)]

    prefix = "[RÉVISION]" if is_retry else ""
    print(f"\n{prefix}{q['question']}")

    user_choices_text = []

    try:
        if is_multiple:
            response = questionary.checkbox(
                "Sélectionnez les réponses (Espace pour cocher) :",
                choices=choices_display,
                style=custom_style,
                qmark="?",
                pointer="❯"
            ).ask()
            user_choices_text = response
        else:
            response = questionary.select(
                "Choisissez la bonne réponse :",
                choices=choices_display,
                style=custom_style,
                qmark="?",
                pointer="❯"
            ).ask()
            if response:
                user_choices_text = [response]
            else:
                user_choices_text = None

    except KeyboardInterrupt:
        raise KeyboardInterrupt

    if user_choices_text is None:
        raise KeyboardInterrupt

    user_indices = [choices_display.index(c) for c in user_choices_text]

    print("-" * 40)
    for i, choice in enumerate(shuffled, start=1):
        marker = " [X]" if (i - 1) in user_indices else " [ ]"
        print(f"{i}. {choice}{marker}")
    print("-" * 40)

    is_correct = set(user_indices) == set(correct_indices_shuffled)

    if is_correct:
        print("✅ Correct !\n")
    else:
        correction_details = []
        for idx in correct_indices_shuffled:
            num = idx + 1
            text = shuffled[idx]
            correction_details.append(f"{num} ({text})")
        bonnes_str = ", ".join(correction_details)
        print(f"❌ Incorrect. La ou les bonnes réponses étaient : {bonnes_str}\n")

    temps = time.time() - t0
    stats["temps_par_question"].append(temps)
    stats["temps_total"] += temps

    emoji, message = analyze_time(temps)
    print(f"{emoji} {temps:.1f}s - {message}")

    return is_correct

def print_stats_finales(total_questions):
    if not stats["temps_par_question"]:
        return

    temps_total = stats["temps_total"]
    vitesse_moy = temps_total / total_questions if total_questions > 0 else 0

    print("\n" + "🎯" * 20)
    print("    BILAN EFFICACITÉ APPRENTISSAGE")
    print("🎯" * 20)
    print(f"⏱️  TEMPS TOTAL : {temps_total/60:.1f}min")
    print(f"⚡  VITESSE MOYENNE : {vitesse_moy:.1f}s/question")
    print(f"✅  ZONE OPTIMALE : {stats['zone_optimale']}/{total_questions}")
    print(f"⚡  RÉPONSES RAPIDES (<15s) : {stats['rapides']}")
    print(f"⏳  RÉPONSES LENTES (>45s) : {stats['lentes']}")
    print("🎯" * 20 + "\n")

# -----------------------------
#            MAIN
# -----------------------------
if __name__ == "__main__":
    score = 0
    questions_answered = 0
    total_questions = 0

    try:
        clear_screen()
        mode = choose_mode()
        
        if "Fichier unique" in mode:
            questions = load_questions_from_single_file()
        else:
            questions = load_questions_all_star(nb_total=20)

        total_questions = len(questions)
        missed_questions = []

        # --- PHASE 1 : QUIZ NORMAL ---
        for i, q in enumerate(questions, start=1):
            clear_screen()
            print(f"--- Question {i}/{total_questions} --- ⏱️")

            if ask_question(q):
                score += 1
                time.sleep(1.5)
            else:
                missed_questions.append(q)
                input("\nAppuyez sur Entrée pour continuer...")

            questions_answered += 1

        clear_screen()
        print("\n" + "=" * 40)
        print(f"Quiz terminé ! Score final : {score} / {total_questions}")
        print_stats_finales(total_questions)
        print("=" * 40)

        # --- PHASE 2 : RÉVISION ---
        if missed_questions:
            print(f"\nVous avez raté {len(missed_questions)} questions.")

            choix = questionary.select(
                "Que voulez-vous faire ?",
                choices=["Lancer la révision", "Quitter"],
                style=custom_style
            ).ask()

            if choix == "Lancer la révision":
                tour = 1
                while missed_questions:
                    clear_screen()
                    print(f"\n{'=' * 15} TOUR DE RÉVISION {tour} {'=' * 15}")
                    time.sleep(1)

                    still_missed = []
                    for i, q in enumerate(missed_questions, start=1):
                        clear_screen()
                        print(f"--- Révision {i}/{len(missed_questions)} (Tour {tour}) --- ⏱️")

                        if not ask_question(q, is_retry=True):
                            still_missed.append(q)
                            input("\nAppuyez sur Entrée...")
                        else:
                            time.sleep(1.5)

                    if still_missed:
                        print(f"\nBilan Tour {tour} : {len(still_missed)} erreurs restantes.")
                        c = questionary.select(
                            "Continuer ?",
                            choices=["Oui", "Non"],
                            style=custom_style
                        ).ask()

                        if c == "Non" or c is None:
                            break
                        random.shuffle(still_missed)

                    missed_questions = still_missed
                    tour += 1

                if not missed_questions:
                    print("\n🎉 Bravo ! Tout est corrigé.")
                    print_stats_finales(total_questions)

    except KeyboardInterrupt:
        print("\n\n!!! Interruption détectée (CTRL+C) !!!")
        sys.exit(0)
