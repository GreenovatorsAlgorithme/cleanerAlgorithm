import pandas as pd
import os
from pathlib import Path

# ========== Récupération des chemins (paths) ==========
# __file__ = chemin du script actuel (ex: C:\Algo\mainCode\cleanerAlgorithm\Notebooks\duplicates.py)
# os.path.abspath(__file__) = même chose mais normalisé (sans .. ni .)
# os.path.dirname(chemin) = Tu lui donnes un chemin de fichier, il te rend le dossier dans lequel il est. (ex: ...\Notebooks)
# Deux fois dirname = on remonte de 2 niveaux → racine du projet (cleanerAlgorithm)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# os.path.join(a, b, c) = assemble des parties de chemin correctement (ex: ROOT + "Data" → ...\cleanerAlgorithm\Data)
DATA_DIR = os.path.join(ROOT, 'Data')


def process_file(file_path: str, save_cleaned: bool = False) -> dict:
    """Charge un CSV ou Excel, affiche les doublons avant/après suppression, optionnellement sauvegarde le fichier nettoyé."""
    # os.path.relpath(chemin, départ) = chemin relatif par rapport à "départ"
    # Ex: relpath("C:\...\Data\agriculture\fichier.csv", ROOT) → "Data\agriculture\fichier.csv"
    # Utile pour afficher un chemin court dans les messages au lieu du chemin absolu
    rel_path = os.path.relpath(file_path, ROOT)
    # try/except : si le fichier est manquant, corrompu ou mal formaté, on ne fait pas planter tout le script,
    # on retourne un dict avec la clé "error" pour que la boucle continue avec le fichier suivant
    try:
        # .lower().endswith('.xlsx') = détecte l’extension sans dépendre de la casse (XLSX ou xlsx)
        if file_path.lower().endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
    except Exception as e:
        return {'file': rel_path, 'error': str(e), 'before': None, 'after': None, 'removed': None}

    n_before = len(df)
    n_dup = df.duplicated().sum()
    df_clean = df.drop_duplicates()
    n_after = len(df_clean)
    removed = n_before - n_after

    # Sauvegarde uniquement si demandé et s’il y avait des doublons (évite d’écraser inutilement)
    if save_cleaned and removed > 0:
        if file_path.lower().endswith('.xlsx'):
            df_clean.to_excel(file_path, index=False)
        else:
            df_clean.to_csv(file_path, index=False)

    return {
        'file': rel_path,
        'before': n_before,
        'after': n_after,
        'duplicates': n_dup,
        'removed': removed,
    }


def main():
    # Path(DATA_DIR) = objet Path (pathlib) pour manipuler le dossier Data
    # .exists() = True si le dossier existe, False sinon
    data_path = Path(DATA_DIR)
    if not data_path.exists():
        print(f"Data folder not found: {DATA_DIR}")
        return

    # .rglob("*.csv") = cherche récursivement tous les fichiers dont le nom se termine par .csv
    #    (dans Data et tous ses sous-dossiers : agriculture, waterQuality, etc.)
    # sorted() = trie la liste pour un affichage prévisible
    # On concatène les listes CSV + XLSX pour traiter les deux types
    data_files = sorted(data_path.rglob('*.csv')) + sorted(data_path.rglob('*.xlsx'))
    if not data_files:
        print(f"No CSV or Excel files under {DATA_DIR}")
        return

    print(f"Found {len(data_files)} file(s) (CSV + Excel) under Data/\n")
    results = []

    # file_path est un objet Path ; process_file attend une chaîne, d'où str(file_path)
    for file_path in data_files:
        out = process_file(str(file_path), save_cleaned=False)
        results.append(out)
        if 'error' in out:
            print(f"  ERROR {out['file']}: {out['error']}")
            continue
        print(f"  {out['file']}")
        print(f"    rows: {out['before']} → {out['after']}  (duplicates removed: {out['removed']})")


if __name__ == '__main__':
    main()
