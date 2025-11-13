import pandas as pd
from deep_translator import GoogleTranslator
import time
import re
import ast

# --- Main script execution ---

# 1. Load your English dataset
try:
    df = pd.read_csv('laptop_test.csv')
    print(f"Successfully loaded {len(df)} rows from .csv file")
except FileNotFoundError:
    print("Error: .csv file not found. Please check the filename.")
    exit()

# 2. Prepare data
df['aspect_terms'] = df['aspect_terms'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else [])

# 3. Prepare sentences with placeholders
print("Preparing sentences with placeholders...")
sentences_to_translate = []
placeholder_maps = []

for index, row in df.iterrows():
    sentence = row['sentence']
    aspect_terms = row['aspect_terms']
    
    if not isinstance(sentence, str) or not sentence.strip():
        sentences_to_translate.append("")
        placeholder_maps.append({})
        continue

    sorted_terms = sorted(aspect_terms, key=len, reverse=True)
    placeholder_map = {}
    temp_sentence = sentence
    
    for i, term in enumerate(sorted_terms):
        placeholder = f"__TERM{i}__"
        temp_sentence = re.sub(r'\b' + re.escape(term) + r'\b', placeholder, temp_sentence, flags=re.IGNORECASE)
        placeholder_map[placeholder] = term
        
    sentences_to_translate.append(temp_sentence)
    placeholder_maps.append(placeholder_map)

# 4. Translate sentences in chunks using deep-translator
print(f"Preparing to translate {len(sentences_to_translate)} sentences...")
translated_texts = []
chunk_size = 100
sleep_between_chunks = 1 # deep-translator is often more stable, so we can be a bit faster

for i in range(0, len(sentences_to_translate), chunk_size):
    chunk = sentences_to_translate[i:i + chunk_size]
    
    current_chunk_num = (i // chunk_size) + 1
    total_chunks = (len(sentences_to_translate) + chunk_size - 1) // chunk_size
    print(f"Translating chunk {current_chunk_num}/{total_chunks}...")
    
    try:
        # Use deep-translator's batch translation
        translated_chunk = GoogleTranslator(source='en', target='hi').translate_batch(chunk)
        translated_texts.extend(translated_chunk)
    except Exception as e:
        print(f"  - Error on chunk {current_chunk_num}: {e}. Falling back to original English for this chunk.")
        translated_texts.extend(chunk)

    time.sleep(sleep_between_chunks)

print("Batch translation successful.")

# 5. Substitute original terms back
print("Substituting original terms back into translated sentences...")
final_sentences = []
for i, translated_sentence in enumerate(translated_texts):
    if translated_sentence is None: # Add a check for None in case the API fails a single sentence
        final_sentences.append(sentences_to_translate[i]) # Fallback to placeholder sentence
        continue

    placeholder_map = placeholder_maps[i]
    final_sentence = translated_sentence
    
    for placeholder, original_term in sorted(placeholder_map.items(), key=lambda item: item[0]):
        final_sentence = final_sentence.replace(placeholder, original_term)
        
    final_sentences.append(final_sentence)

# 6. Create and save the final DataFrame
df['sentence'] = final_sentences
final_df = df[['sentence', 'aspect_terms', 'at_polarity']]

output_filename = 'laptop_test_hinglish.csv'
final_df.to_csv(output_filename, index=False)

print(f"\nTranslation complete! New file saved as '{output_filename}'")