# Learning Platform Recommender System

A sophisticated recommender system for learning platforms that combines content-based filtering and two-tower neural network approaches to provide personalized course recommendations.

## Features

- Content-based filtering using TF-IDF and SBERT embeddings
- Two-tower neural network model for personalized recommendations
- Hybrid recommendation approach combining multiple strategies
- Advanced evaluation metrics and analysis
- GUI interface for easy interaction
- Cold-start handling strategies

## Project Structure

- `adapted_two_tower_model.py`: Implementation of the two-tower neural network model
- `evaluate_two_tower.py`: Evaluation scripts for the recommender system
- `recommender_interface_advanced_v6.py`: Core recommendation logic and interface
- `hybrid_recommender_logic.py`: Implementation of hybrid recommendation approach
- `sbert_recommender_component.py`: SBERT-based content filtering component
- `recommender_gui.py`: GUI interface for the recommender system

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Download the required model files:
- `two_tower.weights.h5`: Pre-trained two-tower model weights
- `tfidf_vectorizer.pkl`: TF-IDF vectorizer for content-based filtering
- `training_history.pkl`: Training history for the model

3. Run the GUI:
```bash
python recommender_gui.py
```

## Data

The system uses processed course data from the `cleaned_courses_with_enhanced_skills.csv` file, which contains:
- Course titles and descriptions
- Enhanced skill tags
- Course metadata
- User interaction data

## Model Architecture

The recommender system uses a hybrid approach combining:
1. Content-based filtering using TF-IDF and SBERT embeddings
2. Two-tower neural network for personalized recommendations
3. Hybrid logic to combine and rank recommendations

## Documentation

Detailed documentation can be found in the following markdown files:
- `recommender_systems_fundamentals_part1.md` through `part4.md`
- `implementation_suggestions.md`
- `recommender_enhancement_summary.md`

## License

This project is licensed under the MIT License - see the LICENSE file for details. 