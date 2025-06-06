import tkinter as tk
from tkinter import ttk, scrolledtext
import pandas as pd
from recommender_interface_advanced_v6 import get_hybrid_recommendations_advanced

class SimpleEnhancedGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 Enhanced Course Recommender System")
        self.root.geometry("900x650")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Header
        header_label = ttk.Label(main_frame, text="🚀 AI-Powered Course Recommender", font=('Arial', 16, 'bold'))
        header_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))
        
        subtitle_label = ttk.Label(main_frame, text="Enhanced with Semantic Matching, Diversity & Personalization", font=('Arial', 10), foreground='blue')
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 20))
        
        row = 2
        
        # Query input
        ttk.Label(main_frame, text="🔍 Search Query:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.query_entry = ttk.Entry(main_frame, width=60, font=('Arial', 10))
        self.query_entry.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # Level selection
        ttk.Label(main_frame, text="📈 Experience Level:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.level_var = tk.StringVar(value="All Levels")
        level_combo = ttk.Combobox(main_frame, textvariable=self.level_var, font=('Arial', 10))
        level_combo['values'] = ('All Levels', 'Beginner', 'Intermediate', 'Advanced')
        level_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # Skills input
        ttk.Label(main_frame, text="💼 Skills (comma-separated):", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.skills_entry = ttk.Entry(main_frame, width=60, font=('Arial', 10))
        self.skills_entry.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # Duration preference
        ttk.Label(main_frame, text="⏱️ Duration Preference:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.duration_var = tk.StringVar(value="any")
        duration_combo = ttk.Combobox(main_frame, textvariable=self.duration_var, font=('Arial', 10))
        duration_combo['values'] = ('any', 'short', 'medium', 'long')
        duration_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # Model selection
        ttk.Label(main_frame, text="🤖 AI Model:", font=('Arial', 10, 'bold')).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        self.model_var = tk.StringVar(value="hybrid")
        model_combo = ttk.Combobox(main_frame, textvariable=self.model_var, font=('Arial', 10))
        model_combo['values'] = ('hybrid', 'tfidf', 'sbert', 'two_tower')
        model_combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        row += 1
        
        # Features info
        features_info = ttk.Label(main_frame, text="✨ All AI enhancements enabled: Semantic Skills • Diversity • Personalization", 
                                foreground='green', font=('Arial', 9))
        features_info.grid(row=row, column=0, columnspan=3, pady=10)
        row += 1
        
        # Search button
        search_button = ttk.Button(main_frame, text="🔍 Search Enhanced Recommendations", command=self.search)
        search_button.grid(row=row, column=0, columnspan=3, pady=10)
        row += 1
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready to search...")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_label.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Results area
        ttk.Label(main_frame, text="📚 Enhanced Recommendations:").grid(row=row, column=0, sticky=tk.W, pady=(5,0))
        row += 1
        self.results_text = scrolledtext.ScrolledText(main_frame, width=90, height=25, font=('Consolas', 9))
        self.results_text.grid(row=row, column=0, columnspan=3, pady=5)
        
    def search(self):
        try:
            self.status_var.set("🔄 Searching with AI enhancements...")
            self.root.update()
            
            # Get input values
            query = self.query_entry.get().strip()
            level = self.level_var.get()
            skills_input = self.skills_entry.get().strip()
            skills = [s.strip().lower() for s in skills_input.split(',')] if skills_input else None
            duration = self.duration_var.get()
            model_type = self.model_var.get()
            
            print(f"🔍 Enhanced Search: query='{query}', skills={skills}, level={level}")
            
            # Get recommendations with ALL enhancements enabled
            results = get_hybrid_recommendations_advanced(
                query_text=query if query else None,
                level=level if level != 'All Levels' else None,
                skills=skills,
                duration_pref=duration if duration != 'any' else None,
                model_type=model_type,
                top_n=5,
                enable_diversity=True,
                enable_fuzzy_skills=True,
                enable_personalization=True
            )
            
            # Display results
            self.display_results(results, query, skills, level)
            
        except Exception as e:
            self.status_var.set(f"❌ Error: {str(e)}")
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"An error occurred: {str(e)}")
            print(f"Error in search: {e}")
            
    def display_results(self, results, query, skills, level):
        self.results_text.delete(1.0, tk.END)
        
        if results.empty:
            self.status_var.set("❌ No recommendations found")
            self.results_text.insert(tk.END, "🚫 No recommendations found.\n\n")
            self.results_text.insert(tk.END, "💡 Try these suggestions:\n")
            self.results_text.insert(tk.END, "• Broaden your search terms\n")
            self.results_text.insert(tk.END, "• Try different skill keywords\n")
            self.results_text.insert(tk.END, "• Change experience level to 'All Levels'\n")
        else:
            self.status_var.set(f"✅ Found {len(results)} enhanced recommendations")
            
            # Header
            self.results_text.insert(tk.END, f"🎯 ENHANCED AI SEARCH RESULTS ({len(results)} courses)\n")
            self.results_text.insert(tk.END, f"🤖 AI Features Active: Semantic Matching ✓ • Diversity ✓ • Personalization ✓\n")
            self.results_text.insert(tk.END, "=" * 85 + "\n\n")
            
            for i, (_, row) in enumerate(results.iterrows(), 1):
                # Course header
                self.results_text.insert(tk.END, f"📚 {i}. {row['title']}\n")
                self.results_text.insert(tk.END, f"🏢 Provider: {row['provider'] if pd.notna(row['provider']) else 'N/A'}\n")
                self.results_text.insert(tk.END, f"📈 Level: {row['level'] if pd.notna(row['level']) else 'N/A'}\n")
                
                # Enhanced skills display
                if 'skills_list' in row and row['skills_list'] and isinstance(row['skills_list'], list):
                    skills_str = ", ".join(row['skills_list'][:5])
                    if len(row['skills_list']) > 5:
                        skills_str += f" (+{len(row['skills_list'])-5} more)"
                    self.results_text.insert(tk.END, f"💼 Skills: {skills_str}\n")
                
                # Course quality indicators  
                rating = row['adjusted_rating']
                if pd.notna(rating) and isinstance(rating, (int, float)):
                    self.results_text.insert(tk.END, f"⭐ Rating: {rating:.2f}\n")
                else:
                    self.results_text.insert(tk.END, f"⭐ Rating: N/A\n")
                
                duration = row['duration']
                if pd.notna(duration):
                    self.results_text.insert(tk.END, f"⏱️ Duration: {duration} hours\n")
                else:
                    self.results_text.insert(tk.END, f"⏱️ Duration: N/A\n")
                
                # NEW: Enhanced difficulty display
                if 'difficulty_score' in row and pd.notna(row['difficulty_score']):
                    difficulty = row['difficulty_score']
                    if difficulty <= 2:
                        difficulty_display = "🟢 Easy"
                    elif difficulty <= 3.5:
                        difficulty_display = "🟡 Medium"
                    else:
                        difficulty_display = "🔴 Advanced"
                    self.results_text.insert(tk.END, f"🎯 Difficulty: {difficulty_display} ({difficulty:.1f}/5.0)\n")
                
                # Enhanced AI scoring display
                score_info = []
                for score_col, score_label in [('tfidf_score', 'TF-IDF'), ('sbert_score', 'SBERT'), 
                                              ('two_tower_score', 'Two-Tower'), ('combined_score', 'Combined')]:
                    if score_col in row and pd.notna(row[score_col]):
                        score_val = row[score_col]
                        if isinstance(score_val, (int, float)) and score_val > 0:
                            score_info.append(f"{score_label}: {score_val:.3f}")
                
                if score_info:
                    self.results_text.insert(tk.END, f"🤖 AI Scores: {' | '.join(score_info)}\n")
                
                # Description
                if 'description' in row and pd.notna(row['description']):
                    desc = str(row['description'])
                    if len(desc) > 200:
                        desc = desc[:200] + "..."
                    self.results_text.insert(tk.END, f"📝 Description: {desc}\n")
                
                # URL
                self.results_text.insert(tk.END, f"🔗 URL: {row['url'] if pd.notna(row['url']) else 'N/A'}\n")
                self.results_text.insert(tk.END, "\n" + "-" * 85 + "\n\n")

def main():
    root = tk.Tk()
    app = SimpleEnhancedGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 