import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pandas as pd
from recommender_interface_advanced_v6 import get_recommendations
import webbrowser

class InteractiveRecommenderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 INTERACTIVE Course Recommender")
        self.root.geometry("1200x850")
        
        self.user_history = [] # Stores item_id strings
        self.history_details = {} # Maps item_id to title for display
        self.displayed_recs = pd.DataFrame() # Store the last recommendations

        # Main layout
        main_paned_window = ttk.PanedWindow(root, orient=tk.VERTICAL)
        main_paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top pane: controls and history
        top_frame = ttk.Frame(main_paned_window, padding=5)
        main_paned_window.add(top_frame, weight=1)

        top_paned_window = ttk.PanedWindow(top_frame, orient=tk.HORIZONTAL)
        top_paned_window.pack(fill=tk.BOTH, expand=True)

        # Left side: Search controls
        controls_frame = ttk.LabelFrame(top_paned_window, text="🔍 Search Controls", padding=10)
        top_paned_window.add(controls_frame, weight=2)
        self.setup_controls_tab(controls_frame)

        # Right side: Session history
        history_frame = ttk.LabelFrame(top_paned_window, text="👤 Session History (click recommendations to add)", padding=10)
        top_paned_window.add(history_frame, weight=1)
        self.setup_history_tab(history_frame)

        # Bottom pane: Recommendations
        results_frame = ttk.LabelFrame(main_paned_window, text="📚 Recommendations", padding=10)
        main_paned_window.add(results_frame, weight=2)
        self.setup_results_tab(results_frame)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready...")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)


    def setup_controls_tab(self, frame):
        # Configure grid
        frame.columnconfigure(1, weight=1)
        
        row = 0
        # Query
        ttk.Label(frame, text="Search Query:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.query_entry = ttk.Entry(frame, width=40)
        self.query_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        row += 1

        # Level
        ttk.Label(frame, text="Level:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.level_var = tk.StringVar(value="All Levels")
        level_combo = ttk.Combobox(frame, textvariable=self.level_var, values=('All Levels', 'Beginner', 'Intermediate', 'Advanced'))
        level_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        row += 1

        # Skills
        ttk.Label(frame, text="Skills:").grid(row=row, column=0, sticky=tk.W, pady=2)
        self.skills_entry = ttk.Entry(frame)
        self.skills_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=2)
        row += 1

        # AI Enhancements (always on for this GUI)
        ttk.Label(frame, text="AI Features:", font=('Arial', 9, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=(10,0))
        ttk.Label(frame, text="Diversity, Personalization, Semantic Matching are ENABLED", foreground='blue').grid(row=row, column=1, sticky=tk.W, pady=(10,0))
        row += 1

        # Search Button
        search_button = ttk.Button(frame, text="Search / Refresh", command=self.search)
        search_button.grid(row=row, column=0, columnspan=2, pady=10)


    def setup_history_tab(self, frame):
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        
        self.history_listbox = tk.Listbox(frame, height=10)
        self.history_listbox.grid(row=0, column=0, sticky="nsew", columnspan=2)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.history_listbox.yview)
        scrollbar.grid(row=0, column=2, sticky="ns")
        self.history_listbox.config(yscrollcommand=scrollbar.set)
        
        clear_button = ttk.Button(frame, text="Clear History", command=self.clear_history)
        clear_button.grid(row=1, column=0, columnspan=3, pady=5)

    def setup_results_tab(self, frame):
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.results_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=('Consolas', 9))
        self.results_text.grid(row=0, column=0, sticky="nsew")
        # Prevent user from typing in the results area, which allows clicks to still register
        self.results_text.bind("<KeyPress>", lambda e: "break")
    
    def search(self, from_history_update=False):
        try:
            self.status_var.set("🔄 Searching...")
            self.root.update_idletasks()

            query = self.query_entry.get().strip()
            level = self.level_var.get()
            skills_input = self.skills_entry.get().strip()
            skills = [s.strip().lower() for s in skills_input.split(',')] if skills_input else None

            if not query and not self.user_history:
                messagebox.showwarning("Input Needed", "Please provide a search query or add items to your history first.")
                self.status_var.set("Ready")
                return

            if from_history_update:
                print("Refreshing recommendations based on updated history...")
            else:
                print(f"Executing new search: query='{query}', skills={skills}, level={level}")

            results = get_recommendations(
                query_text=query,
                level=level if level != 'All Levels' else None,
                skills=skills,
                top_n=10, # Get more to show variety
                user_history=self.user_history,
            )
            
            self.displayed_recs = results.copy()
            self.display_results(results)
            self.status_var.set(f"✅ Found {len(results)} recommendations. Click title to add to history.")

        except Exception as e:
            self.status_var.set(f"❌ Error: {e}")
            messagebox.showerror("Error", f"An error occurred during search: {e}")

    def add_to_history(self, event):
        # Get item from the text widget tag
        try:
            # Get the index of the mouse click for robustness
            index = self.results_text.index(f"@{event.x},{event.y}")

            # Find the first tag that looks like our item_id tag
            item_id = None
            tags = self.results_text.tag_names(index)
            for tag in tags:
                if tag.startswith("item-"):
                    item_id = tag.split("-", 1)[1]
                    break
            
            if not item_id:
                return

            if item_id in self.user_history:
                self.status_var.set(f"Item is already in history.")
                return

            title = self.history_details[item_id]
            self.user_history.append(item_id)
            
            self.history_listbox.insert(tk.END, f"• {title}")
            self.history_listbox.yview(tk.END)
            
            self.status_var.set(f"Added '{title[:30]}...' to history. Refreshing...")
            self.search(from_history_update=True)

        except Exception as e:
            print(f"Error adding to history: {e}")

    def clear_history(self):
        self.user_history.clear()
        self.history_details.clear()
        self.history_listbox.delete(0, tk.END)
        self.status_var.set("History cleared. Refreshing recommendations...")
        self.search(from_history_update=True)

    def display_results(self, results):
        self.results_text.config(state="normal")
        self.results_text.delete(1.0, tk.END)
        self.history_details.clear()

        if results.empty:
            self.results_text.insert(tk.END, "🚫 No recommendations found for your criteria.")
            return
            
        for _, row in results.iterrows():
            item_id = row['item_id']
            title = row['title']
            self.history_details[item_id] = title
            
            # --- Define clickable tag for the title ---
            title_tag = f"item-{item_id}"
            
            # Header
            self.results_text.insert(tk.END, f"📚 {title}\n", (title_tag, "title_font"))
            self.results_text.tag_config(title_tag, foreground="blue", underline=True)
            self.results_text.tag_bind(title_tag, "<Button-1>", self.add_to_history)
            self.results_text.tag_bind(title_tag, "<Enter>", lambda e, t=title_tag: self.results_text.config(cursor="hand2"))
            self.results_text.tag_bind(title_tag, "<Leave>", lambda e, t=title_tag: self.results_text.config(cursor=""))
            self.results_text.tag_config("title_font", font=('Arial', 11, 'bold'))

            # Details
            details = (
                f"   - ID: {item_id}\n"
                f"   - Provider: {row.get('provider', 'N/A')}\n"
                f"   - Level: {row.get('level', 'N/A')}\n"
                f"   - Rating: {row.get('adjusted_rating', 0):.2f} | Duration: {row.get('duration', 'N/A')}h\n"
            )
            self.results_text.insert(tk.END, details)

            # Scores
            scores = []
            for col, label in [('two_tower_score', 'Personalized'), ('sbert_score', 'Semantic'), ('combined_score', 'Hybrid')]:
                if col in row and pd.notna(row[col]) and row[col] > 0:
                    scores.append(f"{label}: {row[col]:.3f}")
            if scores:
                self.results_text.insert(tk.END, f"   - AI Scores: {' | '.join(scores)}\n")

            # URL
            url = row.get('url')
            if pd.notna(url):
                url_tag = f"url-{item_id}"
                self.results_text.insert(tk.END, f"   - URL: ", "link_label")
                self.results_text.insert(tk.END, f"{url}\n", (url_tag, "link_url"))
                self.results_text.tag_config(url_tag, foreground="darkgreen", underline=True)
                self.results_text.tag_bind(url_tag, "<Button-1>", lambda e, link=url: webbrowser.open_new(link))
            
            self.results_text.insert(tk.END, "-"*90 + "\n\n")

        # The text area is made non-editable by the KeyPress binding, so we don't disable it,
        # ensuring the clickable links remain active.


def main():
    try:
        root = tk.Tk()
        app = InteractiveRecommenderGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Failed to launch GUI: {e}")
        messagebox.showerror("Application Error", f"A critical error occurred on startup:\n\n{e}\n\nPlease check the console for details.")

if __name__ == "__main__":
    print("Launching Interactive Recommender GUI...")
    main() 