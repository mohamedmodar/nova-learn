import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pandas as pd
from recommender_interface_advanced_v6 import get_recommendations, df_all_courses
import webbrowser

class InteractiveRecommenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Personalized Course Recommender")
        self.root.geometry("1200x800")
        
        # --- State Management ---
        self.session_history = [] # List of item_ids for liked courses
        self.disliked_history = [] # List of item_ids for disliked courses
        self.last_results = pd.DataFrame()

        # --- Main Layout ---
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)
        
        # --- Left Panel: Search Controls ---
        controls_frame = ttk.LabelFrame(main_frame, text="🔍 Search Controls", padding="10")
        controls_frame.grid(row=0, column=0, padx=(0, 10), pady=(0, 10), sticky="ns")
        main_frame.grid_columnconfigure(0, weight=0)

        # --- Middle Panel: Results ---
        results_frame = ttk.LabelFrame(main_frame, text="📚 Recommendations", padding="10")
        results_frame.grid(row=0, column=1, sticky="nsew")
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # --- Right Panel: History ---
        history_area_frame = ttk.LabelFrame(main_frame, text="🧠 Session Preferences", padding="10")
        history_area_frame.grid(row=0, column=2, sticky="ns", padx=(10, 0))
        main_frame.grid_columnconfigure(2, weight=0)

        self.setup_controls(controls_frame)
        self.setup_results_area(results_frame)
        self.setup_history_area(history_area_frame)
        
    def setup_controls(self, frame):
        row = 0
        # Query
        ttk.Label(frame, text="Search Query:").grid(row=row, column=0, sticky="w", pady=2)
        self.query_entry = ttk.Entry(frame, width=40)
        self.query_entry.grid(row=row+1, column=0, sticky="ew", pady=(0, 10))
        row += 2
        
        # Level
        ttk.Label(frame, text="Level:").grid(row=row, column=0, sticky="w", pady=2)
        self.level_var = tk.StringVar(value="All Levels")
        level_combo = ttk.Combobox(frame, textvariable=self.level_var, values=('All Levels', 'Beginner', 'Intermediate', 'Advanced'))
        level_combo.grid(row=row+1, column=0, sticky="ew", pady=(0, 10))
        row += 2
        
        # Skills
        ttk.Label(frame, text="Skills (comma-separated):").grid(row=row, column=0, sticky="w", pady=2)
        self.skills_entry = ttk.Entry(frame, width=40)
        self.skills_entry.grid(row=row+1, column=0, sticky="ew", pady=(0, 10))
        row += 2

        # AI Model
        ttk.Label(frame, text="AI Model:").grid(row=row, column=0, sticky="w", pady=2)
        self.model_var = tk.StringVar(value="hybrid")
        model_combo = ttk.Combobox(frame, textvariable=self.model_var, values=('hybrid', 'sbert', 'two_tower', 'tfidf'))
        model_combo.grid(row=row+1, column=0, sticky="ew", pady=(0, 10))
        row += 2

        # Search Button
        search_button = ttk.Button(frame, text="Search", command=self.perform_search)
        search_button.grid(row=row, column=0, sticky="ew", pady=10)
        row += 1

    def setup_results_area(self, frame):
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=0)

        # --- Results Display ---
        results_frame = ttk.LabelFrame(frame, text="📚 Recommendations", padding="10")
        results_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, font=('Consolas', 9))
        self.results_text.grid(row=0, column=0, sticky="nsew")
        
        # --- History Panel ---
        history_frame = ttk.LabelFrame(frame, text="🧠 Session Preferences", padding="10")
        history_frame.grid(row=0, column=1, sticky="ns")
        history_frame.grid_rowconfigure(1, weight=1)

        ttk.Label(history_frame, text="Courses added here will personalize\nyour next search.", justify=tk.LEFT).grid(row=0, column=0, sticky="ew")
        
        self.liked_listbox = tk.Listbox(history_frame, height=10, background="#e6ffed")
        self.liked_listbox.grid(row=1, column=0, sticky="ew", pady=5)
        
        ttk.Label(history_frame, text="Disliked Courses 👎").grid(row=2, column=0, sticky="w", pady=(10,0))
        self.disliked_listbox = tk.Listbox(history_frame, height=10, background="#ffe6e6")
        self.disliked_listbox.grid(row=3, column=0, sticky="ew", pady=5)
        
        button_frame = ttk.Frame(history_frame)
        button_frame.grid(row=4, column=0, pady=10)
        ttk.Button(button_frame, text="Clear Liked", command=self.clear_liked_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Disliked", command=self.clear_disliked_history).pack(side=tk.LEFT)

    def setup_history_area(self, frame):
        # Liked History
        ttk.Label(frame, text="Liked Courses 👍").grid(row=0, column=0, sticky="w")
        self.liked_listbox = tk.Listbox(frame, height=10, background="#e6ffed")
        self.liked_listbox.grid(row=1, column=0, sticky="ew", pady=5)
        
        # Disliked History
        ttk.Label(frame, text="Disliked Courses 👎").grid(row=2, column=0, sticky="w", pady=(10,0))
        self.disliked_listbox = tk.Listbox(frame, height=10, background="#ffe6e6")
        self.disliked_listbox.grid(row=3, column=0, sticky="ew", pady=5)
        
        # Clear Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, pady=10)
        ttk.Button(button_frame, text="Clear Liked", command=self.clear_liked_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Disliked", command=self.clear_disliked_history).pack(side=tk.LEFT)

    def perform_search(self):
        query = self.query_entry.get().strip()
        skills_input = self.skills_entry.get().strip()
        skills = [s.strip().lower() for s in skills_input.split(',')] if skills_input else None
        
        if not query and not self.session_history:
            messagebox.showwarning("Search Warning", "Please provide a search query or add items to your liked history.")
            return
            
        print("\n--- Performing New Search ---")
        print(f"Query: '{query}' | Liked Items: {len(self.session_history)} | Disliked Items: {len(self.disliked_history)}")
        
        try:
            self.last_results = get_recommendations(
                query_text=query,
                level=self.level_var.get(),
                skills=skills,
                model_type=self.model_var.get(),
                user_history=self.session_history if self.session_history else None,
                disliked_history=self.disliked_history if self.disliked_history else None,
                top_n=10
            )
            self.display_results()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            print(f"ERROR: {e}")

    def add_to_liked_history(self, item_id, title):
        # If it's currently disliked, remove it from there first
        if item_id in self.disliked_history:
            self.disliked_history.remove(item_id)
            self.update_listbox(self.disliked_listbox, self.disliked_history, "👎")

        # Add to liked history if it's not already there
        if item_id not in self.session_history:
            self.session_history.append(item_id)
            self.update_listbox(self.liked_listbox, self.session_history, "👍")
        else:
            messagebox.showinfo("Info", "This course is already in your liked list.")

    def add_to_disliked_history(self, item_id, title):
        # If it's currently liked, remove it from there first
        if item_id in self.session_history:
            self.session_history.remove(item_id)
            self.update_listbox(self.liked_listbox, self.session_history, "👍")

        # Add to disliked history if it's not already there
        if item_id not in self.disliked_history:
            self.disliked_history.append(item_id)
            self.update_listbox(self.disliked_listbox, self.disliked_history, "👎")
        else:
            messagebox.showinfo("Info", "This course is already in your disliked list.")

    def clear_liked_history(self):
        self.session_history.clear()
        self.liked_listbox.delete(0, tk.END)

    def clear_disliked_history(self):
        self.disliked_history.clear()
        self.disliked_listbox.delete(0, tk.END)

    def update_listbox(self, listbox, history_list, prefix):
        """Helper function to refresh a listbox based on its corresponding list."""
        listbox.delete(0, tk.END)
        # We need to get the titles from the main dataframe
        if not history_list:
            return
        
        history_df = df_all_courses[df_all_courses['item_id'].isin(history_list)]
        # Create a map to preserve order
        id_to_title_map = pd.Series(history_df.title.values,index=history_df.item_id).to_dict()

        for item_id in history_list:
            title = id_to_title_map.get(item_id, "Unknown Title")
            listbox.insert(tk.END, f"{prefix} {title}")

    def display_results(self):
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        
        if self.last_results.empty:
            self.results_text.insert(tk.END, "No recommendations found.")
            self.results_text.config(state=tk.DISABLED)
            return

        for i, row in self.last_results.iterrows():
            item_id, title = row['item_id'], row['title']
            self.results_text.insert(tk.END, f"📚 {title}\n", ("title",))
            self.results_text.insert(tk.END, f"   Provider: {row.get('provider', 'N/A')} | Level: {row.get('level', 'N/A')}\n")
            scores = [f"{lbl}: {row[col]:.3f}" for col, lbl in [('combined_score', 'Hybrid'), ('sbert_score', 'SBERT'), ('two_tower_score', 'Two-Tower'), ('tfidf_score', 'TF-IDF')] if col in row and pd.notna(row[col]) and row[col] > 0]
            if scores: self.results_text.insert(tk.END, f"   🤖 AI Scores: {' | '.join(scores)}\n")

            # --- Button Frame ---
            button_frame = tk.Frame(self.results_text, bg=self.results_text.cget('bg'))
            ttk.Button(button_frame, text="Like 👍", command=lambda i=item_id, t=title: self.add_to_liked_history(i, t)).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Dislike 👎", command=lambda i=item_id, t=title: self.add_to_disliked_history(i, t)).pack(side=tk.LEFT)
            self.results_text.window_create(tk.END, window=button_frame)
            self.results_text.insert(tk.END, "\n\n" + "-"*80 + "\n\n")

        self.results_text.tag_config("title", font=('Arial', 11, 'bold'))
        self.results_text.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    # Apply a modern theme
    style = ttk.Style(root)
    try:
        # 'clam' is a good cross-platform theme
        style.theme_use('clam')
    except tk.TclError:
        print("Clam theme not available, using default.")
    
    app = InteractiveRecommenderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 