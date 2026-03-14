import pandas as pd

# Load datasets
dirty = pd.read_csv("dirty.csv")
clean = pd.read_csv("clean.csv")

# Count duplicates in dirty dataset
duplicates_dirty = dirty.duplicated().sum()

# Count missing values
missing_dirty = dirty.isnull().sum().sum()
missing_clean = clean.isnull().sum().sum()

# Check duplicates in clean dataset
duplicates_clean = clean.duplicated().sum()

# Generate report
report = f"""
Data Cleaning Report
--------------------

Dirty Dataset:
- Duplicates found: {duplicates_dirty}
- Missing values found: {missing_dirty}

Clean Dataset:
- Remaining duplicates: {duplicates_clean}
- Remaining missing values: {missing_clean}

Summary:
{duplicates_dirty} duplicate rows were removed and {missing_dirty} missing values were handled.
The cleaned dataset is now {'100% complete' if missing_clean == 0 else 'not fully complete'}.
"""

# Save report to file
with open("cleaning_report.txt", "w") as file:
    file.write(report)

print("Report generated: cleaning_report.txt")