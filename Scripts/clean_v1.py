import numpy as np
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

REPORT_PATH = os.path.join(ROOT, 'cleaning_report.txt')


class DropingScript:
    _PLACEHOLDERS = ("", "nan", "null", "undefined", "NaN", "None")

    def __init__(self, dataframe, max_missing_fraction=0.5):
        self.dataframe = dataframe.copy()
        self.max_missing_fraction = max_missing_fraction

    def drop_duplicates(self):
        self.dataframe = self.dataframe.drop_duplicates()
        return self

    def drop_nulls(self):
        self.dataframe = self.dataframe.dropna()
        return self

    def drop_rows_with_any_zero(self):
        numeric = self.dataframe.select_dtypes(include=np.number)
        if not numeric.empty:
            self.dataframe = self.dataframe.loc[~(numeric == 0).any(axis=1)]
        return self

    def placeholders_to_nan(self):
        self.dataframe = self.dataframe.replace(list(self._PLACEHOLDERS), np.nan)
        return self

    def drop_or_fill_missing_values(self):
        df = self.dataframe
        n_cols = df.shape[1]
        if n_cols == 0:
            return self
        max_missing = self.max_missing_fraction * n_cols
        self.dataframe = df.loc[df.isna().sum(axis=1) <= max_missing].copy()
        means = self.dataframe.select_dtypes(include=np.number).mean()
        self.dataframe = self.dataframe.fillna(means)
        return self


def process_file(file_path: str, save_cleaned: bool = False) -> dict:
    """Charge un CSV ou Excel, analyse les doublons et valeurs manquantes avant/après,
    optionnellement sauvegarde le fichier nettoyé, et retourne les stats."""
        # os.path.relpath(chemin, départ) = chemin relatif par rapport à "départ"
    # Ex: relpath("C:\...\Data\agriculture\fichier.csv", ROOT) → "Data\agriculture\fichier.csv"
    # Utile pour afficher un chemin court dans les messages au lieu du chemin absolu    
    rel_path = os.path.relpath(file_path, ROOT)
    # try/except : si le fichier est manquant, corrompu ou mal formaté, on ne fait pas planter tout le script,
    # on retourne un dict avec la clé "error" pour que la boucle continue avec le fichier suivant
    try:
                # .lower().endswith('.xlsx') = détecte l’extension sans dépendre de la casse (XLSX ou xlsx)
        if file_path.lower().endswith('.xlsx'):
            dirty = pd.read_excel(file_path)
        else:
            dirty = pd.read_csv(file_path)
    except Exception as e:
        return {'file': rel_path, 'error': str(e)}

    # --- Stats BEFORE cleaning ---
    duplicates_dirty = dirty.duplicated().sum()
    missing_dirty = dirty.isnull().sum().sum()
    n_before = len(dirty)

    # --- Clean using DropingScript ---
    cleaner = DropingScript(dirty)
    cleaner.drop_duplicates() \
           .placeholders_to_nan() \
           .drop_or_fill_missing_values()
    clean = cleaner.dataframe

    # --- Stats AFTER cleaning ---
    duplicates_clean = clean.duplicated().sum()  # should always be 0
    missing_clean = clean.isnull().sum().sum()
    n_after = len(clean)
    removed = n_before - n_after

    # Sauvegarde uniquement si demandé et s’il y avait des doublons (évite d’écraser inutilement)
    if save_cleaned and removed > 0:
        if file_path.lower().endswith('.xlsx'):
            clean.to_excel(file_path, index=False)
        else:
            clean.to_csv(file_path, index=False)

    return {
        'file': rel_path,
        # before
        'n_before': n_before,
        'duplicates_dirty': int(duplicates_dirty),
        'missing_dirty': int(missing_dirty),
        # after
        'n_after': n_after,
        'removed': removed,
        'duplicates_clean': int(duplicates_clean),
        'missing_clean': int(missing_clean),
        # verdict
        'complete': missing_clean == 0,
    }


def generate_report(results: list) -> str:
    """Génère un rapport texte à partir de la liste des résultats de process_file."""
    lines = []
    lines.append("=" * 50)
    lines.append("       DATA CLEANING REPORT")
    lines.append("=" * 50)

    total_duplicates = 0
    total_missing_before = 0
    total_missing_after = 0
    errors = []

    for r in results:
        lines.append(f"\nFile: {r['file']}")
        lines.append("-" * 40)

        if 'error' in r:
            lines.append(f"  ERROR: {r['error']}")
            errors.append(r['file'])
            continue

        lines.append("  Dirty Dataset:")
        lines.append(f"    - Total rows          : {r['n_before']}")
        lines.append(f"    - Duplicates found    : {r['duplicates_dirty']}")
        lines.append(f"    - Missing values found: {r['missing_dirty']}")

        lines.append("  Clean Dataset:")
        lines.append(f"    - Total rows          : {r['n_after']}")
        lines.append(f"    - Remaining duplicates: {r['duplicates_clean']}")
        lines.append(f"    - Remaining missing   : {r['missing_clean']}")

        completeness = "100% complete" if r['complete'] else "not fully complete"
        lines.append(f"  Summary:")
        lines.append(f"    {r['duplicates_dirty']} duplicate row(s) removed.")
        lines.append(f"    {r['missing_dirty']} missing value(s) found before cleaning.")
        lines.append(f"    The cleaned dataset is now {completeness}.")

        total_duplicates += r['duplicates_dirty']
        total_missing_before += r['missing_dirty']
        total_missing_after += r['missing_clean']

    # --- Global summary ---
    lines.append("\n" + "=" * 50)
    lines.append("  GLOBAL SUMMARY")
    lines.append("=" * 50)
    ok_files = [r for r in results if 'error' not in r]
    lines.append(f"  Files processed         : {len(ok_files)}")
    lines.append(f"  Files with errors       : {len(errors)}")
    lines.append(f"  Total duplicates removed: {total_duplicates}")
    lines.append(f"  Total missing (before)  : {total_missing_before}")
    lines.append(f"  Total missing (after)   : {total_missing_after}")
    global_status = "100% complete" if total_missing_after == 0 else "not fully complete"
    lines.append(f"  Global data status      : {global_status}")
    lines.append("=" * 50)

    return "\n".join(lines)


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

    print(f"Found {len(data_files)} file(s) under Data/\n")
    results = []
    # file_path est un objet Path ; process_file attend une chaîne, d'où str(file_path)
    for file_path in data_files:
        out = process_file(str(file_path), save_cleaned=False)
        results.append(out)

        if 'error' in out:
            print(f"  ERROR  {out['file']}: {out['error']}")
        else:
            status = "CLEAN" if out['complete'] else "INCOMPLETE"
            print(f"  [{status}] {out['file']}")
            print(f"    rows: {out['n_before']} → {out['n_after']}  "
                  f"(duplicates: {out['duplicates_dirty']}  |  missing before: {out['missing_dirty']}  |  missing after: {out['missing_clean']})")

    # --- Generate and save report ---
    report_text = generate_report(results)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\nReport generated: {os.path.relpath(REPORT_PATH, ROOT)}")
    print("\n" + report_text)


if __name__ == '__main__':
    main()
