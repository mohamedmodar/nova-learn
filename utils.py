# utils.py
"""Utility functions for the recommender system."""

import re
import pandas as pd
import nltk
import ast
import os

# --- NLTK Path Setup ---
NLTK_DATA_DIR = os.path.join(os.path.expanduser("~"), "nltk_data")
if NLTK_DATA_DIR not in nltk.data.path:
    nltk.data.path.append(NLTK_DATA_DIR)
print(f"Ensured NLTK data path includes: {NLTK_DATA_DIR}")
print(f"Current NLTK data paths: {nltk.data.path}")
os.makedirs(NLTK_DATA_DIR, exist_ok=True)

# --- NLTK Resource Download (Stopwords only) --- 
def download_nltk_resources(resources):
    """Downloads necessary NLTK resources if they are not found."""
    try:
        print("Checking NLTK resources...")
        for resource_id, resource_name in resources.items():
            try:
                nltk.data.find(resource_id, paths=[NLTK_DATA_DIR] + nltk.data.path)
                print(f"  - Resource \t\t{resource_name}\t\t found.")
            except LookupError:
                print(f"  - Resource \t\t{resource_name}\t\t not found. Downloading to {NLTK_DATA_DIR}...")
                nltk.download(resource_name, quiet=False, download_dir=NLTK_DATA_DIR)
                print(f"  - Resource \t\t{resource_name}\t\t downloaded.")
                try:
                    nltk.data.find(resource_id, paths=[NLTK_DATA_DIR])
                    print(f"  - Verified \t\t{resource_name}\t\t presence after download in {NLTK_DATA_DIR}.")
                except LookupError:
                     print(f"  - ERROR: Failed to find \t\t{resource_name}\t\t in {NLTK_DATA_DIR} even after download attempt.")
        print("NLTK resource check complete.")
    except Exception as e:
        print(f"An error occurred during NLTK resource download: {e}")

# Define required resources (Only stopwords needed now for TF-IDF preprocessing)
REQUIRED_NLTK_RESOURCES = {
    "corpora/stopwords": "stopwords"
}
download_nltk_resources(REQUIRED_NLTK_RESOURCES)

# Import modules that depend on the resources
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Initialize stemmer and stopwords after ensuring resources are available
stemmer = PorterStemmer()
stop_words = set(stopwords.words("english"))

# --- Fallback Regex Tokenizer ---
def regex_tokenize(text):
    """A simple regex-based tokenizer splitting on non-alphanumeric characters."""
    if not isinstance(text, str):
        return []
    # Split on one or more non-alphanumeric characters
    tokens = re.split(r"[^a-z0-9]+", text.lower())
    # Remove empty strings that can result from multiple delimiters
    return [token for token in tokens if token]

def preprocess_text_tfidf(text):
    """
    Preprocesses text specifically for TF-IDF using regex tokenizer:
    - Lowercases
    - Removes non-alphanumeric characters (handled by tokenizer)
    - Tokenizes using regex
    - Removes stopwords
    - Stems tokens

    Args:
        text (str): The input text string.

    Returns:
        str: The processed text string, ready for TF-IDF vectorization.
           Returns an empty string if input is not a valid string.
    """
    if not isinstance(text, str):
        return ""
    
    # Tokenize using the fallback regex tokenizer
    tokens = regex_tokenize(text)
        
    # Remove stopwords and stem
    stemmed_tokens = [
        stemmer.stem(word) for word in tokens if word not in stop_words
        # No need for isalnum() check as regex_tokenize handles it
    ]
    return " ".join(stemmed_tokens)

def load_course_data(file_path):
    """
    Loads the course data from a CSV file and performs basic cleaning,
    focusing on the columns specified by the user: Skills, title, adjusted_rating, descrition.

    Args:
        file_path (str): The path to the course data CSV file.

    Returns:
        pd.DataFrame: Loaded and cleaned DataFrame, or None if loading fails.
    """
    try:
        df = pd.read_csv(file_path)
        print(f"Successfully loaded course data from {file_path}. Shape: {df.shape}")
        print(f"Original columns: {df.columns.tolist()}")
        
        # Define the REQUIRED columns based on user clarification
        # Using the LATEST corrected names: Skills, title, adjusted_rating, descrition
        required_cols_map = {
            "skills": "Skills", 
            "title": "title", 
            "adjusted_rating": "adjusted_rating", 
            "descrition": "descrition" # Using CORRECTED name 'descrition'
        }
        
        # Find actual column names (case-insensitive matching)
        actual_cols = {}
        available_cols_lower = {col.lower(): col for col in df.columns}
        
        for target_col, user_specified_name in required_cols_map.items():
            if user_specified_name.lower() in available_cols_lower:
                actual_cols[target_col] = available_cols_lower[user_specified_name.lower()]
            else:
                print(f"Warning: Required column \t\t{user_specified_name}\t\t (target: {target_col}) not found in CSV. Will be treated as missing.")
                actual_cols[target_col] = None # Mark as not found
                # Create the column with None if it doesn't exist at all
                if target_col not in df.columns:
                     df[target_col] = None
                     
        # Rename columns to standard internal names if found with different casing
        rename_dict = {actual: target for target, actual in actual_cols.items() if actual and actual != target}
        if rename_dict:
            print(f"Renaming columns for consistency: {rename_dict}")
            df.rename(columns=rename_dict, inplace=True)
            
        # Ensure standard columns exist, even if source was missing
        for col in required_cols_map.keys():
            if col not in df.columns:
                df[col] = None
                print(f"Ensured standard column \t\t{col}\t\t exists (filled with None).")

        # Clean specific columns
        if "skills" in df.columns:
            df["skills_list"] = df["skills"].apply(parse_skills)
        else:
             df["skills_list"] = pd.Series([[] for _ in range(len(df))]) # Create empty list if skills column missing
             
        # Ensure essential text columns are strings
        if "title" in df.columns:
            df["title"] = df["title"].fillna("").astype(str)
        if "descrition" in df.columns: # Use CORRECTED name
            df["descrition"] = df["descrition"].fillna("").astype(str)
            
        print(f"Columns after loading and standardization: {df.columns.tolist()}")
        # Keep only the relevant columns + the derived skills_list
        final_cols_to_keep = list(required_cols_map.keys()) + ["skills_list"]
        # Filter out any columns that weren't actually found or created
        final_cols_to_keep = [col for col in final_cols_to_keep if col in df.columns]
        
        print(f"Keeping columns: {final_cols_to_keep}")
        return df[final_cols_to_keep]
        
    except FileNotFoundError:
        print(f"Error: Course data file not found at {file_path}.")
        return None
    except Exception as e:
        print(f"Error loading or processing course data from {file_path}: {e}")
        return None

def parse_skills(skill_entry):
    """
    Safely parses the 'skills' column entry into a list of strings.
    Handles NaN, stringified lists, single strings, and actual lists.
    Converts skills to lowercase.
    """
    if pd.isna(skill_entry):
        return []
    try:
        # Handle stringified lists (e.g., "[		skill1		, 		skill2		]")
        if isinstance(skill_entry, str) and skill_entry.startswith("[") and skill_entry.endswith("]"):
            evaluated_list = ast.literal_eval(skill_entry)
            if isinstance(evaluated_list, list):
                # Ensure all elements are strings and handle potential NaN within the list
                return [str(s).lower().strip() for s in evaluated_list if pd.notna(s) and str(s).strip()]
            else:
                # If eval results in non-list, treat as single skill if not NaN
                skill_str = str(evaluated_list).strip()
                return [skill_str.lower()] if pd.notna(evaluated_list) and skill_str else []
        # Handle single string skills (potentially comma-separated - split if needed, or treat as one)
        elif isinstance(skill_entry, str):
             # Simple case: treat the whole string as one skill or split if delimiters are expected
             # For now, treating as one skill after stripping whitespace
            skill_entry_stripped = skill_entry.strip()
            return [skill_entry_stripped.lower()] if skill_entry_stripped else []
        # Handle actual lists provided directly
        elif isinstance(skill_entry, list):
            return [str(s).lower().strip() for s in skill_entry if pd.notna(s) and str(s).strip()]
    except (ValueError, SyntaxError, TypeError) as e:
        # Fallback for unparseable strings: treat as a single skill
        if isinstance(skill_entry, str):
            print(f"Warning: Could not parse skill entry \t\t{skill_entry}\t\t, treating as single skill. Error: {e}")
            skill_entry_stripped = skill_entry.strip()
            return [skill_entry_stripped.lower()] if skill_entry_stripped else []
        else:
            print(f"Warning: Could not parse skill entry of type {type(skill_entry)}: {skill_entry}")
            return []
    # Final fallback for other types (e.g., numbers) - convert to string if not NaN
    skill_entry_str = str(skill_entry).strip()
    return [skill_entry_str.lower()] if pd.notna(skill_entry) and skill_entry_str else []

# Filter function might need adjustment if filtering columns are removed
def filter_courses(df, level=None, providers=None, required_skills=None, duration_pref=None):
    """
    Applies structured filters to the course DataFrame.
    NOTE: This function might be less useful now as columns like 'level', 'provider', 'duration' 
          are not in the user-specified list to keep.
          Keeping the structure but adding warnings.
    """
    if df is None:
        return pd.DataFrame()
        
    filtered_df = df.copy()
    print("Applying filters. Note: Some filter columns might not be available based on user selection.")

    # Filter by level 
    if level and level.lower() != "all levels":
        if "level" in filtered_df.columns:
             filtered_df = filtered_df[filtered_df["level"].str.contains(level, case=False, na=False)]
        else:
            print("Warning: \t\tlevel\t\t column not available for filtering.")

    # Filter by provider
    if providers and isinstance(providers, list) and len(providers) > 0:
        if "provider" in filtered_df.columns:
             filtered_df = filtered_df[filtered_df["provider"].isin(providers)]
        else:
            print("Warning: \t\tprovider\t\t column not available for filtering.")

    # Filter by required skills (using skills_list derived from 'Skills')
    if required_skills and isinstance(required_skills, list) and len(required_skills) > 0:
        if "skills_list" in filtered_df.columns:
            required_skills_lower = {s.lower() for s in required_skills}
            def create_set(x):
                try:
                    return set(x) if isinstance(x, list) else set()
                except TypeError:
                    return set()
            filtered_df["skills_set"] = filtered_df["skills_list"].apply(create_set)
            filtered_df = filtered_df[filtered_df["skills_set"].apply(lambda x: required_skills_lower.issubset(x))]
            filtered_df = filtered_df.drop(columns=["skills_set"])
        else:
             print("Warning: \t\tskills_list\t\t column not available for filtering.")

    # Filter by duration
    if duration_pref and duration_pref != "any":
        if "duration" in filtered_df.columns:
            filtered_df["duration_numeric"] = pd.to_numeric(filtered_df["duration"], errors="coerce")
            if duration_pref == "short":
                filtered_df = filtered_df[filtered_df["duration_numeric"] <= 10]
            elif duration_pref == "medium":
                filtered_df = filtered_df[(filtered_df["duration_numeric"] > 10) & (filtered_df["duration_numeric"] <= 50)]
            elif duration_pref == "long":
                filtered_df = filtered_df[filtered_df["duration_numeric"] > 50]
            filtered_df = filtered_df.drop(columns=["duration_numeric"])
        else:
            print("Warning: \t\tduration\t\t column not available for filtering.")

    return filtered_df

